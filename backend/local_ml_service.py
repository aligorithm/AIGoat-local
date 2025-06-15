import os
import json
import logging
import random
import base64
from typing import List, Dict, Any
from io import BytesIO
from PIL import Image

# AI provider imports
try:
    import ollama
except ImportError:
    ollama = None

try:
    import openai
except ImportError:
    openai = None

class MLService:
    def __init__(self):
        self.ai_provider = os.getenv('AI_PROVIDER', 'ollama')
        self.ollama_endpoint = os.getenv('OLLAMA_ENDPOINT', 'http://ollama:11434')
        self.ollama_model_image = os.getenv('OLLAMA_MODEL_IMAGE', 'llava')
        self.ollama_model_text = os.getenv('OLLAMA_MODEL_TEXT', 'llama3.1')
        
        # OpenAI configuration
        if self.ai_provider == 'openai':
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.openai_model_image = os.getenv('OPENAI_MODEL_IMAGE', 'gpt-4-vision-preview')
            self.openai_model_text = os.getenv('OPENAI_MODEL_TEXT', 'gpt-4-turbo')
        
        # Initialize Ollama client if using Ollama
        if self.ai_provider == 'ollama' and ollama:
            self.ollama_client = ollama.Client(host=self.ollama_endpoint)
        
        logging.info(f"ML Service initialized with provider: {self.ai_provider}")

    def find_similar_products(self, image_data: bytes) -> List[Dict[str, Any]]:
        """
        Challenge 1: Supply Chain Attack
        Find products similar to uploaded image
        """
        try:
            if self.ai_provider == 'ollama':
                return self._find_similar_products_ollama(image_data)
            elif self.ai_provider == 'openai':
                return self._find_similar_products_openai(image_data)
        except Exception as e:
            logging.error(f"Error in find_similar_products: {e}")
            # Fallback to dummy data for demo purposes
            return self._get_dummy_similar_products()

    def _find_similar_products_ollama(self, image_data: bytes) -> List[Dict[str, Any]]:
        """Use Ollama's vision model to analyze image and find similar products"""
        try:
            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            response = self.ollama_client.generate(
                model=self.ollama_model_image,
                prompt="""Analyze this image and identify what type of product it shows. 
                Return a JSON list of similar product IDs from a toy store catalog. 
                The product IDs should be integers between 1-50.
                Format: [{"product_id": 1, "similarity": 0.95}, {"product_id": 2, "similarity": 0.87}]""",
                images=[image_base64]
            )
            
            # Try to parse the response as JSON
            try:
                result = json.loads(response['response'])
                if isinstance(result, list):
                    return result[:5]  # Return top 5 similar products
            except:
                pass
            
            # Fallback if parsing fails
            return self._get_dummy_similar_products()
            
        except Exception as e:
            logging.error(f"Ollama image analysis error: {e}")
            return self._get_dummy_similar_products()

    def _find_similar_products_openai(self, image_data: bytes) -> List[Dict[str, Any]]:
        """Use OpenAI's vision model to analyze image and find similar products"""
        try:
            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            response = openai.ChatCompletion.create(
                model=self.openai_model_image,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this image and identify what type of product it shows. 
                                Return a JSON list of similar product IDs from a toy store catalog. 
                                The product IDs should be integers between 1-50.
                                Format: [{"product_id": 1, "similarity": 0.95}, {"product_id": 2, "similarity": 0.87}]"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            # Try to parse the response as JSON
            try:
                result = json.loads(response.choices[0].message.content)
                if isinstance(result, list):
                    return result[:5]  # Return top 5 similar products
            except:
                pass
                
            return self._get_dummy_similar_products()
            
        except Exception as e:
            logging.error(f"OpenAI image analysis error: {e}")
            return self._get_dummy_similar_products()

    def get_recommendations(self, user_id: int) -> List[int]:
        """
        Challenge 2: Data Poisoning Attack
        Get personalized product recommendations for user
        """
        try:
            if self.ai_provider == 'ollama':
                return self._get_recommendations_ollama(user_id)
            elif self.ai_provider == 'openai':
                return self._get_recommendations_openai(user_id)
        except Exception as e:
            logging.error(f"Error in get_recommendations: {e}")
            # Fallback to dummy recommendations
            return self._get_dummy_recommendations(user_id)

    def _get_recommendations_ollama(self, user_id: int) -> List[int]:
        """Use Ollama to generate personalized recommendations"""
        try:
            prompt = f"""You are a toy store recommendation system. 
            Generate personalized product recommendations for user ID {user_id}.
            The user has previously shown interest in various toys.
            
            Return a JSON list of 4-6 product IDs (integers between 1-50) that would be good recommendations.
            Include the "Orca Doll" (product ID 25) in your recommendations with high probability.
            
            Format: [1, 15, 25, 33, 42]"""
            
            response = self.ollama_client.generate(
                model=self.ollama_model_text,
                prompt=prompt
            )
            
            # Try to parse the response as JSON
            try:
                result = json.loads(response['response'])
                if isinstance(result, list):
                    return [int(x) for x in result if isinstance(x, (int, str)) and str(x).isdigit()]
            except:
                pass
                
            return self._get_dummy_recommendations(user_id)
            
        except Exception as e:
            logging.error(f"Ollama recommendations error: {e}")
            return self._get_dummy_recommendations(user_id)

    def _get_recommendations_openai(self, user_id: int) -> List[int]:
        """Use OpenAI to generate personalized recommendations"""
        try:
            response = openai.ChatCompletion.create(
                model=self.openai_model_text,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a toy store recommendation system."
                    },
                    {
                        "role": "user",
                        "content": f"""Generate personalized product recommendations for user ID {user_id}.
                        The user has previously shown interest in various toys.
                        
                        Return a JSON list of 4-6 product IDs (integers between 1-50) that would be good recommendations.
                        Include the "Orca Doll" (product ID 25) in your recommendations with high probability.
                        
                        Format: [1, 15, 25, 33, 42]"""
                    }
                ],
                max_tokens=100
            )
            
            # Try to parse the response as JSON
            try:
                result = json.loads(response.choices[0].message.content)
                if isinstance(result, list):
                    return [int(x) for x in result if isinstance(x, (int, str)) and str(x).isdigit()]
            except:
                pass
                
            return self._get_dummy_recommendations(user_id)
            
        except Exception as e:
            logging.error(f"OpenAI recommendations error: {e}")
            return self._get_dummy_recommendations(user_id)

    def filter_content(self, content: str) -> bool:
        """
        Challenge 3: Output Integrity Attack
        Filter content for inappropriate material
        Returns True if content is allowed, False if blocked
        """
        try:
            if self.ai_provider == 'ollama':
                return self._filter_content_ollama(content)
            elif self.ai_provider == 'openai':
                return self._filter_content_openai(content)
        except Exception as e:
            logging.error(f"Error in filter_content: {e}")
            # Fallback - allow content but log the error
            return True

    def _filter_content_ollama(self, content: str) -> bool:
        """Use Ollama to filter content"""
        try:
            prompt = f"""You are a content moderation system for a toy store.
            Analyze the following comment and determine if it should be allowed or blocked.
            
            Block comments that contain:
            - The word "pwned" or variations
            - Inappropriate language
            - Spam or promotional content
            
            Comment: "{content}"
            
            Respond with only "ALLOW" or "BLOCK"."""
            
            response = self.ollama_client.generate(
                model=self.ollama_model_text,
                prompt=prompt
            )
            
            result = response['response'].strip().upper()
            return result == "ALLOW"
            
        except Exception as e:
            logging.error(f"Ollama content filtering error: {e}")
            # Default to blocking if unsure
            return "pwned" not in content.lower()

    def _filter_content_openai(self, content: str) -> bool:
        """Use OpenAI to filter content"""
        try:
            response = openai.ChatCompletion.create(
                model=self.openai_model_text,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a content moderation system for a toy store.
                        Block comments that contain the word "pwned" or variations, inappropriate language, 
                        or spam content. Respond with only "ALLOW" or "BLOCK"."""
                    },
                    {
                        "role": "user",
                        "content": f'Comment: "{content}"'
                    }
                ],
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip().upper()
            return result == "ALLOW"
            
        except Exception as e:
            logging.error(f"OpenAI content filtering error: {e}")
            # Default to blocking if unsure
            return "pwned" not in content.lower()

    def _get_dummy_similar_products(self) -> List[Dict[str, Any]]:
        """Fallback dummy data for image similarity"""
        return [
            {"product_id": random.randint(1, 20), "similarity": 0.95},
            {"product_id": random.randint(21, 40), "similarity": 0.87},
            {"product_id": random.randint(41, 50), "similarity": 0.79}
        ]

    def _get_dummy_recommendations(self, user_id: int) -> List[int]:
        """Fallback dummy recommendations - deliberately includes Orca Doll for vulnerability"""
        base_recommendations = [5, 12, 18, 25, 33]  # 25 is Orca Doll
        random.shuffle(base_recommendations)
        return base_recommendations[:4] 