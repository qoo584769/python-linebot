from flask import Blueprint, jsonify, request
from utils.jwt_util import decode_token
from models.member_model import Member

member_bp = Blueprint('member', __name__)

@member_bp.route('/member/<email>', methods=['GET'])
def get_member(email):
  token = request.headers.get('Authorization')
  if not token:
    return jsonify({"message": "缺少 token"}), 403

  decoded_token = decode_token(token.split(' ')[1])
  if not decoded_token:
    return jsonify({"message": "無效的 token"}), 401

  # 驗證使用者身份
  if decoded_token['email'] != email:
    return jsonify({"message": "用戶名不匹配"}), 403

  member = Member.find_by_email(email)
  if member:
    return jsonify({"username": member['username'], "email": member.get('email', '')}), 200
  return jsonify({"message": "用戶不存在"}), 404
