from app import mongo
from bson.objectid import ObjectId

class User:
    def __init__(self, username, email, password, gender, image_folder, _id=None):
        self.username = username
        self.email = email
        self.password = password
        self.gender = gender
        self.image_folder = image_folder
        self._id = _id

    @staticmethod
    def find_by_email(email):
        user_data = mongo.db.users.find_one({'email': email})
        if user_data:
            return User(**user_data)
        return None

    @staticmethod
    def find_by_id(user_id):
        user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if user_data:
            return User(**user_data)
        return None

    def save_to_db(self):
        user_data = {
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'gender': self.gender,
            'image_folder': self.image_folder
        }
        if self._id:
            mongo.db.users.update_one({'_id': ObjectId(self._id)}, {'$set': user_data})
        else:
            self._id = mongo.db.users.insert_one(user_data).inserted_id

    def json(self):
        return {
            'username': self.username,
            'email': self.email,
            'gender': self.gender,
            'image_folder': self.image_folder,
            '_id': str(self._id)
        }
