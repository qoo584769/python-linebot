from flask import Blueprint, request, jsonify, current_app
from models.member_model import Member
from utils.jwt_util import generate_token
from utils.hash_util import hash_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/testapi', methods=['POST'])
def test():
  data = request.get_json()
  username = data['username']
  password = data['password']
  email = data['email']
  # 檢查用戶是否已經存在
  if Member.exists('email'):
    return jsonify({"message": "用戶名已存在"}), 400

  # 使用 argon2 哈希密碼並創建用戶
  Member.create(username, password, email)
  return jsonify({"message": "註冊成功"}), 201

  # return jsonify({"message": "User added", "name": data['username']}), 201

@auth_bp.route('/register', methods=['GET'])
def index():
  return jsonify({"message": token}), 201

@auth_bp.route('/register', methods=['POST'])
def register():
  data = request.get_json()
  # username = data.get('username')
  # password = data.get('password')
  # email = data.get('email', '')
  username = data['username']
  password = data['password']
  email = data['email']

  # 檢查用戶是否已經存在
  if Member.exists(email):
    return jsonify({"message": "用戶名已存在"}), 400

  # 使用 argon2 加密密碼
  Member.create(username, password, email)
  return jsonify({"message": "註冊成功"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
  data = request.get_json()
  email = data['email']
  password = data['password']

  # 驗證帳號和密碼
  if Member.verify_hashed_password(email, password):
    token = generate_token(email)
    return jsonify({"message": "登入成功", "token": token}), 200
  return jsonify({"message": "用戶名或密碼錯誤"}), 400
