// 模态框相关
const modal = document.getElementById("myModal");
const modalImg = document.getElementById("modalImage");
const span = document.getElementsByClassName("close")[0];
const imageModal = document.getElementById("image-modal");
const imageModalImg = document.getElementById("modal-image");
const imageModalClose = document.getElementsByClassName("close-image-modal")[0];

// 图片点击事件
function openModal(src) {
    modal.style.display = "block";
    modalImg.src = src;
}

span.onclick = function () {
    closeModal();
};

window.onclick = function (event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
};

// 关闭图片模态框
function closeImageModal() {
    imageModal.style.display = "none";
}

// 打开图片模态框
function openImageModal(src) {
    imageModal.style.display = "block";
    imageModalImg.src = src;
}

// 全局变量
let currentTagId = null;
let currentPage = 1;
let totalPages = 1;

// 修改后的标签点击处理函数
function handleTagClick(element, event) {
    event.stopPropagation();
    // 确保点击的不是展开按钮及其子元素
    if (event.target.closest('.toggle-btn')) {
        return;
    }

    const tagNode = element.closest('.tag-node');
    if (!tagNode) {
        console.error('未找到标签节点');
        return;
    }

    const tagId = tagNode.dataset.tagId;
    if (!tagId) {
        console.error('标签 ID 未定义');
        return;
    }

    console.log('点击的标签 ID:', tagId);
    getTagQuestions(tagId);
}

function toggleSubTags(btn, event) {
    event.stopPropagation();
    const subTags = btn.parentElement.querySelector('.sub-tags');
    const toggleIcon = btn.querySelector('.toggle-icon');

    if (subTags) {
        subTags.classList.toggle('expanded');
        if (subTags.classList.contains('expanded')) {
            toggleIcon.src = "/static/imgs/收起子标签.png";
        } else {
            toggleIcon.src = "/static/imgs/展开子标签.png";
        }
    }
}

// 获取标签关联题目（分页）
function getTagQuestions(tagId, page = 1) {
    currentTagId = tagId;
    currentPage = page;

    console.log('尝试获取标签 ID 为', tagId, '的题目，当前页码:', page);

    fetch(`/api/get-questions-by-tag?tag_id=${tagId}&page=${page}`)
        .then(response => {
            if (!response.ok) throw new Error('当前题库中暂无此类题');
            return response.json();
        })
        .then(data => {
            console.log('后端返回的数据:', data);
            if (data.success) {
                updateQuestionList(data.questions);
                updatePagination(data);
                totalPages = data.total_pages;
                // 动态显示标签名称
                document.getElementById('current-tag-name').textContent = `${data.tag_name || '当前标签'} `;
            } else {
                showError(data.message);
            }
        })
        .catch(error => {
            console.error('请求错误:', error);
            showError('当前题库中暂无此类题');
        });
}

function updateQuestionList(questions) {
    const list = document.getElementById('tag-question-list');
    list.innerHTML = '';
    // 添加随机复习按钮
    const randomReviewBtn = document.createElement('button');
    randomReviewBtn.id = 'random-review-btn';
    randomReviewBtn.textContent = '开始标签复习';
    randomReviewBtn.className = 'question-card';
    randomReviewBtn.onclick = () => randomReview(currentTagId);
    list.appendChild(randomReviewBtn);

    if (questions.length === 0) {
        const noQuestionsMessage = document.createElement('div');
        noQuestionsMessage.textContent = '当前题库中暂无此类题';
        noQuestionsMessage.classList.add('no-questions-message');
        list.appendChild(noQuestionsMessage);
    } else {
        questions.forEach(question => {
            const div = document.createElement('div');
            div.className = 'question-card';
            div.dataset.question = JSON.stringify(question);
            div.innerHTML = `
                <h3>${question.content}</h3>
                <div class="question-info">
                    <span>类型：${question.type}</span>
                    <span>${question.username}的正确率：${(question.review_accuracy * 100).toFixed(2)}%</span>
                </div>
            `;
            div.onclick = () => showQuestionModal(JSON.parse(div.dataset.question));
            list.appendChild(div);
        });
    }
}

