from flask import Blueprint, request, jsonify, current_app, make_response
from app.utils import generate_token, revoke_token, upload_images_to_cloudinary, delete_from_cloudinary, clear_folder
from app.models import User
from app.forms import RegistrationForm, LoginForm
from app import bcrypt
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, get_jwt_header
import cloudinary.uploader
import random
from datetime import datetime
import requests
import glob

auth_bp = Blueprint('auth', __name__)
main_bp = Blueprint('main', __name__)

def generate_unique_number():
    while True:
        unique_number = random.randint(100, 999999999)
        if not User.find_by_unique_number(unique_number):
            return unique_number

@auth_bp.route("/register", methods=['POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        images = request.files.getlist('images')
        if len(images) < 20:
            return jsonify({'message': '20 images are required.'}), 400

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        unique_number = generate_unique_number()
        gender_numeric = 1 if form.gender.data == 'male' else 0  # Assign 1 for male, 0 for female
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, gender=form.gender.data, unique_number=unique_number, gender_numeric=gender_numeric, image_urls=[])
        user.save_to_db()

        folder_name = f"sec_images/{unique_number}_{gender_numeric}"
        image_urls = upload_images_to_cloudinary(images, folder_name)

        user.image_urls = image_urls
        user.save_to_db()

        token = generate_token(user._id)
        current_time = datetime.now()
        
         # Call incremental learning endpoint
        try:
            res = requests.post('http://localhost:5001/incremental_train')
            if res.status_code != 200:
                user.delete_from_db()  # Delete the user record if training fails
                try:
                    delete_cloudinary = delete_from_cloudinary(folder_name=folder_name)
                except Exception as e:
                    current_app.logger.error(f"Error deleting folder from Cloudinary: {str(e)}")
                    return jsonify({'message': 'User registered deleted, but failed to clean up folder on Cloudinary.'}), 500                
                current_app.logger.info(f"User registeration failed: {form.email.data} at {current_time.date()} {current_time.time()}")
                return jsonify({'message': 'Registration failed. Incremental training unsuccessful.'}), 500
        except requests.RequestException as e:
            user.delete_from_db()  # Delete the user record if there's a request error
            try:
                delete_cloudinary = delete_from_cloudinary(folder_name=folder_name)
            except Exception as e:
                current_app.logger.error(f"Error deleting folder from Cloudinary: {str(e)}")
                return jsonify({'message': 'User registered deleted, but failed to clean up folder on Cloudinary.'}), 500
            current_app.logger.info(f"User registeration failed: {form.email.data} at {current_time.date()} {current_time.time()}")
            return jsonify({'message': 'Registration failed. Error in training service.', 'error': str(e)}), 500

        current_app.logger.info(f"User registered: {form.email.data} at {current_time.date()} {current_time.time()}")
        response = make_response(jsonify({'message': 'User registered successfully.', 'token': token}), 201)
        response.headers['Authorization'] = f'Bearer {token}'
        return response
    else:
        return jsonify({'errors': form.errors}), 400

@auth_bp.route("/login", methods=['POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.find_by_email(form.email.data)
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            token = generate_token(user._id)
            current_time = datetime.now()
            current_app.logger.info(f"User logged in: {form.email.data} at {current_time.date()} {current_time.time()}")
            response = make_response(jsonify({'message': 'Login successful.', 'token': token}), 200)
            response.headers['Authorization'] = f'Bearer {token}'
            return response
        else:
            current_time = datetime.now()
            current_app.logger.warning(f"Failed login attempt: {form.email.data} at {current_time.date()} {current_time.time()}")
            return jsonify({'message': 'Login unsuccessful. Please check email and password.'}), 401
    else:
        return jsonify({'errors': form.errors}), 400
    

import requests
import time
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

auth_bp = Blueprint("auth_bp", __name__)

import requests
import time
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/continuous_auth", methods=['POST'])
@jwt_required()
def continuous_auth():
    jwt_token = request.headers.get("Authorization")
    
    headers = {
        "Authorization": f"Bearer {jwt_token.split()[1]}" if jwt_token else None
    }

    while True:
        not_human_count = 0
        
        for _ in range(3):
            try:
                response = requests.get("http://localhost:5005/api/get_labels")
                
                # Check if the response is successful and contains JSON data
                if response.status_code == 200 and response.headers.get('Content-Type') == 'application/json':
                    detected_data = response.json()
                    print(detected_data.get("detected_labels", []))
                    
                    # Check if "person" is not in detected labels
                    if "person" not in detected_data.get("detected_labels", []):
                        print('person not detected')
                        not_human_count += 1
                else:
                    print("Unexpected response format or status code:", response.status_code, response.text)

            except requests.exceptions.RequestException as e:
                print("Request failed:", e)
                return jsonify({"error": "Failed to reach detection service"}), 500

            except ValueError as json_error:
                print("JSON decode error:", json_error)
                print("Response content:", response.text)  # Log what the server actually returned
                return jsonify({"error": "Invalid response format from detection service"}), 500

            time.sleep(1)  # Delay between requests within this cycle

        if not_human_count == 3:
            logout_response = requests.delete('http://localhost:5000/logout', headers=headers)
            print("User logged out:", logout_response.text)
            return jsonify({"message": "User logged out due to continuous non-human detection."}), 200
        # else:
        #     identity_wrong = 0
        #     for _ in range(2):
        #         try:
        #             #folder path
        #             folder_path = '/home/kaiz/Desktop/sec_auth_face_extractor/captured_images'
        #             clear_folder(folder_path)
        #             response = requests.get("http://localhost:5003/capture_now")

        #             # Define the URL to send the POST request
        #             url = 'http://localhost:5001/predict'  

        #             # Use glob to find all .jpg files in a specified directory
        #             image_paths = glob.glob('/home/kaiz/Desktop/sec_auth_face_extractor/captured_images/*.jpg')

        #             # Loop through the found images and send each one
        #             for image_path in image_paths:
        #                 with open(image_path, 'rb') as img:
        #                     files = {'file': img}
        #                     response = requests.post(url, files=files)
                            
        #                     # Check the response from the server
        #                     if response.status_code == 200:
        #                         print(f"Image {image_path} uploaded successfully!")
        #                     else:
        #                         print(f"Failed to upload image {image_path}. Status code: {response.status_code}")

                    
        #             # Check if the response is successful and contains JSON data
        #             if response.status_code == 200 and response.headers.get('Content-Type') == 'application/json':
        #                 detected_data = response.json()
        #                 identity = detected_data.get("identity", [])
        #                 if identity:
        #                     identity = identity[0]
        #                 print(identity)
        #                 #query the user with this identity
        #                 user = User.find_by_unique_number(identity)

        #                 #get id passed with the jwt
        #                 current_user_id = get_jwt_identity()

        #                 # Check if "person" is not in detected labels
        #                 if current_user_id is not user._id:
        #                     print('invalid user')
        #                     identity_wrong += 1
        #                     clear_folder(folder_path)
        #             else:
        #                 print("Unexpected response format or status code:", response.status_code, response.text)

        #         except requests.exceptions.RequestException as e:
        #             print("Request failed:", e)
        #             return jsonify({"error": "Failed to reach detection service"}), 500

        #         except ValueError as json_error:
        #             print("JSON decode error:", json_error)
        #             print("Response content:", response.text)  # Log what the server actually returned
        #             return jsonify({"error": "Invalid response format from detection service"}), 500

        #         time.sleep(1)  # Delay between requests within this cycle

        #     if identity_wrong == 2:
        #         logout_response = requests.delete('http://localhost:5000/logout', headers=headers)
        #         print("User logged out:", logout_response.text)
        #         return jsonify({"message": "User logged out due to continuous wrong identity detection."}), 200
        
        time.sleep(5)  # Delay before the next cycle


                   

@auth_bp.route("/logout", methods=['DELETE'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    revoke_token(jti)
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id)
    current_time = datetime.now()
    current_app.logger.info(f"User logged out: {user.email} At {current_time.date()} {current_time.time()}")
    return jsonify({"message": "Successfully logged out"}), 200

@main_bp.route("/protected", methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id)
    current_time = datetime.now()
    current_app.logger.info(f"Protected route accessed by user: {user.email} at {current_time.date()} {current_time.time()}")
    return jsonify({'message': f'Welcome {user.username}'}), 200
