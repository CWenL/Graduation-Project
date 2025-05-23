import base64
import json
import socket
from flask import request
import SQLiteOp as sp
import analysis_html
import manage_file
import re
import Password_Encryption as pe
import os
import time
import datetime
import random
import csv
import uuid
import requests
from io import StringIO
'''
后端处理/服务接口
'''

def login(InPutPassword, session):
    stored_password = session.get('password')
    if pe.verify_password(InPutPassword, stored_password, bytes.fromhex(session['salt'])):
        return True
    else:
        return False


def record_login(session):
    if 'login' in session and session['login'] == "login_success":
        return True
    username = request.cookies.get('username')
    if username:
        res = get_sql_user(username)
        if res:
            session['username'] = username
            session['password'] = res[0][1]
            session['power'] = res[0][3]
            session['login'] = "login_success"
            return True
    return False

sql_select_forum='''
 select * from forum
 '''

sql_select_news='''
 select * from CrawlerData
 '''
sql_select_news_ForId='''
 select * from CrawlerData where WebId = ?
 '''
sql_select_user="select * from user where username = ?;"
sql_Post_Owner="select username from Forum where PostingsID = ?;"
sql_Wrong_Owner="select username from study where id = ?;"
sql_select_All_user="select * from user where power is not 'admin';"
sql_Ban_user="update user set state = 1 where username = ?"
sql_UnBan_user="update user set state = 0 where username = ?"
sql_promote_user="update user set Power = 'CommunityAdmin' where username =?"
sql_remote_user="update user set Power = 'user' where username =?"
sql_update_post_view="update Forum set PostingsViewNum = PostingsViewNum+1 where PostingsID =?"
sql_update_post="update Forum set Title = ?,PostingsText = ?,tag = ? where PostingsID = ?"
sql_select_studydata="select * from study where username = ?"
sql_select_studydataForID="select * from study where id = ?;"
sql_select_forumdata="select * from forum where username = ?"
sql_select_commentdata="select * from comment where username = ?"
sql_select_All_commentdata="select * from comment;"
sql_select_commentdataForId="select * from comment where PostingsID = ?;"
sql_select_review="select * from reviewstate where username = ? and push_date = ? and reviewed = 0;"
sql_select_reviewed="select * from reviewstate where username = ? and push_date = ? and reviewed = 1;"
sql_select_label_with_Type="select label from study where label IS NOT NULL and Type = ?;"
sql_select_tag_for_forum="select tag from forum where tag IS NOT NULL;"
sql_select_label="select label from study where label IS NOT NULL;"
 
def get_sql_forum():
    res=sp.sql_execute_select_noVariable(sql_select_forum)
    return res

def get_sql_news():
    res=sp.sql_execute_select_noVariable(sql_select_news)
    return res

def get_sql_news_ForId(nid):
    res=sp.sql_execute_select(sql_select_news_ForId,(nid,))
    return res[0]
    

def get_sql_user(username):
    res=sp.sql_execute_select(sql_select_user,(username,))
    return res

def get_sql_Post_Owner(post_id):
    res=sp.sql_execute_select(sql_Post_Owner,(post_id,))
    return res

def get_sql_Wrong_Owner(Wrong_id):
    res=sp.sql_execute_select(sql_Wrong_Owner,(Wrong_id,))
    return res

def get_sql_All_user():
    res=sp.sql_execute_select_noVariable(sql_select_All_user)
    return res

def Ban_user(username):
    sp.sql_cursor_execute(sql_Ban_user,(username,))
    return

def UnBan_user(username):
    sp.sql_cursor_execute(sql_UnBan_user,(username,))
    return

def promote_user(username):
    sp.sql_cursor_execute(sql_promote_user,(username,))
    return

def remote_user(username):
    sp.sql_cursor_execute(sql_remote_user,(username,))
    return

def get_sql_notice():
    sql_select_notice="select * from notice where Notice_date like '%"+str(datetime.date.today())+"%';"
    res=sp.sql_execute_select_noVariable(sql_select_notice)
    return res

