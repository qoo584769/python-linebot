from flask import Blueprint, jsonify, request

from models.user_model import User
from utils.jwt_util import decode_token

user_bp = Blueprint('user', __name__)

db = User()


@user_bp.route('/user/<email>', methods=['GET'])
def get_user(email):
	token = request.headers.get('Authorization')
	if not token:
		return jsonify({'message': '缺少 token'}), 403

	decoded_token = decode_token(token.split(' ')[1])
	if not decoded_token:
		return jsonify({'message': '無效的 token'}), 401

	# 驗證使用者身份
	if decoded_token['email'] != email:
		return jsonify({'message': '用戶名不匹配'}), 403

	user = db.find_by_email(email)
	if user:
		result = {
			'username': user['username'],
			'email': user.get('email', ''),
			'friends': user['friends'],
			'rooms': user['rooms'],
		}
		return jsonify(result), 200

	return jsonify({'message': '用戶不存在'}), 404
