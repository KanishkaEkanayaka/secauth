from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
import logging
from logging.handlers import RotatingFileHandler

mongo = PyMongo()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    mongo.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    from app.routes import auth_bp, main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Logging setup
    if not app.debug:
        handler = RotatingFileHandler('logs/app.log', maxBytes=10000, backupCount=1)
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Flask App Startup')

    from app.utils import token_in_blacklist

    # Setup token blacklist check
    @jwt.token_in_blocklist_loader
    def check_if_token_in_blacklist(jwt_header, jwt_payload):
        return token_in_blacklist(jwt_payload)

    return app