def Delete_Comment(Comment_id):
    sql_Delete_Comment="delete from comment where CommentID = ? ;"
    sp.sql_cursor_execute(sql_Delete_Comment,(Comment_id,))
    return

def Delete_StudyData(question_id):
    sql_Delete_StudyData="delete from study where id = ? ;"
    sp.sql_cursor_execute(sql_Delete_StudyData,(question_id,))
    return

def Delete_Post(post_id):
    sql_Delete_post="delete from Forum where PostingsID = ? ;"
    sp.sql_cursor_execute(sql_Delete_post,(post_id,))
    return

def get_sql_studydata(username, page=None, per_page=None, start_date=None, end_date=None):
    # 构建基础的 SQL 查询语句
    base_sql = sql_select_studydata
    params = [username]
    # 若提供了开始日期和结束日期，添加日期筛选条件
    if start_date and end_date:
        base_sql += " AND FinishTime BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    # 若未提供分页参数，直接执行查询
    if page is None and per_page is None:
        res = sp.sql_execute_select(base_sql, tuple(params))
        return res
    # 计算偏移量以实现分页
    offset = (page - 1) * per_page
    # 拼接 LIMIT 和 OFFSET 子句到 SQL 查询语句
    sql = f"{base_sql} LIMIT {per_page} OFFSET {offset}"
    res = sp.sql_execute_select(sql, tuple(params))
    return res

def get_sql_studydata_count(username, start_date=None, end_date=None):
    # 构造用于查询总数的基础 SQL 语句
    base_sql = "SELECT COUNT(*) FROM Study WHERE Username = ?"
    params = [username]
    # 若提供了开始日期和结束日期，添加日期筛选条件
    if start_date and end_date:
        base_sql += " AND FinishTime BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    # 执行查询
    res = sp.sql_execute_select(base_sql, tuple(params))
    # 提取查询结果中的总数
    total = res[0][0] if res else 0
    return total

def get_sql_forumdata(username, page=None, per_page=None, start_date=None, end_date=None):
    base_sql = sql_select_forumdata
    params = [username]
    if start_date and end_date:
        base_sql += " AND PostingsTime BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    if page is None and per_page is None:
        res = sp.sql_execute_select(base_sql, tuple(params))
        return res
    offset = (page - 1) * per_page
    sql = f"{base_sql} LIMIT {per_page} OFFSET {offset}"
    res = sp.sql_execute_select(sql, tuple(params))
    return res

def get_sql_forumdata_count(username, start_date=None, end_date=None):
    base_sql = "SELECT COUNT(*) FROM Forum WHERE Username = ?"
    params = [username]
    if start_date and end_date:
        base_sql += " AND PostingsTime BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    res = sp.sql_execute_select(base_sql, tuple(params))
    total = res[0][0] if res else 0
    return total

def get_all_sql_forumdata(page=None, per_page=None, start_date=None, end_date=None, keyword=None):
    # 初始化基础 SQL 语句和参数列表
    conditions = []
    params = []
    # 添加搜索条件
    if keyword:
        keyword_condition = "Title LIKE ? OR PostingsText LIKE ? OR tag LIKE ?"
        conditions.append(keyword_condition)
        params.extend(['%' + keyword + '%', '%' + keyword + '%', '%' + keyword + '%'])
    # 添加日期筛选条件
    if start_date and end_date:
        date_condition = "PostingsTime BETWEEN ? AND ?"
        conditions.append(date_condition)
        params.extend([start_date, end_date])
    # 构建完整的 WHERE 子句
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
    else:
        where_clause = ""
    # 构建完整的 SQL 语句
    base_sql = "SELECT * FROM Forum"
    if where_clause:
        base_sql += " " + where_clause
    base_sql += " ORDER BY PostingsTime DESC"
    # 分页处理
    if page is not None and per_page is not None:
        offset = (page - 1) * per_page
        base_sql += f" LIMIT {per_page} OFFSET {offset}"
    # 打印 SQL 语句和参数，方便调试
    print(base_sql, tuple(params))
    # 执行 SQL 查询
    res = sp.sql_execute_select(base_sql, tuple(params))
    return res

