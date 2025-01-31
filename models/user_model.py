import os

from bson import json_util
from dotenv import load_dotenv

from models.db_client import MongoDBClient
from utils.hash_util import hash_password, verify_password

# 載入 .env 文件
load_dotenv()

# 從環境變數中獲取 MongoDB URI
mongo_uri = os.getenv('MONGO_URI')


class User:
	def __init__(self):
		self.client = MongoDBClient()

		self.member_collection = self.client.database['users']

	@staticmethod
	def get_collection():
		db = MongoDBClient.get_db()
		return db['users']

	# @staticmethod
	# def create(username, password, email=''):
	def create(self, username, password, email, friends, rooms):
		hashed_password = hash_password(password)
		user_id = self.member_collection.insert_one(
			{
				'username': username,
				'password': hashed_password,
				'email': email,
				'friends': friends,
				'rooms': rooms,
			}
		).inserted_id
		return user_id

	# @staticmethod
	# def find_by_email(email):
	def find_by_email(self, email):
		user = self.member_collection.find_one({'email': email})
		if user is not None:
			return user
		return False

	# @staticmethod
	# def exists(email):
	def exists(self, email):
		return self.find_by_email(email) is not None

	# @staticmethod
	# def verify_hashed_password(email, password):
	def verify_hashed_password(self, email, password):
		member = self.find_by_email(email)
		if member:
			return verify_password(member['password'], password)
		return False

	# 刪除使用者
	def del_one_user(self, email):
		res = self.member_collection.delete_one({'email': email})
		return res

	# 解參考DBREF
	def member_dereference(self, doc_ref):
		if not doc_ref:
			return []
		result = [
			self.client.database.dereference(doc)
			for doc in doc_ref
			if self.client.database.dereference(doc)
		]
		return json_util.dumps(result)
