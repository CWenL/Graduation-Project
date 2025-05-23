
// 初始化变量
let currentQuestionId = null;
let isCorrect = null;
let hasUploaded = false;
let currentPage = 1;
let userUploadedAnswerFile = null;
let userAnswerBlobUrl = null;
let answerPicturePath = null; // 新增：存储正确答案路径

// 模态框相关
const modal = document.getElementById("myModal");
const modalImg = document.getElementById("modalImage");
const span = document.getElementsByClassName("close")[0];

// 图片点击事件
function openModal(src) {
    modal.style.display = "block";
    modalImg.src = src;
}

span.onclick = function () {
    modal.style.display = "none";
};

window.onclick = function (event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
};

// 页面加载时获取第一题和当日已复习错题
window.onload = function () {
    getNewQuestion();
    getReviewedQuestions(currentPage);
};

// 选择文件后显示用户上传的图片和正确答案
document.getElementById('answer-file').addEventListener('change', function () {
    hasUploaded = this.files.length > 0;

    // 读取文件，显示图片（暂存前端）
    const file = this.files[0];
    if (file) {
        userUploadedAnswerFile = file;
        const reader = new FileReader();
        reader.onload = function (e) {
            userAnswerBlobUrl = e.target.result;
            const userAnswerImage = document.getElementById('user-answer-picture');
            userAnswerImage.src = userAnswerBlobUrl;
            document.querySelector('.user-answer-section').style.display = 'block';

            // 显示正确答案
            showCorrectAnswer();
        };
        reader.readAsDataURL(file);
    }
});

// 显示正确答案
function showCorrectAnswer() {
    const correctSection = document.querySelector('.correct-answer-section');
    const actionButtons = document.getElementById('action-buttons');
    const answerPicture = document.getElementById('answer-picture');

    answerPicture.src = answerPicturePath;
    correctSection.style.display = 'block';
    actionButtons.style.display = 'block';
}

// 替换答案
function replaceAnswer() {
    if (!userUploadedAnswerFile) {
        alert('请先上传你的解答图片');
        return;
    }

    const formData = new FormData();
    formData.append('question_id', currentQuestionId);
    formData.append('replace-file', userUploadedAnswerFile);

    fetch(`/api/replace-answer/${currentQuestionId}`, {
        method: 'POST',
        body: formData
    })
      .then(response => {
            if (!response.ok) throw new Error('请求失败');
            return response.json();
        })
      .then(data => {
            if (data.success) {
                alert('答案替换成功！');
                // 清理前端暂存数据
                userUploadedAnswerFile = null;
                document.getElementById('user-answer-picture').src = '';
                document.querySelector('.user-answer-section').style.display = 'none';
                document.getElementById('replace-answer').style.display = 'none';
                document.getElementById('action-buttons').style.display = 'none';
                document.getElementById('answer-form').style.display = 'none';
                const newQuestionBtn = document.getElementById('new-question-btn');
                newQuestionBtn.style.display = 'block';

                // 更新正确答案图片展示
                const answerPicture = document.getElementById('answer-picture');
                answerPicture.src = userAnswerBlobUrl;

                // 刷新答案图片的显示
                answerPicture.onload = function() {
                    document.querySelector('.correct-answer-section').style.display = 'block';
                };
            } else {
                alert('答案替换失败：' + data.message);
            }
        })
      .catch(error => {
            console.error('请求错误:', error);
            alert('请求失败，请重试');
        });
}

// 不替换答案
function notReplaceAnswer() {
    // 清理前端暂存数据
    userUploadedAnswerFile = null;
    document.getElementById('user-answer-picture').src = '';
    document.querySelector('.user-answer-section').style.display = 'none';
    document.getElementById('replace-answer').style.display = 'none';
    document.getElementById('action-buttons').style.display = 'none';
    document.getElementById('answer-form').style.display = 'none';
    alert('保留原有答案，你可以继续获取新题目。');
    // 显示获取新题目按钮
    const newQuestionBtn = document.getElementById('new-question-btn');
    newQuestionBtn.style.display = 'block';
}

