from flask import Blueprint, jsonify, request

from models.chat_model import Chat
from models.user_model import User
from utils.jwt_util import generate_token

auth_bp = Blueprint('auth', __name__)

db_user = User()
db_chat = Chat()


@auth_bp.route('/register', methods=['POST'])
def register():
	data = request.get_json()
	# username = data.get('username')
	# password = data.get('password')
	# email = data.get('email', '')
	username = data['username']
	password = data['password']
	email = data['email']
	friends = data.get('friends', [])
	rooms = data.get('rooms', [])

	# 檢查用戶是否已經存在
	if db_user.find_by_email(email):
		return jsonify({'message': '用戶名已存在'}), 400
	# if db_user.exists(email):
	#   return jsonify({"message": "用戶名已存在"}), 400
	get_room = db_chat.get_rooms()
	if get_room and not len(rooms):
		rooms.append(
			{
				'room_id': str(get_room['_id']),
				'room_name': get_room['room_name'],
				'room_type': 'group',
			}
		)
	# 使用 argon2 加密密碼
	user_id = db_user.create(username, password, email, friends, rooms)
	db_chat.add_to_room(get_room['_id'], str(user_id))
	return jsonify({'message': '註冊成功'}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
	data = request.get_json()
	email = data['email']
	password = data['password']

	# 驗證帳號和密碼
	if db_user.verify_hashed_password(email, password):
		token = generate_token(email)
		return jsonify({'message': '登入成功', 'token': token}), 200
	return jsonify({'message': '用戶名或密碼錯誤'}), 400


@auth_bp.route('/deleteone', methods=['POST'])
def deleteone():
	data = request.get_json()
	email = data['email']
	db_user.del_one_user(email)
	return jsonify({'message': '刪除成功'}), 200
