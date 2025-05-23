import sqlite3
import os
import hmac
import hashlib
import SQLiteOp as sp

def update_user_encryption():
    # 连接数据库
    conn = sp.connect_db()
    c = conn.cursor()

    # 查询未加密的用户（假设 salt 字段为 NULL 代表未加密）
    c.execute("SELECT username, password FROM user WHERE salt IS NULL")
    users = c.fetchall()

    for username, plain_password in users:
        # 生成盐值
        salt = os.urandom(16)
        # 使用 HMAC-SHA512 加密密码
        hashed_password = hmac.new(
            salt, 
            plain_password.encode('utf-8'), 
            hashlib.sha512
        ).hexdigest()
        salt_hex = salt.hex()  # 转换为十六进制字符串存储

        # 更新数据库记录
        c.execute(
            "UPDATE user SET password = ?, salt = ? WHERE username = ?",
            (hashed_password, salt_hex, username)
        )

    # 提交更改并关闭连接
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_user_encryption()
    print("用户密码加密更新完成")