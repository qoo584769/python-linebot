import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from pymongo import MongoClient

from api.auth import auth_bp
from api.member import member_bp
from linebotApi.linebotApi import line_bot_bp
# import config
from config import TestConfig
# 載入 .env 文件
load_dotenv()

# 初始化 Flask 應用
app = Flask(__name__)
CORS(app)

# 設定應用的秘鑰 (可以放在 .env 檔案中)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

# 註冊藍圖
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(member_bp, url_prefix='/api')
app.register_blueprint(line_bot_bp, url_prefix='/linebot')

if __name__ == '__main__':
    app.run(debug=True)