def get_all_sql_forumdata_count(start_date=None, end_date=None, keyword=None):
    base_sql = "SELECT COUNT(*) FROM Forum"
    params = []
    # 添加搜索条件
    if keyword:
        base_sql += " WHERE Title LIKE ? OR PostingsText LIKE ?"
        params.extend(['%' + keyword + '%', '%' + keyword + '%'])
    # 添加日期筛选条件
    if start_date and end_date:
        if keyword:
            base_sql += " AND"
        else:
            base_sql += " WHERE"
        base_sql += " PostingsTime BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    res = sp.sql_execute_select(base_sql, tuple(params))
    total = res[0][0] if res else 0
    return total

sql_select_LikeStatus="SELECT 1 FROM Likes WHERE username = ? AND post_id = ?"
def check_user_liked_post(username,post_id):
    db=sp.connect_db()
    cursor=db.cursor()
    cursor.execute(sql_select_LikeStatus,(username,post_id))
    result = cursor.fetchone()
    if not result:
        db.close()
        return False
    return True

def update_post(post_id,post_tittle,post_content,Label):
    sp.sql_cursor_execute(sql_update_post,(post_tittle,post_content,Label,post_id))
    return

def Update_Post_ViewNum(post_id):
    sp.sql_cursor_execute(sql_update_post_view,(post_id,))
    return 

def get_sql_commentdata(username, page=None, per_page=None, start_date=None, end_date=None):
    base_sql = sql_select_commentdata
    params = [username]
    if start_date and end_date:
        base_sql += " AND CommentTime BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    if page is None and per_page is None:
        res = sp.sql_execute_select(base_sql, tuple(params))
        return res
    offset = (page - 1) * per_page
    sql = f"{base_sql} LIMIT {per_page} OFFSET {offset}"
    res = sp.sql_execute_select(sql, tuple(params))
    return res

def get_sql_commentdata_count(username, start_date=None, end_date=None):
    base_sql = "SELECT COUNT(*) FROM Comment WHERE Username = ?"
    params = [username]
    if start_date and end_date:
        base_sql += " AND CommentTime BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    res = sp.sql_execute_select(base_sql, tuple(params))
    total = res[0][0] if res else 0
    return total

def get_sql_All_commentdata():
    res=sp.sql_execute_select_noVariable(sql_select_All_commentdata)
    return res

def get_sql_commentdataForId(cid):
    res=sp.sql_execute_select(sql_select_commentdataForId,(cid,))
    return res

def get_sql_Only_label(TableName,type=None):
    if TableName=="forum":
        rows=sp.sql_execute_select_noVariable(sql_select_tag_for_forum)
    elif TableName=="study":
        rows=sp.sql_execute_select(sql_select_label_with_Type,(type,))
    elif TableName=="upload":
        rows=sp.sql_execute_select_noVariable(sql_select_label)
    # 将所有标签分割并去重,使用集合的唯一性
    unique_labels = set()
    for row in rows:
        tags = row[0].split('#')  # 假设标签用 '#' 分隔
        unique_labels.update([tag.strip() for tag in tags if tag.strip()])  # 去除首尾空格并添加到集合中
    return sorted(unique_labels)



# 获取当日未复习的题目
def get_sql_review(username,today):
    res=sp.sql_execute_select(sql_select_review,(username,today))
    return res

sql_select_reviewedQuestions='''
SELECT s.*
FROM Study s
JOIN ReviewState rs ON s.id = rs.WrongQuestionID
WHERE rs.push_date = ?
  AND rs.reviewed = 1
  AND rs.username = ?;
'''
# 获取当日已复习的题目
def get_sql_reviewed(username,today):
    res=sp.sql_execute_select(sql_select_reviewedQuestions,(today,username))
    return res

