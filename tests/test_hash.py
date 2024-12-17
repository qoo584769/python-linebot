import pytest
from app2 import app, mongo
from config import TestConfig
from utils.hash_util import hash_password, verify_password

@pytest.fixture()
def create_app():
  app.config.from_object(TestConfig)
  yield app

@pytest.fixture()
def client(create_app):
  with create_app.test_client() as client:
    yield client

def test_hash_password(client):
  test_password = '123456'
  first_pass = hash_password(test_password)
  second_pass = hash_password(test_password)
  assert first_pass is not second_pass

def test_verify_password(client):
  test_password = '123456'
  hashed_pass = hash_password(test_password)
  ver_hash = verify_password(hashed_pass, test_password)
  assert ver_hash == True