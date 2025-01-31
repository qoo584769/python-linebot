import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
# 從環境變數中獲取 MongoDB URI
mongo_uri = os.getenv('MONGO_URI')


class MongoDBClient:
	_instance = None

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super(MongoDBClient, cls).__new__(cls)
			cls._instance._client = MongoClient(mongo_uri)
			cls._instance._database = cls._instance._client['northwind']
		return cls._instance

	@property
	def database(self):
		return self._instance._database