sql_select_reviewedNum = '''
SELECT COUNT(*) AS reviewed_count
FROM Study s
JOIN ReviewState rs ON s.id = rs.WrongQuestionID
WHERE rs.push_date = ?
  AND rs.reviewed = 1
  AND rs.username = ?;
'''
def get_sql_reviewedNum(username):
    res = sp.sql_execute_select(sql_select_reviewedNum, (datetime.date.today(), username))
    if res:
        return res[0][0]  # 假设返回的是一个字典列表，取第一个字典中的计数值
    else:
        return 0  # 如果没有记录，返回 0
def get_sql_yesterday_reviewedNum(username):
    res = sp.sql_execute_select(sql_select_reviewedNum, (datetime.date.today()-datetime.timedelta(days=1), username))
    if res:
        return res[0][0]  # 假设返回的是一个字典列表，取第一个字典中的计数值
    else:
        return 0  # 如果没有记录，返回 0

# 根据id寻找学习记录
def get_sql_studyForID(question_id):
    query = "SELECT * FROM study WHERE id = ?"
    result = sp.sql_execute2(query, (question_id,), commit=False)
    if result:
        # 定义列名
        columns = ['id', 'username', 'content', 'type', 'label', 'question_picture', 'answer_picture', 'finish_time', 'recent_review_time', 'weight', 'push_date', 'review_accuracy']
        # 将元组转换为字典
        return dict(zip(columns, result[0]))
    return None

# 根据id寻找帖子
sql_select_postForID="SELECT * FROM Forum WHERE PostingsID = ?;"
def get_sql_postForID(post_id):
    res=sp.sql_execute_select(sql_select_postForID,(post_id,))
    return res

# 计算至今相隔天数
def days_between_time(time):
    date_obj = datetime.datetime.strptime(time, "%Y-%m-%d").date()
    delta = abs(datetime.date.today() - date_obj).days
    return delta

update_Weight="update study set CurrentWeight = ? where id = ?;"
update_WeightTime="update study set CurrentWeightUpdateTime = ?  where id = ?;"
def updata_this_id_Weight_and_time(Rid,ResWeight):
    sp.sql_cursor_execute(update_Weight,(ResWeight,Rid))
    sp.sql_cursor_execute(update_WeightTime,(datetime.date.today(),Rid))
    return

def adjust_decay_coefficient(correct_rate):
    """根据正确率调整衰减系数 λ"""
    if correct_rate < 20:
        return 1.5
    elif correct_rate < 50:
        return 0.9
    elif correct_rate < 80:
        return 0.75
    else:
        return 0.1

# 基于记忆曲线的权重更新算法
def update_Weights_login(studydata,stability):
    now = datetime.date.today() # 获取当前时间
    for sdata in studydata:
        sdataID=sdata[0]
        FinishTime= sdata[7]
        RecentReviewTime= sdata[8] if sdata[8] else None
        Weight= sdata[9]
        # 如果权重还没更新过，则更新时间就是该错题的上传时间
        WeightUpdateTime=sdata[10] if sdata[10] else FinishTime
        Days=days_between_time(WeightUpdateTime)

        # 控制权重增加
        if Days!=0 and RecentReviewTime is None:
            ResWeight=Weight+0.3*Days*stability
            updata_this_id_Weight_and_time(sdataID,ResWeight)
        elif Days!=0 and RecentReviewTime is not None:
            ResWeight=Weight+0.15*Days*stability
            updata_this_id_Weight_and_time(sdataID,ResWeight)
        elif Days ==0:
            return
    return