// 更新分页控件
function updatePagination(data) {
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    const pageNumbers = document.getElementById('page-numbers');
    pageNumbers.innerHTML = '';
    prevBtn.disabled = !data.has_prev;
    nextBtn.disabled = !data.has_next;
    currentPage = data.current_page;
    const maxVisible = 3;
    const totalPages = data.total_pages;
    const start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    const end = Math.min(totalPages, start + maxVisible - 1);
    // 首页按钮
    if (start > 1) {
        createPageButton(1);
        if (start > 2) addEllipsis();
    }
    // 中间页码
    for (let i = start; i <= end; i++) {
        createPageButton(i);
    }
    // 尾页按钮
    if (end < totalPages) {
        if (end < totalPages - 1) addEllipsis();
        createPageButton(totalPages);
    }
}

// 创建页码按钮
function createPageButton(page) {
    const btn = document.createElement('button');
    btn.textContent = page;
    if (page === currentPage) btn.classList.add('active');
    btn.onclick = () => getTagQuestions(currentTagId, page);
    document.getElementById('page-numbers').appendChild(btn);
}

// 添加省略号
function addEllipsis() {
    const span = document.createElement('span');
    span.textContent = '...';
    document.getElementById('page-numbers').appendChild(span);
}

// 显示题目详情模态框
function showQuestionModal(question) {
    const modal = document.getElementById('question-detail-modal');
    const detail = document.getElementById('question-detail');
    let recentReviewTimeText = '暂未复习';
    if (question.recent_review_time) {
        recentReviewTimeText = new Date(question.recent_review_time).toLocaleString();
    }
    detail.innerHTML = `
        <h2>${question.content}</h2>
        <div class="detail-group">
            <h3>题目信息</h3>
            <p style="text-align:left;">ID：${question.id}</p>
            <p style="text-align:left;">类型：${question.type}</p>
            <p style="text-align:left;">标签：${question.label}</p>
        </div>
        <div class="detail-group" style="text-align:left;">
            <h3>学习记录</h3>
            <p>完成时间：${new Date(question.finish_time).toLocaleString()}</p>
            <p>最近复习：${recentReviewTimeText}</p>
            <p>${question.username}的正确率：${(question.review_accuracy * 100).toFixed(2)}%</p>
            <!-- 新增收藏按钮 -->
            <button class="collect-btn" onclick="collectQuestion(${question.id})">收藏到我的错题本</button>
        </div>
        <div class="image-group">
            <h3>题目图片</h3>
            ${question.question_picture ? `<img src="/${question.question_picture}" class="detail-image" onclick="openImageModal('/${question.question_picture}')">` : '<p>无题目图片</p>'}
        </div>
        <div class="image-group">
            <h3>答案图片</h3>
            ${question.answer_picture ? `<img src="/${question.answer_picture}" class="detail-image" onclick="openImageModal('/${question.answer_picture}')">` : '<p>无答案图片</p>'}
        </div>
    `;

    modal.style.display = 'block';
}

// 关闭模态框
function closeModal() {
    document.getElementById('question-detail-modal').style.display = 'none';
}

// 错误提示
function showError(message) {
    const list = document.getElementById('tag-question-list');
    list.innerHTML = `<div class="error-message">${message}</div>`;
}

// 分页控制
function prevPage() {
    if (currentPage > 1) getTagQuestions(currentTagId, currentPage - 1);
}

function nextPage() {
    if (currentPage < totalPages) getTagQuestions(currentTagId, currentPage + 1);
}

