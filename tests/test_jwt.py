import pytest
from app2 import app, mongo
from config import TestConfig
from utils.jwt_util import generate_token, decode_token

@pytest.fixture()
def create_app():
  app.config.from_object(TestConfig)
  yield app

@pytest.fixture()
def client(create_app):
  with create_app.test_client() as client:
    with app.app_context():
      yield client

def test_generate_token(client):
  name = 'testuser'
  token = generate_token(name)
  decoded = decode_token(token)
  assert isinstance(decoded, dict)
  assert decoded['username'] == name