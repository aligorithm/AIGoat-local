import json
import logging
from datetime import datetime
from models import db, Product, Category, User, Comment, product_categories
from sqlalchemy.exc import IntegrityError

def migrate_data():
    """Migrate data to local database"""
    try:
        logging.info("Starting local data migration...")
        
        # Create tables
        db.create_all()
        
        # Load and migrate categories
        migrate_categories()
        
        # Load and migrate products
        migrate_products()
        
        # Create sample users
        migrate_users()
        
        # Create sample comments
        migrate_comments()
        
        logging.info("Local data migration completed successfully!")
        
    except Exception as e:
        logging.error(f"Error during local migration: {e}")
        raise

def migrate_categories():
    """Migrate categories data"""
    try:
        # Check if categories already exist
        if Category.query.first():
            logging.info("Categories already exist, skipping...")
            return
            
        # Load categories from JSON file
        with open('categories.json', 'r') as f:
            categories_data = json.load(f)
        
        for cat_data in categories_data:
            try:
                category = Category(
                    id=cat_data['id'],
                    name=cat_data['name'],
                    slug=cat_data['slug'],
                    parent=cat_data.get('parent', 0),
                    description=cat_data.get('description', ''),
                    display=cat_data.get('display', 'default'),
                    image_id=cat_data.get('image', {}).get('id'),
                    image_src=cat_data.get('image', {}).get('src', ''),
                    image_name=cat_data.get('image', {}).get('name', ''),
                    image_alt=cat_data.get('image', {}).get('alt', ''),
                    menu_order=cat_data.get('menu_order', 0),
                    count=cat_data.get('count', 0)
                )
                
                db.session.add(category)
                
            except IntegrityError:
                db.session.rollback()
                logging.warning(f"Category {cat_data['id']} already exists")
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error creating category {cat_data.get('id', 'unknown')}: {e}")
        
        db.session.commit()
        logging.info(f"Successfully migrated {len(categories_data)} categories")
        
    except Exception as e:
        logging.error(f"Error migrating categories: {e}")
        raise

