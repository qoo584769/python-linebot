import pytest
from app2 import app, mongo
from config import TestConfig

@pytest.fixture(scope="module")
def app_context():
  """初始化 Flask 應用上下文"""
  with app.app_context():
    yield mongo.membership  # 返回資料庫對象

@pytest.fixture(scope="function")
def clean_db(app_context):
  """每個測試前清空資料庫"""
  # 清空測試資料庫
  app_context.members.drop()
  return app_context.members

@pytest.fixture()
def create_app():
  app.config.from_object(TestConfig)
  yield app
  # with app.test_client() as client:
  #   yield client

@pytest.fixture()
def client(create_app):
  with create_app.test_client() as client:
    yield client

@pytest.mark.skip(reason = '測試範例')
def test_request_example(client, clean_db):
  user_data = {
    'username': 'testuser',
    'password': 'testpassword',
    'email': 'testuser@example.com',
  }
  response = client.post("/api/testapi", json=user_data)
  assert response.status_code == 201
  json_data = response.get_json()
  assert '註冊成功' in json_data['message']

@pytest.mark.skip(reason = '註冊測試已成功')
# 註冊測試
def test_register(client, clean_db):
  user_data = {
    'username': 'testuser',
    'password': 'testpassword',
    'email': 'testuser@example.com',
  }
  response = client.post('/api/register',
    json=user_data
  )
    # headers={'Content-Type':'application/json'}
  assert response.status_code == 201
  json_data = response.get_json()
  # assert response['message'] == '註冊成功'
  assert '註冊成功' in json_data['message'], f'response data {response.data}'

  # 確保用戶已經被插入資料庫
  user = clean_db.find_one({"username": "testuser"})
  assert user is not None
  assert user['username'] == 'testuser'

@pytest.mark.skip(reason = '登入測試已成功')
# 登入測試
def test_login(client, clean_db):
  # 先註冊用戶
  user_data = {
    'username': 'testuser',
    'password': 'testpassword',
    'email': 'testuser@example.com',
  }
  response = client.post('/api/register',
    json=user_data
  )

  login_data={'username': 'testuser', 'password': 'testpassword' }
  # 登入測試
  response = client.post('/api/login', 
    json=login_data
  )

  assert response.status_code == 200
  json_data = response.get_json()
  assert '登入成功' in json_data['message']
  assert isinstance(json_data['token'], str)

@pytest.mark.skip(reason = '驗證測試已成功')
# 驗證會員資料
def test_get_member(client, clean_db):
  # 先註冊用戶
  user_data = {
    'username': 'testuser',
    'password': 'testpassword',
    'email': 'testuser@example.com',
  }
  response = client.post('/api/register',
    json=user_data
  )

  # 模擬登入獲取 token
  login_data={'username': 'testuser', 'password': 'testpassword' }

  response = client.post('/api/login', 
    json=login_data
  )

  assert response.status_code == 200
  json_data = response.get_json()
  assert '登入成功' in json_data['message']
  assert isinstance(json_data['token'], str)

  # token = json.loads(response.data.decode())['token']
  token = json_data['token']
  
  # 用 token 獲取會員資料
  response = client.get('/api/member/testuser',
    headers={'Authorization': f'Bearer {token}'}
  )
  json_data = response.get_json()
  assert response.status_code == 200
  assert 'testuser' in json_data['username']
  assert 'testuser@example.com' in json_data['email']


  # 測試未提供 token 的情況

@pytest.mark.skip(reason = '無token測試已成功')
# 測試未提供 token 的情況
def test_get_member_no_token(client, clean_db):
  response = client.get('/api/member/testuser')
  json_data = response.get_json()
  assert response.status_code == 403
  assert '缺少 token' in json_data['message']

@pytest.mark.skip(reason = '無效 token 測試已成功')
# 測試無效 token 的情況
def test_get_member_invalid_token(client, clean_db):
  response = client.get('/api/member/testuser',
    headers={'Authorization': 'Bearer invalid_token'}
  )
  json_data = response.get_json()
  assert response.status_code == 401
  assert '無效的 token' in json_data['message']