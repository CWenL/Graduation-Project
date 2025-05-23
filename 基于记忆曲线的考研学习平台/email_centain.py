import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_verification_email(to_email, verification_code):
    from_email = "cwenj9uy@163.com"  # 替换为你的网易邮箱地址
    from_password = "JHy5H38U78ELgQ7N"  # 替换为你网易邮箱的授权密码

    # 创建邮件内容
    subject = "验证码"
    body = f"您的验证码是：{verification_code}"

    # 设置邮件的发件人、收件人和主题
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # 连接到网易邮箱的SMTP服务器
        server = smtplib.SMTP_SSL('smtp.163.com', 465)  # 使用SSL连接
        server.login(from_email, from_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败: {e}")
