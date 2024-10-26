import cloudinary.api
from flask_jwt_extended import create_access_token
from datetime import timedelta
from app import mongo
from bson.objectid import ObjectId
import cloudinary.uploader
import os
import shutil

def clear_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Remove file or symbolic link
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Remove directory and all contents
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

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

def delete_from_cloudinary(folder_name):
    # Delete the contents of the folder from Cloudinary
    cloudinary.api.delete_resources_by_prefix(folder_name)
    
    # # List all resources under the specific folder
    # resources = cloudinary.api.resources(prefix=folder_name, resource_type='image')
    # public_ids = [resource['public_id'] for resource in resources['resources']]
    
    # # Delete each image individually
    # if public_ids:
    #     cloudinary.api.delete_resources(public_ids)

    # Now delete the folder
    cloudinary.api.delete_folder(folder_name, resource_type='upload')

    