def update_Weights_Review_label(question_id,username,stability):
    # 当用户复习完这道题目，根据这道题的最初完成时间，计算距今相隔的天数，按照记忆曲线的规律降低权重
    userdata=sp.sql_execute_select(sql_select_studydata,(username,))
    reviewQuestion=sp.sql_execute_select(sql_select_studydataForID,(question_id,))
    FinishTime=reviewQuestion[0][7]
    # 获取最近一次权重更新时间
    recent_review_time=reviewQuestion[0][8] if reviewQuestion[0][8] else FinishTime
    NowWeight=reviewQuestion[0][9]
    Finish_to_Now_Days=days_between_time(FinishTime)
    recent_review_to_Now_Days=days_between_time(recent_review_time)
    resWeight=NowWeight
    # 0.2-0.4-0.7-0.8-0.85
    if Finish_to_Now_Days==1:
        resWeight=NowWeight*2
    elif Finish_to_Now_Days<=2:
        resWeight=NowWeight*pow((1+0.2*stability),recent_review_to_Now_Days)
    elif Finish_to_Now_Days<=4:
        resWeight=NowWeight*pow((1+0.4*stability),recent_review_to_Now_Days)
    elif Finish_to_Now_Days<=7:
        resWeight=NowWeight*pow((1+0.7*stability),recent_review_to_Now_Days)
    elif Finish_to_Now_Days<=14:
        resWeight=NowWeight*pow((1+0.8*stability),recent_review_to_Now_Days)
    elif Finish_to_Now_Days<=28:
        resWeight=NowWeight*pow((1+0.85*stability),recent_review_to_Now_Days)
    updata_this_id_Weight_and_time(question_id,resWeight)
    # 本题完成复习后要更新所有该用户错题中带有本题标签的题目的weight，使其减少一部分
    # 获取当前题目的标签
    Labels = reviewQuestion[0][4].split('#')[1:]  # 去掉第一个空标签
    # 更新所有带有相同标签的题目的权重
    for label in Labels:
        query="SELECT id, CurrentWeight, Label FROM Study WHERE Username = ? AND Label LIKE ?"
        
        related_questions = sp.sql_execute_select(query,(username,'#'+label))
        # print(related_questions)
        for q_id, weight, q_labels in related_questions:
            new_weight = weight * 0.9  # 权重减少 10%
            # 更新权重
            updata_this_id_Weight_and_time(q_id,new_weight)
    return

def update_weightForlabel(label1,label2=None,label3=None):
    unique_labels = set()
    unique_labels.add(label1)
    unique_labels.add(label2)
    unique_labels.add(label3)
    for label in unique_labels:
        # 批量更新权重
        # 构造包含通配符的标签
        label_with_wildcards = f"%{label}%"
        sql_select_studydataForLabel="update study set CurrentWeight=CurrentWeight*1.1,CurrentWeightUpdateTime = ? where Label like ?;"
        res=sp.sql_cursor_execute(sql_select_studydataForLabel,(datetime.date.today(),label_with_wildcards))
    return

get_SumWeight='''
SELECT SUM(CurrentWeight) AS total_weight
FROM Study
WHERE Username = ? ;
'''
sql_select_studydataForID="select * from study where ID = ?;"
# 获取该用户所有错题权重的总和
def get_SumWeightForUser(username):
    res=sp.sql_execute_select(get_SumWeight,(username,))
    return res

# 基于记忆曲线的随机复习推送
def weighted_random_choice(username, studyForUsername, review_modal=None):
    total_weight = get_SumWeightForUser(username)[0][0]
    # 如果总权重为 0 或没有错题，直接返回 None
    if total_weight == 0 or not studyForUsername:
        return None
    # 查询当天已经推送过的题目
    now = datetime.date.today()
    query_pushed_questions = "SELECT WrongQuestionID FROM ReviewState WHERE username = ? AND push_date = ?"
    pushed_questions = sp.sql_execute_select(query_pushed_questions, (username, now))
    pushed_question_ids = [row[0] for row in pushed_questions]
    # 过滤掉当天已经推送过的题目
    filtered_studyForUsername = [item for item in studyForUsername if item[0] not in pushed_question_ids]
    if not filtered_studyForUsername:
        return None
    # 提取题目ID
    questionID = [id for id, _, _, _, _, _, _, _, _, _, _, _, _ in filtered_studyForUsername]
    # 提取概率值
    probability = [weights / total_weight for _, _, _, _, _, _, _, _, _, weights, _, _, _ in filtered_studyForUsername]
    # 使用概率进行随机选择
    selected_questionID = random.choices(questionID, weights=probability)[0]
    resQuestion = sp.sql_execute_select(sql_select_studydataForID, (selected_questionID,))
    # 将该错题推送记录添加到Reviewstate表中
    state_insert = "INSERT INTO ReviewState (username, WrongQuestionID, push_date) VALUES (?, ?, ?);"
    sp.sql_cursor_execute(state_insert, (resQuestion[0][1], resQuestion[0][0], now))
    if resQuestion:
        # 定义列名
        columns = ['id', 'username', 'content', 'type', 'label', 'question_picture', 'answer_picture', 'finish_time', 'recent_review_time', 'weight', 'push_date', 'review_accuracy', 'original_study_id']
        # 将元组转换为字典
        return dict(zip(columns, resQuestion[0]))
    return resQuestion

