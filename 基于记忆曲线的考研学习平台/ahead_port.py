from functools import wraps
import math
import re
import threading
from flask import Blueprint, Flask, abort, flash, jsonify, render_template,request,redirect,make_response,url_for,g,session,send_file,send_from_directory
import pandas as pd
import requests
import schedule
from sqlalchemy import desc, func, or_, text
from SQLiteOp import connect_db
import behind_port as bp
import os
import Password_Encryption as pe
import SQLiteOp as sp
import time
import uuid
from flask_sqlalchemy import SQLAlchemy
import redis
import json
import datetime
import random

general=os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/pictures'  # 设置上传文件的保存路径
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}  # 允许的文件扩展名
app.secret_key = 'mysecret_key'  # 设置一个用于签名会话的密钥
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.before_request
def before_request():
    g.db=connect_db()

@app.teardown_request
def teardown_requset(exception):
    g.db.close()

# 定义仅验证用户是否登录的装饰器
def require_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not bp.record_login(session): # 若未登录则去index，否则继续执行装饰的函数
            print("未登录")
            return redirect(url_for('index'))
        if bp.get_sql_user(session['username'])[0][5]==1: # 若被封禁则去index，否则继续执行装饰的函数
            print("该账户被禁用")
            return render_template("login.html", show_alert3=True)
        return func(*args, **kwargs)
    return wrapper