// 处理结果提交
function handleResult(correct) {
    isCorrect = correct;
    const resultFeedback = document.getElementById('result-feedback');
    const replaceSection = document.getElementById('replace-answer');
    const newQuestionBtn = document.getElementById('new-question-btn');
    const replaceBtn = document.getElementById('replace-btn');
    document.getElementById('action-buttons').style.display = 'none';
    document.getElementById('answer-form').style.display = 'none';

    // 显示反馈弹窗
    showFeedback(correct);
    // 显示结果反馈
    resultFeedback.className = correct ? 'result-feedback correct' : 'result-feedback incorrect';
    resultFeedback.textContent = correct ? '恭喜你，答案正确！' : '很遗憾，答案错误。';
    resultFeedback.style.display = 'block';

    // 显示替换答案选项（如果正确）
    if (correct) {
        replaceSection.style.display = 'block';
        replaceBtn.disabled = false;
    } else {
        newQuestionBtn.style.display = 'block';
    }

    // 提交复习结果
    fetch(`/api/record-result/${currentQuestionId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_correct: correct })
    })
      .then(response => {
            if (!response.ok) throw new Error('请求失败');
            return response.json();
        })
      .then(data => {
            if (data.success) {
                getReviewedQuestions(currentPage); // 刷新已复习错题列表
            } else {
                alert('结果提交失败：' + data.message);
            }
        })
      .catch(error => {
            console.error('请求错误:', error);
            alert('请求失败，请重试');
        });
}

// 获取新题目
function getNewQuestion() {
    fetch('/api/get-new-question')
      .then(response => {
            if (!response.ok) throw new Error('请求失败');
            return response.json();
        })
      .then(data => {
            if (data.success) {
                const question = data.question;
                currentQuestionId = question.id;
                // 存储正确答案路径
                answerPicturePath = question.AnswerPicture;
                document.getElementById('question-id').textContent = question.id;
                document.getElementById('question-id-input').value = question.id;
                document.getElementById('replace-question-id').value = question.id;
                document.getElementById('question-content').textContent = question.content;
                document.getElementById('question-type').textContent = question.type;
                document.getElementById('question-label').textContent = question.label;
                document.getElementById('question-image').src = question.QuestionPicture;
                document.getElementById('finish-time').textContent = question.FinishTime;
                document.getElementById('recent-review-time').textContent = question.recent_review_time;
                document.getElementById('current-weight').textContent = question.current_weight.toFixed(2);
                document.getElementById('review-accuracy').textContent = (question.review_accuracy * 100).toFixed(2) + "%";
                // 清空其他区域
                document.getElementById('answer-picture').src = '';
                document.getElementById('user-answer-picture').src = '';
                document.querySelector('.correct-answer-section').style.display = 'none';
                document.querySelector('.user-answer-section').style.display = 'none';
                document.getElementById('action-buttons').style.display = 'none';
                document.getElementById('result-feedback').style.display = 'none';
                document.getElementById('replace-answer').style.display = 'none';
                const newQuestionBtn = document.getElementById('new-question-btn');
                newQuestionBtn.style.display = 'none';

                // 重置上传状态
                document.getElementById('answer-file').value = '';
                document.getElementById('replace-btn').disabled = true;
                document.getElementById('replace-file').value = '';

                // 重置前端显示
                document.getElementById('answer-form').style.display = 'block';
                // 清理前端暂存数据
                userUploadedAnswerFile = null;
                userAnswerBlobUrl = null;
            } else {
                alert(data.message);
            }
        })
      .catch(error => {
            console.error('请求错误:', error);
            alert('请求失败，请重试');
        });
}

// 获取当日已复习错题（分页）
function getReviewedQuestions(page) {
    fetch(`/api/get-reviewed-questions?page=${page}`)
      .then(response => {
            if (!response.ok) throw new Error('请求失败');
            return response.json();
        })
      .then(data => {
            if (data.success) {
                const questionList = document.getElementById('reviewed-question-list');
                questionList.innerHTML = '';
                data.questions.forEach(question => {
                    const questionDiv = document.createElement('div');
                    questionDiv.classList.add('reviewed-question');
                    // 存储完整题目信息
                    questionDiv.dataset.question = JSON.stringify(question);
                    questionDiv.innerHTML = `
                        <div class="question-title">问题简述：${question.content}</div>
                        <div class="question-meta">
                            <span><i class="meta-icon"><img src="/static/imgs/日历.png" alt="时间日历" width="24" height="24"></i>
                             ${new Date(question.FinishTime).toLocaleString()}</span>
                        </div>
                    `;
                    // 添加点击事件，点击时显示题目详情
                    questionDiv.addEventListener('click', function () {
                        const question = JSON.parse(this.dataset.question);
                        showQuestionDetail(question);
                    });
                    questionList.appendChild(questionDiv);
                });

                const prevPageBtn = document.getElementById('prev-page');
                const nextPageBtn = document.getElementById('next-page');
                const pageNumbersDiv = document.getElementById('page-numbers');
                pageNumbersDiv.innerHTML = '';

                prevPageBtn.disabled = !data.has_prev;
                nextPageBtn.disabled = !data.has_next;
                currentPage = page;

                const maxVisiblePages = 3; // 最大显示的页码数量
                const totalPages = data.total_pages;

                if (totalPages <= maxVisiblePages) {
                    // 如果总页数少于等于最大显示数量，显示所有页码
                    for (let i = 1; i <= totalPages; i++) {
                        const pageButton = document.createElement('button');
                        pageButton.textContent = i;
                        if (i === currentPage) {
                            pageButton.classList.add('active');
                        }
                        pageButton.addEventListener('click', function () {
                            getReviewedQuestions(i);
                        });
                        pageNumbersDiv.appendChild(pageButton);
                    }
                } else {
                    // 总页数超过最大显示数量，进行省略处理
                    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
                    let endPage = startPage + maxVisiblePages - 1;

                    if (endPage > totalPages) {
                        endPage = totalPages;
                        startPage = Math.max(1, endPage - maxVisiblePages + 1);
                    }

                    // 显示第一页
                    if (startPage > 1) {
                        const firstPageButton = document.createElement('button');
                        firstPageButton.textContent = 1;
                        if (1 === currentPage) {
                            firstPageButton.classList.add('active');
                        }
                        firstPageButton.addEventListener('click', function () {
                            getReviewedQuestions(1);
                        });
                        pageNumbersDiv.appendChild(firstPageButton);

                        if (startPage > 2) {
                            const ellipsis = document.createElement('span');
                            ellipsis.textContent = '...';
                            pageNumbersDiv.appendChild(ellipsis);
                        }
                    }

                    // 显示中间页码
                    for (let i = startPage; i <= endPage; i++) {
                        const pageButton = document.createElement('button');
                        pageButton.textContent = i;
                        if (i === currentPage) {
                            pageButton.classList.add('active');
                        }
                        pageButton.addEventListener('click', function () {
                            getReviewedQuestions(i);
                        });
                        pageNumbersDiv.appendChild(pageButton);
                    }

                    // 显示最后一页
                    if (endPage < totalPages) {
                        if (endPage < totalPages - 1) {
                            const ellipsis = document.createElement('span');
                            ellipsis.textContent = '...';
                            pageNumbersDiv.appendChild(ellipsis);
                        }

                        const lastPageButton = document.createElement('button');
                        lastPageButton.textContent = totalPages;
                        if (totalPages === currentPage) {
                            lastPageButton.classList.add('active');
                        }
                        lastPageButton.addEventListener('click', function () {
                            getReviewedQuestions(totalPages);
                        });
                        pageNumbersDiv.appendChild(lastPageButton);
                    }
                }
            } else {
                alert(data.message);
            }
        })
      .catch(error => {
            console.error('请求错误:', error);
            alert('请求失败，请重试');
        });
}

// 显示题目详情
function showQuestionDetail(question) {
    const detailDiv = document.getElementById('selected-question-detail');
    detailDiv.innerHTML = `
        <h2>${question.content}</h2>
        <p>题目 ID：${question.id}</p>
        <p>题目类型：${question.type}</p>
        <p>题目标签：${question.label}</p>
        <p>答案情况：${question.is_correct ? '正确' : '错误'}</p>
        <p>完成时间：${question.FinishTime}</p>
        <p>最近复习时间：${question.recent_review_time}</p>
        <p>当前权重：${question.current_weight}</p>
        <p>正确率：${question.review_accuracy * 100}%</p>
        <p>题目：</p>
	    <img src="${question.QuestionPicture}" alt="问题" class="image-preview"onclick="openModal(this.src)">
        <p>答案：</p>
	    <img src="${question.AnswerPicture}" alt="问题" class="image-preview"onclick="openModal(this.src)">
    `;
}

// 上一页
function prevPage() {
    if (currentPage > 1) {
        getReviewedQuestions(currentPage - 1);
    }
}

// 下一页
function nextPage() {
    getReviewedQuestions(currentPage + 1);
}

// 阻止按钮的默认行为并手动触发文件输入框的点击事件
const customUploadButton = document.getElementById('custom-upload-button');
const fileInput = document.getElementById('answer-file');
customUploadButton.addEventListener('click', function (event) {
    event.preventDefault();
    fileInput.click();
});

// 监听文件选择事件
fileInput.addEventListener('change', function (event) {
    const fileName = document.getElementById('file-name');
    if (event.target.files.length > 0) {
        fileName.textContent = event.target.files[0].name;
    } else {
        fileName.textContent = '未选择任何文件';
    }
});

// 新增：反馈弹窗相关
const feedbackModal = document.getElementById('feedbackModal');
const feedbackIcon = document.getElementById('feedbackIcon');
const feedbackTitle = document.getElementById('feedbackTitle');
const feedbackMessage = document.getElementById('feedbackMessage');

// 显示反馈弹窗
function showFeedback(isCorrect) {
    if (isCorrect) {
        feedbackIcon.className = 'feedback-icon correct';
        feedbackIcon.textContent = '✓';
        feedbackTitle.textContent = '恭喜你，答案正确！';
        feedbackMessage.textContent = '继续保持！';
    } else {
        feedbackIcon.className = 'feedback-icon incorrect';
        feedbackIcon.textContent = '✗';
        feedbackTitle.textContent = '答案错误';
        feedbackMessage.textContent = '再仔细想想吧！';
    }
    feedbackModal.classList.add('show');
}

// 关闭反馈弹窗
function closeFeedback() {
    feedbackModal.classList.remove('show');
}