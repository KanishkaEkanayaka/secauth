from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    MONGO_URI = os.getenv('MONGO_URI')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    CLOUDINARY_CLOUD_NAME=os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY=os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET=os.getenv('CLOUDINARY_API_SECRET')
    WTF_CSRF_ENABLED = False  # Disable CSRF protection