# 重新计算用户标签权重的函数
def recalculate_user_tag_weights(username):
    query = """
    INSERT OR REPLACE INTO UserTagWeight (user_username, tag_id, weight)
    SELECT s.username, t.id, SUM(s.CurrentWeight)
    FROM Study s
    JOIN StudyTag st ON s.id = st.study_id
    JOIN Tag t ON st.tag_id = t.id
    WHERE s.username =?
    GROUP BY s.username, t.id;
    """
    sp.sql_cursor_execute(query, (username,))

def get_original_path(question_id,PictureType):
    query = "SELECT ? FROM Study WHERE id = ?"
    res=sp.sql_execute_select(query,(PictureType,question_id))
    return res[0][0] if res else None

def save_base64_image(base64_data, upload_folder, filename):
    """
    处理并保存 base64 编码的图片
    :param base64_data: base64 编码的图片数据
    :param upload_folder: 图片保存的文件夹路径
    :param filename: 保存的文件名
    :return: 保存成功返回 True，失败返回 False
    """
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    try:
        # 提取 base64 编码的数据
        if base64_data.startswith('data:image'):
            base64_data = base64_data.split(',')[1]
        # 解码 base64 数据
        image_data = base64.b64decode(base64_data)
        # 保存文件
        file_path = os.path.join(upload_folder, filename)
        with open(file_path, 'wb') as f:
            f.write(image_data)
        return True
    except Exception as e:
        print(f"保存 base64 图片时出错: {e}")
        return False

def save_answer_image(file,upload_folder,username,picture_Type):
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    # 生成唯一的编号
    unique_id = str(uuid.uuid4())[:8]  # 使用 UUID 生成唯一的编号，取前8位
    # 重命名文件为用户名+编号.jpg
    answer_filename = f"{username}_{picture_Type}_{unique_id}.jpg"
    if isinstance(file, str) and file.startswith('data:image'):
        # 如果是 base64 编码的图片数据
        if save_base64_image(file, upload_folder, answer_filename):
            return answer_filename
        else:
            return None
    else:
        try:
            file.save(os.path.join(upload_folder, answer_filename))
            return answer_filename
        except AttributeError:
            print("传入的不是有效的文件对象或 base64 数据")
            return None


def update_study_picture_table(picture_id, PictureType, new_filename):
    # 更新 Study 表中的 PictureType 字段
    query = "UPDATE Study SET "+PictureType+" = ? WHERE id = ?"
    sp.sql_cursor_execute(query,(new_filename,picture_id))
    return

def update_forum_picture_table(post_id, PictureType, new_filename):
    # 更新 forum 表中的 PostingsPicture 字段
    query = "UPDATE Forum SET "+PictureType+" = ? WHERE PostingsID = ?"
    sp.sql_cursor_execute(query,('/static/pictures/'+new_filename,post_id))
    return

def update_study_table(content, Type, study_id,question_label):
    # 更新 Study 表中的 PictureType 字段
    query = "UPDATE Study SET content = ?, Type = ?, Label = ? WHERE id = ?"
    sp.sql_cursor_execute(query,(content,Type,question_label,study_id))
    return

