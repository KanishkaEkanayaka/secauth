from flask import Blueprint, request, jsonify, current_app, make_response
from app.utils import generate_token, revoke_token, upload_images_to_cloudinary
from app.models import User
from app.forms import RegistrationForm, LoginForm
from app import bcrypt
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import cloudinary.uploader
import random

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
        if len(images) < 50:
            return jsonify({'message': 'More than 50 images are required.'}), 400

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        unique_number = generate_unique_number()
        gender_numeric = 1 if form.gender.data == 'male' else 0  # Assign 1 for male, 0 for female
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, gender=form.gender.data, unique_number=unique_number, gender_numeric=gender_numeric, image_urls=[])
        user.save_to_db()

        folder_name = f"sec_auth_images/{unique_number}_{gender_numeric}"
        image_urls = upload_images_to_cloudinary(images, folder_name)

        user.image_urls = image_urls
        user.save_to_db()

        token = generate_token(user._id)
        current_app.logger.info(f"User registered: {form.email.data}")
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
            current_app.logger.info(f"User logged in: {form.email.data}")
            response = make_response(jsonify({'message': 'Login successful.', 'token': token}), 200)
            response.headers['Authorization'] = f'Bearer {token}'
            return response
        else:
            current_app.logger.warning(f"Failed login attempt: {form.email.data}")
            return jsonify({'message': 'Login unsuccessful. Please check email and password.'}), 401
    else:
        return jsonify({'errors': form.errors}), 400

@auth_bp.route("/logout", methods=['DELETE'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    revoke_token(jti)
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id)
    current_app.logger.info(f"User logged out: {user.email}")
    return jsonify({"message": "Successfully logged out"}), 200

@main_bp.route("/protected", methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id)
    current_app.logger.info(f"Protected route accessed by user: {user.email}")
    return jsonify({'message': f'Welcome {user.username}'}), 200
