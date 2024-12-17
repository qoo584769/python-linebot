import jwt
import datetime
from flask import current_app

def generate_token(email):
  expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
  token = jwt.encode({
    'email': email,
    'exp': expiration_time
  }, current_app.config['SECRET_KEY'], algorithm='HS256')
  return token

def decode_token(token):
  try:
    decoded = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    return decoded
  except jwt.ExpiredSignatureError:
    return None
  except jwt.InvalidTokenError:
    return None
