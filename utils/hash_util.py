from argon2 import PasswordHasher

ph = PasswordHasher()

# 密碼加密
def hash_password(password: str) -> str:
  return ph.hash(password)

# 密碼驗證
def verify_password(stored_hash: str, password: str) -> bool:
  try:
    return ph.verify(stored_hash, password)
  except Exception:
    return False