def require_permission(permissions, notice_type=None):
    def decorator(func):
        @wraps(func)  # 关键修改
        def wrapper(*args, **kwargs):
            username = session.get('username')
            if not username:
                return jsonify({'code': 401, 'message': '未登录'}), 401
            power = bp.get_sql_user(username)[0][3] if bp.get_sql_user(username) else None
            if notice_type == 'global' and power != 'admin':
                return jsonify({'code': 403, 'message': '只有管理员可以发布全服公告'}), 403
            if power not in permissions:
                return jsonify({'code': 403, 'message': '无权限操作'}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        if bp.record_login(session):
            return redirect(url_for("homepage"))
        else:
            return render_template("login.html")
    elif request.method == 'POST':
        username = request.form.get('username')
        InPutPassword = request.form.get('password')
        remember = request.form.get('remember')
        user_type = request.form.get('user_type', 'user')  # 默认普通用户
        session['username'] = username  # 在session中存入用户名
        try:
            res = bp.get_sql_user(username)  # 判断用户名是否存在
            if not res:
                raise ValueError("该用户不存在")
            session['password'] = res[0][1]  # 在session中存入数据库中的密码
            session['power'] = res[0][3]  # 在session中存入用户权限
            session['salt'] = res[0][6]  # 在session中存入数据库中的salt
            if res[0][5] == 1:
                return render_template("login.html", show_alert3=True)
            if bp.login(InPutPassword, session):
                session['login'] = "login_success"
                if user_type=="user":
                    if remember == "on":  # 如果勾选记住，新建cookie
                        response = make_response(redirect(url_for('homepage')))
                        max_age = 30 * 24 * 60 * 60
                        # 由于是 HTTP 环境，不设置 Secure 属性
                        response.set_cookie('username', username, max_age=max_age, httponly=True)
                        return response
                    return redirect(url_for("homepage"))
                elif user_type=="admin" and session['power'] in ['admin','CommunityAdmin']:
                    if remember == "on":  # 如果勾选记住，新建cookie
                        response = make_response(redirect(url_for('adminOp')))
                        max_age = 30 * 24 * 60 * 60
                        # 由于是 HTTP 环境，不设置 Secure 属性
                        response.set_cookie('username', username, max_age=max_age, httponly=True)
                        return response
                    return redirect(url_for("adminOp"))
                else: # 权限不足
                    session['login'] = ""
                    return render_template("login.html", show_alert4=True,show_register=False)
            else:
                return render_template("login.html", show_alert2=True,show_register=False)
        except Exception as e:
            print(f"登录失败: {e}")
            session['username'] = None
            session['password'] = None
            session['power'] = None
            session['salt'] = None
            return render_template("login.html", show_alert2=True)

# 用户注册
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    surepassword = request.form.get('surepassword')
    email = request.form.get('email')
    power = "user"
    if username=="" or password=="" or email=="":
        print("不可留白！")
        return render_template('login.html', show_alert1=True, show_register=True)  # 传递 show_alert 标志
    # 使用参数化查询避免 SQL 注入
    user_insert = "INSERT INTO user (username, password, email, power, salt) VALUES (?, ?, ?, ?, ?);"
    session['username'] = username  # 在session中存入用户名
    # 判断用户名是否存在
    res = bp.get_sql_user(username)
    if res:  # 如果查询到用户名已存在
        print("该用户名已存在")
        return render_template('login.html', show_alert1=True, show_register=True)  # 传递 show_alert 标志
    elif password != surepassword:
        print("前后密码不一致")
        return render_template('login.html', show_alert1=True, show_register=True)  # 传递 show_alert 标志
    else:
        # 生成盐
        salt = pe.generate_salt()
        salt_hex = salt.hex()  # 转换为十六进制字符串用于存储
        # 哈希Hmac-512加密
        hashed_password = pe.hash_password(password, salt_hex)
        # 插入新用户
        sp.sql_cursor_execute(user_insert, (username, hashed_password, email, power, salt_hex))
        print("注册成功")
        return redirect(url_for('index'))

def get_user_study_and_review_counts(username):
    with app.app_context():
        # 获取学习记录总数
        study_count = db.session.query(func.count(Study.id)).filter_by(Username=username).scalar()
        # 获取复习记录总数
        review_count = db.session.query(func.count(ReviewState.Rid)).filter_by(username=username).scalar()
        return study_count, review_count

# 用户主页
@app.route('/homepage')
@require_login
def homepage():
    username=session['username']
    studydata=bp.get_sql_studydata(username)
    study_counts,review_counts=get_user_study_and_review_counts(username)
    # 更新错题复习权重,通过昨日到今日的复习正确率获取增长速率稳定值
    stability=bp.adjust_decay_coefficient(get_correct_ToYesDay_data(username))
    bp.update_Weights_login(studydata,stability)
    #同步更新用户-权重-标签表的权重数据
    bp.recalculate_user_tag_weights(username)
    labei_review=get_top_three_tags_by_username(username)
    session['reviewcomplete']=""
    session['Postingcomplete']=""
    session['Commentcomplete']=""
    session['Noticecomplete']=""
    labei_review=get_top_three_tags_by_username(username)
    return render_template("homepage.html",username=username,power=session['power'],study_counts=study_counts,review_counts=review_counts,labei_review=labei_review)

# 了解网站思想
@app.route('/learning_us')
@require_login
def learning_us():
    username=session['username']
    return render_template("learning.html",username=username,power=session['power'])


# 配置 JSON 不进行 ASCII 转义
app.config['JSON_AS_ASCII'] = False
# 平台公告
@app.route('/GlobalNotice', methods=['GET'])
@require_login
def GlobalNotice():
    username=session['username']
    return render_template("GlobalNotice.html",username=username,power=session['power'])

# 退出页面
@app.route('/logout')
def loginout():
    # 清除 session
    session.pop('username', None)
    session.pop('password', None)
    session.pop('power', None)
    session.pop('login', None)
    # 清除 cookie
    response = make_response(redirect(url_for('index')))
    response.set_cookie('username', '', expires=0)
    return response

# 管理员面板
@app.route('/adminOp')
@require_permission(['admin', 'CommunityAdmin'])
def adminOp():
    power=session['power']
    AdminName=session['username']
    return render_template("adminOp.html",AdminName=AdminName,power=power) # 获取索引值

# 获取论坛帖子标签
@app.route('/get_forum_tags')
@require_login
def get_forum_tags():
    # 获取论坛的所有标签
    tags = bp.get_sql_Only_label(TableName="forum")
    return jsonify(sorted(tags))

@app.route('/community')
@require_login
def CommunityPage():
    # 获取当前页码，默认为第 1 页
    page = request.args.get('page', 1, type=int)
    # 每页显示的帖子数量
    per_page = 6
    # 获取搜索关键词
    keyword = request.args.get('keyword', '').strip()
    # 获取标签筛选参数
    tag = request.args.get('tag', '').strip()
    # 初始化条件列表和参数列表
    conditions = []
    params = []
    # 构建标签筛选条件
    if tag:
        conditions.append("tag LIKE ?")
        params.append(f'%{tag}%')
    # 添加搜索条件
    if keyword:
        conditions.extend(["Title LIKE ?", "PostingsText LIKE ?", "tag LIKE ?"])
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
    # 构建完整的 WHERE 子句
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    # 构建完整的 SQL 语句
    base_sql = f"SELECT * FROM Forum {where_clause} ORDER BY PostingsTime DESC"
    # 分页处理
    if page is not None and per_page is not None:
        offset = (page - 1) * per_page
        base_sql += f" LIMIT {per_page} OFFSET {offset}"
    # 执行 SQL 查询
    res = sp.sql_execute_select(base_sql, tuple(params))
    # 获取数据总数
    count_sql = f"SELECT COUNT(*) FROM Forum {where_clause}"
    total = sp.sql_execute_select(count_sql, tuple(params))[0][0]
    total_pages = (total + per_page - 1) // per_page
    # 构建分页对象
    pagination = {
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'page': page,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < total_pages else None,
        'total_pages': total_pages,
        'keyword': keyword,  # 保留搜索关键词
        'tag': tag  # 保留标签筛选
    }
    session['Postingcomplete'] = session.get('Postingcomplete', None)
    message = session['Postingcomplete']
    if message == "发布成功":
        session['Postingcomplete'] = ""
        return render_template("community.html", username=session['username'], power=session['power'], forum=res, message=message, pagination=pagination, keyword=keyword, tag=tag)
    return render_template("community.html", username=session['username'], power=session['power'], forum=res, message="", pagination=pagination, keyword=keyword, tag=tag)

# 查看贴子
@app.route('/post/<int:post_id>')
@require_login
def post_detail(post_id):
    # 从数据库中查询帖子内容
    res = sp.sql_execute_select("SELECT * FROM Forum WHERE PostingsID = ?", (post_id,))
    commentdata=bp.get_sql_commentdataForId(post_id)
    username=session['username']
    # 从forum表中获取唯一的标签组
    labeldata=bp.get_sql_Only_label("forum",res[0][3])
    # 防止重复点赞
    liked = bp.check_user_liked_post(session['username'], post_id)  # 检查用户是否已点赞
    if res:
        session['Commentcomplete']=(session['Commentcomplete']) if session['Commentcomplete'] else "?"
        message=session['Commentcomplete']
        #更新观看数
        bp.Update_Post_ViewNum(post_id)
        # 判断该查看该帖子的是否是发布者，若是则进入进入发布者所属的界面
        if username==res[0][2] or session['power'] in ['admin','CommunityAdmin']:
            return render_template('post_detail_owner.html', post=res[0],power=session['power'],liked=liked,commentdata=enumerate(commentdata),message="",labeldata=labeldata)
        else:
            return render_template('post_detail.html', post=res[0],power=session['power'],liked=liked,commentdata=enumerate(commentdata),message="")
    else:
        return "帖子未找到", 404

@app.route('/update_post', methods=['POST'])
@require_login
def update_post():
    post_id = request.form.get('post_id')
    post_tittle = request.form.get('post_tittle')
    post_content = request.form.get('post_body')
    Label = request.form.get('post_tag')
    post_image = request.files.get('post_image')
    username=session['username']
    if post_image and allowed_file(post_image.filename):
        # 获取原图片路径
        original_path = bp.get_original_path(post_id,"PostingsPicture")
        # 删除原图片文件
        if original_path and os.path.exists(original_path):
            os.remove(original_path)
        # 保存新的问题图片
        new_filename = bp.save_answer_image(post_image,app.config['UPLOAD_FOLDER'],username,"post")
        # 更新 Study 表中的 QuestionPicture 字段
        bp.update_forum_picture_table(post_id, "PostingsPicture", new_filename)
    # 更新 Study 表中的其他字段
    bp.update_post(post_id,post_tittle,post_content,Label)
    # 更新数据库逻辑
    # if session['power'] in ['admin','CommunityAdmin']:
    #     return redirect(url_for('adminOp'))
    return redirect(url_for('post_detail', post_id=post_id))

# 上传贴子
@app.route('/To_Post',methods=['GET'])
@require_login
def To_Post():
    return render_template("To_Post.html",power=session['power'])

# 上传贴子
@app.route('/input_POST',methods=['POST'])
@require_login
def input_POST():
    post_title = request.form['post_title']
    post_content = request.form['post_content']
    post_tags = request.form['post_tags']
    username=session['username']
    # 处理上传的图片
    post_image = request.files.get('post_image') if request.files.get('post_image') else None
    # 获取当前日期和时间
    now = datetime.datetime.now()
    post_time = now.strftime("%Y-%m-%d %H:%M")
    #这个实际为服务端的ip，但是为了展示效果暂时设置为这个
    public_ip = bp.get_public_ip()
    # 正确的用户ip通过下列函数获取，但本地测试获取的本地ip，无法查询归属地
    # user_ip = request.remote_addr
    if public_ip:
        location = bp.get_ip_location(public_ip)
        print(f"当前设备公网 IP {public_ip} 的归属地是: {location}")
    else:
        print("无法获取公网 IP，因此无法查询归属地。")
    if post_image:
        # 保存图片
        new_Post_Picture_Link = bp.save_answer_image(post_image,app.config['UPLOAD_FOLDER'],username,"Post")
        insert_Post="INSERT INTO Forum (title, username, PostingsTime, IpLoc, tag, PostingsText, PostingsPicture, PostingsSupport) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
        sp.sql_cursor_execute(insert_Post, (post_title, username, post_time, location, post_tags, post_content, "/static/pictures/"+new_Post_Picture_Link, 0))
    else:
        insert_Post="INSERT INTO Forum (title, username, PostingsTime, IpLoc, tag, PostingsText, PostingsSupport) VALUES (?, ?, ?, ?, ?, ?, ?);"
        sp.sql_cursor_execute(insert_Post, (post_title, username, post_time, location, post_tags, post_content, 0))
    session['Postingcomplete']="发布成功"
    # 重定向回帖子详情页，刷新评论区
    return redirect(url_for('CommunityPage'))

#提交评论
@app.route('/submit_comment', methods=['POST'])
@require_login
def InputComment():
    username=session['username']
    comment_text = request.form['comment_text']  # 获取用户输入的评论内容
    # 处理文件上传
    comment_image =request.files.get('comment_image') if request.files.get('comment_image') else None # 获取上传的文件
    post_id=request.form['post_id']
    # 获取当前日期和时间
    now = datetime.datetime.now()
    # 格式化时间，只保留到分钟
    CommentTime = now.strftime("%Y-%m-%d %H:%M")
    if comment_image:
        # 保存新的解答图片
        new_Comment_Picture_Link = bp.save_answer_image(comment_image,app.config['UPLOAD_FOLDER'],username,"Comment")
        insert_Comment="INSERT INTO Comment (PostingsID, username, Comment, CommentTime, CommentImg) VALUES (?, ?, ?, ?, ?);"
        sp.sql_cursor_execute(insert_Comment, (post_id, username, comment_text, CommentTime, "/static/pictures/"+new_Comment_Picture_Link))
    else:
        insert_Comment="INSERT INTO Comment (PostingsID, username, Comment, CommentTime) VALUES (?, ?, ?, ?);"
        sp.sql_cursor_execute(insert_Comment, (post_id, username, comment_text, CommentTime))
    session['Commentcomplete']="发布成功"
    # 重定向回帖子详情页，刷新评论区
    return redirect(url_for('post_detail', post_id=post_id))

@app.route('/like', methods=['POST'])
@require_login
def like_post():
    data = request.get_json()
    post_id = data.get("post_id")
    action = data.get("action")  # "like" or "unlike"
    if bp.record_login(session) is False:
            return render_template("login.html")
    username = session.get("username")  # 需要确保用户已登录
    if not post_id or action not in ["like", "unlike"]:
        return jsonify({"success": False, "error": "无效请求"})
    db = sp.connect_db()
    cursor = db.cursor()
    # 查询当前点赞数
    cursor.execute("SELECT PostingsSupport FROM Forum WHERE PostingsID = ?", (post_id,))
    result = cursor.fetchone()
    if not result:
        db.close()
        return jsonify({"success": False, "error": "帖子不存在"})
    new_likes = result[0]
    if action == "like":
        new_likes += 1
        cursor.execute("UPDATE Forum SET PostingsSupport = ? WHERE PostingsID = ?", (new_likes, post_id))
        cursor.execute("INSERT INTO Likes (username, post_id) VALUES (?, ?)", (username, post_id))
    elif action == "unlike":
        # 取消点赞
        cursor.execute("DELETE FROM Likes WHERE username = ? AND post_id = ?", (username, post_id))
        new_likes -= 1 if new_likes > 0 else 0
        cursor.execute("UPDATE Forum SET PostingsSupport = ? WHERE PostingsID = ?", (new_likes, post_id))
    db.commit()
    db.close()
    return jsonify({"success": True, "likes": new_likes})

# 最新资讯页面
@app.route('/News')
@require_login
def NewsPage():
    news=bp.get_sql_news()
    return render_template("News.html",username=session['username'],power=session['power'],news=enumerate(news)) # 获取索引值

@app.route('/news_detail/<int:news_id>')
@require_login
def news_detail(news_id):
    news = bp.get_sql_news_ForId(news_id)
    return render_template('news_detail.html',power=session['power'], news=news)

# 学习规划页面
@app.route('/planpage')
@require_login
def PlanPage():
    res=bp.get_sql_user(session['username'])
    user_study_plan = res[0][4]
    if user_study_plan:
        study_plan = json.loads(user_study_plan)
    else:
        study_plan = {
            "phase1": {
                "start_date": "",
                "end_date": "",
                "daily_hours": 0,
                "math_hours": 0,
                "english_hours": 0,
                "politics_hours": 0,
                "professional_hours": 0
            },
            "phase2": {
                "start_date": "",
                "end_date": "",
                "daily_hours": 0,
                "math_hours": 0,
                "english_hours": 0,
                "politics_hours": 0,
                "professional_hours": 0
            },
                "phase3": {
                "start_date": "",
                "end_date": "",
                "daily_hours": 0,
                "math_hours": 0,
                "english_hours": 0,
                "politics_hours": 0,
                "professional_hours": 0
            }
        }
    return render_template("Study_Plan.html",study_plan=study_plan,power=session['power'])

# 学习规划页面
@app.route('/plan', methods=['POST'])
@require_login
def plan():
    # 获取表单数据
    username = session['username']
    phase1_start = request.form.get('phase1_start')
    phase1_end = request.form.get('phase1_end')
    phase1_daily_hours = request.form.get('phase1_daily_hours')
    phase1_math_hours = request.form.get('phase1_math_hours')
    phase1_english_hours = request.form.get('phase1_english_hours')
    phase1_politics_hours = request.form.get('phase1_politics_hours')
    phase1_professional_hours = request.form.get('phase1_professional_hours')

    phase2_start = request.form.get('phase2_start')
    phase2_end = request.form.get('phase2_end')
    phase2_daily_hours = request.form.get('phase2_daily_hours')
    phase2_math_hours = request.form.get('phase2_math_hours')
    phase2_english_hours = request.form.get('phase2_english_hours')
    phase2_politics_hours = request.form.get('phase2_politics_hours')
    phase2_professional_hours = request.form.get('phase2_professional_hours')

    phase3_start = request.form.get('phase3_start')
    phase3_end = request.form.get('phase3_end')
    phase3_daily_hours = request.form.get('phase3_daily_hours')
    phase3_math_hours = request.form.get('phase3_math_hours')
    phase3_english_hours = request.form.get('phase3_english_hours')
    phase3_politics_hours = request.form.get('phase3_politics_hours')
    phase3_professional_hours = request.form.get('phase3_professional_hours')

    # 构造 JSON 格式的学习规划
    study_plan = {
        "phase1": {
            "start_date": phase1_start,
            "end_date": phase1_end,
            "daily_hours": int(phase1_daily_hours),
            "math_hours": int(phase1_math_hours),
            "english_hours": int(phase1_english_hours),
            "politics_hours": int(phase1_politics_hours),
            "professional_hours": int(phase1_professional_hours)
        },
        "phase2": {
            "start_date": phase2_start,
            "end_date": phase2_end,
            "daily_hours": int(phase2_daily_hours),
            "math_hours": int(phase2_math_hours),
            "english_hours": int(phase2_english_hours),
            "politics_hours": int(phase2_politics_hours),
            "professional_hours": int(phase2_professional_hours)
        },
        "phase3": {
            "start_date": phase3_start,
            "end_date": phase3_end,
            "daily_hours": int(phase3_daily_hours),
            "math_hours": int(phase3_math_hours),
            "english_hours": int(phase3_english_hours),
            "politics_hours": int(phase3_politics_hours),
            "professional_hours": int(phase3_professional_hours)
        }
    }
    plan_insert = "UPDATE User SET StudyPlan = ? WHERE Username = ?"
    sp.sql_cursor_execute(plan_insert, (json.dumps(study_plan), username))
    charts_info, success, msg = dc.generate_pie_charts(username, study_plan, app)
    # 保存图表信息到数据库，指定图表类型为学习规划相关的四种类型
    chart_types = ["一轮复习每日学习时间安排", "二轮强化每日学习时间安排", "三轮冲刺每日学习时间安排", "一轮、二轮、三轮各占的时间"]
    if success:
        save_success, save_msg = save_charts_to_db(username, charts_info, chart_types=chart_types)
        if save_success:
            return render_template('Study_Plan.html', study_plan=study_plan,power=session['power'], message="学习规划已保存并更新图表！")
        else:
            return render_template('Study_Plan.html',study_plan=study_plan, power=session['power'], message=save_msg)
    else:
        return render_template('Study_Plan.html', study_plan=study_plan,power=session['power'], message=msg)

@app.route('/api/get_study_plan', methods=['GET'])
@require_login
def get_study_plan():
    username = session['username']
    user_data = bp.get_sql_user(username)
    if user_data:
        try:
            study_plan = json.loads(user_data[0][4])
            return jsonify({"success": True, "study_plan": study_plan})
        except (json.JSONDecodeError, IndexError):
            return jsonify({"success": False, "message": "无法解析学习计划数据"})
    else:
        return jsonify({"success": False, "message": "未获取到用户数据"})

@app.template_filter('ceil')
def ceil_filter(value):
    return math.ceil(value)

# 个人页面
@app.route('/userpage')
@require_login
def userpage():
    study_page = request.args.get('study_page', 1, type=int)
    forum_page = request.args.get('forum_page', 1, type=int)
    comment_page = request.args.get('comment_page', 1, type=int)
    per_page = 10  # 每页显示数量
    username=session['username']
    user=bp.get_sql_user(username) #用户个人信息
    # 获取日期参数
    study_start_date = request.args.get('study_start_date')
    study_end_date = request.args.get('study_end_date')
    forum_start_date = request.args.get('forum_start_date')
    forum_end_date = request.args.get('forum_end_date')
    comment_start_date = request.args.get('comment_start_date')
    comment_end_date = request.args.get('comment_end_date')
   # 错题分页
    studydata = bp.get_sql_studydata(username, study_page, per_page, study_start_date, study_end_date)
    study_total = bp.get_sql_studydata_count(username, study_start_date, study_end_date)
    # 帖子分页
    forumdata = bp.get_sql_forumdata(username, forum_page, per_page, forum_start_date, forum_end_date)
    forum_total = bp.get_sql_forumdata_count(username, forum_start_date, forum_end_date)
    # 评论分页
    commentdata = bp.get_sql_commentdata(username, comment_page, per_page, comment_start_date, comment_end_date)
    comment_total = bp.get_sql_commentdata_count(username, comment_start_date, comment_end_date)
    # 获取用户当日成功复习的数量
    reviewNum=bp.get_sql_reviewedNum(username)
    return render_template("userpage.html",username=session['username'],user=user,studydata=studydata,forumdata=forumdata,commentdata=commentdata,
                           study_page=study_page,
                           forum_page=forum_page,
                           comment_page=comment_page,
                           per_page=per_page,
                           study_total=study_total,
                           forum_total=forum_total,
                           comment_total=comment_total,
                           study_start_date=study_start_date,study_end_date=study_end_date,forum_start_date=forum_start_date,
                           forum_end_date=forum_end_date,comment_start_date=comment_start_date,comment_end_date=comment_end_date,
                           reviewNum=reviewNum,power=session['power'])

# 每日复习
@app.route('/review', methods=['GET', 'POST'])
@require_login
def review():
    username = session['username']
    reviewNum=bp.get_sql_reviewedNum(username)
    return render_template("review.html", username=username, power=session['power'],reviewNum=reviewNum)

@app.route('/Tags_Review/<string:Type_tag>')
@require_login
def Tags_Review(Type_tag):
    username = session['username']
    power = session.get('power')
    root_tags = Tag.query.filter(
        Tag.subject == Type_tag,
        Tag.description.is_(None)
    ).all()
    if not root_tags:
        flash("该学科下没有可用标签", "warning")
        return redirect(url_for('index'))
    def build_tree(Type_tag):
        root_tags = Tag.query.filter(
            Tag.subject == Type_tag,
            Tag.description.is_(None)
        ).all()
        tree_data = []
        for root_tag in root_tags:
            node = {
                'id': root_tag.id,
                'text': root_tag.tag_name,
                'children': []
            }
            # 查找二级标签
            second_level_tags = Tag.query.filter(
                Tag.subject == Type_tag,
                Tag.description.like(f'%父标签: {root_tag.tag_name}%')
            ).all()
            for second_tag in second_level_tags:
                sub_node = {
                    'id': second_tag.id,
                    'text': second_tag.tag_name,
                    'children': []
                }
                # 查找三级标签
                third_level_tags = Tag.query.filter(
                    Tag.subject == Type_tag,
                    Tag.description.like(f'%父标签: {second_tag.tag_name}%')
                ).all()
                for third_tag in third_level_tags:
                    sub_sub_node = {
                        'id': third_tag.id,
                        'text': third_tag.tag_name,
                        'children': []
                    }
                    sub_node['children'].append(sub_sub_node)
                node['children'].append(sub_node)
            tree_data.append(node)
        return tree_data
    try:
        tag_tree = build_tree(Type_tag)
    except Exception as e:
        print(f"[ERROR] 构建标签树时出现异常: {e}")
        flash(f"标签树构建失败: {str(e)}", "error")
        return redirect(url_for('index'))
    return render_template(
        "Tags_Review.html",
        username=username,
        power=power,
        Type_tag=Type_tag,
        tag_tree=tag_tree
    )

@app.route('/api/get-questions-by-tag', methods=['GET'])
@require_login
def get_questions_by_tag():
    try:
        tag_id = request.args.get('tag_id', type=int)
        if not tag_id:
            return jsonify({"success": False, "message": "缺少 tag_id 参数"}), 400
        # 获取当前标签及其所有子标签
        all_tags = get_all_child_tags(tag_id)
        tag_ids = [tag.id for tag in all_tags]
        # 获取当前标签对象
        current_tag = db.session.get(Tag, tag_id)

        page = request.args.get('page', 1, type=int)
        per_page = 5  # 每页数量可自定义
        # 关联查询 StudyTag 和 Study
        query = db.session.query(Study).join(
            StudyTag, Study.id == StudyTag.study_id
        ).filter(StudyTag.tag_id.in_(tag_ids))  # 查询所有关联标签
        # 分页处理
        paginated_questions = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        # 获取当前用户的 username
        current_user_username = session['username']

        # 查询当前用户收藏的题目
        user_collected_questions = db.session.query(Study).filter(
            Study.original_study_id.in_([q.id for q in paginated_questions.items]),
            Study.Username == current_user_username
        ).all()

        collected_question_ids = {q.original_study_id: q for q in user_collected_questions}

        result = []
        for study in paginated_questions.items:
            if study.id in collected_question_ids:
                # 如果题目已被收藏，使用收藏记录中的数据
                collected_study = collected_question_ids[study.id]
                result.append({
                    "id": collected_study.id,
                    "username": collected_study.Username,
                    "content": collected_study.content,
                    "type": collected_study.Type,
                    "label": collected_study.Label,
                    "question_picture": collected_study.QuestionPicture,
                    "answer_picture": collected_study.AnswerPicture,
                    "finish_time": str(collected_study.FinishTime) if collected_study.FinishTime else None,
                    "recent_review_time": str(collected_study.RecentReviewTime) if collected_study.RecentReviewTime else None,
                    "current_weight": collected_study.CurrentWeight,
                    "review_accuracy": collected_study.review_accuracy
                })
            else:
                # 如果题目未被收藏，使用原始发布者的数据
                result.append({
                    "id": study.id,
                    "username": study.Username,
                    "content": study.content,
                    "type": study.Type,
                    "label": study.Label,
                    "question_picture": study.QuestionPicture,
                    "answer_picture": study.AnswerPicture,
                    "finish_time": str(study.FinishTime) if study.FinishTime else None,
                    "recent_review_time": str(study.RecentReviewTime) if study.RecentReviewTime else None,
                    "current_weight": study.CurrentWeight,
                    "review_accuracy": study.review_accuracy
                })

        return jsonify({
            "success": True,
            "questions": result,
            "has_next": paginated_questions.has_next,
            "has_prev": paginated_questions.has_prev,
            "total_pages": paginated_questions.pages,
            "total_items": paginated_questions.total,
            "current_page": paginated_questions.page,
            "prev_num": paginated_questions.prev_num if paginated_questions.has_prev else None,
            "next_num": paginated_questions.next_num if paginated_questions.has_next else None,
            "tag_name": current_tag.tag_name if current_tag else None
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": "服务器内部错误",
            "error": str(e)
        }), 500

def get_all_child_tags(tag_id):
    """迭代法获取所有子标签（包含当前标签）"""
    current_tag = db.session.get(Tag, tag_id)
    if not current_tag:
        return []
    
    all_tags = [current_tag]  # 包含当前标签
    stack = [current_tag]     # 模拟栈，存储待处理的标签
    
    while stack:
        parent_tag = stack.pop()
        # 查找当前标签的直接子标签（描述中包含父标签名）
        children = Tag.query.filter(
            Tag.subject == parent_tag.subject,
            Tag.description.like(f'%父标签: {parent_tag.tag_name}%')
        ).all()
        
        for child in children:
            if child not in all_tags:  # 去重
                all_tags.append(child)
                stack.append(child)  # 将子标签加入栈，继续处理
    
    return all_tags
    
# 替换正确答案图片
@app.route('/api/replace-answer/<int:question_id>', methods=['POST'])
def replace_answer(question_id):
    new_answer_file = request.files.get('replace-file')
    username = session.get('username')
    if new_answer_file and allowed_file(new_answer_file.filename):
        try:
            # 获取原图片路径和文件名
            original_answer_path = bp.get_original_path(question_id, "AnswerPicture")
            # 若原图片不存在，按 upload 逻辑新建图片
            unique_id = str(uuid.uuid4())[:8]
            # 重命名文件为用户名+编号.jpg
            answer_filename = f"{username}_answer_{unique_id}.jpg"
            answer_image_path = os.path.join(app.config['UPLOAD_FOLDER'], answer_filename)
            new_answer_file.save(answer_image_path)
            # 更新数据库中的 AnswerPicture 字段
            answer_image_path = answer_image_path.replace('\\', '/')
            bp.update_study_picture_table(question_id, "AnswerPicture", answer_image_path)
            return jsonify({"success": True, "message": "答案替换成功"})
        except Exception as e:
            print(f"处理解答图片时出错: {e}")
            return jsonify({"success": False, "message": "答案替换失败"})
    return jsonify({"success": False, "message": "无效的文件"})


# 记录复习结果
@app.route('/api/record-result/<int:question_id>', methods=['POST'])
def record_result(question_id):
    data = request.get_json()
    is_correct = data.get('is_correct')
    review_module = data.get('review_module')
    username = session.get('username')
    if review_module == 'tag_review':
        # 标签复习模块，插入新记录
        bp.insert_new_review_state(question_id, is_correct, username)
    else:
        # 错题本复习模块，更新已有记录
        bp.update_review_state(question_id, is_correct)
    # 更新 ReviewState 表中的 recent_review_time 状态
    bp.update_recent_review_time(question_id)
    # 更新同类标签权重
    stability=bp.adjust_decay_coefficient(get_correct_ToYesDay_data(username))
    bp.update_Weights_Review_label(question_id, username,stability)
    # 同步更新用户 - 权重 - 标签表的权重数据
    bp.recalculate_user_tag_weights(username)
    # 更新复习正确率
    update_review_accuracy(question_id)
    # 生成并保存图表
    success, msg = generate_and_save_charts(username)
    session['reviewcomplete'] = msg
    return jsonify({"success": True, "message": "结果记录成功"})


# 获取新题目 API
@app.route('/api/get-new-question', methods=['GET'])
def get_new_question():
    try:
        username = session.get('username')
        studydata = bp.get_sql_studydata(username)
        Wrong = bp.get_sql_review(username, datetime.date.today())
        if not Wrong:
            TodayReview = bp.weighted_random_choice(username, studydata)
        else:
            QuestionID = Wrong[0][2]
            TodayReview = bp.get_sql_studyForID(QuestionID)
        if TodayReview:
            return jsonify({
                "success": True,
                "question": {
                    "id": TodayReview['id'],
                    "type": TodayReview['type'],
                    "content": TodayReview['content'],
                    "label": TodayReview['label'],
                    "QuestionPicture": TodayReview['question_picture'],
                    "AnswerPicture": TodayReview['answer_picture'],
                    "FinishTime": TodayReview['finish_time'],
                    "recent_review_time": TodayReview['recent_review_time'],
                    "review_accuracy": TodayReview['review_accuracy'],
                    "current_weight": TodayReview['weight']
                }
            })
        else:
            return jsonify({"success": False, "message": "没有可用的题目"})
    except Exception as e:
        print(f"get-new-question 错误: {e}")
        return jsonify({"success": False, "message": "服务器内部错误"}), 500

@app.route('/api/random-question-by-tag', methods=['GET'])
@require_login
def random_question_by_tag():
    try:
        tag_id = request.args.get('tag_id', type=int)
        if not tag_id:
            return jsonify({"success": False, "message": "缺少 tag_id 参数"}), 400
        # 获取当前标签及其所有子标签
        all_tags = get_all_child_tags(tag_id)
        tag_ids = [tag.id for tag in all_tags]
        # 获取当前用户的 username
        current_user_username = session['username']
        # 查询当天已经推送过的题目
        now = datetime.date.today()
        pushed_questions = db.session.query(ReviewState.WrongQuestionID).filter(
            ReviewState.username == current_user_username,
            ReviewState.push_date == now
        ).all()
        pushed_question_ids = [row[0] for row in pushed_questions]
        # 关联查询 StudyTag 和 Study，并排除当天已经推送过的题目
        query = db.session.query(Study).join(
            StudyTag, Study.id == StudyTag.study_id
        ).filter(
            StudyTag.tag_id.in_(tag_ids),
            ~Study.id.in_(pushed_question_ids)
        )
        # 按记忆曲线权重随机抽取题目
        question = query.order_by(db.func.random() * Study.CurrentWeight).first()
        if question:
            # 查询当前用户是否收藏了该题目
            user_collected_question = db.session.query(Study).filter(
                Study.original_study_id == question.id,
                Study.Username == current_user_username
            ).first()
            if user_collected_question:
                # 如果题目已被收藏，使用收藏记录中的数据
                result = {
                    "id": user_collected_question.id,
                    "username": user_collected_question.Username,
                    "content": user_collected_question.content,
                    "type": user_collected_question.Type,
                    "label": user_collected_question.Label,
                    "question_picture": user_collected_question.QuestionPicture,
                    "answer_picture": user_collected_question.AnswerPicture,
                    "finish_time": str(user_collected_question.FinishTime) if user_collected_question.FinishTime else None,
                    "recent_review_time": str(user_collected_question.RecentReviewTime) if user_collected_question.RecentReviewTime else None,
                    "current_weight": user_collected_question.CurrentWeight,
                    "review_accuracy": user_collected_question.review_accuracy
                }
            else:
                # 如果题目未被收藏，使用原始发布者的数据
                result = {
                    "id": question.id,
                    "username": question.Username,
                    "content": question.content,
                    "type": question.Type,
                    "label": question.Label,
                    "question_picture": question.QuestionPicture,
                    "answer_picture": question.AnswerPicture,
                    "finish_time": str(question.FinishTime) if question.FinishTime else None,
                    "recent_review_time": str(question.RecentReviewTime) if question.RecentReviewTime else None,
                    "current_weight": question.CurrentWeight,
                    "review_accuracy": question.review_accuracy
                }
            # 将该错题推送记录添加到 ReviewState 表中
            new_review_state = ReviewState(
                username=current_user_username,
                WrongQuestionID=question.id,
                push_date=now
            )
            db.session.add(new_review_state)
            db.session.commit()
            return jsonify({
                "success": True,
                "question": result
            })
        else:
            return jsonify({"success": False, "message": "没有符合条件的题目"}), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "服务器内部错误",
            "error": str(e)
        }), 500
    
