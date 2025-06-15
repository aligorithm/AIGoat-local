import datetime
import logging
import requests
import os
import random
import json
import base64
from functools import wraps
from io import BytesIO
from PIL import Image
import jwt
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from models import Product, Category, User, db, Comment, product_categories
from local_ml_service import MLService
from local_storage import LocalStorage

from flask_cors import CORS

# Configure logging
log_handler = logging.StreamHandler()
log_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)

class FlushHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'a_secret_key_that_you_should_change')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

CORS(app, resources={r"/*": {"origins": "*"}})
logging.basicConfig(level=logging.DEBUG)
app.logger.addHandler(FlushHandler())

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Initialize services
storage = LocalStorage()
ml_service = MLService()

# Dummy user data
users = {
    'babyshark': 'doodoo123'
}

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization').split(" ")[1] if 'Authorization' in request.headers else None
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['username']
        except:
            return jsonify({'message': 'Token is invalid!'}), 403

        return f(current_user, *args, **kwargs)

    return decorated

user_carts = {
    'babyshark': []
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

def get_product_by_id(product_id):
    return Product.query.get(product_id)

def get_products_by_ids(ids, products):
    id_list = [int(id_str) for id_str in ids.split(',')]
    result = [product for product in products if product.id in id_list]
    return result

@app.route('/')
def home():
    return "Welcome to the AI Goat Store!"

@app.route('/api/recommendations', methods=['GET'])
@token_required
def get_recommendations(current_user):
    user = User.query.filter_by(username=current_user).first_or_404()
    
    try:
        # Use local ML service for recommendations
        recommended_products_ids = ml_service.get_recommendations(user.id)
        recommended_products_ids = recommended_products_ids[:4]
        
        user.recommendations = recommended_products_ids
        db.session.commit()
        
        recommended_products = Product.query.filter(Product.id.in_(recommended_products_ids)).all()
        
        for product_id in recommended_products_ids:
            product = Product.query.get(product_id)
            if product:
                logging.info(f"Product ID {product_id} exists in database: {product.to_dict()}")
            else:
                logging.info(f"Product ID {product_id} does not exist in database")

        return jsonify([p.to_dict() for p in recommended_products])
    except Exception as e:
        logging.error(f"Error getting recommendations: {e}")
        return jsonify({'error': f'Failed to get recommendations: {str(e)}'}), 500

@app.route('/api/cart', methods=['GET'])
@token_required
def get_cart(current_user):
    try:
        user = User.query.filter_by(username=current_user).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        cart_products = Product.query.filter(Product.id.in_(user.cart)).all()
        cart_products_serialized = [product.to_dict() for product in cart_products]

        return jsonify(cart_products_serialized)
    except Exception as e:
        logging.error(f'Error fetching cart: {e}')
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        if username in users and users[username] == password:
            token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, app.config['SECRET_KEY'], algorithm="HS256")
            logging.info(token)
            return jsonify({'message': 'Login successful for {"user_id": 1}', 'token': token})
        return jsonify({'message': 'Invalid credentials'}), 401
    except Exception as e:
        logging.error(f'Error during login: {e}')
        print(f'Error during login: {e}')
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/api/analyze-photo', methods=['OPTIONS', 'POST'])
def product_lookup():
    if request.method == 'OPTIONS':
        return '', 204

    matched_products = []
    if request.method == 'POST':
        try:
            app.logger.info('Processing image upload for product similarity')
            
            if 'image' not in request.files:
                return jsonify({'error': 'No image file provided'}), 400
            
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if file and allowed_file(file.filename):
                # Save uploaded image
                image_data = file.read()
                filename = storage.save_upload(file.filename, image_data)
                
                # Use ML service for image analysis
                similar_products = ml_service.find_similar_products(image_data)
                
                # Get product details from database
                product_ids = [p['product_id'] for p in similar_products]
                products = Product.query.filter(Product.id.in_(product_ids)).all()
                
                matched_products = [p.to_dict() for p in products]
                
                return jsonify({
                    'matched_products': matched_products,
                    'upload_filename': filename
                })
            else:
                return jsonify({'error': 'Invalid file type'}), 400
                
        except Exception as e:
            app.logger.error(f'Error in product lookup: {e}')
            return jsonify({'error': f'Error processing image: {str(e)}'}), 500

    return jsonify({'matched_products': matched_products})

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/products/categories', methods=['GET'])
def fetch_categories():
    categories = Category.query.all()
    return jsonify([category.to_dict() for category in categories])

