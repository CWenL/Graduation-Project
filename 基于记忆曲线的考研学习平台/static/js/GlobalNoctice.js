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
// 关闭模态框
function closeModal() {
    imageModal.style.display = 'none';
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

let noticeType = 'global'; // 使用 let 定义，允许后续修改
const communityNoticeType = 'community';
let currentPage = 1;

function fetchNotices() {
    const keyword = document.getElementById('keyword')?.value || '';
    const username = document.getElementById('username')?.value || '';
    const queryParams = new URLSearchParams({
        page: currentPage,
        keyword,
        username
    });
    const apiUrl = `/api/${noticeType}-notice`; // 动态生成 API URL
    fetch(`${apiUrl}?${queryParams}`)
        .then(response => response.json())
        .then(data => {
            if (data.code === 200) {
                renderNotices(data.data);
                renderPagination(data.pagination);
            } else {
                console.error('获取公告失败:', data.message);
            }
        })
        .catch(error => console.error('请求错误:', error));
}

// 显示全平台公告
function showGlobalNotices() {
    // 切换样式
    document.getElementById('global-notice-item').style.backgroundColor = 'rgb(222, 224, 225)';
    document.getElementById('community-notice-item').style.backgroundColor = 'transparent';
    // 隐藏公告详情，显示公告列表
    hideNoticeDetail();
    noticeType = 'global'; // 设置公告类型为全平台公告
    currentPage = 1; // 重置当前页码
    fetchNotices(); // 获取全平台公告
}
// 显示社区公告
function showCommunityNotices() {
    // 切换样式
    document.getElementById('community-notice-item').style.backgroundColor = 'rgb(222, 224, 225)';
    document.getElementById('global-notice-item').style.backgroundColor = 'transparent';
    // 隐藏公告详情，显示公告列表
    hideNoticeDetail();
    noticeType = communityNoticeType; // 设置公告类型为社区公告
    currentPage = 1; // 重置当前页码
    fetchNotices(); // 获取社区公告
}
function renderNotices(notices) {
    const noticeList = document.getElementById('notice-list');
    noticeList.innerHTML = '';
    notices.forEach(notice => {
        const item = document.createElement('div');
        item.className = 'notice-item';
        item.innerHTML = `
            <div class="notice-title">${notice.NoticeName}</div>
            <div class="notice-meta">
                <span><i class="meta-icon"><img src="/static/imgs/日历.png" alt="时间日历" width="24" height="24"></i>
                 ${new Date(notice.Notice_date).toLocaleString()}</span>
                <span><i class="meta-icon"><img src="/static/imgs/发布者.png" alt="时间日历" width="24" height="24"></i>
                 ${notice.username}</span>
            </div>
        `;
        item.addEventListener('click', () => showNoticeDetail(notice));
        noticeList.appendChild(item);
    });
}

function renderPagination(pagination) {
    const paginationDiv = document.getElementById('pagination-buttons');
    paginationDiv.innerHTML = '';
    if (pagination.current_page > 1) {
        const prevButton = document.createElement('button');
        prevButton.textContent = '上一页';
        prevButton.onclick = () => { currentPage--; fetchNotices(); };
        paginationDiv.appendChild(prevButton);
    }
    for (let i = 1; i <= pagination.total_pages; i++) {
        const button = document.createElement('button');
        button.textContent = i;
        if (i === pagination.current_page) {
            button.disabled = true;
            button.style.backgroundColor = '#4b8cd2';
            button.style.color = 'white';
        }
        button.onclick = () => { currentPage = i; fetchNotices(); };
        paginationDiv.appendChild(button);
    }
    if (pagination.current_page < pagination.total_pages) {
        const nextButton = document.createElement('button');
        nextButton.textContent = '下一页';
        nextButton.onclick = () => { currentPage++; fetchNotices(); };
        paginationDiv.appendChild(nextButton);
    }
}

function showNoticeDetail(notice) {
    const noticeDetail = document.getElementById('notice-detail-container');
    const paginationContainer = document.getElementById('pagination-buttons');
    let imageHtml = '';
    if (notice.NoticePicture) {
        imageHtml = `<img src="${notice.NoticePicture}" style="width: 700px; height: auto;" alt="NoticePicture" onclick="openImageModal('${notice.NoticePicture}')">`;
    }
    noticeDetail.innerHTML = `
        <div class="new-notice-detail" style="width:100%">
            <h1 class="notice_detail-title">${notice.NoticeName}</h1><br>
            <div class="notice-meta" style="text-align:center;">${new Date(notice.Notice_date).toLocaleString()}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            发布者：${notice.username}</div>
            <div class="nav-area">
                <div class="detail-content">${notice.Notice_content}</div>
                ${imageHtml}
            </div>
            <div class="nav-area">
                <span><a href="javascript:hideNoticeDetail()" class="back-btn">返回列表</a></span>
            </div>
        </div>
    `;
    noticeDetail.style.display = 'block';
    paginationContainer.style.display = 'none'; // 隐藏分页
    document.getElementById('notice-list').style.display = 'none'; // 隐藏列表
}

// 隐藏公告详情
function hideNoticeDetail() {
    const noticeDetail = document.getElementById('notice-detail-container');
    const paginationContainer = document.getElementById('pagination-buttons');
    noticeDetail.style.display = 'none';
    paginationContainer.style.display = 'block'; // 显示分页
    document.getElementById('notice-list').style.display = 'block'; // 显示列表
}

// 初始化加载全平台公告
showGlobalNotices();

// 搜索功能
document.getElementById('search-button').addEventListener('click', () => {
    currentPage = 1;
    fetchNotices();
});