def migrate_products():
    """Migrate products data"""
    try:
        # Check if products already exist
        if Product.query.first():
            logging.info("Products already exist, skipping...")
            return
            
        # Load products from JSON file
        with open('products.json', 'r') as f:
            products_data = json.load(f)
        
        for prod_data in products_data:
            try:
                # Convert date strings to datetime objects
                date_created = datetime.fromisoformat(prod_data['date_created'].replace('Z', '+00:00'))
                date_modified = datetime.fromisoformat(prod_data['date_modified'].replace('Z', '+00:00'))
                
                product = Product(
                    id=prod_data['id'],
                    name=prod_data['name'],
                    slug=prod_data['slug'],
                    permalink=prod_data['permalink'],
                    date_created=date_created,
                    date_created_gmt=date_created,
                    date_modified=date_modified,
                    date_modified_gmt=date_modified,
                    type=prod_data['type'],
                    status=prod_data['status'],
                    featured=prod_data['featured'],
                    catalog_visibility=prod_data['catalog_visibility'] != 'hidden',
                    description=prod_data['description'],
                    short_description=prod_data['short_description'],
                    sku=prod_data['sku'],
                    price=float(prod_data['price']) if prod_data['price'] else 0.0,
                    regular_price=float(prod_data['regular_price']) if prod_data['regular_price'] else 0.0,
                    sale_price=float(prod_data['sale_price']) if prod_data['sale_price'] else None,
                    price_html=prod_data.get('price_html', ''),
                    on_sale=prod_data['on_sale'],
                    purchasable=prod_data['purchasable'],
                    total_sales=prod_data.get('total_sales', 0),
                    virtual=prod_data['virtual'],
                    downloadable=prod_data['downloadable'],
                    downloads=prod_data.get('downloads', []),
                    download_limit=prod_data.get('download_limit', 0),
                    download_expiry=prod_data.get('download_expiry', 0),
                    external_url=prod_data.get('external_url', ''),
                    button_text=prod_data.get('button_text', ''),
                    tax_status=prod_data.get('tax_status', 'taxable'),
                    tax_class=prod_data.get('tax_class', ''),
                    manage_stock=prod_data['manage_stock'],
                    stock_quantity=prod_data.get('stock_quantity'),
                    stock_status=prod_data['stock_status'],
                    backorders=prod_data.get('backorders', 'no'),
                    backorders_allowed=prod_data.get('backorders_allowed', False),
                    backordered=prod_data.get('backordered', False),
                    sold_individually=prod_data['sold_individually'],
                    weight=prod_data.get('weight', ''),
                    dimensions=prod_data.get('dimensions', {}),
                    shipping_required=prod_data['shipping_required'],
                    shipping_taxable=prod_data['shipping_taxable'],
                    shipping_class=prod_data.get('shipping_class', ''),
                    shipping_class_id=prod_data.get('shipping_class_id', 0),
                    reviews_allowed=prod_data['reviews_allowed'],
                    average_rating=float(prod_data.get('average_rating', 0.0)),
                    rating_count=prod_data.get('rating_count', 0),
                    parent_id=prod_data.get('parent_id', 0),
                    purchase_note=prod_data.get('purchase_note', ''),
                    tags=prod_data.get('tags', []),
                    images=prod_data.get('images', []),
                    attributes=prod_data.get('attributes', []),
                    default_attributes=prod_data.get('default_attributes', []),
                    variations=prod_data.get('variations', []),
                    grouped_products=prod_data.get('grouped_products', []),
                    meta_data=prod_data.get('meta_data', []),
                    acf=prod_data.get('acf', {})
                )
                
                db.session.add(product)
                
                # Add category associations
                if 'categories' in prod_data:
                    for cat_data in prod_data['categories']:
                        category = Category.query.get(cat_data['id'])
                        if category:
                            product.categories.append(category)
                
            except IntegrityError:
                db.session.rollback()
                logging.warning(f"Product {prod_data['id']} already exists")
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error creating product {prod_data.get('id', 'unknown')}: {e}")
        
        db.session.commit()
        logging.info(f"Successfully migrated {len(products_data)} products")
        
    except Exception as e:
        logging.error(f"Error migrating products: {e}")
        raise

def migrate_users():
    """Create sample users"""
    try:
        # Check if users already exist
        if User.query.first():
            logging.info("Users already exist, skipping...")
            return
            
        # Load user data
        with open('user_data.json', 'r') as f:
            users_data = json.load(f)
        
        for user_data in users_data:
            try:
                user = User(
                    id=user_data['id'],
                    username=user_data['username'],
                    cart=user_data.get('cart', []),
                    recommendations=user_data.get('recommendations', [])
                )
                
                db.session.add(user)
                
            except IntegrityError:
                db.session.rollback()
                logging.warning(f"User {user_data['username']} already exists")
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error creating user {user_data.get('username', 'unknown')}: {e}")
        
        db.session.commit()
        logging.info("Successfully migrated users")
        
    except Exception as e:
        logging.error(f"Error migrating users: {e}")
        raise

def migrate_comments():
    """Create sample comments"""
    try:
        # Create some sample comments for products
        sample_comments = [
            {"content": "Great toy for kids!", "product_id": 1},
            {"content": "Very educational and fun", "product_id": 2},
            {"content": "My child loves this!", "product_id": 3},
            {"content": "Good quality product", "product_id": 5},
        ]
        
        for comment_data in sample_comments:
            try:
                # Check if product exists
                product = Product.query.get(comment_data['product_id'])
                if product:
                    comment = Comment(
                        content=comment_data['content'],
                        product_id=comment_data['product_id']
                    )
                    db.session.add(comment)
                    
            except Exception as e:
                logging.error(f"Error creating comment: {e}")
        
        db.session.commit()
        logging.info("Successfully created sample comments")
        
    except Exception as e:
        logging.error(f"Error migrating comments: {e}")

if __name__ == '__main__':
    migrate_data() 