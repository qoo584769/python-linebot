import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class Config:
  MONGO_URI=os.getenv('MONGO_URI')
  SECRET_KEY=os.getenv('SECRET_KEY')
  TESTING = False

class TestConfig(Config):
  MONGO_URI=os.getenv('MONGO_URI')
  SECRET_KEY=os.getenv('SECRET_KEY')
  TESTING = True