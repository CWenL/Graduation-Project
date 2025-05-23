erDiagram
    USER {
        int Username PK
        string Password
        string Email
        string Power
        string StudyPlan
        string State
        string Salt
        string BafaKey
    }
    
    FORUM {
        int PostingsID PK
        string Title
        string Username FK
        datetime PostingsTime
        string IpLoc
        string Tag
        string PostingsText
        string PostingsPicture
        int PostingsSupport
        int PostingsViewNum
    }
    
    LIKES {
        string Username FK PK
        int PostingsID FK PK
    }
    
    COMMENT {
        int CommentID PK
        int PostingsID FK
        string Username FK
        string Comment
        datetime CommentTime
        string CommentImg
    }
    
    CRAWLERDATA {
        int WebId PK
        string Title
        datetime UpdateTime
        string Publisher
        string Content
        string WebsiteLink
        string WebsitePicture
    }
    
    STUDY {
        int id PK
        string Username FK
        string Content
        string Type
        string Label
        string QuestionPicture
        string AnswerPicture
        datetime FinishTime
        datetime RecentReviewTime
        float CurrentWeight
        datetime CurrentWeightUpdateTime
        int original_study_id
    }
    
    REVIEWSTATE {
        int Rid PK
        string username FK
        int WrongQuestionID FK
        date push_date
        bool is_correct
        bool reviewed
        datetime recent_review_time
    }
    
    NOTICE {
        int nid PK
        string NoticeName
        string username FK
        string Power FK
        date Notice_date
        string Notice_content
        string NoticePicture
        string notice_type
    }
    
    USERCHART {
        int id PK
        string username FK
        string chart_type
        string chart_path
    }
    
    TAG {
        int id PK
        string tag_name UK
        string subject
        string color
        string description
        datetime created_at
    }
    
    STUDYTAG {
        int study_id PK FK
        int tag_id PK FK
    }
    
    USERTAGWEIGHT {
        string user_username PK FK
        int tag_id PK FK
        float weight
    }
    
    USER ||--o{ FORUM : 发帖
    USER ||--o{ LIKES : 点赞
    USER ||--o{ COMMENT : 评论
    USER ||--o{ STUDY : 学习记录
    USER ||--o{ REVIEWSTATE : 复习状态
    USER ||--o{ NOTICE : 发布通知
    USER ||--o{ USERCHART : 图表
    USER }|..|{ TAG : 标签权重（通过USERTAGWEIGHT）
    
    FORUM ||--o{ LIKES : 被点赞
    FORUM ||--o{ COMMENT : 被评论
    STUDY ||--o{ REVIEWSTATE : 错题复习
    STUDY }|..|{ TAG : 标签（通过STUDYTAG）
    TAG ||--o{ STUDYTAG : 关联学习记录
    TAG }|..|{ USER : 用户标签权重（通过USERTAGWEIGHT）