@app.route('/api/collect_question', methods=['POST'])
def collect_question():
    data = request.get_json()
    original_study_id = data.get('original_study_id')
    username = session['username']

    original_question = Study.query.filter_by(
        id=original_study_id,
        original_study_id=None,
        Username=username
    ).first()
    if original_question:
        return jsonify({"success": False, "message": "你不能收藏自己上传的题目"}), 400

    existing_question = Study.query.filter_by(
        original_study_id=original_study_id,
        Username=username
    ).first()
    if existing_question:
        return jsonify({"success": False, "message": "该题目已存在于你的错题本中"}), 400

    original_question = db.session.get(Study, original_study_id)
    if not original_question:
        return jsonify({"success": False, "message": "原始题目不存在"}), 404

    new_study = Study(
        Username=username,
        content=original_question.content,
        Type=original_question.Type,
        Label=original_question.Label,
        FinishTime=datetime.date.today(),
        QuestionPicture=original_question.QuestionPicture,
        AnswerPicture=original_question.AnswerPicture,
        CurrentWeightUpdateTime=datetime.date.today(),
        review_accuracy=0,
        original_study_id=original_study_id
    )
    db.session.add(new_study)
    try:
        db.session.commit()
        new_study_id = new_study.id
        return jsonify({"success": True, "message": "题目收藏成功", "new_study_id": new_study_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"收藏失败: {str(e)}"}), 500

