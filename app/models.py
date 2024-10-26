from app import mongo
from bson.objectid import ObjectId

class User:
    def __init__(self, username, email, password, gender, unique_number, gender_numeric, image_urls, _id=None):
        self.username = username
        self.email = email
        self.password = password
        self.gender = gender
        self.unique_number = unique_number
        self.gender_numeric = gender_numeric
        self.image_urls = image_urls
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

    @staticmethod
    def find_by_unique_number(unique_number):
        user_data = mongo.db.users.find_one({'unique_number': unique_number})
        if user_data:
            return User(**user_data)
        return None

    def save_to_db(self):
        user_data = {
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'gender': self.gender,
            'unique_number': self.unique_number,
            'gender_numeric': self.gender_numeric,
            'image_urls': self.image_urls
        }
        if self._id:
            mongo.db.users.update_one({'_id': ObjectId(self._id)}, {'$set': user_data})
        else:
            self._id = mongo.db.users.insert_one(user_data).inserted_id

    def delete_from_db(self):
        """Deletes the user from the database based on the user ID."""
        if self._id:
            mongo.db.users.delete_one({'_id': ObjectId(self._id)})
            return True  
        return False  

    def json(self):
        return {
            'username': self.username,
            'email': self.email,
            'gender': self.gender,
            'unique_number': self.unique_number,
            'gender_numeric': self.gender_numeric,
            'image_urls': self.image_urls,
            '_id': str(self._id)
        }