function randomReview(tagId) {
    fetch(`/api/random-question-by-tag?tag_id=${tagId}`)
        .then(response => {
            if (!response.ok) throw new Error('请求失败');
            return response.json();
        })
        .then(data => {
            console.log('randomReview 接收到的后端数据:', data);
            if (data.success) {
                showReviewModal(data.question);
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('请求错误:', error);
            alert('请求失败，请重试');
        });
}

function showReviewModal(question) {
    console.log('进入 showReviewModal，question 数据:', question);
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'review-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close" onclick="closeReviewModal()">&times;</span>
            <div class="reviewed-question">
                <h2>${question.content}</h2>
                <p>题目 ID：${question.id}</p>
                <p>题目类型：${question.type}</p>
                <p>题目标签：${question.label}</p>
                <p>问题：</p>
                <img src="/${question.question_picture}" alt="问题" class="detail-image" onclick="openImageModal('/${question.question_picture}')">
                <p>完成时间：${new Date(question.finish_time).toLocaleString()}</p>
                <p>最近复习时间：${new Date(question.recent_review_time).toLocaleString()}</p>
                <p>当前权重：${question.current_weight}</p>
                <p>${question.username}的正确率：${(question.review_accuracy * 100).toFixed(2)}%</p>
            </div>
            <div class="correct-answer-section" style="display: none;">
                <h3>正确答案:</h3>
                <img id="answer-picture" src="/${question.answer_picture}" alt="正确答案图片" class="image-preview" onclick="openImageModal('/${question.answer_picture}')">
            </div>
            <form id="answer-form" enctype="multipart/form-data" style="display: block;">
                <input type="hidden" name="question_id" value="${question.id}">
                <h2>答案上传区</h2>
                <input class="file_input" type="file" name="answer-file" id="answer-file" accept="image/*">
                <div class="upload-container">
                    <label for="answer-file">
                        <button class="upload-button" id="custom-upload-button" type="button"> <!-- 关键：type="button" 避免表单提交 -->
                            <span>选择文件</span>
                            <span>+</span>
                        </button>
                    </label>
                </div>
                <div class="file-name">
                    <span class="file-icon">📁</span>
                    <span id="file-name">未选择任何文件</span>
                </div>
            </form>
            <div class="user-answer-section" style="display: none; text-align: center;">
                <div class="card-header"><h3>你上传的解答图片</h3></div>
                <img id="user-answer-picture" src="" alt="用户解答图片" class="image-preview" onclick="openImageModal(this.src)">
            </div>
            <div class="result-feedback" id="result-feedback" style="display: none;"></div>
            <div class="button-group" id="action-buttons" style="display: none;text-align: center;">
                <button class="btn btn-success" type="button" id="correct-btn" style="width: 20%;--bs-btn-bg: #2bd184;">✔</button>
                <button class="btn btn-danger" type="button" id="incorrect-btn" style="width: 20%;">✖</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    modal.style.display = 'block';

    // 阻止上传区域点击事件冒泡（保留，避免误触关闭模态框）
    const uploadContainer = modal.querySelector('.upload-container');
    if (uploadContainer) {
        uploadContainer.addEventListener('click', function (e) {
            e.stopPropagation();
        });
    }

    // 绑定上传按钮点击事件：手动触发文件输入框，不提交表单
    const uploadButton = modal.querySelector('#custom-upload-button');
    const fileInput = modal.querySelector('#answer-file');
    if (uploadButton && fileInput) {
        uploadButton.addEventListener('click', (e) => {
            e.preventDefault(); // 防止意外默认行为
            fileInput.click(); // 触发文件选择对话框
        });
    }

    // 文件选择后的处理（预览图片）
    fileInput.addEventListener('change', function () {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const userAnswerImage = modal.querySelector('#user-answer-picture');
                userAnswerImage.src = e.target.result;
                modal.querySelector('.user-answer-section').style.display = 'block';
                showReviewCorrectAnswer(modal, question.answer_picture);
            };
            reader.readAsDataURL(file);
        }
    });

    const correctBtn = modal.querySelector('#correct-btn');
    if (correctBtn) {
        correctBtn.addEventListener('click', async () => {
            console.log('点击了正确按钮，题目 ID:', question.id);
            const newStudyId = await collectQuestionAutomatically(question.id);
            const useId = newStudyId || question.id; // 如果收藏失败，使用原始 id
            handleReviewResult(1, useId);
        });
    }
    const incorrectBtn = modal.querySelector('#incorrect-btn');
    if (incorrectBtn) {
        incorrectBtn.addEventListener('click', async () => {
            console.log('点击了错误按钮，题目 ID:', question.id);
            const newStudyId = await collectQuestionAutomatically(question.id);
            const useId = newStudyId || question.id; // 如果收藏失败，使用原始 id
            handleReviewResult(0, useId);
        });
    }
    }