@app.route('/api/check-question-status', methods=['POST'])
@require_login
def check_question_status():
    data = request.get_json()
    original_study_id = data.get('original_study_id')
    username = session.get('username')
    # 查询原始题目
    original_question = Study.query.get(original_study_id)
    if not original_question:
        return jsonify({"success": False, "message": "原始题目不存在"})
    # 检查用户是否为原始发布者
    is_publisher = original_question.Username == username
    # 检查题目是否已被收藏
    existing_question = Study.query.filter_by(
        original_study_id=original_study_id,
        Username=username
    ).first()
    is_collected = bool(existing_question)
    result = {
        "success": True,
        "is_publisher": is_publisher,
        "is_collected": is_collected
    }
    if is_collected:
        result["study_id"] = existing_question.id
    return jsonify(result)

# 获取当日已复习错题（分页）
@app.route('/api/get-reviewed-questions', methods=['GET'])
def get_reviewed_questions():
    username = session.get('username')
    page = request.args.get('page', 1, type=int)
    per_page = 5  # 每页显示 5 条记录
    Reviewed = bp.get_sql_reviewed(username, datetime.date.today())
    total_pages = (len(Reviewed) + per_page - 1) // per_page  # 计算总页数
    start = (page - 1) * per_page
    end = start + per_page
    paginated_reviewed = Reviewed[start:end]
    has_next = end < len(Reviewed)
    has_prev = start > 0
    result = []
    for review in paginated_reviewed:
        question_id = review[0]
        study = bp.get_sql_studyForID(question_id)
        if study:
            result.append({
                "id": study['id'],
                "type": study['type'],
                "content": study['content'],
                "label": study['label'],
                "QuestionPicture": study['question_picture'],
                "AnswerPicture": study['answer_picture'],
                "FinishTime": study['finish_time'],
                "recent_review_time": study['recent_review_time'],
                "weight": study['weight'],
                "review_accuracy": study['review_accuracy'],
                "is_correct": review[4]  # 假设 is_correct 在这个位置
            })
    return jsonify({
        "success": True,
        "questions": result,
        "has_next": has_next,
        "has_prev": has_prev,
        "total_pages": total_pages  # 添加总页数字段
    })



# 生成并保存图表
def generate_and_save_charts(username):
    try:
        # 生成复习情况折线图|题型科目占比饼图|柱状折线可视化错题与复习图|复习正确率折线图
        line_charts_info, success, msg = generate_error_review_line(username)
        type_study_pie_charts_info, success, msg = generate_type_study_pie(username)
        review_study_bar_line_charts_info1, success, msg = generate_review_study_bar_line(username, "Atom")
        review_study_bar_line_charts_info2, success, msg = generate_review_study_bar_line(username)
        correctZheXian, success, msg = generate_correct_rate_chart(username)
        user_tag_heatmap, success, msg = generate_user_tag_heatmap_file(username)
        if success:
            # 保存图表信息到数据库
            save_success1, save_msg = save_charts_to_db(username, line_charts_info, chart_types=["错题复习情况"])
            save_success2, save_msg = save_charts_to_db(username, type_study_pie_charts_info,
                                                        chart_types=["各科目题目的占比"])
            save_success3, save_msg = save_charts_to_db(username, review_study_bar_line_charts_info1,
                                                        chart_types=["复习与学习综合图（原子标签版）"])
            save_success4, save_msg = save_charts_to_db(username, review_study_bar_line_charts_info2,
                                                        chart_types=["复习与学习综合图（组合标签版）"])
            save_success5, save_msg = save_charts_to_db(username, correctZheXian, chart_types=["复习正确率折线图"])
            save_success6, save_msg = save_charts_to_db(username, user_tag_heatmap, chart_types=["用户标签热力图"])
            if save_success1 and save_success2 and save_success3 and save_success4 and save_success5 and save_success6:
                print("复习完成并更新图表")
                return True, "复习完成并更新图表"
            else:
                return False, save_msg
        else:
            return False, msg
    except Exception as e:
        print(f"生成并保存图表时出错: {e}")
        return False, str(e)


# 计算并更新复习正确率
def update_review_accuracy(study_id):
    # 查询该题目的所有复习记录
    username=session['username']
    review_query = "SELECT COUNT(*) FROM ReviewState WHERE WrongQuestionID =? AND reviewed = 1 AND username=?"
    total_reviews = sp.sql_execute2(review_query, (study_id,username), commit=False)[0][0]
    correct_query = "SELECT COUNT(*) FROM ReviewState WHERE WrongQuestionID =? AND reviewed = 1 AND is_correct = 1 AND username=?"
    correct_reviews = sp.sql_execute2(correct_query, (study_id,username), commit=False)[0][0]
    if total_reviews == 0:
        accuracy = 0
    else:
        accuracy = correct_reviews / total_reviews
    # 更新 study 表中的复习正确率
    update_query = "UPDATE study SET review_accuracy =? WHERE id =? and username=?"
    sp.sql_cursor_execute(update_query, (accuracy, study_id,username))

# 学习数据可视化
@app.route('/DataChart')
@require_login
def DataChartPage():
    username=session['username']
    user=bp.get_sql_user(username)
    study_counts,review_counts=get_user_study_and_review_counts(username)
    return render_template("Learn_Data_Visualization.html",user=user,power=session['power'],study_counts=study_counts,review_counts=review_counts)

# 上传错题
@app.route('/uploadpage')
@require_login
def uploadpage():
    user=bp.get_sql_user(session['username'])
    labeldata=bp.get_sql_Only_label("upload")
    return render_template("upload.html",user=user,labeldata=labeldata,power=session['power'])

@app.route('/api/tags', methods=['GET'])
def get_tags():
    subject = request.args.get('subject')
    search = request.args.get('search', '')
    # 查询对应科目的标签
    query = """
        SELECT t.id, t.tag_name, t.color, 
               CASE 
                   WHEN t.description LIKE '父标签: %' THEN SUBSTR(t.description, 6) 
                   ELSE NULL 
               END as parent_tag
        FROM Tag t
        WHERE t.subject = ? AND t.tag_name LIKE ?
    """
    rows = sp.sql_execute2(query, (subject, f'%{search}%'),commit=False)
    tag_groups = {}
    for row in rows:
        tag_id, tag_name, color, parent_tag = row
        if parent_tag not in tag_groups:
            tag_groups[parent_tag] = {
                'text': parent_tag,
                'children': []
            }
        tag_groups[parent_tag]['children'].append({
            'id': f'#{tag_name}',
            'text': f'#{tag_name}',
            'color': color
        })
    results = list(tag_groups.values())
    return jsonify(results)

@app.route('/upload', methods=['POST'])
@require_login
def upload():
    # 获取表单中的文字内容
    text_content = request.form.get('text_content')
    # 获取表单中的题目类型
    question_type = request.form.get('question_type')
    # 获取上传的题目图片和解答图片
    question_file = request.files.get('question_file')
    answer_file = request.files.get('answer_file')
    # 获取用户用户名
    username = session.get('username', 'anonymous')
    # 处理标签
    selected_tags = request.form.getlist('tags')
    custom_tags = []
    if request.form.get('custom_label_checkbox') == "on":
        custom_label1 = request.form.get('custom_label1')
        custom_label2 = request.form.get('custom_label2')
        custom_label3 = request.form.get('custom_label3')
        for label in [custom_label1, custom_label2, custom_label3]:
            if label:
                custom_tags.append(f"#{label}")
    all_tags = selected_tags + custom_tags
    Label = ''.join(all_tags)
    question_image_path = None
    answer_image_path = None
    if question_file and allowed_file(question_file.filename):
        # 生成唯一的编号
        unique_id = str(uuid.uuid4())[:8]
        # 重命名文件为用户名+编号.jpg
        question_filename = f"{username}_question_{unique_id}.jpg"
        question_image_path = os.path.join(app.config['UPLOAD_FOLDER'], question_filename)
        question_file.save(question_image_path)
    if answer_file and allowed_file(answer_file.filename):
        # 生成唯一的编号
        unique_id = str(uuid.uuid4())[:8]
        # 重命名文件为用户名+编号.jpg
        answer_filename = f"{username}_answer_{unique_id}.jpg"
        answer_image_path = os.path.join(app.config['UPLOAD_FOLDER'], answer_filename)
        answer_file.save(answer_image_path)
    if question_image_path or answer_image_path:
        # 替换路径中的反斜杠为正斜杠
        question_image_path = question_image_path.replace('\\', '/') if question_image_path else None
        answer_image_path = answer_image_path.replace('\\', '/') if answer_image_path else None
        # 保存文字内容和图片路径到数据库
        sp.sql_cursor_execute('INSERT INTO study (username, content, Type, Label, QuestionPicture, AnswerPicture, FinishTime) VALUES (?, ?, ?, ?, ?, ?, ?)',
                              (username, text_content, question_type, Label, question_image_path, answer_image_path, datetime.date.today()))
        # 获取新插入的 study 记录的 ID
        study_id_query = "SELECT MAX(id) FROM study WHERE username =?;"
        study_id = sp.sql_execute2(study_id_query, (username,), commit=False)[0][0]
        labeldata = bp.get_sql_Only_label("upload")
        # 处理自定义标签，检查并插入
        for tag in custom_tags:
            tag_name = tag[1:]  # 去除 # 符号
            # 检查该科目下是否已有该标签
            check_query = "SELECT id FROM Tag WHERE tag_name =? AND subject =?"
            existing_tag = sp.sql_execute2(check_query, (tag_name, question_type), commit=False)
            if not existing_tag:
                # 若不存在，则插入新标签
                insert_query = "INSERT INTO Tag (tag_name, subject, color, description) VALUES (?,?, '#e8ddff',?)"
                sp.sql_cursor_execute(insert_query, (tag_name, question_type, "父标签: 自定义-"+question_type))
        
        # 更新 study_tag 表
        for tag in all_tags:
            tag_name = tag[1:]  # 去除 # 符号
            tag_id_query = "SELECT id FROM Tag WHERE tag_name =? AND subject =?"
            tag_id = sp.sql_execute2(tag_id_query, (tag_name, question_type), commit=False)[0][0]
            insert_study_tag_query = "INSERT INTO StudyTag (study_id, tag_id) VALUES (?,?)"
            sp.sql_cursor_execute(insert_study_tag_query, (study_id, tag_id))
        # 更新相关label权重，每当有多一道相关标签的题目被上传为错题，就增加所有带该标签问题的复习权重
        for tag in all_tags:
            bp.update_weightForlabel(tag)
        #同步更新用户-权重-标签表的权重数据
        bp.recalculate_user_tag_weights(username)
        # 生成错题上传数量折线图|题型科目占比饼图|柱状折线可视化错题与复习图|复习正确率折线图|标签热力图
        charts_info, success, msg = generate_error_upload_line(username)
        type_study_pie_charts_info, success, msg = generate_type_study_pie(username)
        review_study_bar_line_charts_info1, success, msg = generate_review_study_bar_line(username, "atom")
        review_study_bar_line_charts_info2, success, msg = generate_review_study_bar_line(username)
        correctZheXian, success, msg = generate_correct_rate_chart(username)
        user_tag_heatmap, success, msg = generate_user_tag_heatmap_file(username)
        if success:
            # 保存图表信息到数据库
            save_success1, save_msg = save_charts_to_db(username, charts_info, chart_types=["错题上传数量"])
            save_success2, save_msg = save_charts_to_db(username, type_study_pie_charts_info, chart_types=["各科目题目的占比"])
            save_success3, save_msg = save_charts_to_db(username, review_study_bar_line_charts_info1, chart_types=["复习与学习综合图（原子标签版）"])
            save_success4, save_msg = save_charts_to_db(username, review_study_bar_line_charts_info2, chart_types=["复习与学习综合图（组合标签版）"])
            save_success5, save_msg = save_charts_to_db(username, correctZheXian, chart_types=["复习正确率折线图"])
            save_success6, save_msg = save_charts_to_db(username, user_tag_heatmap, chart_types=["用户标签热力图"])
            if save_success1 and save_success2 and save_success3 and save_success4 and save_success5 and save_success6:
                return render_template("upload.html", message="上传成功并更新图表！", labeldata=labeldata, power=session['power'])
            else:
                return render_template("upload.html", message=save_msg, labeldata=labeldata, power=session['power'])
        else:
            return render_template("upload.html", message=msg, labeldata=labeldata, power=session['power'])
    else:
        return render_template("upload.html", message="上传失败，文件格式不支持！", labeldata=labeldata, power=session['power'])


