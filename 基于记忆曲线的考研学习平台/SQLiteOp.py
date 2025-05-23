import sqlite3, os
import jieba

def connect_db():
    basedir = os.path.abspath(os.path.dirname(__file__))
    database_url = os.path.join(basedir+"\\config\\db\\","cst21014.db")
    return sqlite3.connect(database_url, timeout=10) # 设置超时时间为10秒

# 由于创建分词器时重复链接数据库会清除该分词器的创建，所以改为统一链接一个数据库
def sql_execute(sql,db):
    try:
        db.execute(sql)
        db.commit()
    except BaseException as e:
        pass
        print("出错了",e)

def sql_execute2(sql, params=None, commit=True):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        if commit:
            conn.commit()
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        print(f"数据库错误: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def sql_cursor_execute(sql, params=None):
    try:
        db = connect_db()
        cursor = db.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        db.commit()
        db.close()
    except BaseException as e:
        print("出错了", e)


def sql_execute_select_noVariable(sql): # 查询语句不带参数
    try:
        db=connect_db()
        res = db.cursor().execute(sql).fetchall()
        db.close()
        return res # 返回一个列表
    except BaseException as e:
        pass
        # print("出错了",e)

def sql_execute_select(sql,variable): # 查询语句带参数
    try:
        db=connect_db()
        res = db.cursor().execute(sql,variable).fetchall()
        db.close()
        return res # 返回一个列表
    except BaseException as e:
        print("出错了",e)
        return None
        # print("出错了",e)

def sql_select_like(keyword):
    try:
        db=connect_db()
        cursor = db.cursor()
        # 使用模糊查询来查找相似的关键字
        cursor.execute("SELECT anime_id FROM anime WHERE anime_cn_name LIKE ('%" +keyword  + "%')")
        res = cursor.fetchall()
        db.close()
        return res
    except BaseException as e:
        return None
        # print("出错了",e)

# Power三种权限：管理员/普通用户/游客
sql_createUserTable='''
    CREATE TABLE User (
        Username VARCHAR(20) PRIMARY KEY,
        Password VARCHAR(20) NOT NULL,
        email VARCHAR(30),
        Power VARCHAR(20),
        StudyPlan TEXT,
        state BOOLEAN  DEFAULT 0,
        salt TEXT NOT NULL,
        bafaKey TEXT
        )
'''

#交流帖子表
sql_createForumTable='''
    create table Forum (
        PostingsID INTEGER PRIMARY KEY AUTOINCREMENT,
        Title VARCHAR(20),
        Username VARCHAR(20),
        PostingsTime VARCHAR(20), IpLoc VARCHAR(20), tag VARCHAR(50),
        PostingsText TEXT,
        PostingsPicture VARCHAR(70),
        PostingsSupport INT, 
        PostingsViewNum INT DEFAULT 1,
        FOREIGN KEY (Username) REFERENCES User(Username) ON DELETE CASCADE
    )
'''

#点赞记录（防止重复）
sql_create_Likes='''
CREATE TABLE IF NOT EXISTS Likes (
    Username VARCHAR(20),  -- 修正拼写错误
    post_id INTEGER,
    PRIMARY KEY (Username, post_id),
    FOREIGN KEY (Username) REFERENCES User(Username) ON DELETE CASCADE,
    FOREIGN KEY (post_id) REFERENCES Forum(PostingsID) ON DELETE CASCADE
);
'''

#交流评论表
sql_createCommentTable='''
    create table Comment (
        CommentID INTEGER PRIMARY KEY AUTOINCREMENT,
        PostingsID INTEGER,
        Username VARCHAR(20),
        Comment TEXT,
        CommentTime VARCHAR(30), CommentImg VARCHAR(70),
        FOREIGN KEY (PostingsID) REFERENCES Forum(PostingsID) ON DELETE CASCADE,
        FOREIGN KEY (Username) REFERENCES User(Username) ON DELETE CASCADE
    )
'''

# https://www.dxsbb.com/news/list_41.html      https://www.dxsbb.com/news/87035.html 网站爬虫
# 爬虫获取数据表
sql_createCrawlerDataTable='''
    create table CrawlerData (
        WebId INTEGER PRIMARY KEY,
        Title VARCHAR(20),
        UpdateTime VARCHAR(30),
        Publisher VARCHAR(20),
        Content TEXT,
        WebsiteLink VARCHAR(100),
        WebsitePicture VARCHAR(70)
    )
'''
# 个人学习数据（错题本）表，用于根据记忆曲线，计算权重安排复习
sql_createStudyTable='''
    create table Study (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Username VARCHAR(20),
        content TEXT,
        Type VARCHAR(20), Label VARCHAR(80),
        QuestionPicture VARCHAR(70),
        AnswerPicture VARCHAR(70),
        FinishTime Date,
        RecentReviewTime Date,
        CurrentWeight REAL DEFAULT 1, 
        CurrentWeightUpdateTime VARCHAR(30),
        original_study_id INT,
        FOREIGN KEY (Username) REFERENCES User(Username) ON DELETE CASCADE
    )
'''

sql_createDailyReview='''
    CREATE TABLE ReviewState (
        Rid INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(20),
        WrongQuestionID INTEGER,
        push_date DATE NOT NULL,
        is_correct BOOLEAN DEFAULT 0,
        reviewed BOOLEAN DEFAULT 0,
        recent_review_time DATETIME,
        FOREIGN KEY (username) REFERENCES User(Username) ON DELETE CASCADE,
        FOREIGN KEY (WrongQuestionID) REFERENCES Study(id) ON DELETE CASCADE
);
'''

sql_create_notice='''
    CREATE TABLE notice (
        nid INTEGER PRIMARY KEY AUTOINCREMENT,
        NoticeName Varchar(20),
        username VARCHAR(20),
        Power VARCHAR(20),
        Notice_date DATE,
        Notice_content TEXT ,
        NoticePicture VARCHAR(70),
        notice_type VARCHAR(20) DEFAULT 'global',
        FOREIGN KEY (Power) REFERENCES User(Power),
        FOREIGN KEY (username) REFERENCES User(Username) ON DELETE CASCADE
);
'''

sql_create_UserChart_table='''
CREATE TABLE UserChart (
	id INTEGER NOT NULL, 
	username VARCHAR(20), 
	chart_type VARCHAR(50), 
	chart_path VARCHAR(200), 
	PRIMARY KEY (id), 
	FOREIGN KEY(username) REFERENCES User (Username) ON DELETE CASCADE
)
'''

sql_create_tags='''
CREATE TABLE Tag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name VARCHAR(40) NOT NULL UNIQUE,
    subject VARCHAR(20),
    color VARCHAR(20),
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
'''

sql_create_study_tags='''
CREATE TABLE StudyTag (
    study_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (study_id, tag_id),
    FOREIGN KEY (study_id) REFERENCES "Study"(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES "Tag"(id) ON DELETE CASCADE
);
'''
sql_create_weights_tags='''
CREATE TABLE IF NOT EXISTS "UserTagWeight" (
    user_username VARCHAR(20),
    tag_id INTEGER,
    weight REAL DEFAULT 0,
    PRIMARY KEY (user_username, tag_id),
    FOREIGN KEY (user_username) REFERENCES "User"(Username) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES "Tag"(id)
);
'''

sql_create_weights_tags_trigger='''
-- 创建一个更新 UserTagWeight 表的触发器
CREATE TRIGGER update_user_tag_weight
AFTER UPDATE OF CurrentWeight ON "Study"
BEGIN
    -- 清空 UserTagWeight 表中的现有数据
    DELETE FROM "UserTagWeight";
    -- 重新插入计算好的权重值
    INSERT INTO "UserTagWeight" (user_username, tag_id, weight)
    SELECT 
        s.Username,
        t.tag_id,
        SUM(s.CurrentWeight) AS total_weight
    FROM 
        "Study" s
    JOIN 
        "StudyTag" st ON s.id = st.study_id
    JOIN 
        "Tag" t ON st.tag_id = t.tag_id
    GROUP BY 
        s.Username, t.tag_id;
END;
'''
# -- 创建索引提升查询效率
sql_create_study_tags_index="CREATE INDEX idx_study_tag ON StudyTag (study_id, tag_id);"
sql_create_weights_tags_index="CREATE INDEX idx_user_tag_weight ON UserTagWeight (user_username, tag_id);"

sql_user_insert='''
insert into user values('admin','198198','cst21014@stu.com','admin','','')
'''

sql_tag_insert1='''
-- 插入父标签
INSERT INTO Tag (tag_name, subject, color, description)
VALUES 
    ('微积分', '数学', NULL, NULL),
    ('线性代数', '数学', NULL, NULL),
    ('概率论与数理统计', '数学', NULL, NULL),
    ('基础能力', '英语', NULL, NULL),
    ('题型专项', '英语', NULL, NULL),
    ('理论基础', '政治', NULL, NULL),
    ('题型技巧', '政治', NULL, NULL);
'''
sql_tag_insert2='''
-- 插入微积分的子标签
INSERT INTO Tag (tag_name, subject, color, description)
VALUES 
    ('极限与连续', '数学', '#ecffed', '微积分'),
    ('函数极限', '数学', '#ecffed', '父标签: 极限与连续'),
    ('数列极限', '数学', '#ecffed', '父标签: 极限与连续'),
    ('无穷小与无穷大', '数学', '#ecffed', '父标签: 极限与连续'),
    ('导数与微分', '数学', '#ecffed', '父标签: 微积分'),
    ('导数的定义', '数学', '#ecffed', '父标签: 导数与微分'),
    ('求导法则', '数学', '#ecffed', '父标签: 导数与微分'),
    ('高阶导数', '数学', '#ecffed', '父标签: 导数与微分'),
    ('中值定理', '数学', '#ecffed', '父标签: 微积分'),
    ('罗尔中值定理', '数学', '#ecffed', '父标签: 中值定理'),
    ('拉格朗日中值定理', '数学', '#ecffed', '父标签: 中值定理'),
    ('柯西中值定理', '数学', '#ecffed', '父标签: 中值定理'),
    ('不定积分', '数学', '#ecffed', '父标签: 微积分'),
    ('不定积分的概念', '数学', '#ecffed', '父标签: 不定积分'),
    ('换元积分法', '数学', '#ecffed', '父标签: 不定积分'),
    ('分部积分法', '数学', '#ecffed', '父标签: 不定积分'),
    ('定积分', '数学', '#ecffed', '父标签: 微积分'),
    ('定积分的定义', '数学', '#ecffed', '父标签: 定积分'),
    ('定积分的性质', '数学', '#ecffed', '父标签: 定积分'),
    ('牛顿 - 莱布尼茨公式', '数学', '#ecffed', '父标签: 定积分'),
    ('定积分应用', '数学', '#ecffed', '父标签: 微积分'),
    ('平面图形的面积', '数学', '#ecffed', '父标签: 定积分应用'),
    ('体积', '数学', '#ecffed', '父标签: 定积分应用'),
    ('弧长', '数学', '#ecffed', '父标签: 定积分应用'),
    ('微分方程', '数学', '#ecffed', '父标签: 微积分'),
    ('一阶微分方程', '数学', '#ecffed', '父标签: 微分方程'),
    ('可分离变量的微分方程', '数学', '#ecffed', '父标签: 一阶微分方程'),
    ('一阶线性微分方程', '数学', '#ecffed', '父标签: 一阶微分方程'),
    ('高阶线性微分方程', '数学', '#ecffed', '父标签: 微分方程'),
    ('多元函数微分学', '数学', '#ecffed', '父标签: 微积分'),
    ('多元函数的极限与连续', '数学', '#ecffed', '父标签: 多元函数微分学'),
    ('偏导数', '数学', '#ecffed', '父标签: 多元函数微分学'),
    ('全微分', '数学', '#ecffed', '父标签: 多元函数微分学'),
    ('重积分', '数学', '#ecffed', '父标签: 微积分'),
    ('二重积分', '数学', '#ecffed', '父标签: 重积分'),
    ('三重积分', '数学', '#ecffed', '父标签: 重积分'),
    ('曲线曲面积分', '数学', '#ecffed', '父标签: 微积分'),
    ('第一类曲线积分', '数学', '#ecffed', '父标签: 曲线曲面积分'),
    ('第二类曲线积分', '数学', '#ecffed', '父标签: 曲线曲面积分'),
    ('第一类曲面积分', '数学', '#ecffed', '父标签: 曲线曲面积分'),
    ('第二类曲面积分', '数学', '#ecffed', '父标签: 曲线曲面积分');
'''

sql_tag_insert3='''
-- 插入线性代数的子标签
INSERT INTO Tag (tag_name, subject, color, description)
VALUES 
    ('行列式', '数学', '#def0ff', '父标签: 线性代数'),
    ('行列式的定义', '数学', '#def0ff', '父标签: 行列式'),
    ('行列式的性质', '数学', '#def0ff', '父标签: 行列式'),
    ('行列式的计算', '数学', '#def0ff', '父标签: 行列式'),
    ('矩阵', '数学', '#def0ff', '父标签: 线性代数'),
    ('矩阵的运算', '数学', '#def0ff', '父标签: 矩阵'),
    ('逆矩阵', '数学', '#def0ff', '父标签: 矩阵'),
    ('矩阵的秩', '数学', '#def0ff', '父标签: 矩阵'),
    ('向量组的线性相关性', '数学', '#def0ff', '父标签: 线性代数'),
    ('向量组的线性组合', '数学', '#def0ff', '父标签: 向量组的线性相关性'),
    ('向量组的线性相关与无关', '数学', '#def0ff', '父标签: 向量组的线性相关性'),
    ('向量组的秩', '数学', '#def0ff', '父标签: 向量组的线性相关性'),
    ('线性方程组', '数学', '#def0ff', '父标签: 线性代数'),
    ('齐次线性方程组', '数学', '#def0ff', '父标签: 线性方程组'),
    ('非齐次线性方程组', '数学', '#def0ff', '父标签: 线性方程组'),
    ('特征值与特征向量', '数学', '#def0ff', '父标签: 线性代数'),
    ('特征值与特征向量的定义', '数学', '#def0ff', '父标签: 特征值与特征向量'),
    ('相似矩阵', '数学', '#def0ff', '父标签: 特征值与特征向量'),
    ('矩阵的对角化', '数学', '#def0ff', '父标签: 特征值与特征向量'),
    ('二次型', '数学', '#def0ff', '父标签: 线性代数'),
    ('二次型的定义', '数学', '#def0ff', '父标签: 二次型'),
    ('二次型的标准形', '数学', '#def0ff', '父标签: 二次型'),
    ('正定二次型', '数学', '#def0ff', '父标签: 二次型');
'''

sql_tag_insert4='''
-- 插入概率论与数理统计的子标签
INSERT INTO Tag (tag_name, subject, color, description)
VALUES 
    ('随机事件和概率', '数学', '#ffe0ea', '父标签: 概率论与数理统计'),
    ('随机事件', '数学', '#ffe0ea', '父标签: 随机事件和概率'),
    ('概率的定义', '数学', '#ffe0ea', '父标签: 随机事件和概率'),
    ('概率的性质', '数学', '#ffe0ea', '父标签: 随机事件和概率'),
    ('条件概率', '数学', '#ffe0ea', '父标签: 随机事件和概率'),
    ('随机变量及其分布', '数学', '#ffe0ea', '父标签: 概率论与数理统计'),
    ('离散型随机变量', '数学', '#ffe0ea', '父标签: 随机变量及其分布'),
    ('连续型随机变量', '数学', '#ffe0ea', '父标签: 随机变量及其分布'),
    ('分布函数', '数学', '#ffe0ea', '父标签: 随机变量及其分布'),
    ('多维随机变量及其分布', '数学', '#ffe0ea', '父标签: 概率论与数理统计'),
    ('二维随机变量', '数学', '#ffe0ea', '父标签: 多维随机变量及其分布'),
    ('边缘分布', '数学', '#ffe0ea', '父标签: 多维随机变量及其分布'),
    ('条件分布', '数学', '#ffe0ea', '父标签: 多维随机变量及其分布'),
    ('随机变量的数字特征', '数学', '#ffe0ea', '父标签: 概率论与数理统计'),
    ('数学期望', '数学', '#ffe0ea', '父标签: 随机变量的数字特征'),
    ('方差', '数学', '#ffe0ea', '父标签: 随机变量的数字特征'),
    ('协方差与相关系数', '数学', '#ffe0ea', '父标签: 随机变量的数字特征'),
    ('大数定律和中心极限定理', '数学', '#ffe0ea', '父标签: 概率论与数理统计'),
    ('切比雪夫大数定律', '数学', '#ffe0ea', '父标签: 大数定律和中心极限定理'),
    ('辛钦大数定律', '数学', '#ffe0ea', '父标签: 大数定律和中心极限定理'),
    ('独立同分布的中心极限定理', '数学', '#ffe0ea', '父标签: 大数定律和中心极限定理'),
    ('数理统计的基本概念', '数学', '#ffe0ea', '父标签: 概率论与数理统计'),
    ('总体与样本', '数学', '#ffe0ea', '父标签: 数理统计的基本概念'),
    ('统计量', '数学', '#ffe0ea', '父标签: 数理统计的基本概念'),
    ('抽样分布', '数学', '#ffe0ea', '父标签: 数理统计的基本概念'),
    ('参数估计', '数学', '#ffe0ea', '父标签: 概率论与数理统计'),
    ('点估计', '数学', '#ffe0ea', '父标签: 参数估计'),
    ('区间估计', '数学', '#ffe0ea', '父标签: 参数估计'),
    ('假设检验', '数学', '#ffe0ea', '父标签: 概率论与数理统计'),
    ('单个正态总体的假设检验', '数学', '#ffe0ea', '父标签: 假设检验'),
    ('两个正态总体的假设检验', '数学', '#ffe0ea', '父标签: 假设检验');
'''

sql_tag_insert5='''
-- 插入英语基础能力的子标签
INSERT INTO Tag (tag_name, subject, color, description)
VALUES 
    ('词汇积累', '英语', '#FF9800', '父标签: 基础能力'),
    ('语法学习', '英语', '#FF9800', '父标签: 基础能力'),
    ('长难句分析', '英语', '#FF9800', '父标签: 基础能力');
'''

sql_tag_insert6='''
-- 插入英语题型专项的子标签
INSERT INTO Tag (tag_name, subject, color, description)
VALUES 
    ('阅读理解', '英语', '#FF5722', '父标签: 题型专项'),
    ('写作', '英语', '#FF5722', '父标签: 题型专项'),
    ('翻译', '英语', '#FF5722', '父标签: 题型专项'),
    ('完型填空', '英语', '#FF5722', '父标签: 题型专项');
'''

sql_tag_insert7='''
-- 插入政治理论基础的子标签
INSERT INTO Tag (tag_name, subject, color, description)
VALUES 
    ('马克思主义基本原理', '政治', '#eb77ff', '父标签: 理论基础'),
    ('毛泽东思想和中国特色社会主义理论体系概论', '政治', '#eb77ff', '父标签: 理论基础'),
    ('中国近现代史纲要', '政治', '#eb77ff', '父标签: 理论基础'),
    ('思想道德修养与法律基础', '政治', '#eb77ff', '父标签: 理论基础'),
    ('形势与政策以及当代世界经济与政治', '政治', '#eb77ff', '父标签: 理论基础');
'''
sql_tag_insert8='''
-- 插入政治题型技巧的子标签
INSERT INTO Tag (tag_name, subject, color, description)
VALUES 
    ('选择题技巧', '政治', '#ac7eff', '父标签: 题型技巧'),
    ('分析题技巧', '政治', '#ac7eff', '父标签: 题型技巧');
'''

def create_table(sql):
    try:
        db = connect_db()
        db.execute(sql)
        db.commit()
        db.close()
    except BaseException as e:
        print('建表出错，', e)

def insert_data_with_value(db, sql_without_values, values):
    try:
        db.execute(sql_without_values, values)
        db.commit()
    except BaseException as e:
        print('插入出错（传参），', e)

def insert_data_without_value(db, sql_with_values):
    try:
        db.execute(sql_with_values)
        db.commit()
    except BaseException as e:
        print('出错（非传参），', e)
    
def update_data(db, sql):
    insert_data_without_value(db, sql)
    
def delete_data(db, sql):
    insert_data_without_value(db, sql)

def select_data(db,sql):
    try:
        result = db.cursor().execute(sql).fetchall()
        return result
    except BaseException as e:
        print('出错（选择数据），', e)

sql_drop_user='''
drop table user
'''

# 自定义分词函数
def jieba_tokenize(input_text):
    return [word for word in jieba.cut(input_text)]

# 创建数据库全文索引
fts_creation_scripts = [
    "CREATE VIRTUAL TABLE Forum_fts USING fts5(Title, PostingsText, Username, tokenize = 'unicode61');",
    "INSERT INTO Forum_fts(rowid, Title, PostingsText, Username) SELECT PostingsID, Title, PostingsText, Username FROM Forum;",
    "CREATE VIRTUAL TABLE Comment_fts USING fts5(Comment, Username, tokenize = 'unicode61');",
    "INSERT INTO Comment_fts(rowid, Comment, Username) SELECT CommentID, Comment, Username FROM Comment;",
    "CREATE VIRTUAL TABLE CrawlerData_fts USING fts5(Title, Content, Publisher, tokenize = 'unicode61');",
    "INSERT INTO CrawlerData_fts(rowid, Title, Content, Publisher) SELECT WebId, Title, Content ,Publisher FROM CrawlerData;",
    "CREATE VIRTUAL TABLE Study_fts USING fts5(content, Username, Type, Label, tokenize = 'unicode61');",
    "INSERT INTO Study_fts(rowid, content, Username, Type, Label) SELECT id, content, Username, Type, Label FROM Study;",
    "CREATE VIRTUAL TABLE notice_fts USING fts5(NoticeName, Notice_content, Username, tokenize = 'unicode61');",
    "INSERT INTO notice_fts(rowid, NoticeName, Notice_content, Username) SELECT nid, NoticeName, Notice_content, Username FROM notice;"
]
# 创建数据同步触发器
trigger_creation_scripts = [
    """
    CREATE TRIGGER forum_insert AFTER INSERT ON Forum
    BEGIN
        INSERT INTO Forum_fts(rowid, Title, PostingsText, Username) VALUES (new.PostingsID, new.Title, new.PostingsText, new.Username);
    END;
    """,
    """
    CREATE TRIGGER forum_update AFTER UPDATE ON Forum
    BEGIN
        UPDATE Forum_fts SET Title = new.Title, PostingsText = new.PostingsText, Username=new.Username WHERE rowid = old.PostingsID;
    END;
    """,
    """
    CREATE TRIGGER forum_delete AFTER DELETE ON Forum
    BEGIN
        DELETE FROM Forum_fts WHERE rowid = old.PostingsID;
    END;
    """,
    """
    CREATE TRIGGER comment_insert AFTER INSERT ON Comment
    BEGIN
        INSERT INTO Comment_fts(rowid, Comment, Username) VALUES (new.CommentID, new.Comment, new.Username);
    END;
    """,
    """
    CREATE TRIGGER comment_update AFTER UPDATE ON Comment
    BEGIN
        UPDATE Comment_fts SET Comment = new.Comment, Username=new.Username WHERE rowid = old.CommentID;
    END;
    """,
    """
    CREATE TRIGGER comment_delete AFTER DELETE ON Comment
    BEGIN
        DELETE FROM Comment_fts WHERE rowid = old.CommentID;
    END;
    """,
    """
    CREATE TRIGGER crawlerdata_insert AFTER INSERT ON CrawlerData
    BEGIN
        INSERT INTO CrawlerData_fts(rowid, Title, Content, Publisher) VALUES (new.WebId, new.Title, new.Content, new.Publisher);
    END;
    """,
    """
    CREATE TRIGGER crawlerdata_update AFTER UPDATE ON CrawlerData
    BEGIN
        UPDATE CrawlerData_fts SET Title = new.Title, Content = new.Content, new.Publisher WHERE rowid = old.WebId;
    END;
    """,
    """
    CREATE TRIGGER crawlerdata_delete AFTER DELETE ON CrawlerData
    BEGIN
        DELETE FROM CrawlerData_fts WHERE rowid = old.WebId;
    END;
    """,
    """
    CREATE TRIGGER study_insert AFTER INSERT ON Study
    BEGIN
        INSERT INTO Study_fts(rowid, content, Username, Type, Label) VALUES (new.id, new.content, new.Username, new.Type, new.Label);
    END;
    """,
    """
    CREATE TRIGGER study_update AFTER UPDATE ON Study
    BEGIN
        UPDATE Study_fts SET content = new.content, Username = new.Username, Type = new.Type, Label = new.Label WHERE rowid = old.id;
    END;
    """,
    """
    CREATE TRIGGER study_delete AFTER DELETE ON Study
    BEGIN
        DELETE FROM Study_fts WHERE rowid = old.id;
    END;
    """,
    """
    CREATE TRIGGER notice_insert AFTER INSERT ON notice
    BEGIN
        INSERT INTO notice_fts(rowid, NoticeName, Notice_content, Username) VALUES (new.nid, new.NoticeName, new.Notice_content, new.Username);
    END;
    """,
    """
    CREATE TRIGGER notice_update AFTER UPDATE ON notice
    BEGIN
        UPDATE notice_fts SET NoticeName = new.NoticeName, Notice_content = new.Notice_content, Username = new.Username WHERE rowid = old.nid;
    END;
    """,
    """
    CREATE TRIGGER notice_delete AFTER DELETE ON notice
    BEGIN
        DELETE FROM notice_fts WHERE rowid = old.nid;
    END;
    """
]

def init():
    db = connect_db()
    # try:
    #     sql_execute(sql_drop_user) # 清除user表
    # except BaseException as e:
    #     pass

    try:
        sql_execute(sql_createUserTable) # 建user表
    except BaseException as e:
        pass

    try:
        sql_execute(sql_create_UserChart_table) # 建UserChart表
    except BaseException as e:
        pass

    try:
        sql_execute(sql_user_insert) # 插入用户信息
    except BaseException as e:
        pass

    try:
        sql_execute(sql_createForumTable) # 建Forum表
    except BaseException as e:
        pass

    try:
        sql_execute(sql_create_Likes) # 建Likes表
    except BaseException as e:
        pass

    try:
        sql_execute(sql_createCommentTable) # 建Comment表
    except BaseException as e:
        pass

    try:
        sql_execute(sql_createCrawlerDataTable) # 建爬虫数据表sql_createStudyTable
    except BaseException as e:
        pass

    try:
        sql_execute(sql_createStudyTable) # 建个人学习数据表
    except BaseException as e:
        pass

    try:
        sql_execute(sql_createDailyReview) # 建每日推送的错题存储表
    except BaseException as e:
        pass

    try:
        sql_execute(sql_create_notice) # 建全服通知表
    except BaseException as e:
        pass

    try:
        sql_execute(sql_create_tags) # 建标签表
    except BaseException as e:
        pass
    

    try:
        sql_execute(sql_create_study_tags) # 建错题标签中间表
        sql_execute(sql_create_study_tags_index) # 建错题标签中间表查询索引
    except BaseException as e:
        pass
    try:
        sql_execute(sql_create_weights_tags) # 建权重标签用户中间表
        sql_execute(sql_create_weights_tags_index) # 建权重标签用户中间表索引
        sql_execute(sql_create_weights_tags_trigger) # 建标签权重触发器同步更新

    except BaseException as e:
        pass
    
    try:
        sql_execute(sql_tag_insert1) # 建标签表
        sql_execute(sql_tag_insert2) # 建标签表
        sql_execute(sql_tag_insert3) # 建标签表
        sql_execute(sql_tag_insert4) # 建标签表
        sql_execute(sql_tag_insert5) # 建标签表
        sql_execute(sql_tag_insert6) # 建标签表
        sql_execute(sql_tag_insert7) # 建标签表
        sql_execute(sql_tag_insert8) # 建标签表
    except BaseException as e:
        pass
    print('生成默认管理员账户admin,密码198198')
    # 创建分词器
    db.create_function('jieba_tokenize', 1, jieba_tokenize)
    for scripts in fts_creation_scripts:
        try:
            sql_execute(scripts,db)
        except BaseException as e:
            print(e)
            pass    
    for scripts in trigger_creation_scripts:
        try:
            sql_execute(scripts,db)
        except BaseException as e:
            # print(e)
            pass

# init()
# 数据迁移代码，由于后续大改标签的存储结构
# -- database: c:\Users\16936\Desktop\基于记忆曲线的考研学习平台\config\db\cst21014.db

# -- 禁用外键约束
# PRAGMA foreign_keys = OFF;

# -- 彻底清空关联表数据
# DELETE FROM StudyTag;
# DELETE FROM UserTagWeight;
# DELETE FROM Tag;

# -- 创建临时表存储父子关系
# CREATE TEMPORARY TABLE parent_relations (
#     child_tag TEXT PRIMARY KEY,
#     parent_tag TEXT
# );

# -- 插入父子关系数据（确保父标签唯一）
# INSERT INTO parent_relations (child_tag, parent_tag) VALUES
# -- 基础父子关系
# ('极限与连续', '微积分'), ('导数与微分', '微积分'), ('中值定理', '微积分'),
# ('不定积分', '微积分'), ('定积分', '微积分'), ('定积分应用', '微积分'),
# ('微分方程', '微积分'), ('多元函数微分学', '微积分'), ('重积分', '微积分'),
# ('曲线曲面积分', '微积分'), ('行列式', '线性代数'), ('矩阵', '线性代数'),
# ('向量组的线性相关性', '线性代数'), ('线性方程组', '线性代数'),
# ('特征值与特征向量', '线性代数'), ('二次型', '线性代数'),
# ('随机事件和概率', '概率论与数理统计'), ('随机变量及其分布', '概率论与数理统计'),
# ('多维随机变量及其分布', '概率论与数理统计'), ('随机变量的数字特征', '概率论与数理统计'),
# ('大数定律和中心极限定理', '概率论与数理统计'), ('数理统计的基本概念', '概率论与数理统计'),
# ('参数估计', '概率论与数理统计'), ('假设检验', '概率论与数理统计'),
# ('词汇积累', '基础能力'), ('语法学习', '基础能力'), ('长难句分析', '基础能力'),
# ('阅读理解', '题型专项'), ('写作', '题型专项'), ('翻译', '题型专项'),
# ('完型填空', '题型专项'), ('马克思主义基本原理', '理论基础'),
# ('毛泽东思想和中国特色社会主义理论体系概论', '理论基础'),
# ('中国近现代史纲要', '理论基础'), ('思想道德修养与法律基础', '理论基础'),
# ('形势与政策以及当代世界经济与政治', '理论基础'), ('选择题技巧', '题型技巧'),
# ('分析题技巧', '题型技巧');

# -- 插入父标签（跳过重复）
# INSERT OR IGNORE INTO Tag (tag_name, subject, color, description)
# SELECT parent_tag, '数学', NULL, NULL
# FROM parent_relations
# WHERE parent_tag IN ('微积分', '线性代数', '概率论与数理统计')
# UNION ALL
# SELECT parent_tag, '英语', NULL, NULL
# FROM parent_relations
# WHERE parent_tag IN ('基础能力', '题型专项')
# UNION ALL
# SELECT parent_tag, '政治', NULL, NULL
# FROM parent_relations
# WHERE parent_tag IN ('理论基础', '题型技巧');

# -- 创建临时表存储拆分后的标签
# CREATE TEMPORARY TABLE temp_tags (
#     tag_name TEXT PRIMARY KEY,
#     subject TEXT,
#     color TEXT,
#     description TEXT
# );

# -- 拆分原始数据并填充临时表（排除细分标签）
# INSERT INTO temp_tags (tag_name, subject, color, description)
# SELECT DISTINCT
#     TRIM(REPLACE(value, '#', '')),  -- 去除#符号
#     CASE
#         WHEN TRIM(REPLACE(value, '#', '')) IN (
#             SELECT child_tag FROM parent_relations
#         ) THEN (
#             SELECT subject FROM parent_relations
#             JOIN Tag ON parent_relations.parent_tag = Tag.tag_name
#             WHERE child_tag = TRIM(REPLACE(value, '#', ''))
#         )
#         ELSE '未知'
#     END,
#     CASE
#         WHEN TRIM(REPLACE(value, '#', '')) IN (
#             SELECT child_tag FROM parent_relations WHERE parent_tag IN ('微积分', '线性代数', '概率论与数理统计')
#         ) THEN '#ecffed'
#         WHEN TRIM(REPLACE(value, '#', '')) IN (
#             SELECT child_tag FROM parent_relations WHERE parent_tag IN ('基础能力', '题型专项')
#         ) THEN '#FF9800'
#         WHEN TRIM(REPLACE(value, '#', '')) IN (
#             SELECT child_tag FROM parent_relations WHERE parent_tag IN ('理论基础', '题型技巧')
#         ) THEN '#eb77ff'
#         ELSE '#d4d4d4'
#     END,
#     CASE
#         WHEN TRIM(REPLACE(value, '#', '')) IN (
#             SELECT child_tag FROM parent_relations
#         ) THEN '父标签: ' || (
#             SELECT parent_tag FROM parent_relations
#             WHERE child_tag = TRIM(REPLACE(value, '#', ''))
#         )
#         ELSE NULL
#     END
# FROM (
#     SELECT value FROM Study, json_each('["' || REPLACE(REPLACE(Label, '#', '","'), '""', '"') || '"]')
#     WHERE Label IS NOT NULL AND Label != ''
# )
# WHERE value NOT IN (
#     -- 排除细分标签
#     '函数极限', '数列极限', '无穷小与无穷大', '导数的定义', '求导法则', '高阶导数', '罗尔中值定理', '拉格朗日中值定理', '柯西中值定理', '不定积分的概念', '换元积分法', '分部积分法', '定积分的定义', '定积分的性质', '牛顿 - 莱布尼茨公式', '平面图形的面积', '体积', '弧长', '一阶微分方程', '可分离变量的微分方程', '一阶线性微分方程', '高阶线性微分方程', '多元函数的极限与连续', '偏导数', '全微分', '二重积分', '三重积分', '第一类曲线积分', '第二类曲线积分', '第一类曲面积分', '第二类曲面积分',
#     '行列式的定义', '行列式的性质', '行列式的计算', '矩阵的运算', '逆矩阵', '矩阵的秩', '向量组的线性组合', '向量组的线性相关与无关', '向量组的秩', '齐次线性方程组', '非齐次线性方程组', '特征值与特征向量的定义', '相似矩阵', '矩阵的对角化', '二次型的定义', '二次型的标准形', '正定二次型',
#     '随机事件', '概率的定义', '概率的性质', '条件概率', '离散型随机变量', '连续型随机变量', '分布函数', '二维随机变量', '边缘分布', '条件分布', '数学期望', '方差', '协方差与相关系数', '切比雪夫大数定律', '辛钦大数定律', '独立同分布的中心极限定理', '总体与样本', '统计量', '抽样分布', '点估计', '区间估计', '单个正态总体的假设检验', '两个正态总体的假设检验'
# )
# AND value != '';

# -- 插入所有标签（包括细分标签）
# INSERT INTO temp_tags (tag_name, subject, color, description) VALUES
# -- 数学标签
# ('微积分', '数学', NULL, NULL),
# ('函数', '数学', '#ecffed', '父标签: 微积分'),
# ('极限与连续', '数学', '#ecffed', '父标签: 微积分'),
# ('导数与微分', '数学', '#ecffed', '父标签: 微积分'),
# ('微分方程', '数学', '#ecffed', '父标签: 微积分'),
# ('函数极限', '数学', '#ecffed', '父标签: 极限与连续'),
# ('数列极限', '数学', '#ecffed', '父标签: 极限与连续'),
# ('无穷小与无穷大', '数学', '#ecffed', '父标签: 极限与连续'),
# ('导数的定义', '数学', '#ecffed', '父标签: 导数与微分'),
# ('求导法则', '数学', '#ecffed', '父标签: 导数与微分'),
# ('高阶导数', '数学', '#ecffed', '父标签: 导数与微分'),
# ('罗尔中值定理', '数学', '#ecffed', '父标签: 中值定理'),
# ('拉格朗日中值定理', '数学', '#ecffed', '父标签: 中值定理'),
# ('柯西中值定理', '数学', '#ecffed', '父标签: 中值定理'),
# ('不定积分的概念', '数学', '#ecffed', '父标签: 不定积分'),
# ('换元积分法', '数学', '#ecffed', '父标签: 不定积分'),
# ('分部积分法', '数学', '#ecffed', '父标签: 不定积分'),
# ('定积分的定义', '数学', '#ecffed', '父标签: 定积分'),
# ('定积分的性质', '数学', '#ecffed', '父标签: 定积分'),
# ('牛顿 - 莱布尼茨公式', '数学', '#ecffed', '父标签: 定积分'),
# ('平面图形的面积', '数学', '#ecffed', '父标签: 定积分应用'),
# ('体积', '数学', '#ecffed', '父标签: 定积分应用'),
# ('弧长', '数学', '#ecffed', '父标签: 定积分应用'),
# ('一阶微分方程', '数学', '#ecffed', '父标签: 微分方程'),
# ('可分离变量的微分方程', '数学', '#ecffed', '父标签: 一阶微分方程'),
# ('一阶线性微分方程', '数学', '#ecffed', '父标签: 一阶微分方程'),
# ('高阶线性微分方程', '数学', '#ecffed', '父标签: 微分方程'),
# ('多元函数的极限与连续', '数学', '#ecffed', '父标签: 多元函数微分学'),
# ('偏导数', '数学', '#ecffed', '父标签: 多元函数微分学'),
# ('全微分', '数学', '#ecffed', '父标签: 多元函数微分学'),
# ('二重积分', '数学', '#ecffed', '父标签: 重积分'),
# ('三重积分', '数学', '#ecffed', '父标签: 重积分'),
# ('第一类曲线积分', '数学', '#ecffed', '父标签: 曲线曲面积分'),
# ('第二类曲线积分', '数学', '#ecffed', '父标签: 曲线曲面积分'),
# ('第一类曲面积分', '数学', '#ecffed', '父标签: 曲线曲面积分'),
# ('第二类曲面积分', '数学', '#ecffed', '父标签: 曲线曲面积分'),
# -- 线性代数
# ('线性代数', '数学', NULL, NULL),
# ('行列式', '数学', '#def0ff', '父标签: 线性代数'),
# ('矩阵', '数学', '#def0ff', '父标签: 线性代数'),
# ('向量组的线性相关性', '数学', '#def0ff', '父标签: 线性代数'),
# ('线性方程组', '数学', '#def0ff', '父标签: 线性代数'),
# ('特征值与特征向量', '数学', '#def0ff', '父标签: 线性代数'),
# ('二次型', '数学', '#def0ff', '父标签: 线性代数'),
# ('行列式的定义', '数学', '#def0ff', '父标签: 行列式'),
# ('行列式的性质', '数学', '#def0ff', '父标签: 行列式'),
# ('行列式的计算', '数学', '#def0ff', '父标签: 行列式'),
# ('矩阵的运算', '数学', '#def0ff', '父标签: 矩阵'),
# ('逆矩阵', '数学', '#def0ff', '父标签: 矩阵'),
# ('矩阵的秩', '数学', '#def0ff', '父标签: 矩阵'),
# ('向量组的线性组合', '数学', '#def0ff', '父标签: 向量组的线性相关性'),
# ('向量组的线性相关与无关', '数学', '#def0ff', '父标签: 向量组的线性相关性'),
# ('向量组的秩', '数学', '#def0ff', '父标签: 向量组的线性相关性'),
# ('齐次线性方程组', '数学', '#def0ff', '父标签: 线性方程组'),
# ('非齐次线性方程组', '数学', '#def0ff', '父标签: 线性方程组'),
# ('特征值与特征向量的定义', '数学', '#def0ff', '父标签: 特征值与特征向量'),
# ('相似矩阵', '数学', '#def0ff', '父标签: 特征值与特征向量'),
# ('矩阵的对角化', '数学', '#def0ff', '父标签: 特征值与特征向量'),
# ('二次型的定义', '数学', '#def0ff', '父标签: 二次型'),
# ('二次型的标准形', '数学', '#def0ff', '父标签: 二次型'),
# ('正定二次型', '数学', '#def0ff', '父标签: 二次型'),

# -- 概率论与数理统计
# ('概率论与数理统计', '数学', NULL, NULL),
# ('随机事件和概率', '数学', '#ffe0ea', '父标签: 概率论与数理统计'),
# ('随机变量及其分布', '数学', '#ffe0ea', '父标签: 概率论与数理统计'),
# ('多维随机变量及其分布', '数学', '#ffe0ea', '父标签: 概率论与数理统计'),
# ('随机变量的数字特征', '数学', '#ffe0ea', '父标签: 概率论与数理统计'),
# ('大数定律和中心极限定理', '数学', '#ffe0ea', '父标签: 概率论与数理统计'),
# ('数理统计的基本概念', '数学', '#ffe0ea', '父标签: 概率论与数理统计'),
# ('参数估计', '数学', '#ffe0ea', '父标签: 概率论与数理统计'),
# ('假设检验', '数学', '#ffe0ea', '父标签: 概率论与数理统计'),
# ('随机事件', '数学', '#ffe0ea', '父标签: 随机事件和概率'),
# ('概率的定义', '数学', '#ffe0ea', '父标签: 随机事件和概率'),
# ('概率的性质', '数学', '#ffe0ea', '父标签: 随机事件和概率'),
# ('条件概率', '数学', '#ffe0ea', '父标签: 随机事件和概率'),
# ('离散型随机变量', '数学', '#ffe0ea', '父标签: 随机变量及其分布'),
# ('连续型随机变量', '数学', '#ffe0ea', '父标签: 随机变量及其分布'),
# ('分布函数', '数学', '#ffe0ea', '父标签: 随机变量及其分布'),
# ('二维随机变量', '数学', '#ffe0ea', '父标签: 多维随机变量及其分布'),
# ('边缘分布', '数学', '#ffe0ea', '父标签: 多维随机变量及其分布'),
# ('条件分布', '数学', '#ffe0ea', '父标签: 多维随机变量及其分布'),
# ('数学期望', '数学', '#ffe0ea', '父标签: 随机变量的数字特征'),
# ('方差', '数学', '#ffe0ea', '父标签: 随机变量的数字特征'),
# ('协方差与相关系数', '数学', '#ffe0ea', '父标签: 随机变量的数字特征'),
# ('切比雪夫大数定律', '数学', '#ffe0ea', '父标签: 大数定律和中心极限定理'),
# ('辛钦大数定律', '数学', '#ffe0ea', '父标签: 大数定律和中心极限定理'),
# ('独立同分布的中心极限定理', '数学', '#ffe0ea', '父标签: 大数定律和中心极限定理'),
# ('总体与样本', '数学', '#ffe0ea', '父标签: 数理统计的基本概念'),
# ('统计量', '数学', '#ffe0ea', '父标签: 数理统计的基本概念'),
# ('抽样分布', '数学', '#ffe0ea', '父标签: 数理统计的基本概念'),
# ('点估计', '数学', '#ffe0ea', '父标签: 参数估计'),
# ('区间估计', '数学', '#ffe0ea', '父标签: 参数估计'),
# ('单个正态总体的假设检验', '数学', '#ffe0ea', '父标签: 假设检验'),
# ('两个正态总体的假设检验', '数学', '#ffe0ea', '父标签: 假设检验'),
# -- 英语标签
# ('基础能力', '英语', NULL, NULL),
# ('语法学习', '英语', '#FF9800', '父标签: 基础能力'),
# ('虚拟语气', '英语', '#FF9800', '父标签: 语法学习'),
# ('倒装结构', '英语', '#FF9800', '父标签: 语法学习'),
# ('词汇积累', '英语', '#FF9800', '父标签: 基础能力'),
# ('长难句分析', '英语', '#FF9800', '父标签: 基础能力'),
# ('题型专项', '英语', NULL, NULL),
# ('阅读理解', '英语', '#FF5722', '父标签: 题型专项'),
# ('推理判断题', '英语', '#FF5722', '父标签: 阅读理解'),
# ('词义猜测题', '英语', '#FF5722', '父标签: 阅读理解'),
# ('写作', '英语', '#FF5722', '父标签: 题型专项'),
# ('翻译', '英语', '#FF5722', '父标签: 题型专项'),
# ('完型填空', '英语', '#FF5722', '父标签: 题型专项'),

# -- 政治标签
# ('理论基础', '政治', NULL, NULL),
# ('马克思主义基本原理', '政治', '#eb77ff', '父标签: 理论基础'),
# ('剩余价值理论', '政治', '#eb77ff', '父标签: 马克思主义基本原理'),
# ('毛泽东思想和中国特色社会主义理论体系概论', '政治', '#eb77ff', '父标签: 理论基础'),
# ('中国近现代史纲要', '政治', '#eb77ff', '父标签: 理论基础'),
# ('思想道德修养与法律基础', '政治', '#eb77ff', '父标签: 理论基础'),
# ('形势与政策以及当代世界经济与政治', '政治', '#eb77ff', '父标签: 理论基础'),
# ('题型技巧', '政治', NULL, NULL),
# ('选择题技巧', '政治', '#ac7eff', '父标签: 题型技巧'),
# ('分析题技巧', '政治', '#ac7eff', '父标签: 题型技巧'),
# ('材料分析题', '政治', '#ac7eff', '父标签: 分析题技巧');


# -- 插入子标签数据，包含细分标签（使用 OR IGNORE）
# INSERT OR IGNORE INTO Tag (tag_name, subject, color, description)
# SELECT tag_name, subject, color, description
# FROM temp_tags
# WHERE tag_name NOT IN (
#     SELECT parent_tag FROM parent_relations
#     WHERE parent_tag IN ('微积分', '线性代数', '概率论与数理统计', '基础能力', '题型专项', '理论基础', '题型技巧')
# )
# UNION ALL
# SELECT 
#     CASE 
#         WHEN child_tag IN ('函数极限', '数列极限', '无穷小与无穷大', '导数的定义', '求导法则', '高阶导数', '罗尔中值定理', '拉格朗日中值定理', '柯西中值定理', '不定积分的概念', '换元积分法', '分部积分法', '定积分的定义', '定积分的性质', '牛顿 - 莱布尼茨公式', '平面图形的面积', '体积', '弧长', '一阶微分方程', '可分离变量的微分方程', '一阶线性微分方程', '高阶线性微分方程', '多元函数的极限与连续', '偏导数', '全微分', '二重积分', '三重积分', '第一类曲线积分', '第二类曲线积分', '第一类曲面积分', '第二类曲面积分') THEN child_tag
#         WHEN child_tag IN ('行列式的定义', '行列式的性质', '行列式的计算', '矩阵的运算', '逆矩阵', '矩阵的秩', '向量组的线性组合', '向量组的线性相关与无关', '向量组的秩', '齐次线性方程组', '非齐次线性方程组', '特征值与特征向量的定义', '相似矩阵', '矩阵的对角化', '二次型的定义', '二次型的标准形', '正定二次型') THEN child_tag
#         WHEN child_tag IN ('随机事件', '概率的定义', '概率的性质', '条件概率', '离散型随机变量', '连续型随机变量', '分布函数', '二维随机变量', '边缘分布', '条件分布', '数学期望', '方差', '协方差与相关系数', '切比雪夫大数定律', '辛钦大数定律', '独立同分布的中心极限定理', '总体与样本', '统计量', '抽样分布', '点估计', '区间估计', '单个正态总体的假设检验', '两个正态总体的假设检验') THEN child_tag
#     END,
#     CASE 
#         WHEN parent_tag IN ('微积分', '线性代数', '概率论与数理统计') THEN '数学'
#         WHEN parent_tag IN ('基础能力', '题型专项') THEN '英语'
#         WHEN parent_tag IN ('理论基础', '题型技巧') THEN '政治'
#     END,
#     CASE 
#         WHEN parent_tag IN ('微积分', '线性代数', '概率论与数理统计') THEN '#ecffed'
#         WHEN parent_tag IN ('基础能力', '题型专项') THEN '#FF9800'
#         WHEN parent_tag IN ('理论基础', '题型技巧') THEN '#eb77ff'
#     END,
#     '父标签: ' || parent_tag
# FROM parent_relations
# WHERE child_tag IN (
#     '函数极限', '数列极限', '无穷小与无穷大', '导数的定义', '求导法则', '高阶导数', '罗尔中值定理', '拉格朗日中值定理', '柯西中值定理', '不定积分的概念', '换元积分法', '分部积分法', '定积分的定义', '定积分的性质', '牛顿 - 莱布尼茨公式', '平面图形的面积', '体积', '弧长', '一阶微分方程', '可分离变量的微分方程', '一阶线性微分方程', '高阶线性微分方程', '多元函数的极限与连续', '偏导数', '全微分', '二重积分', '三重积分', '第一类曲线积分', '第二类曲线积分', '第一类曲面积分', '第二类曲面积分',
#     '行列式的定义', '行列式的性质', '行列式的计算', '矩阵的运算', '逆矩阵', '矩阵的秩', '向量组的线性组合', '向量组的线性相关与无关', '向量组的秩', '齐次线性方程组', '非齐次线性方程组', '特征值与特征向量的定义', '相似矩阵', '矩阵的对角化', '二次型的定义', '二次型的标准形', '正定二次型',
#     '随机事件', '概率的定义', '概率的性质', '条件概率', '离散型随机变量', '连续型随机变量', '分布函数', '二维随机变量', '边缘分布', '条件分布', '数学期望', '方差', '协方差与相关系数', '切比雪夫大数定律', '辛钦大数定律', '独立同分布的中心极限定理', '总体与样本', '统计量', '抽样分布', '点估计', '区间估计', '单个正态总体的假设检验', '两个正态总体的假设检验'
# );


# -- 清理临时表
# DROP TABLE parent_relations;
# DROP TABLE temp_tags;

# -- 重新关联 StudyTag
# INSERT INTO StudyTag (study_id, tag_id)
# SELECT s.id, t.id
# FROM Study s
# CROSS JOIN Tag t
# WHERE s.Label LIKE '%' || '#' || t.tag_name || '%';

# -- 重新计算权重
# INSERT INTO UserTagWeight (user_username, tag_id, weight)
# SELECT s.Username, t.id, SUM(s.CurrentWeight)
# FROM Study s
# JOIN StudyTag st ON s.id = st.study_id
# JOIN Tag t ON st.tag_id = t.id
# GROUP BY s.Username, t.id;

# -- 重新启用外键约束
# PRAGMA foreign_keys = ON;



# db=connect_db()
# sql_execute(sql_tag_insert1,db) # 建标签表
# sql_execute(sql_tag_insert2,db) # 建标签表
# sql_execute(sql_tag_insert3,db) # 建标签表
# sql_execute(sql_tag_insert4,db) # 建标签表
# sql_execute(sql_tag_insert5,db) # 建标签表
# sql_execute(sql_tag_insert6,db) # 建标签表
# sql_execute(sql_tag_insert7,db) # 建标签表
# sql_execute(sql_tag_insert8,db) # 建标签表