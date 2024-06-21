from flask_jwt_extended import create_access_token
from datetime import timedelta
from app import mongo
from bson.objectid import ObjectId
import cloudinary.uploader

def generate_token(user_id):
    expires = timedelta(hours=24)
    token = create_access_token(identity=str(user_id), expires_delta=expires)
    return token

def revoke_token(jti):
    mongo.db.token_blacklist.insert_one({'jti': jti})

def token_in_blacklist(jwt_payload):
    jti = jwt_payload['jti']
    token = mongo.db.token_blacklist.find_one({'jti': jti})
    return token is not None

def upload_images_to_cloudinary(images, folder_name):
    image_urls = []
    for image in images:
        result = cloudinary.uploader.upload(image, folder=folder_name)
        image_urls.append(result['url'])
    return image_urls