@app.route('/uploads/<filename>')
@require_login
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 查看错题详情
@app.route('/Wrong/<int:Wrong_id>')
@require_login
def Wrong_detail(Wrong_id):
    username=session['username']
    # 从数据库中查询错题内容
    res = sp.sql_execute_select("SELECT * FROM study WHERE id = ?" , (Wrong_id,))
    if res and username==res[0][1]:
        return render_template('Wrong_detail_owner.html', Wrong=res[0])  
    elif session['power']=='admin':
        return render_template('Wrong_detail_owner.html', Wrong=res[0]) 
    elif username!=res[0][1]:
        return render_template('Wrong_detail.html', Wrong=res[0]) 
    else:
        return "帖子未找到", 404

@app.route('/update_study', methods=['POST'])
@require_login
def update_question():
    question_id = request.form.get('question_id')
    question_type = request.form.get('question_type')
    question_label = request.form.get('question_label')
    question_body = request.form.get('question_body')
    question_image = request.files.get('question_image')
    answer_image = request.files.get('answer_image')
    username=session['username']
    if question_image and allowed_file(question_image.filename):
        # 获取原图片路径
        original_path = bp.get_original_path(question_id,"QuestionPicture")
        # 删除原图片文件
        if original_path and os.path.exists(original_path):
            os.remove(original_path)
        # 保存新的问题图片
        new_question_filename = bp.save_answer_image(question_image,app.config['UPLOAD_FOLDER'],username,"question")
        # 更新 Study 表中的 QuestionPicture 字段
        bp.update_study_picture_table(question_id, "QuestionPicture", new_question_filename)
    if answer_image and allowed_file(answer_image.filename):
        # 获取原图片路径
        original_path = bp.get_original_path(question_id,"AnswerPicture")
        # 删除原图片文件
        if original_path and os.path.exists(original_path):
            os.remove(original_path)
        # 保存新的解答图片
        new_answer_filename = bp.save_answer_image(answer_image,app.config['UPLOAD_FOLDER'],username,"answer")
        # 更新 Study 表中的 AnswerPicture 字段
        bp.update_study_picture_table(question_id, "AnswerPicture", new_answer_filename)
    # 更新 Study 表中的其他字段
    bp.update_study_table(question_body,question_type,question_id,question_label)
    # 更新数据库逻辑
    return redirect(url_for('Wrong_detail', Wrong_id=question_id))

@app.route('/delete_question/<int:question_id>', methods=['DELETE'])
@require_login
def delete_question(question_id):
    Wrong_Owner=bp.get_sql_Wrong_Owner(question_id)
    username=session['username']
    user=bp.get_sql_user(username)
    if Wrong_Owner != username or user[0][3] !="admin" or user[0][3] !="CommunityAdmin":
        return jsonify({'success': False, 'message': '你并不是帖主也并非管理员'})
    study=bp.get_sql_studyForID(question_id)
    if study:
        bp.Delete_StudyData(question_id)
        return jsonify({'success': True, 'message': '学习记录删除成功'})
    else:
        return jsonify({'success': False, 'message': '学习记录不存在'})

@app.route('/delete_post/<int:post_id>', methods=['DELETE'])
@require_login
def delete_post(post_id):
    Post_Owner=bp.get_sql_Post_Owner(post_id)
    username=session['username']
    user=bp.get_sql_user(username)
    if Post_Owner != username and user[0][3] !="admin" and user[0][3] !="CommunityAdmin":
        return jsonify({'success': False, 'message': '你并不是帖主也并非管理员'})
    post=bp.get_sql_postForID(post_id)
    if post:
        bp.Delete_Post(post_id)
        forum = request.args.get('section')
        return jsonify({'success': True, 'message': '帖子删除成功','section':forum})
    else:
        return jsonify({'success': False, 'message': '该帖子不存在'})

import email_centain as em
# 路由：进入修改密码页面
@app.route('/change_password', methods=['GET', 'POST'])
@require_login
def change_password():
    user=bp.get_sql_user(session['username'])
    email=user[0][2]
    if request.method == 'POST':
        verification_code = str(random.randint(100000, 999999))  # 生成验证码
        # 存储验证码到 session
        session['verification_code'] = verification_code
        session['email'] = email  # 存储邮箱以便后续使用
        # 这里你可以发送验证码到邮箱，使用第三方邮件服务
        em.send_verification_email(email,verification_code)
        return redirect(url_for('verify_code'))  # 跳转到验证码验证页面
    return render_template('change_password.html',email=email)  # 显示修改密码页面

# 路由：进入验证码验证页面
@app.route('/verify_code', methods=['GET', 'POST'])
@require_login
def verify_code():
    if request.method == 'POST':
        input_code = request.form['verification_code']
        
        if input_code == session.get('verification_code'):
            return redirect(url_for('set_new_password'))  # 验证成功，跳转到设置新密码页面
        else:
            return "验证码错误，请重新输入。"

    return render_template('verify_code.html')  # 显示验证码输入页面

# 路由：设置新密码
@app.route('/set_new_password', methods=['GET', 'POST'])
@require_login
def set_new_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        tryAgain = request.form['tryAgain']
        username=session['username']
        if tryAgain==new_password:
             # 生成新的盐值(hex()转字符串，不如数据库中是BLOB形式)
            salt = pe.generate_salt().hex()
            # 使用新盐值加密新密码
            hashed_password = pe.hash_password(new_password, salt)
            # 更新密码逻辑，可以将新密码存储到数据库中
            update_password="update user set password= ? ,salt = ? where username=?"
            sp.sql_cursor_execute(update_password,(hashed_password, salt, username))
            # 假设更新成功，返回成功信息
            session['login'] is None
            return redirect(url_for('index'))
        else:
            return redirect(url_for('set_new_password'))

    return render_template('set_new_password.html')  # 显示设置新密码页面

# 把 max 和 min 函数注入到 Jinja2 环境中
app.jinja_env.globals.update(max=max, min=min)
@app.route('/search', methods=['GET'])
@require_login
def search():
    keyword = request.args.get('keyword')
    selected_categories = request.args.getlist('categories') or ['新闻资讯', '社区帖子', '社区评论', '学习数据专区', '通知']
    if not keyword:
        return "请提供搜索关键词", 400
    page = int(request.args.get('page', 1))
    per_page = 10
    # 执行搜索
    results, total_results = bp.search_database(keyword)
    all_results = []
    # 将所有结果按分类顺序合并到一个列表中
    for category in selected_categories:
        for result in results[category]:
            all_results.append((category, result))
            
    start = (page - 1) * per_page
    end = start + per_page
    paginated_all_results = all_results[start:end]
    # 重新组织分页后的结果，并对结果中的关键词进行标红处理
    paginated_results = {category: [] for category in selected_categories}
    for category, result in paginated_all_results:
        highlighted_result = []
        for item in result:
            if isinstance(item, str):
                # 使用正则表达式将关键词替换为带有红色样式的 HTML 标签 && html中使用safe过滤器，使得jinja不去转义
                highlighted_item = re.sub(re.escape(keyword), f'<span style="color: red;">{keyword}</span>', item, flags=re.IGNORECASE)
                highlighted_result.append(highlighted_item)
            else:
                highlighted_result.append(item)
        paginated_results[category].append(highlighted_result)

    total_count = len(all_results)
    total_pages = (total_count + per_page - 1) // per_page

    return render_template('search_results.html', keyword=keyword, results=paginated_results,
                           selected_categories=selected_categories, page=page, total_pages=total_pages,
                           total_count=total_count)

