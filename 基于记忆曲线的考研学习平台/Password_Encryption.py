import hashlib
import hmac
import os

# 生成盐值
def generate_salt():
    return os.urandom(16)

# 使用 HMAC - SHA512 结合盐值加密密码
def hash_password(password, salt):
    if isinstance(salt, str):
        salt = bytes.fromhex(salt)
    h = hmac.new(salt, password.encode('utf-8'), hashlib.sha512)
    return h.hexdigest()

# 验证密码
def verify_password(input_password, stored_password, salt):
    input_hashed_password = hash_password(input_password, salt)
    print(input_hashed_password)
    return input_hashed_password == stored_password