function showReviewCorrectAnswer(modal, answerPath) {
    const correctSection = modal.querySelector('.correct-answer-section');
    const actionButtons = modal.querySelector('#action-buttons');
    const answerPicture = modal.querySelector('#answer-picture');
    
    answerPicture.src = `/${answerPath}`;
    correctSection.style.display = 'block';
    actionButtons.style.display = 'block';
}

function handleReviewResult(isCorrect, questionId) {
    const modal = document.getElementById('review-modal');
    const resultFeedback = modal.querySelector('#result-feedback');
    const answerform = modal.querySelector('#answer-form');
    const actionButtons = modal.querySelector('#action-buttons');
    resultFeedback.className = isCorrect ? 'result-feedback correct' : 'result-feedback incorrect';
    resultFeedback.textContent = isCorrect ? '恭喜你，答案正确！' : '很遗憾，答案错误。';
    resultFeedback.style.display = 'block';
    answerform.style.display = 'none';
    actionButtons.style.display = 'none';
    // 新增标识字段
    const reviewModule = 'tag_review'; 
    // 提交复习结果到后端（需补充后端接口）
    fetch(`/api/record-result/${questionId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_correct: isCorrect, review_module: reviewModule })
    })
      .then(response => {
            if (!response.ok) throw new Error('请求失败');
            return response.json();
        })
      .then(data => {
            if (data.success) {
                // 可添加刷新逻辑
            } else {
                alert(data.message);
            }
        })
      .catch(error => {
            console.error('请求错误:', error);
            alert('请求失败，请重试');
        });
    // 添加“下一题”按钮
    const nextQuestionButton = document.createElement('button');
    nextQuestionButton.textContent = '下一题';
    nextQuestionButton.className = 'btn-3d';
    nextQuestionButton.style.display = 'block';
    nextQuestionButton.style.margin = '10px auto';
    // 获取“开始标签复习”按钮的点击事件处理函数
    const randomReviewBtn = document.getElementById('random-review-btn');
    const randomReviewClickHandler = randomReviewBtn.onclick;
    nextQuestionButton.addEventListener('click', () => {
        if (randomReviewClickHandler) {
            // 调用“开始标签复习”按钮的点击事件处理函数
            randomReviewClickHandler();
        } else {
            console.error('未找到“开始标签复习”按钮的点击事件处理函数');
        }
        closeReviewModal(); // 关闭当前模态框
    });
    // 将按钮插入到复习结果文本附近
    resultFeedback.parentNode.insertBefore(nextQuestionButton, resultFeedback.nextSibling);
}

// 自动收藏函数（仅传递原始题目 ID）
function collectQuestionAutomatically(originalStudyId) {
    return fetch(`/api/check-question-status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ original_study_id: originalStudyId })
    })
   .then(response => response.json())
   .then(data => {
        if (data.success) {
            if (data.is_publisher) {
                // 用户是原始发布者，不执行收藏操作，返回原始题目 ID
                return originalStudyId;
            }
            if (data.is_collected) {
                // 题目已收藏，返回收藏记录的 ID
                return data.study_id;
            }
            // 题目未收藏，执行收藏操作
            return fetch(`/api/collect_question`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ original_study_id: originalStudyId })
            })
           .then(response => response.json())
           .then(data => data.new_study_id);
        } else {
            console.error(data.message);
            return null;
        }
    })
   .catch(error => {
        console.error('检查题目状态时出错:', error);
        return null;
    });
}

function collectQuestion(originalStudyId) {
    fetch(`/api/collect_question`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            original_study_id: originalStudyId,
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("题目已成功收藏到错题本！");
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error("收藏请求失败:", error);
        alert("收藏失败，请重试");
    });
}

function closeReviewModal() {
    const modal = document.getElementById('review-modal');
    if (modal) {
        document.body.removeChild(modal);
    }
}