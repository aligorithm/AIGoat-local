import os
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

class LocalStorage:
    def __init__(self):
        self.endpoint_url = os.getenv('MINIO_ENDPOINT', 'http://minio:9000')
        self.access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        self.region = 'us-east-1'
        
        # Bucket names
        self.supply_chain_bucket = os.getenv('SUPPLY_CHAIN_BUCKET', 'supply-chain-bucket')
        self.data_poisoning_bucket = os.getenv('DATA_POISONING_BUCKET', 'data-poisoning-bucket')
        self.uploads_bucket = os.getenv('UPLOADS_BUCKET', 'uploads-bucket')
        
        # Initialize S3 client for MinIO
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            logging.info(f"Storage client initialized with MinIO endpoint: {self.endpoint_url}")
        except Exception as e:
            logging.error(f"Failed to initialize storage client: {e}")
            self.s3_client = None

    def initialize_buckets(self):
        """Create necessary buckets if they don't exist"""
        if not self.s3_client:
            logging.error("Storage client not initialized")
            return

        buckets_to_create = [
            self.supply_chain_bucket,
            self.data_poisoning_bucket,
            self.uploads_bucket
        ]
        
        for bucket_name in buckets_to_create:
            try:
                # Check if bucket exists
                self.s3_client.head_bucket(Bucket=bucket_name)
                logging.info(f"Bucket {bucket_name} already exists")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    # Bucket doesn't exist, create it
                    try:
                        self.s3_client.create_bucket(Bucket=bucket_name)
                        logging.info(f"Created bucket: {bucket_name}")
                        
                        # Initialize bucket with sample data
                        self._initialize_bucket_data(bucket_name)
                        
                    except Exception as create_error:
                        logging.error(f"Failed to create bucket {bucket_name}: {create_error}")
                else:
                    logging.error(f"Error checking bucket {bucket_name}: {e}")

    def _initialize_bucket_data(self, bucket_name: str):
        """Initialize bucket with sample data for the challenges"""
        try:
            if bucket_name == self.supply_chain_bucket:
                # Initialize supply chain data (product images metadata)
                sample_data = {
                    "product_images": {
                        "1": {"name": "teddy_bear.jpg", "features": [0.1, 0.2, 0.3, 0.4, 0.5]},
                        "2": {"name": "robot_toy.jpg", "features": [0.6, 0.7, 0.8, 0.9, 1.0]},
                        "25": {"name": "orca_doll.jpg", "features": [0.2, 0.4, 0.6, 0.8, 1.0]}
                    }
                }
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key='product_features.json',
                    Body=json.dumps(sample_data),
                    ContentType='application/json'
                )
                
            elif bucket_name == self.data_poisoning_bucket:
                # Initialize recommendation training data
                sample_data = {
                    "user_preferences": {
                        "1": {"liked_products": [1, 5, 12], "categories": ["toys", "educational"]},
                        "2": {"liked_products": [25, 18, 33], "categories": ["dolls", "animals"]}
                    },
                    "recommendation_model": "trained_model_v1.pkl"
                }
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key='training_data.json',
                    Body=json.dumps(sample_data),
                    ContentType='application/json'
                )
                
                # Add a vulnerable file that can be discovered
                sensitive_data = {
                    "user_recommendations_dataset": bucket_name,
                    "model_poisoning_possible": True,
                    "hidden_products": [25]  # Orca Doll
                }
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key='sensitive_data.txt',
                    Body=json.dumps(sensitive_data),
                    ContentType='application/json'
                )
                
            logging.info(f"Initialized sample data for bucket: {bucket_name}")
            
        except Exception as e:
            logging.error(f"Failed to initialize data for bucket {bucket_name}: {e}")

    def save_upload(self, filename: str, file_data: bytes) -> Optional[str]:
        """Save uploaded file to MinIO"""
        if not self.s3_client:
            logging.error("Storage client not initialized")
            return None
            
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{filename}"
            
            # Upload file
            self.s3_client.put_object(
                Bucket=self.uploads_bucket,
                Key=unique_filename,
                Body=file_data,
                ContentType='image/jpeg'
            )
            
            logging.info(f"Uploaded file: {unique_filename}")
            return unique_filename
            
        except Exception as e:
            logging.error(f"Failed to upload file {filename}: {e}")
            return None

    def get_file(self, bucket: str, key: str) -> Optional[bytes]:
        """Get file from MinIO"""
        if not self.s3_client:
            return None
            
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except Exception as e:
            logging.error(f"Failed to get file {key} from bucket {bucket}: {e}")
            return None

    def list_files(self, bucket: str, prefix: str = '') -> list:
        """List files in bucket"""
        if not self.s3_client:
            return []
            
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            return [obj['Key'] for obj in response.get('Contents', [])]
        except Exception as e:
            logging.error(f"Failed to list files in bucket {bucket}: {e}")
            return []

    def put_file(self, bucket: str, key: str, data: bytes, content_type: str = 'application/octet-stream') -> bool:
        """Put file to MinIO"""
        if not self.s3_client:
            return False
            
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=data,
                ContentType=content_type
            )
            return True
        except Exception as e:
            logging.error(f"Failed to put file {key} to bucket {bucket}: {e}")
            return False

    def get_presigned_url(self, bucket: str, key: str, expiration: int = 3600) -> Optional[str]:
        """Generate presigned URL for file access"""
        if not self.s3_client:
            return None
            
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logging.error(f"Failed to generate presigned URL for {key}: {e}")
            return None

    def delete_file(self, bucket: str, key: str) -> bool:
        """Delete file from MinIO"""
        if not self.s3_client:
            return False
            
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            return True
        except Exception as e:
            logging.error(f"Failed to delete file {key} from bucket {bucket}: {e}")
            return False

    def get_bucket_info(self) -> Dict[str, Any]:
        """Get information about configured buckets"""
        return {
            'endpoint': self.endpoint_url,
            'buckets': {
                'supply_chain': self.supply_chain_bucket,
                'data_poisoning': self.data_poisoning_bucket,
                'uploads': self.uploads_bucket
            }
        } 