@app.route('/products', methods=['GET'])
def fetch_products():
    # Get the 'ids' parameter from the request
    ids = request.args.get('ids')
    
    if ids:
        # If 'ids' parameter is provided, filter products by those IDs
        products = get_products_by_ids(ids, Product.query.all())
    else:
        # If no 'ids' parameter, return all products
        products = Product.query.all()
    
    return jsonify([product.to_dict() for product in products])

@app.route('/products/categories/<int:category_id>', methods=['GET'])
def fetch_category_by_id(category_id):
    category = Category.query.get_or_404(category_id)
    products = Product.query.filter(Product.categories.contains(category)).all()
    return jsonify([product.to_dict() for product in products])

@app.route('/products/<int:product_id>/comments', methods=['POST'])
def add_product_comment(product_id):
    try:
        data = request.json
        content = data.get('content', '')
        
        # Use ML service for content filtering
        is_allowed = ml_service.filter_content(content)
        
        if not is_allowed:
            return jsonify({'error': 'Comment blocked by content filter'}), 400
        
        product = Product.query.get_or_404(product_id)
        
        new_comment = Comment(content=content, product_id=product_id)
        db.session.add(new_comment)
        db.session.commit()
        
        return jsonify({
            'message': 'Comment added successfully',
            'comment': new_comment.to_dict()
        })
        
    except Exception as e:
        logging.error(f'Error adding comment: {e}')
        return jsonify({'error': f'Failed to add comment: {str(e)}'}), 500

@app.route('/products/<int:product_id>/comments', methods=['GET'])
def fetch_product_comments(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        comments = Comment.query.filter_by(product_id=product_id).all()
        return jsonify([comment.to_dict() for comment in comments])
    except Exception as e:
        logging.error(f'Error fetching comments: {e}')
        return jsonify({'error': f'Failed to fetch comments: {str(e)}'}), 500

@app.route('/products/<int:product_id>', methods=['GET'])
def fetch_product_by_id(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

# Hint endpoints
@app.route('/hints/challenge1/1', methods=['GET'])
def hint_1_1():
    return jsonify({'hint': 'Look for file upload vulnerabilities in the image analysis endpoint'})

@app.route('/hints/challenge1/2', methods=['GET'])
def hint_1_2():
    return jsonify({'hint': 'Check what happens when you upload different file types'})

@app.route('/hints/challenge1/3', methods=['GET'])
def hint_1_3():
    return jsonify({'hint': 'The sensitive data might be stored in a predictable location'})

@app.route('/hints/challenge2/1', methods=['GET'])
def hint_2_1():
    return jsonify({'hint': 'User recommendations are based on training data - can you influence it?'})

@app.route('/hints/challenge2/2', methods=['GET'])
def hint_2_2():
    return jsonify({'hint': 'Check if you can upload your own training data'})

@app.route('/hints/challenge2/3', methods=['GET'])
def hint_2_3():
    return jsonify({'hint': 'Look for the Orca Doll in the recommendation dataset'})

@app.route('/hints/challenge3/1', methods=['GET'])
def hint_3_1():
    return jsonify({'hint': 'Content filters can sometimes be bypassed with clever prompting'})

@app.route('/hints/challenge3/2', methods=['GET'])
def hint_3_2():
    return jsonify({'hint': 'Try different variations of the forbidden word'})

@app.route('/hints/challenge3/3', methods=['GET'])
def hint_3_3():
    return jsonify({'hint': 'AI systems can be fooled by encoding or obfuscation techniques'})

def initialize_data():
    """Initialize database and storage on startup"""
    try:
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Check if data already exists
            if Product.query.first() is None:
                logging.info("Initializing database with sample data...")
                # Import and run migration
                from migrate_data_local import migrate_data
                migrate_data()
                logging.info("Database initialization complete!")
            
            # Initialize storage buckets
            storage.initialize_buckets()
            logging.info("Storage initialization complete!")
            
    except Exception as e:
        logging.error(f"Error during initialization: {e}")

if __name__ == '__main__':
    initialize_data()
    app.run(host='0.0.0.0', port=5000, debug=True) 