# sql连接协议
# 获取项目根目录
basedir = os.path.abspath(os.path.dirname(__file__))
# 构建数据库文件的绝对路径
db_path = os.path.join(basedir, "config", "db", "cst21014.db")
# 配置 SQLAlchemy 的数据库连接 URI
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 数据库模型'''''''''''''''''''''
class Forum(db.Model):
    __tablename__ = 'Forum'
    PostingsID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Title = db.Column(db.String(20))
    Username = db.Column(db.String(20), db.ForeignKey('User.Username'))  # 外键关联 User.Username
    PostingsTime = db.Column(db.String(20))
    IpLoc = db.Column(db.String(20))
    tag = db.Column(db.String(50))
    PostingsText = db.Column(db.Text)
    PostingsPicture = db.Column(db.String(70))
    PostingsSupport = db.Column(db.Integer)
    PostingsViewNum = db.Column(db.Integer, default=1)

class User(db.Model):
    __tablename__ = 'User'
    Username = db.Column(db.String(20), primary_key=True)
    Password = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(30))
    Power = db.Column(db.String(20))  # 原 Role 字段
    StudyPlan = db.Column(db.Text)
    state = db.Column(db.Boolean, default=0)
    salt = db.Column(db.Text)
    bafaKey = db.Column(db.Text)

class UserChart(db.Model):
    __tablename__ = 'UserChart'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), db.ForeignKey('User.Username', ondelete='CASCADE'))
    chart_type = db.Column(db.String(50))
    chart_path = db.Column(db.String(200))

# 公告模型
class Notice(db.Model):
    __tablename__ = 'Notice'
    nid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NoticeName = db.Column(db.String(20))
    username = db.Column(db.String(20), db.ForeignKey('User.Username'))
    Notice_date = db.Column(db.String(20))
    Notice_content = db.Column(db.Text)
    NoticePicture = db.Column(db.String(70))
    power = db.Column(db.String(20))
    notice_type = db.Column(db.String(20), default='global')
    user = db.relationship('User', backref=db.backref('notices', lazy=True))

# 点赞记录模型
class Likes(db.Model):
    __tablename__ = 'Likes'
    Username = db.Column(db.String(20), db.ForeignKey('User.Username'), primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('Forum.PostingsID'), primary_key=True)

# 交流评论模型
class Comment(db.Model):
    __tablename__ = 'Comment'
    CommentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PostingsID = db.Column(db.Integer, db.ForeignKey('Forum.PostingsID'))
    Username = db.Column(db.String(20), db.ForeignKey('User.Username'))
    Comment = db.Column(db.Text)
    CommentTime = db.Column(db.String(30))
    CommentImg = db.Column(db.String(70))

# 爬虫获取的数据模型
class CrawlerData(db.Model):
    __tablename__ = 'CrawlerData'
    WebId = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(20))
    UpdateTime = db.Column(db.String(30))
    Publisher = db.Column(db.String(20))
    Content = db.Column(db.Text)
    WebsiteLink = db.Column(db.String(100))
    WebsitePicture = db.Column(db.String(70))

# 学习数据模型
class Study(db.Model):
    __tablename__ = 'Study'
    id = db.Column(db.Integer, primary_key=True)
    Username = db.Column(db.String(20), db.ForeignKey('User.Username'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    Type = db.Column(db.String(20), nullable=False)
    Label = db.Column(db.Text, nullable=False)
    QuestionPicture = db.Column(db.String(255))
    AnswerPicture = db.Column(db.String(255))
    FinishTime = db.Column(db.Date)
    CurrentWeight = db.Column(db.Float, default=1)
    CurrentWeightUpdateTime = db.Column(db.String(30))
    review_accuracy = db.Column(db.Float, default=0.0)
    RecentReviewTime = db.Column(db.Date)
    original_study_id=db.Column(db.Integer)

# 复习数据模型
class ReviewState(db.Model):
    __tablename__ = 'ReviewState'
    Rid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), db.ForeignKey('User.Username'), nullable=False)
    WrongQuestionID = db.Column(db.Integer, db.ForeignKey('Study.id'), nullable=False)
    push_date = db.Column(db.Date, nullable=False)
    reviewed = db.Column(db.Boolean, default=False)
    is_correct = db.Column(db.Boolean, default=False)
    recent_review_time = db.Column(db.DateTime)

class Tag(db.Model):
    __tablename__ = 'Tag'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tag_name = db.Column(db.String(40), nullable=False, unique=True)
    subject = db.Column(db.String(20))
    color = db.Column(db.String(20))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=func.current_timestamp())

from sqlalchemy import PrimaryKeyConstraint

class StudyTag(db.Model):
    __tablename__ = 'StudyTag'
    study_id = db.Column(db.Integer, nullable=False)
    tag_id = db.Column(db.Integer, nullable=False)
    __table_args__ = (
        db.ForeignKeyConstraint(['study_id'], ['Study.id'], ondelete='CASCADE'),
        db.ForeignKeyConstraint(['tag_id'], ['Tag.id'], ondelete='CASCADE'),
        PrimaryKeyConstraint ('study_id', 'tag_id', name='pk_study_tag')
    )

class UserTagWeight(db.Model):
    __tablename__ = 'UserTagWeight'
    user_username = db.Column(db.String(20))
    tag_id = db.Column(db.Integer)
    weight = db.Column(db.Float, default=0)
    __table_args__ = (
        db.ForeignKeyConstraint(['user_username'], ['User.Username'], ondelete='CASCADE'),
        db.ForeignKeyConstraint(['tag_id'], ['Tag.id']),
        PrimaryKeyConstraint ('user_username', 'tag_id', name='pk_UserTagWeight')
    )

# 获取单个帖子详情接口
@app.route('/api/community/posts/<int:post_id>', methods=['GET'])
@require_permission(['admin', 'CommunityAdmin'])
def get_post(post_id):
    post = Forum.query.get(post_id)
    if not post:
        return jsonify({'code': 404, 'message': '帖子不存在'}), 404
    return jsonify({
        'code': 200,
        'message': '获取帖子详情成功',
        'data': post_to_dict(post)
    })

@app.route('/api/community/posts/<int:post_id>', methods=['DELETE'])
@require_login
def admin_delete_post(post_id):
    try:
        username = session['username']
        user = User.query.filter_by(Username=username).first()
        # 获取帖子所有者
        post = Forum.query.get(post_id)
        if not post:
            return jsonify({'code': 404, 'message': '帖子不存在'}), 404
        post_owner = post.Username
        # 权限验证：帖主或管理员（Power 为 admin/CommunityAdmin）
        if post_owner != username and user.Power not in ["admin", "CommunityAdmin"]:
            return jsonify({'code': 403, 'message': '你不是帖主也不是管理员'}), 403
        # 删除帖子
        db.session.delete(post)
        db.session.commit()
        return jsonify({'code': 200, 'message': '帖子删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'删除失败：{str(e)}'}), 500

@app.route('/api/community/posts', methods=['GET'])
@require_permission(['admin', 'CommunityAdmin'])
def get_posts():
    page = int(request.args.get('page', 1))  # 获取页码，默认第1页
    per_page = 6  # 每页显示6条
    # 解析查询参数
    username = request.args.get('username')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    keyword = request.args.get('keyword')
    query = Forum.query
    # 动态添加筛选条件
    if username:
        query = query.filter_by(Username=username)
    if start_time:
        query = query.filter(Forum.PostingsTime >= start_time)
    if end_time:
        query = query.filter(Forum.PostingsTime <= end_time)
    if keyword:
        query = query.filter(Forum.PostingsText.like(f'%{keyword}%'))
    # 分页查询
    paginated_data = query.order_by(Forum.PostingsTime.desc()).paginate(page=page, per_page=per_page, error_out=False)
    posts = paginated_data.items
    total_pages = paginated_data.pages
    current_page = paginated_data.page
    return jsonify({
        'code': 200,
        'message': '获取帖子成功',
        'data': [post_to_dict(post) for post in posts],
        'pagination': {
            'current_page': current_page,
            'total_pages': total_pages
        }
    })

def post_to_dict(post):
    return {
        'post_id': post.PostingsID,
        'title': post.Title,
        'username': post.Username,
        'postings_time': post.PostingsTime,
        'ip_loc': post.IpLoc,
        'tag': post.tag,
        'postings_text': post.PostingsText,
        'postings_picture': post.PostingsPicture,
        'postings_support': post.PostingsSupport,
        'postings_view_num': post.PostingsViewNum
    }
# 评论管理模块
# 获取所有评论
@app.route('/api/admin/comments', methods=['GET'])
@require_permission(['admin', 'CommunityAdmin'])
def get_all_comments():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    keyword = request.args.get('keyword')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    query = Comment.query
    if keyword:
        query = query.filter(Comment.Comment.like(f'%{keyword}%'))
    if start_time:
        query = query.filter(Comment.CommentTime >= start_time)
    if end_time:
        query = query.filter(Comment.CommentTime <= end_time)
    paginated = query.order_by(Comment.CommentTime.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        'code': 200,
        'message': '获取评论列表成功',
        'data': [
            {
                'CommentID': c.CommentID,
                'PostingsID': c.PostingsID,
                'Username': c.Username,
                'Comment': c.Comment,
                'CommentTime': c.CommentTime,
                'CommentImg': c.CommentImg
            }
            for c in paginated.items
        ],
        'pagination': {
            'current_page': paginated.page,
            'total_pages': paginated.pages
        }
    })

# 删除评论
@app.route('/api/admin/comments/<int:comment_id>', methods=['DELETE'])
@require_permission(['admin', 'CommunityAdmin'])
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'code': 404, 'message': '评论不存在'}), 404
    try:
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'code': 200, 'message': '评论删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'删除失败: {str(e)}'}), 500

# 用户管理路由
@app.route('/api/user/list', methods=['GET'])
@require_permission(['admin'])
def get_users():
    page = int(request.args.get('page', 1))
    per_page = 6
    keyword = request.args.get('keyword', '')
    query = User.query.filter(
        User.Username.contains(keyword) |
        User.email.contains(keyword)
    )
    paginated_data = query.order_by(User.Username.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        'code': 200,
        'message': '获取用户列表成功',
        'data': [user_to_dict(user) for user in paginated_data.items],
        'pagination': {
            'current_page': paginated_data.page,
            'total_pages': paginated_data.pages
        }
    })

@app.route('/api/user/ban/<username>', methods=['POST'])
@require_permission(['admin'])
def ban_user(username):
    try:
        user = User.query.get(username)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        data = request.get_json()
        state = data.get('state', True)  # 默认进行封禁操作
        user.state = state
        db.session.commit()
        message = '用户已封禁' if state else '用户已解封'
        return jsonify({'code': 200, 'message': message})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'操作失败：{str(e)}'}), 500

@app.route('/api/user/promote/<username>', methods=['POST'])
@require_permission(['admin'])
def promote_user(username):
    try:
        user = User.query.get(username)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        if user.Power == 'user':
            user.Power = 'CommunityAdmin'
            message = '权限提升为社区管理员成功'
        elif user.Power == 'CommunityAdmin':
            user.Power = 'user'
            message = '权限已撤销，恢复为普通用户'
        db.session.commit()
        return jsonify({'code': 200, 'message': message})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'操作失败：{str(e)}'}), 500

def user_to_dict(user):
    return {
        'username': user.Username,
        'email': user.email,
        'power': user.Power,
        'state': user.state,
        'study_plan': user.StudyPlan,
        'salt': user.salt
    }

@app.route('/api/<string:notice_type>-notice', methods=['GET'])
@require_permission(['admin', 'CommunityAdmin','user'], notice_type='<notice_type>')
def get_notices(notice_type):
    # 先根据公告类型筛选数据
    base_query = Notice.query.filter(Notice.notice_type == notice_type)
    page = int(request.args.get('page', 1))
    per_page = 6
    username = request.args.get('username')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    keyword = request.args.get('keyword')
    # 在筛选出的公告类型数据基础上进行搜索条件筛选
    if username:
        base_query = base_query.filter(Notice.username == username)
    if start_time:
        try:
            start_date = datetime.datetime.strptime(start_time, '%Y-%m-%d')
            base_query = base_query.filter(Notice.Notice_date >= start_date)
        except ValueError:
            pass
    if end_time:
        try:
            end_date = datetime.datetime.strptime(end_time, '%Y-%m-%d')
            base_query = base_query.filter(Notice.Notice_date <= end_date)
        except ValueError:
            pass
    if keyword:
        base_query = base_query.filter(
        or_(
            Notice.NoticeName.like(f'%{keyword}%'),
            Notice.Notice_content.like(f'%{keyword}%')
        )
        )
    # 分页查询
    paginated_data = base_query.order_by(Notice.Notice_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    notices = paginated_data.items
    total_pages = paginated_data.pages
    current_page = paginated_data.page
    return jsonify({
        'code': 200,
        'message': f'获取{notice_type}公告成功',
        'data': [
            {
                'nid': notice.nid,
                'NoticeName': notice.NoticeName,
                'username': notice.username,
                'Notice_date': notice.Notice_date,
                'Notice_content': notice.Notice_content,
                'NoticePicture': notice.NoticePicture,
                'power': notice.power,
                'notice_type': notice.notice_type
            }
            for notice in notices
        ],
        'pagination': {
            'current_page': current_page,
            'total_pages': total_pages
        }
    })

# 创建公告
@app.route('/api/<string:notice_type>-notice', methods=['POST'])
@require_permission(['admin', 'CommunityAdmin'], notice_type='<notice_type>')
def create_notice(notice_type):
    data = request.get_json()
    required_fields = ['NoticeName', 'Notice_content']
    username = session.get('username')
    power= bp.get_sql_user(username)[0][3] if bp.get_sql_user(username) else None
    if not all(field in data for field in required_fields):
        return jsonify({'code': 400, 'message': '缺少必要字段'}), 400
    power = bp.get_sql_user(username)[0][3] if bp.get_sql_user(username) else None
    if power not in ["admin", "CommunityAdmin"]:
        return jsonify({
            'code': 403,
            'message': '无权限发布社区公告'
        }), 403
    NoticeName = data.get('NoticeName')
    text_content = data.get('Notice_content')
    NoticePicture = data.get('NoticePicture')
    now = datetime.datetime.now()
    Notice_date = now.strftime("%Y-%m-%d %H:%M")
    new_notice = Notice(
        NoticeName=NoticeName,
        username=username,
        Notice_date=Notice_date,
        Notice_content=text_content,
        power=power,
        notice_type=notice_type  # 设置公告类型
    )
    if NoticePicture:
        NoticePicture = bp.save_answer_image(NoticePicture, app.config['UPLOAD_FOLDER'], username, notice_type+"Notice")
        new_notice.NoticePicture = "/static/pictures/" + NoticePicture
    db.session.add(new_notice)
    db.session.commit()
    session['CommunityNoticecomplete'] = "发布成功"
    return jsonify({
        'code': 200,
        'message': '社区公告创建成功'
    })


@app.route('/api/<string:notice_type>-notice/<int:notice_id>', methods=['DELETE'])
@require_permission(['admin', 'CommunityAdmin'], notice_type='<notice_type>')
def delete_notice(notice_type, notice_id):
    notice = Notice.query.filter_by(nid=notice_id, notice_type=notice_type).first()
    if not notice:
        return jsonify({
            'code': 404,
            'message': f'{notice_type}公告未找到'
        }), 404
    try:
        db.session.delete(notice)
        db.session.commit()
        return jsonify({
            'code': 200,
            'message': f'{notice_type}公告删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'删除{notice_type}公告时出现错误: {str(e)}'
        }), 500


@app.route('/api/<string:notice_type>-notice/<int:notice_id>', methods=['GET'])
@require_permission(['admin', 'CommunityAdmin'], notice_type='<notice_type>')
def get_single_notice(notice_type, notice_id):
    notice = Notice.query.filter_by(nid=notice_id, notice_type=notice_type).first()
    if not notice:
        return jsonify({
            'code': 404,
            'message': f'{notice_type}公告未找到'
        }), 404
    return jsonify({
        'code': 200,
        'message': f'获取{notice_type}公告详情成功',
        'data': {
            'nid': notice.nid,
            'NoticeName': notice.NoticeName,
            'username': notice.username,
            'Notice_date': notice.Notice_date,
            'Notice_content': notice.Notice_content,
            'NoticePicture': notice.NoticePicture,
            'power': notice.power,
            'notice_type': notice.notice_type
        }
    })

@app.route('/api/news', methods=['GET'])
def get_news():
    # 初始化基础查询
    base_query = CrawlerData.query
    # 获取请求参数
    page = int(request.args.get('page', 1))
    per_page = 6
    publisher = request.args.get('publisher')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    keyword = request.args.get('keyword')
    # 根据参数进行筛选
    if publisher:
        base_query = base_query.filter(CrawlerData.Publisher == publisher)
    if start_time:
        try:
            start_date = datetime.datetime.strptime(start_time, '%Y-%m-%d')
            base_query = base_query.filter(CrawlerData.UpdateTime >= start_date)
        except ValueError:
            pass
    if end_time:
        try:
            end_date = datetime.datetime.strptime(end_time, '%Y-%m-%d')
            base_query = base_query.filter(CrawlerData.UpdateTime <= end_date)
        except ValueError:
            pass
    if keyword:
        base_query = base_query.filter(CrawlerData.Content.like(f'%{keyword}%'))
    # 分页查询
    paginated_data = base_query.order_by(CrawlerData.UpdateTime.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    news = paginated_data.items
    total_pages = paginated_data.pages
    current_page = paginated_data.page
    return jsonify({
        'code': 200,
        'message': '获取新闻资讯成功',
        'data': [
            {
                'WebId': news_item.WebId,
                'Title': news_item.Title,
                'UpdateTime': news_item.UpdateTime,
                'Publisher': news_item.Publisher,
                'Content': news_item.Content,
                'WebsiteLink': news_item.WebsiteLink,
                'WebsitePicture': news_item.WebsitePicture
            }
            for news_item in news
        ],
        'pagination': {
            'current_page': current_page,
            'total_pages': total_pages
        }
    })

import draw_chart as dc
    
@app.route('/get_chart_list')
@require_login
def get_chart_list():
    username = session['username']
    # 查询用户的所有图表记录
    charts = UserChart.query.filter_by(username=username).all()
    chart_list = []
    for chart in charts:
        chart_list.append((chart.chart_path, chart.chart_type))
    return jsonify(chart_list)

def save_charts_to_db(username, charts_info, chart_types=None):
    """
    保存图表信息到数据库。
    :param username: 用户名
    :param charts_info: 图表信息列表，包含图表路径和类型
    :param chart_types: 可选参数，指定要保存的图表类型列表。如果为 None，则删除所有类型
    :return: 保存是否成功，以及相应的消息
    """
    try:
        with app.app_context():
            # 如果指定了图表类型，则只删除这些类型的记录
            if chart_types:
                UserChart.query.filter(UserChart.username == username, UserChart.chart_type.in_(chart_types)).delete()
            else:
                # 否则删除用户的所有图表记录
                UserChart.query.filter_by(username=username).delete()
            print(chart_types)
            for path, chart_type in charts_info:
                # 确保路径使用正斜杠
                sanitized_path = path.replace('\\', '/')
                new_chart = UserChart(
                    username=username,
                    chart_type=chart_type,
                    chart_path=sanitized_path
                )
                db.session.add(new_chart)
            db.session.commit()
        return True, "图表保存成功"
    except Exception as e:
        print(e)
        db.session.rollback()
        return False, f"图表保存失败: {str(e)}"
    
def generate_error_upload_line(username):
    try:
        # 获取错题上传数据
        error_upload_data = get_error_upload_data(username)
        upload_dates = [data.date for data in error_upload_data]
        upload_counts = [data.count for data in error_upload_data]
        # 生成错题上传数量折线图
        line_chart = dc.ZheXian(upload_dates, upload_counts, "错题上传数量")
        # 保存图表
        chart_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'chart'))
        os.makedirs(chart_dir, exist_ok=True)
        chart_path = os.path.join(chart_dir, f"{username}_error_upload_line.html")
        line_chart.render(chart_path)
        return [(f"chart/{username}_error_upload_line.html", "错题上传数量")], True, ""
    except Exception as e:
        return [], False, f"图表生成失败: {str(e)}"

import plotly.offline as pyo
def generate_user_tag_heatmap_file(username):
    try:
        # 获取热力图数据
        unique_tags, heatmap_data = get_user_tag_heatmap_data(username)
        # 生成热力图
        heatmap_fig = dc.generate_user_tag_heatmap(unique_tags, heatmap_data)
        # 保存热力图为 HTML 文件
        chart_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'chart'))
        os.makedirs(chart_dir, exist_ok=True)
        chart_path = os.path.join(chart_dir, f"{username}_user_tag_heatmap.html")
        pyo.plot(heatmap_fig, filename=chart_path, auto_open=False)
        return [(f"chart/{username}_user_tag_heatmap.html", "用户标签热力图")], True, ""
    except Exception as e:
        import traceback
        traceback.print_exc()
        return [], False, f"图表生成失败: {str(e)}"

def get_error_review_data(username):
    with app.app_context():
        # 获取不重复的日期和每个日期的复习记录数量
        error_review_data = (
            db.session.query(
                ReviewState.push_date.label('date'),
                func.count(ReviewState.Rid).label('count')
            )
            .filter(ReviewState.username == username)
            .group_by(ReviewState.push_date)
            .order_by(ReviewState.push_date)
            .all()
        )
        return error_review_data

def get_error_upload_data(username):
    with app.app_context():
        # 获取不重复的日期和每个日期的学习记录数量
        error_upload_data = (
            db.session.query(
                Study.FinishTime.label('date'),
                func.count(Study.id).label('count')
            )
            .filter(Study.Username == username)
            .group_by(Study.FinishTime)
            .order_by(Study.FinishTime)
            .all()
        )
        return error_upload_data

def get_type_study_data(username):
    with app.app_context():
        # 获取学习记录的类型和数量
        study_type_counts = db.session.query(
            Study.Type.label('type'),
            func.count(Study.id).label('count')
        ).filter_by(Username=username).group_by(Study.Type).all()
        return study_type_counts

def get_correct_rate_data(username):
    """获取用户每天的复习题目正确率数据"""
    with app.app_context():
        try:
            # 查询每天的总题数和正确题数
            query = db.session.query(
                func.date(ReviewState.recent_review_time).label('date'),
                func.count(ReviewState.Rid).label('total_questions'),
                func.sum(db.cast(ReviewState.is_correct, db.Integer)).label('correct_questions')
            ).filter(
                ReviewState.username == username,
                ReviewState.reviewed == 1,
                ReviewState.recent_review_time.isnot(None)  # 排除 recent_review_time 为 NULL 的记录
            ).group_by(
                func.date(ReviewState.recent_review_time)
            ).order_by(
                func.date(ReviewState.recent_review_time)
            ).all()
            # 将查询结果转换为 DataFrame
            data = [
                {
                    'date': item.date,
                    'total_questions': item.total_questions,
                    'correct_questions': item.correct_questions
                }
                for item in query
            ]
            df = pd.DataFrame(data)
            # 计算正确率
            df['correct_rate'] = (df['correct_questions'] / df['total_questions'] * 100).round(1)
            return df
        except Exception as e:
            print(f"查询出错: {e}")
            return pd.DataFrame()

def get_correct_ToYesDay_data(username):
    """获取用户昨天和今天整体的复习题目正确率数据"""
    with app.app_context():
        try:
            today = datetime.datetime.now().date()
            yesterday = today - datetime.timedelta(days=1)
            # 查询昨天和今天的总题数和正确题数
            query = db.session.query(
                func.sum(db.cast(ReviewState.is_correct, db.Integer)).label('correct_questions'),
                func.count(ReviewState.Rid).label('total_questions')
            ).filter(
                ReviewState.username == username,
                ReviewState.reviewed == 1,
                ReviewState.recent_review_time.isnot(None),  # 排除 recent_review_time 为 NULL 的记录
                func.date(ReviewState.recent_review_time).in_([today, yesterday])
            ).first()
            if query:
                correct_questions = query.correct_questions
                total_questions = query.total_questions

                if total_questions > 0:
                    correct_rate = (correct_questions / total_questions) * 100
                    return round(correct_rate, 1)
                else:
                    return 0.0
            else:
                return 0.0
        except Exception as e:
            print(f"查询出错: {e}")
            return 0.0

# 获取题目类型数据，获取标签出现次数和对应标签权重总和和对应标签复习次数数据
def get_label_stats(username):
    with app.app_context():
        # 获取所有学习记录的标签和问题ID
        try:
            study_labels = db.session.query(
                Study.Label,
                Study.id, 
                Study.CurrentWeight
                ).filter_by(Username=username).all()
        except Exception as e:
            print(f"查询出错: {e}")
        if not study_labels:
            return {}, {}, {}
        # 构建标签和对应问题ID及权重的映射
        label_to_question_ids = {}
        label_to_weights = {}
        for label_entry in study_labels:
            # 去掉#符号并分割标签
            raw_labels = label_entry.Label.replace('#', ' ').split()
            for raw_label in raw_labels:
                # 进一步分割可能包含多余空格的标签
                sub_labels = raw_label.split()
                for label in sub_labels:
                    label = label.strip()  # 去除首尾空格
                    if label:
                        question_id = label_entry.id
                        weight = label_entry.CurrentWeight
                        if label in label_to_question_ids:
                            label_to_question_ids[label].append(question_id)
                            label_to_weights[label].append(weight)
                        else:
                            label_to_question_ids[label] = [question_id]
                            label_to_weights[label] = [weight]
        # 获取每个问题ID的复习次数
        question_review_counts = db.session.query(
            ReviewState.WrongQuestionID,
            func.count(ReviewState.Rid).label('review_count')
        ).filter(ReviewState.username == username).group_by(ReviewState.WrongQuestionID).all()
        # 构建问题ID到复习次数的映射
        question_id_to_review_count = {q_id: count for q_id, count in question_review_counts}
        # 计算每个标签的总出现次数、权重总和和复习次数
        label_counts = {}
        label_weight_sum = {}
        label_review_counts = {}
        for label in label_to_question_ids:
            label_counts[label] = len(label_to_question_ids[label])
            label_weight_sum[label] = sum(label_to_weights[label])
            total_reviews = sum(question_id_to_review_count.get(q_id, 0) for q_id in label_to_question_ids[label])
            label_review_counts[label] = total_reviews
        return label_counts, label_weight_sum, label_review_counts

def get_label_stats_without_splitting(username):
    with app.app_context():
        # 获取所有学习记录的标签和问题ID
        study_labels = db.session.query(Study.Label, Study.id, Study.CurrentWeight).filter_by(Username=username).all()
        if not study_labels:
            return {}, {}, {}
        # 构建标签和对应问题ID及权重的映射
        label_to_question_ids = {}
        label_to_weights = {}
        for label_entry in study_labels:
            label = label_entry.Label
            question_id = label_entry.id
            weight = label_entry.CurrentWeight
            if label in label_to_question_ids:
                label_to_question_ids[label].append(question_id)
                label_to_weights[label].append(weight)
            else:
                label_to_question_ids[label] = [question_id]
                label_to_weights[label] = [weight]
        # 获取每个问题ID的复习次数
        question_review_counts = db.session.query(
            ReviewState.WrongQuestionID,
            func.count(ReviewState.Rid).label('review_count')
        ).filter(ReviewState.username == username).group_by(ReviewState.WrongQuestionID).all()
        # 构建问题ID到复习次数的映射
        question_id_to_review_count = {q_id: count for q_id, count in question_review_counts}
        # 计算每个标签的总出现次数、权重总和和复习次数
        label_counts = {}
        label_weight_sum = {}
        label_review_counts = {}
        for label in label_to_question_ids:
            label_counts[label] = len(label_to_question_ids[label])
            label_weight_sum[label] = sum(label_to_weights[label])
            total_reviews = sum(question_id_to_review_count.get(q_id, 0) for q_id in label_to_question_ids[label])
            label_review_counts[label] = total_reviews
        return label_counts, label_weight_sum, label_review_counts

def parse_tag_description(description):
    """
    从标签描述中解析父标签
    :param description: 标签描述字符串
    :return: 父标签名称，若不存在则返回 None
    """
    if not isinstance(description, str):
        return None
    match = re.search(r'父标签: (\w+)', description)
    if match:
        return match.group(1)
    return None

def get_user_tag_heatmap_data(username):
    """
    从数据库获取用户已接触标签的热力图数据
    :param username: 用户名
    :return: 标签名称列表和热力图数据矩阵
    """
    # 查询用户已接触过的标签及其权重
    query = """
        SELECT t.tag_name, utw.weight, t.description
        FROM Tag t
        JOIN UserTagWeight utw ON t.id = utw.tag_id
        WHERE utw.user_username = :username
    """
    result = sp.sql_execute2(query, {"username": username}, commit=False)
    # 整理数据为 DataFrame
    data = []
    tag_description_mapping = {}
    for row in result:
        tag_name = row[0]
        weight = row[1]
        description = row[2]
        data.append((tag_name, weight))
        tag_description_mapping[tag_name] = description
    df = pd.DataFrame(data, columns=['标签名称', '标签权重'])
    # 构建标签的父子关系映射
    tag_relations = {}
    for tag, desc in tag_description_mapping.items():
        parent_tag = parse_tag_description(desc)
        if parent_tag:
            if parent_tag not in tag_relations:
                tag_relations[parent_tag] = []
            tag_relations[parent_tag].append(tag)
    # 查询所有标签的 id 和名称映射
    query_all_tags = "SELECT id, tag_name FROM Tag"
    all_tags_result = sp.sql_execute2(query_all_tags, commit=False)
    tag_id_name_mapping = {row[0]: row[1] for row in all_tags_result}
    # 查询题目 - 标签关联信息
    query_study_tag = """
        SELECT st1.tag_id, st2.tag_id
        FROM StudyTag st1
        JOIN StudyTag st2 ON st1.study_id = st2.study_id AND st1.tag_id < st2.tag_id
    """
    study_tag_result = sp.sql_execute2(query_study_tag, commit=False)
    tag_pair_count = {}
    for tag_id1, tag_id2 in study_tag_result:
        # 检查键是否存在
        if tag_id1 in tag_id_name_mapping and tag_id2 in tag_id_name_mapping:
            tag1 = tag_id_name_mapping[tag_id1]
            tag2 = tag_id_name_mapping[tag_id2]
            if (tag1, tag2) not in tag_pair_count:
                tag_pair_count[(tag1, tag2)] = 0
            tag_pair_count[(tag1, tag2)] += 1
    # 构建热力图的数据矩阵
    unique_tags = df['标签名称'].unique()
    heatmap_data = []
    for tag1 in unique_tags:
        row_data = []
        for tag2 in unique_tags:
            if tag1 == tag2:
                # 对角线位置，使用自身的权重
                weight = df[df['标签名称'] == tag1]['标签权重'].values[0]
            else:
                # 非对角线位置，考虑标签关联
                weight = 0
                weight1 = df[df['标签名称'] == tag1]['标签权重'].values[0]
                weight2 = df[df['标签名称'] == tag2]['标签权重'].values[0]
                parent1 = parse_tag_description(tag_description_mapping[tag1])
                parent2 = parse_tag_description(tag_description_mapping[tag2])
                # 检查是否为父子关系
                if tag1 in tag_relations and tag2 in tag_relations[tag1]:
                    weight = weight2 * 0.5 + weight1 * (1 - 0.5)
                elif tag2 in tag_relations and tag1 in tag_relations[tag2]:
                    weight = weight1 * 0.5 + weight2 * (1 - 0.5)
                # 检查是否为兄弟关系
                elif parent1 and parent2 and parent1 == parent2:
                    weight = weight1 * 0.3 + weight2 * 0.3
                # 检查是否同时出现在同一题目中
                if (tag1, tag2) in tag_pair_count:
                    weight += weight1 * 0.3 + weight2 * 0.3 + tag_pair_count[(tag1, tag2)]
            row_data.append(weight)
        heatmap_data.append(row_data)
    return unique_tags, heatmap_data

def generate_error_review_line(username):
    try:
        # 获取复习情况数据
        error_review_data = get_error_review_data(username)
        review_dates = [data.date for data in error_review_data]
        review_counts = [data.count for data in error_review_data]
        # 生成复习情况折线图
        line_chart = dc.ZheXian(review_dates, review_counts, "错题复习情况")
        # 保存图表
        chart_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'chart'))
        os.makedirs(chart_dir, exist_ok=True)
        chart_path = os.path.join(chart_dir, f"{username}_error_review_line.html")
        line_chart.render(chart_path)
        return [(f"chart/{username}_error_review_line.html", "错题复习情况")], True, ""
    except Exception as e:
        return [], False, f"图表生成失败: {str(e)}"

def generate_type_study_pie(username):
    try:
        # 获取题型数据
        study_type_counts=get_type_study_data(username)
        # 生成复习情况折线图
        line_chart = dc.create_study_type_pie(study_type_counts)
        # 保存图表
        chart_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'chart'))
        os.makedirs(chart_dir, exist_ok=True)
        chart_path = os.path.join(chart_dir, f"{username}_type_study_pie.html")
        line_chart.render(chart_path)
        return [(f"chart/{username}_type_study_pie.html", "各科目题目的占比")], True, ""
    except Exception as e:
        return [], False, f"图表生成失败: {str(e)}"
    
def generate_review_study_bar_line(username, isAtom=None):
    try:
        # 获取数据
        if isAtom:
            label_stats=get_label_stats(username)
            # 生成更新柱状折线图
            line_chart = dc.create_label_chart(label_stats,"复习与学习综合图（原子标签版）")
            # 保存图表
            chart_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'chart'))
            os.makedirs(chart_dir, exist_ok=True)
            chart_path = os.path.join(chart_dir, f"{username}_review_study_bar_line.html")
            line_chart.render(chart_path)
            return [(f"chart/{username}_review_study_bar_line.html", "复习与学习综合图（原子标签版）")], True, ""
        else:
            label_stats=get_label_stats_without_splitting(username)
            # 生成更新柱状折线图
            line_chart = dc.create_label_chart(label_stats,"复习与学习综合图（组合标签版）")
            # 保存图表
            chart_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'chart'))
            os.makedirs(chart_dir, exist_ok=True)
            chart_path = os.path.join(chart_dir, f"{username}_review_complex_study_bar_line.html")
            line_chart.render(chart_path)
            return [(f"chart/{username}_review_complex_study_bar_line.html", "复习与学习综合图（组合标签版）")], True, ""
    except Exception as e:
        return [], False, f"图表生成失败: {str(e)}"

def generate_correct_rate_chart(username):
    """生成正确率折线图并保存"""
    try:
        # 获取正确率数据
        df = get_correct_rate_data(username)
        if df is None or df.empty:
            return None, False, "没有找到正确率数据"
        # 创建折线图
        line_chart = dc.create_correct_rate_line(df)
        if not line_chart:
            return None, False, "图表生成失败"
        # 保存图表
        chart_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'chart'))
        os.makedirs(chart_dir, exist_ok=True)
        chart_path = os.path.join(chart_dir, f"{username}_correct_rate_line.html")
        line_chart.render(chart_path)
        return [(f"chart/{username}_correct_rate_line.html", "复习正确率折线图")], True, ""
    except Exception as e:
        return None, False, f"图表生成失败: {str(e)}"

# 获取私钥API
@app.route('/api/get-bafa-key', methods=['GET'])
def api_get_bafa_key():
    if 'username' not in session:
        return jsonify({
            'success': False,
            'msg': '未登录'
        }), 401
    username = session['username']
    user = User.query.filter_by(Username=username).first()
    if not user:
        return jsonify({
            'success': False,
            'msg': '用户不存在'
        }), 404
    return jsonify({
        'success': True,
        'bafaKey': user.bafaKey or ''
    })

# 设置私钥API
@app.route('/api/set-bafa-key', methods=['POST'])
def api_set_bafa_key():
    if 'username' not in session:
        return jsonify({
            'success': False,
            'msg': '未登录'
        }), 401
    
    data = request.get_json()
    new_bafa_key = data.get('new_bafa_key')
    if not new_bafa_key:
        return jsonify({
            'success': False,
            'msg': '请输入私钥'
        }), 400
    
    username = session['username']
    user = User.query.filter_by(Username=username).first()
    if not user:
        return jsonify({
            'success': False,
            'msg': '用户不存在'
        }), 404
    
    user.bafaKey = new_bafa_key
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'msg': '私钥设置成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'msg': f'操作失败：{str(e)}'
        }), 500

# 根据巴法云API文档设置的微信推送模块
def send_daily_review_notification(message,topic):
    with app.app_context():
        user = User.query.filter_by(Username=session['username']).first()
    headers={
        'Content-Type' : "application/x-www-form-urlencoded"
    }
    # 巴法云API参数
    url = "http://api.bemfa.com/api/wechat/v1/"
    data = {
        "uid": user.bafaKey,  # 替换为你的私钥
        "type": 1,
        "time": 0,
        "device": topic,     # 替换为你的主题名
        "msg": message
    }
    # 发送请求
    response = requests.post(url, data=data,headers=headers)
    # 检查响应状态码
    if response.status_code == 200:
        try:
            # 尝试解析响应内容为 JSON
            result = response.json()
            print(f"推送结果：{result}")
        except requests.exceptions.JSONDecodeError:
            # 若解析失败，打印原始响应内容
            print(f"服务器返回非 JSON 内容：{response.text}")
    else:
        # 若状态码不是 200，打印错误信息
        print(f"请求失败，状态码：{response.status_code}，响应内容：{response.text}")

def send_daily_review_plan_thread(user, message, topic):
    """
    发送微信推送通知（简化版）
    参数:
        user: User对象（必须包含bafaKey属性）
        message: 要发送的消息内容
        topic: 消息主题/设备名
    """
    url = "http://api.bemfa.com/api/wechat/v1/"
    data = {
        "uid": user.bafaKey,
        "type": 1,
        "time": 0,
        "device": topic,
        "msg": message
    }
    try:
        response = requests.post(
            url,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10  # 添加超时设置
        )
        return response.status_code == 200  # 简单返回成功/失败状态
    except requests.exceptions.RequestException:
        return False

def get_top_three_tags_by_username(username):
    try:
        with app.app_context():
            # 使用 db.session 来进行查询，假设 db 是 SQLAlchemy 的实例
            top_three_tags = db.session.query(Tag.tag_name).join(
                UserTagWeight, UserTagWeight.tag_id == Tag.id
            ).filter(
                UserTagWeight.user_username == username
            ).order_by(
                desc(UserTagWeight.weight)
            ).limit(3).all()
            # 提取标签名称
            tag_names = [tag[0] for tag in top_three_tags]
            # 格式化字符串
            tag_str = "今日建议学习："
            for index, tag in enumerate(tag_names, 1):
                tag_str += f"{tag}、"
            if tag_str.endswith("、"):
                tag_str = tag_str[:-1]  # 去掉最后一个顿号
            return tag_str
    except Exception as e:
        print(f"查询出错: {e}")
        return "今日复习建议学习暂无推荐标签"
    finally:
        db.session.close()  # 关闭 session

def scheduled_push():
    """执行推送任务"""
    try:
        with app.app_context():
            # 获取目标用户
            users = User.query.filter(
                User.bafaKey.isnot(None),
                User.bafaKey != ''
            ).all()
            # 记录执行时间
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{now} 开始执行推送任务，共{len(users)}个用户")
            # 遍历用户推送
            for user in users:
                try:
                    msg1, msg2 = bp.get_current_study_phase_msg(user.StudyPlan)
                    send_daily_review_plan_thread(user,msg1, "学习阶段")
                    send_daily_review_plan_thread(user,msg2, "今日分配")
                    msg3=get_top_three_tags_by_username(user.Username)
                    send_daily_review_plan_thread(user,msg3, "今日重点")
                    # 获取用户当日成功复习的数量
                    reviewNum=bp.get_sql_reviewedNum(user.Username)
                    yesterday_reviewNum=bp.get_sql_yesterday_reviewedNum(user.Username)
                    msg4 = f"昨天复习了{yesterday_reviewNum}道题，继续加油！"
                    msg5 = f"今日已完成{reviewNum}道题，继续加油！"
                    send_daily_review_notification(msg4,"昨日复习数")
                    send_daily_review_notification(msg5,"今日复习错题数")
                except Exception as e:
                    app.logger.error(f"用户 {user.Username} 推送失败: {str(e)}")
    except Exception as e:
        app.logger.error(f"推送任务执行失败: {str(e)}")

import get_html as gh
def craw_scheduled_task():
    """爬虫任务，每天12点调用gh.startCraw()"""
    try:
        with app.app_context():
            gh.startCraw()
    except Exception as e:
        app.logger.error(f"爬虫任务执行失败: {str(e)}")

def run_scheduler():
    """启动调度器线程"""
    # 确保在应用上下文中初始化
    with app.app_context():
        # 设置定时任务
        schedule.every().day.at("18:34").do(scheduled_push)
        schedule.every().day.at("15:04").do(craw_scheduled_task)
        # 运行调度循环
        while True:
            schedule.run_pending()
            time.sleep(1)

def start_background_scheduler():
    """启动后台调度线程"""
    # 创建并启动线程
    scheduler_thread = threading.Thread(
        target=run_scheduler,
        name="SchedulerThread",
        daemon=True  # 设置为守护线程
    )
    scheduler_thread.start()
    return scheduler_thread

if __name__=="__main__":
    # 在应用上下文内创建数据库表
    with app.app_context():
        db.create_all()
    start_background_scheduler()
    app.run(host='127.0.0.1', port=11451, debug=True)