def update_review_state(question_id,is_correct):
    # 更新 ReviewState 表中的 reviewed 状态
    query1 = "UPDATE ReviewState SET reviewed = 1 WHERE WrongQuestionID = ? and push_date = ?"
    query2 = "UPDATE ReviewState SET is_correct = ? WHERE WrongQuestionID = ? and push_date = ?"
    sp.sql_cursor_execute(query1,(question_id,datetime.date.today()))
    sp.sql_cursor_execute(query2,(is_correct,question_id,datetime.date.today()))
    return

def insert_new_review_state(question_id, is_correct, username):
    # 插入新记录到 ReviewState 表
    query = "INSERT INTO ReviewState (WrongQuestionID, push_date, reviewed, is_correct, username) VALUES (?, ?, ?, ?, ?)"
    sp.sql_cursor_execute(query, (question_id, datetime.date.today(), 1, is_correct, username))
    return

def update_recent_review_time(question_id):
    # 更新 ReviewState 表中的 recent_review_time 状态
    query1 = "UPDATE study SET RecentReviewTime = ? WHERE id = ?"
    query2 = "UPDATE ReviewState SET recent_review_time = ? WHERE WrongQuestionID = ? and push_date = ?"
    sp.sql_cursor_execute(query1,(datetime.date.today(),question_id))
    sp.sql_cursor_execute(query2,(datetime.date.today(),question_id,datetime.date.today()))
    return

# def get_ip_location(ip):
#     try:
#         # 调用公共 API 查询 IP 归属地
#         api_url = f"http://ip-api.com/json/{ip}?lang=zh-CN"
#         response = requests.get(api_url)
#         response.raise_for_status()  # 检查请求是否成功
#         # 解析返回的 JSON 数据
#         ip_data = response.json()
#         # 提取归属地信息
#         location = {
#             "国家": ip_data.get("country", "未知"),
#             "地区": ip_data.get("regionName", "未知"),
#             "城市": ip_data.get("city", "未知"),
#             "ISP": ip_data.get("isp", "未知")
#         }
#         return location
#     except Exception as e:
#         print(f"查询 IP 归属地失败: {e}")
#         return {"错误": "无法获取 IP 归属地"}

def get_public_ip():
    try:
        response = requests.get('https://icanhazip.com')
        if response.status_code == 200:
            return response.text.strip()
        else:
            return None
    except requests.RequestException:
        return None

def get_local_ip():
    try:
        # 创建一个 UDP 套接字
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 连接到一个公共的 IP 地址和端口，这里使用 Google 的公共 DNS 服务器
        s.connect(("8.8.8.8", 80))
        # 获取本地 IP 地址
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except socket.error:
        return None

def get_ip_location(ip):
    url = f"http://ip-api.com/json/{ip}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                country = data.get('country', '未知')
                region = data.get('regionName', '未知')
                city = data.get('city', '未知')
                # 重新组合归属地信息
                location_str = f"{country}-{region}-{city}"
                return location_str
            else:
                return "内网测试ip"
        else:
            return f"请求失败，状态码: {response.status_code}"
    except requests.RequestException as e:
        return f"请求发生错误: {e}"

import os.path

