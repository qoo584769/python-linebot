import os

from dotenv import load_dotenv
from pymongo import MongoClient

from utils.hash_util import hash_password, verify_password
# 載入 .env 文件
load_dotenv()

# 從環境變數中獲取 MongoDB URI
mongo_uri = os.getenv("MONGO_URI")

try:
  client = MongoClient(mongo_uri)
  print('連接成功')
except Exception as e:
  print(e)

class Member:
  @staticmethod
  def get_collection():
    db = client['membership']
    return db['members']

  @staticmethod
  def create(username, password, email=''):
    hashed_password = hash_password(password)
    collection = Member.get_collection()
    collection.insert_one({
      "username": username,
      "password": hashed_password,
      "email": email
    })

  @staticmethod
  def find_by_email(email):
    collection = Member.get_collection()
    return collection.find_one({"email": email})

  @staticmethod
  def exists(email):
    return Member.find_by_email(email) is not None

  @staticmethod
  def verify_hashed_password(email, password):
    member = Member.find_by_email(email)
    if member:
      return verify_password(member['password'], password)
    return False