# 将数据写入 CSV 文件
def write_to_csv(data,file_path,create_sql):

    # 如果文件存在，则删除文件
    if os.path.exists(file_path):
        os.remove(file_path)
    with open(file_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(get_rows(create_sql))  
        writer.writerows(data)  

import re
def get_rows(sql_query):
    # 使用正则表达式捕获括在括号中的单词（字段名）
    variable_names = re.findall(r'\b([A-Z][A-Z_]+)\b', re.search(r'\((.*?)\)', sql_query.replace('\n', '')).group(1))
    # 获取奇数索引的数据
    filtered_columns = variable_names[0::2]
    return filtered_columns

def escape_fts5(keyword):
    special_chars = ['+', '-', '|', '*', '?', '"', '(', ')', '\'']
    for char in special_chars:
        keyword = keyword.replace(char, f'\\{char}')
    return keyword

def get_total_results(results):
    total = 0
    # 遍历每个分类并计算其总结果数
    for category, category_results in results.items():
        total += category_results
    return total

# 全文索引搜索
def search_database(keyword):
    keyword = escape_fts5(keyword)
    # 连接到数据库
    db = sp.connect_db()
    cursor = db.cursor()
    # 初始化分类结果字典
    classified_results = {
        '社区帖子': [],
        '社区评论': [],
        '学习数据专区': [],
        '新闻资讯': [],
        '通知': []
    }
    # 查询总数
    total_results = {
        '社区帖子': 0,
        '社区评论': 0,
        '新闻资讯': 0,
        '学习数据专区': 0,
        '通知': 0
    }
    # 查询每个分类的结果及总数
    queries = {
        '社区帖子': f"SELECT * FROM Forum WHERE PostingsID IN (SELECT rowid FROM Forum_fts WHERE Forum_fts MATCH '{keyword}')",
        '社区评论': f"SELECT * FROM Comment WHERE CommentID IN (SELECT rowid FROM Comment_fts WHERE Comment_fts MATCH '{keyword}')",
        '新闻资讯': f"SELECT * FROM CrawlerData WHERE WebId IN (SELECT rowid FROM CrawlerData_fts WHERE CrawlerData_fts MATCH '{keyword}')",
        '学习数据专区': f"SELECT * FROM Study WHERE id IN (SELECT rowid FROM Study_fts WHERE Study_fts MATCH '{keyword}')",
        '通知': f"SELECT * FROM notice WHERE nid IN (SELECT rowid FROM notice_fts WHERE notice_fts MATCH '{keyword}')"
    }
    # 执行查询并获取结果
    for category, query in queries.items():
        cursor.execute(query)
        results = cursor.fetchall()
        classified_results[category].extend(results)
        total_results[category] = len(results)
    # 关闭数据库连接
    db.close()
    # 将结果转换为可序列化的格式
    for category, results in classified_results.items():
        classified_results[category] = [list(result) for result in results]
    return classified_results, total_results


def get_current_study_phase_msg(user_study_plan):
    """
    根据当前日期判断学习阶段并生成消息
    参数:
        user_study_plan: 从数据库读取的StudyPlan JSON字符串
    返回:
        msg: 包含当前阶段和学习时间的消息
    """
    # 将JSON字符串转换为字典
    try:
        study_plan = json.loads(user_study_plan)
    except (json.JSONDecodeError, TypeError):
        return "学习计划数据格式不正确"
    # 获取当前日期
    today = datetime.datetime.now().date()
    current_phase = None
    # 检查每个阶段的时间范围
    for phase_name, phase_data in study_plan.items():
        try:
            start_date = datetime.datetime.strptime(phase_data["start_date"], "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(phase_data["end_date"], "%Y-%m-%d").date()
            if start_date <= today <= end_date:
                if phase_name=="phase1":
                    current_phase=[phase_name,"一轮基础阶段"]
                elif phase_name=="phase2":
                    current_phase=[phase_name,"二轮强化阶段"]
                elif phase_name=="phase3":
                    current_phase=[phase_name,"三轮冲刺阶段"]
                break
        except (ValueError, KeyError):
            continue
    if not current_phase:
        return "当前不在任何学习阶段内，请检查学习计划日期设置"
    # 获取当前阶段数据
    phase_data = study_plan[current_phase[0]]
    # 构建消息
    msg1 = (
        f"当前为{current_phase[1]}-你今日总学习时间为{phase_data['daily_hours']}h"
    )
    msg2 = (
        f"数: {phase_data['math_hours']}h"
        f"-英: {phase_data['english_hours']}h"
        f"-政: {phase_data['politics_hours']}h"
        f"-专业课: {phase_data['professional_hours']}h"
    )
    return msg1,msg2


