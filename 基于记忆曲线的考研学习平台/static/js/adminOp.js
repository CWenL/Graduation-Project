document.addEventListener('DOMContentLoaded', function () {
    const powerContainer = document.getElementById('power-container');
    const userPower = powerContainer.dataset.power;
    console.log('用户权限（JavaScript 输出）:', userPower);
    if (userPower === 'CommunityAdmin') {
        const userLink = document.getElementById('user-nav-link');
        const noticeLink = document.getElementById('global-notice-nav-link');
        if (userLink) {
            userLink.classList.add('disabled-link');
        }
        if (noticeLink) {
            noticeLink.classList.add('disabled-link');
        }
    }
});
// 侧边栏控制
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('collapsed');
    document.getElementById('content').classList.toggle('collapsed');
}

// 社区管理模块
const Community = {
    loadPosts: function (params = {}) {
        const keyword = document.getElementById('searchKeyword').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;

        const baseParams = {
            keyword: keyword,
            start_time: startDate,
            end_time: endDate
        };
        const urlParams = new URLSearchParams({ ...baseParams, ...params });
        fetch(`/api/community/posts?${urlParams}`)
           .then(response => response.json())
           .then(data => {
                if (data.code === 200) {
                    Community.renderCommunityContent(data.data);
                    Community.renderPagination(data.pagination.current_page, data.pagination.total_pages);
                }
            });
    },

    renderCommunityContent: function (posts) {
        const postList = document.getElementById('postList');
        postList.innerHTML = '';
        posts.forEach(post => {
            const card = document.createElement('div');
            card.className = 'card post-card';
            //列表中查看只截取前20个字符
            let content = post.postings_text;
            if (content.length > 20) {
                content = content.substring(0, 20) + '...';
            }
            card.innerHTML = `
                <div class="card-body">
                    <h5 class="card-title">标题：${post.title}</h5>
                    <p class="card-text">内容：${content}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">发布时间：${post.postings_time}</small>
                        <small class="text-muted">发布者：${post.username}</small>
                        <div>
                            <button class="btn btn-primary btn-sm" onclick="Community.showPostModal(${post.post_id})">查看详情</button>
                            <a class="btn btn-primary btn-sm" href="/post/${post.post_id}">修改</a>
                            <button class="btn btn-danger btn-sm ms-2" onclick="Community.deletePost(${post.post_id})">删除</button>
                        </div>
                    </div>
                </div>
            `;
            postList.appendChild(card);
        });
    },

    renderPagination: function (currentPage, totalPages) {
        const pagination = document.getElementById('pagination-container');
        let html = '<nav aria-label="Page navigation example"><ul class="pagination">';
        html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="Community.loadPosts({page: ${currentPage - 1}}); event.preventDefault();">«</a>
                </li>`;
        for (let i = 1; i <= totalPages; i++) {
            html += `<li class="page-item ${currentPage === i ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="Community.loadPosts({page: ${i}}); event.preventDefault();">${i}</a>
                    </li>`;
        }
        html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="Community.loadPosts({page: ${currentPage + 1}}); event.preventDefault();">»</a>
                </li>`;
        html += '</ul></nav>';
        pagination.innerHTML = html;
    },

    searchPosts: function () {
        this.loadPosts({ page: 1 });
    },

    clearSearch: function () {
        document.getElementById('searchKeyword').value = '';
        document.getElementById('startDate').value = '';
        document.getElementById('endDate').value = '';
        this.loadPosts({ page: 1 });
    },

    deletePost: function (postId) {
        if (confirm('确定要删除该帖子吗？')) {
            fetch(`/api/community/posts/${postId}`, { method: 'DELETE' })
               .then(response => response.json())
               .then(data => {
                    if (data.code === 200) {
                        alert('帖子删除成功');
                        this.loadPosts({
                            page: document.querySelector('.pagination .active a')?.innerText || 1
                        });
                    } else {
                        alert('帖子删除失败：' + data.message);
                    }
                });
        }
    },

    showPostModal: function (postId) {
        fetch(`/api/community/posts/${postId}`)
           .then(response => response.json())
           .then(data => {
                if (data.code === 200) {
                    const modal = document.createElement('div');
                    modal.className = 'modal fade';
                    modal.id = 'postModal';
                    let pictureHtml = data.data.postings_picture ?
                        `<img src="${data.data.postings_picture}" alt="配图" class="img-fluid mt-3">` : '';
                    modal.innerHTML = `
                        <div class="modal-dialog modal-lg">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">帖子详情</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <p><strong>标题:</strong> ${data.data.title}</p>
                                    <p><strong>用户名:</strong> ${data.data.username}</p>
                                    <p><strong>发布时间:</strong> ${data.data.postings_time}</p>
                                    <p><strong>内容:</strong> ${data.data.postings_text}</p>
                                    ${pictureHtml}
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                                </div>
                            </div>
                        </div>
                    `;
                    document.body.appendChild(modal);
                    new bootstrap.Modal(modal).show();
                }
            });
    }
};

// 评论管理
const CommentManager = {
    currentPage: 1,
    perPage: 10,
    loadComments: function (page = 1) {
        const keyword = document.getElementById('comment-searchKeyword').value;
        const startDate = document.getElementById('comment-startDate').value;
        const endDate = document.getElementById('comment-endDate').value;
        fetch(`/api/admin/comments?page=${page}&per_page=${this.perPage}&keyword=${keyword}&start_time=${startDate}&end_time=${endDate}`)
           .then(response => response.json())
           .then(data => {
                if (data.code === 200) {
                    const commentList = document.getElementById('comment-list');
                    commentList.innerHTML = '';
                    
                    data.data.forEach(comment => {
                        const card = document.createElement('div');
                        card.className = 'card mb-3';
                        //列表中查看只截取前20个字符
                        let content = comment.Comment;
                        if (content.length > 20) {
                            content = content.substring(0, 20) + '...';
                        }
                        card.innerHTML = `
                            <div class="card-header">
                                <h5>评论ID: ${comment.CommentID}
                                <button class="btn btn-danger btn-sm" onclick="CommentManager.deleteComment(${comment.CommentID})">删除</button>
                                <button class="btn btn-primary btn-sm" onclick="Community.showPostModal(${comment.PostingsID})">查看该帖详情</button></h5>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-8">
                                        <p class="card-text">内容: ${content}</p>
                                        ${comment.CommentImg ? `<img src="${comment.CommentImg}" data-src="${comment.CommentImg}" class="img-fluid preview-image" style="max-width: 100px;">` : ''}
                                    </div>
                                    <small class="text-muted">发布者: ${comment.Username}</small>
                                    <small class="text-muted">时间: ${comment.CommentTime}</small>
                                </div>
                            </div>
                        `;
                        commentList.appendChild(card);
                    });
                    // 初始化图片预览事件
                    document.querySelectorAll('.preview-image').forEach(img => {
                        img.addEventListener('click', function() {
                            const modal = new bootstrap.Modal('#imageModal');
                            document.getElementById('modal-image').src = this.dataset.src;
                            modal.show();
                        });
                    });
                    this.renderPagination(data.pagination);
                }
            });
    },

    renderPagination: function (pagination) {
        const container = document.getElementById('comment-pagination-container');
        container.innerHTML = '';
        
        const prevBtn = document.createElement('button');
        prevBtn.className = 'btn btn-primary me-2';
        prevBtn.textContent = '上一页';
        prevBtn.disabled = pagination.current_page === 1;
        prevBtn.onclick = () => this.loadComments(pagination.current_page - 1);
        container.appendChild(prevBtn);

        for (let i = 1; i <= pagination.total_pages; i++) {
            const btn = document.createElement('button');
            btn.className = `btn btn-secondary me-2 ${i === pagination.current_page ? 'active' : ''}`;
            btn.textContent = i;
            btn.onclick = () => this.loadComments(i);
            container.appendChild(btn);
        }

        const nextBtn = document.createElement('button');
        nextBtn.className = 'btn btn-primary';
        nextBtn.textContent = '下一页';
        nextBtn.disabled = pagination.current_page === pagination.total_pages;
        nextBtn.onclick = () => this.loadComments(pagination.current_page + 1);
        container.appendChild(nextBtn);
    },

    searchComments: function () {
        this.loadComments(1);
    },

    clearSearch: function () {
        document.getElementById('comment-searchKeyword').value = '';
        document.getElementById('comment-startDate').value = '';
        document.getElementById('comment-endDate').value = '';
        this.loadComments(1);
    },

    deleteComment: function (commentId) {
        if (confirm('确认要删除该评论吗？')) {
            fetch(`/api/admin/comments/${commentId}`, { method: 'DELETE' })
               .then(response => response.json())
               .then(data => {
                    if (data.code === 200) {
                        alert('删除成功');
                        this.loadComments(this.currentPage);
                    } else {
                        alert('删除失败: ' + data.message);
                    }
                });
        }
    }
};

// 用户管理模块
const User = {
    loadUsers: function (params = {}) {
        const keyword = document.getElementById('userSearch')?.value || '';
        const urlParams = new URLSearchParams({ ...params, keyword });
        fetch(`/api/user/list?${urlParams}`)
           .then(response => response.json())
           .then(data => {
                if (data.code === 200) {
                    User.renderUserList(data.data);
                    User.renderUserPagination(data.pagination.current_page, data.pagination.total_pages);
                }
            });
    },

    renderUserList: function (users) {
        const userList = document.getElementById('userList');
        userList.innerHTML = '';
        users.forEach(user => {
            const card = document.createElement('div');
            card.className = 'card user-card mb-3';
            card.innerHTML = `
                <div class="card-body">
                    <h5 class="card-title">用户名：${user.username}</h5>
                    <p class="card-text">邮箱：${user.email}</p>
                    <p class="card-text">权限：${user.power}</p>
                    <p class="card-text">状态：${user.state ? '已封禁' : '正常'}</p>
                    <div>
                        ${user.power === 'admin' ? '' :
                        `<button class="btn btn-${user.power === 'user' ? 'warning' : 'secondary'} btn-sm me-2" 
                           onclick="User.promoteUser('${user.username}')">
                            ${user.power === 'user' ? '提升为社区管理员' : '撤销社区管理员权限'}
                        </button>`}
                        ${user.state ?
                        `<button class="btn btn-success btn-sm me-2" onclick="User.unbanUser('${user.username}')">解除封禁</button>` :
                        `<button class="btn btn-danger btn-sm me-2" onclick="User.banUser('${user.username}')">封禁账户</button>`}
                    </div>
                </div>
            `;
            userList.appendChild(card);
        });
    },

    renderUserPagination: function (currentPage, totalPages) {
        const pagination = document.getElementById('userPagination');
        let html = '<nav aria-label="Page navigation example"><ul class="pagination">';
        html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="User.loadUsers({page: ${currentPage - 1}}); event.preventDefault();">«</a>
                </li>`;
        for (let i = 1; i <= totalPages; i++) {
            html += `<li class="page-item ${currentPage === i ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="User.loadUsers({page: ${i}}); event.preventDefault();">${i}</a>
                    </li>`;
        }
        html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="User.loadUsers({page: ${currentPage + 1}}); event.preventDefault();">»</a>
                </li>`;
        html += '</ul></nav>';
        pagination.innerHTML = html;
    },

    searchUsers: function () {
        this.loadUsers({ page: 1 });
    },

    banUser: function (username) {
        if (confirm(`确认要封禁用户 ${username} 吗？`)) {
            fetch(`/api/user/ban/${username}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ state: true })
            })
              .then(response => response.json())
              .then(data => {
                    if (data.code === 200) {
                        alert('用户已封禁');
                        User.loadUsers();
                    } else {
                        alert(data.message);
                    }
                });
        }
    },

    promoteUser: function (username) {
        if (confirm(`确认要对用户 ${username} 进行权限操作吗？`)) {
            fetch(`/api/user/promote/${username}`, { method: 'POST' })
               .then(response => response.json())
               .then(data => {
                    if (data.code === 200) {
                        alert(data.message);
                        this.loadUsers();
                    } else {
                        alert(data.message);
                    }
                });
        }
    },

    unbanUser: function (username) {
        if (confirm(`确认要解除用户 ${username} 的封禁吗？`)) {
            fetch(`/api/user/ban/${username}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ state: false })
            })
              .then(response => response.json())
              .then(data => {
                    if (data.code === 200) {
                        alert('用户已解封');
                        User.loadUsers();
                    } else {
                        alert(data.message);
                    }
                });
        }
    }
};
// 全服公告管理模块
const GlobalNotice = {
    currentPage: 1,
    perPage: 6,
    loadNotices: function (params = {}) {
        const keyword = document.getElementById('global-searchKeyword').value;
        const startDate = document.getElementById('global-startDate').value;
        const endDate = document.getElementById('global-endDate').value;

        const baseParams = {
            keyword: keyword,
            start_time: startDate,
            end_time: endDate,
            ...params
        };
        const urlParams = new URLSearchParams(baseParams);
        
        fetch(`/api/global-notice?${urlParams}`)
           .then(response => response.json())
           .then(data => {
                if (data.code === 200) {
                    GlobalNotice.renderNoticeContent(data.data);
                    GlobalNotice.renderPagination(data.pagination.current_page, data.pagination.total_pages);
                }
            });
    },

    renderNoticeContent: function (notices) {
        const noticeList = document.getElementById('global-notice-list');
        noticeList.innerHTML = '';
        notices.forEach(notice => {
            const card = document.createElement('div');
            card.className = 'card notice-card';
            //列表中查看只截取前20个字符
            let content = notice.Notice_content;
            if (content.length > 20) {
                content = content.substring(0, 20) + '...';
            }
            card.innerHTML = `
                <div class="card-body">
                    <h5 class="card-title">标题：${notice.NoticeName}</h5>
                    <p class="card-text">内容：${content}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">发布时间：${notice.Notice_date}</small>
                        <div>
                            <button class="btn btn-primary btn-sm" onclick="GlobalNotice.showNoticeModal(${notice.nid})">查看详情</button>
                            <button class="btn btn-danger btn-sm ms-2" onclick="GlobalNotice.deleteNotice(${notice.nid})">删除</button>
                        </div>
                    </div>
                </div>
            `;
            noticeList.appendChild(card);
        });
    },

    renderPagination: function (currentPage, totalPages) {
        const pagination = document.getElementById('global-pagination-container');
        let html = '<nav aria-label="Page navigation example"><ul class="pagination">';
        html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="GlobalNotice.loadNotices({page: ${currentPage - 1}}); event.preventDefault();">«</a>
                </li>`;
        for (let i = 1; i <= totalPages; i++) {
            html += `<li class="page-item ${currentPage === i ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="GlobalNotice.loadNotices({page: ${i}}); event.preventDefault();">${i}</a>
                    </li>`;
        }
        html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="GlobalNotice.loadNotices({page: ${currentPage + 1}}); event.preventDefault();">»</a>
                </li>`;
        html += '</ul></nav>';
        pagination.innerHTML = html;
    },
    showCreateNoticeModal: function () {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'createGlobalNoticeModal';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">创建全服公告</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label for="modal-global-notice-name" class="form-label">公告名称</label>
                            <input type="text" class="form-control" id="modal-global-notice-name" required>
                        </div>
                        <div class="mb-3">
                            <label for="modal-global-notice-content" class="form-label">内容</label>
                            <textarea class="form-control" id="modal-global-notice-content" rows="3" required></textarea>
                        </div>
                        <div class="mb-3">
                            <label for="modal-global-notice-picture" class="form-label">配图</label>
                            <input type="file" class="form-control" id="modal-global-notice-picture">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        <button type="button" class="btn btn-primary" onclick="GlobalNotice.createNotice()">创建</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        new bootstrap.Modal(modal).show();
    },
    createNotice: async function () {
        const NoticeName = document.getElementById('modal-global-notice-name').value;
        const Notice_content = document.getElementById('modal-global-notice-content').value;
        const noticePictureInput = document.getElementById('modal-global-notice-picture');

        if (!NoticeName || !Notice_content) {
            alert('公告名称和内容不能为空');
            return;
        }

        let NoticePicture = null;
        if (noticePictureInput.files.length > 0) {
            const file = noticePictureInput.files[0];
            const reader = new FileReader();
            reader.readAsDataURL(file);
            await new Promise((resolve) => {
                reader.onload = () => {
                    NoticePicture = reader.result;
                    resolve();
                };
            });
        }

        const data = {
            NoticeName: NoticeName,
            Notice_content: Notice_content,
            NoticePicture: NoticePicture
        };

        fetch('/api/global-notice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
          .then(response => response.json())
          .then(data => {
                if (data.code === 200) {
                    alert('全服公告创建成功');
                    GlobalNotice.loadNotices();
                    document.getElementById('modal-global-notice-name').value = '';
                    document.getElementById('modal-global-notice-content').value = '';
                    document.getElementById('modal-global-notice-picture').value = '';
                    const modal = bootstrap.Modal.getInstance(document.getElementById('createGlobalNoticeModal'));
                    modal.hide();
                } else {
                    alert(data.message);
                }
            });
    },
    searchNotices: function () {
        this.loadNotices({ page: 1 });
    },

    clearSearch: function () {
        document.getElementById('global-searchKeyword').value = '';
        document.getElementById('global-startDate').value = '';
        document.getElementById('global-endDate').value = '';
        this.loadNotices({ page: 1 });
    },

    deleteNotice: function (noticeId) {
        if (confirm('确定要删除该公告吗？')) {
            fetch(`/api/global-notice/${noticeId}`, { method: 'DELETE' })
               .then(response => response.json())
               .then(data => {
                    if (data.code === 200) {
                        alert('公告删除成功');
                        this.loadNotices({
                            page: document.querySelector('#global-pagination-container .pagination .active a')?.innerText || 1
                        });
                    } else {
                        alert('公告删除失败：' + data.message);
                    }
                });
        }
    },

    showNoticeModal: function (noticeId) {
        fetch(`/api/global-notice/${noticeId}`)
           .then(response => response.json())
           .then(data => {
                if (data.code === 200) {
                    const modal = document.createElement('div');
                    modal.className = 'modal fade';
                    modal.id = 'globalNoticeModal';
                    let pictureHtml = data.data.NoticePicture ?
                        `<img src="${data.data.NoticePicture}" alt="配图" class="img-fluid mt-3">` : '';
                    modal.innerHTML = `
                        <div class="modal-dialog modal-lg">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">全服公告详情</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <p><strong>公告名称:</strong> ${data.data.NoticeName}</p>
                                    <p><strong>发布者:</strong> ${data.data.username}</p>
                                    <p><strong>发布日期:</strong> ${data.data.Notice_date}</p>
                                    <p><strong>内容:</strong> ${data.data.Notice_content}</p>
                                    ${pictureHtml}
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                                </div>
                            </div>
                        </div>
                    `;
                    document.body.appendChild(modal);
                    new bootstrap.Modal(modal).show();
                }
            });
    },

    showCreateNoticeModal: function () {
        // 检查是否已存在该 modal，存在则移除
        let existingModal = document.getElementById('createGlobalNoticeModal');
        if (existingModal) {
            existingModal.remove();
        }
        // 创建 modal 元素
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'createGlobalNoticeModal';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">创建全服公告</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label for="modal-global-notice-name" class="form-label">公告名称</label>
                            <input type="text" class="form-control" id="modal-global-notice-name" required>
                        </div>
                        <div class="mb-3">
                            <label for="modal-global-notice-content" class="form-label">内容</label>
                            <textarea class="form-control" id="modal-global-notice-content" rows="3" required></textarea>
                        </div>
                        <div class="mb-3">
                            <label for="modal-global-notice-picture" class="form-label">配图</label>
                            <input type="file" class="form-control" id="modal-global-notice-picture">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        <button type="button" class="btn btn-primary" onclick="GlobalNotice.createNotice()">创建</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        // modal 隐藏后自动移除 DOM 中的元素
        modal.addEventListener('hidden.bs.modal', function () {
            modal.remove();
        });
        new bootstrap.Modal(modal).show();
    },

    createNotice: async function () {
        const NoticeName = document.getElementById('modal-global-notice-name').value;
        const Notice_content = document.getElementById('modal-global-notice-content').value;
        const noticePictureInput = document.getElementById('modal-global-notice-picture');

        if (!NoticeName || !Notice_content) {
            alert('公告名称和内容不能为空');
            return;
        }

        let NoticePicture = null;
        if (noticePictureInput.files.length > 0) {
            const file = noticePictureInput.files[0];
            const reader = new FileReader();
            reader.readAsDataURL(file);
            await new Promise((resolve) => {
                reader.onload = () => {
                    NoticePicture = reader.result;
                    resolve();
                };
            });
        }

        const data = {
            NoticeName: NoticeName,
            Notice_content: Notice_content,
            NoticePicture: NoticePicture
        };

        fetch('/api/global-notice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
            .then(response => response.json())
            .then(data => {
                if (data.code === 200) {
                    alert('全服公告创建成功');
                    GlobalNotice.loadNotices();
                    // 清空输入框
                    document.getElementById('modal-global-notice-name').value = '';
                    document.getElementById('modal-global-notice-content').value = '';
                    document.getElementById('modal-global-notice-picture').value = '';
                    // 隐藏并移除 modal
                    const modalElem = document.getElementById('createGlobalNoticeModal');
                    if (modalElem) {
                        const modalInstance = bootstrap.Modal.getInstance(modalElem);
                        modalInstance.hide();
                    }
                } else {
                    alert(data.message);
                }
            });
    }
};

// 社区公告管理模块
const CommunityNotice = {
    currentPage: 1,
    perPage: 6,
    loadNotices: function (params = {}) {
        const keyword = document.getElementById('community-searchKeyword').value;
        const startDate = document.getElementById('community-startDate').value;
        const endDate = document.getElementById('community-endDate').value;

        const baseParams = {
            keyword: keyword,
            start_time: startDate,
            end_time: endDate,
            ...params
        };
        const urlParams = new URLSearchParams(baseParams);
        
        fetch(`/api/community-notice?${urlParams}`)
           .then(response => response.json())
           .then(data => {
                if (data.code === 200) {
                    CommunityNotice.renderNoticeContent(data.data);
                    CommunityNotice.renderPagination(data.pagination.current_page, data.pagination.total_pages);
                }
            });
    },

    renderNoticeContent: function (notices) {
        const noticeList = document.getElementById('community-notice-list');
        noticeList.innerHTML = '';
        notices.forEach(notice => {
            const card = document.createElement('div');
            card.className = 'card notice-card';
            //列表中查看只截取前20个字符
            let content = notice.Notice_content;
            if (content.length > 20) {
                content = content.substring(0, 20) + '...';
            }
            card.innerHTML = `
                <div class="card-body">
                    <h5 class="card-title">标题：${notice.NoticeName}</h5>
                    <p class="card-text">内容：${content}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">发布时间：${notice.Notice_date}</small>
                        <div>
                            <button class="btn btn-primary btn-sm" onclick="CommunityNotice.showNoticeModal(${notice.nid})">查看详情</button>
                            <button class="btn btn-danger btn-sm ms-2" onclick="CommunityNotice.deleteNotice(${notice.nid})">删除</button>
                        </div>
                    </div>
                </div>
            `;
            noticeList.appendChild(card);
        });
    },

    renderPagination: function (currentPage, totalPages) {
        const pagination = document.getElementById('community-pagination-container');
        let html = '<nav aria-label="Page navigation example"><ul class="pagination">';
        html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="CommunityNotice.loadNotices({page: ${currentPage - 1}}); event.preventDefault();">«</a>
                </li>`;
        for (let i = 1; i <= totalPages; i++) {
            html += `<li class="page-item ${currentPage === i ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="CommunityNotice.loadNotices({page: ${i}}); event.preventDefault();">${i}</a>
                    </li>`;
        }
        html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="CommunityNotice.loadNotices({page: ${currentPage + 1}}); event.preventDefault();">»</a>
                </li>`;
        html += '</ul></nav>';
        pagination.innerHTML = html;
    },
    showCreateNoticeModal: function () {
        // 检查是否已经存在该 modal 元素，存在则先移除
        let existingModal = document.getElementById('createCommunityNoticeModal');
        if (existingModal) {
            existingModal.remove();
        }
        // 创建 modal 元素
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'createCommunityNoticeModal';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">创建社区公告</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label for="modal-community-notice-name" class="form-label">公告名称</label>
                            <input type="text" class="form-control" id="modal-community-notice-name" required>
                        </div>
                        <div class="mb-3">
                            <label for="modal-community-notice-content" class="form-label">内容</label>
                            <textarea class="form-control" id="modal-community-notice-content" rows="3" required></textarea>
                        </div>
                        <div class="mb-3">
                            <label for="modal-community-notice-picture" class="form-label">配图</label>
                            <input type="file" class="form-control" id="modal-community-notice-picture">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        <button type="button" class="btn btn-primary" onclick="CommunityNotice.createNotice()">创建</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        // 在 modal 隐藏后，将该元素从 DOM 中移除
        modal.addEventListener('hidden.bs.modal', function () {
            modal.remove();
        });
        new bootstrap.Modal(modal).show();
    },

    // 单一的 createNotice 定义
    createNotice: async function () {
        const NoticeName = document.getElementById('modal-community-notice-name').value;
        const Notice_content = document.getElementById('modal-community-notice-content').value;
        const noticePictureInput = document.getElementById('modal-community-notice-picture');

        if (!NoticeName || !Notice_content) {
            alert('公告名称和内容不能为空');
            return;
        }

        let NoticePicture = null;
        if (noticePictureInput.files.length > 0) {
            const file = noticePictureInput.files[0];
            const reader = new FileReader();
            reader.readAsDataURL(file);
            await new Promise((resolve) => {
                reader.onload = () => {
                    NoticePicture = reader.result;
                    resolve();
                };
            });
        }

        const data = {
            NoticeName: NoticeName,
            Notice_content: Notice_content,
            NoticePicture: NoticePicture
        };

        fetch('/api/community-notice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
          .then(response => response.json())
          .then(data => {
                if (data.code === 200) {
                    alert('社区公告创建成功');
                    CommunityNotice.loadNotices();
                    // 清空输入框
                    document.getElementById('modal-community-notice-name').value = '';
                    document.getElementById('modal-community-notice-content').value = '';
                    document.getElementById('modal-community-notice-picture').value = '';
                    // 隐藏并移除 modal
                    const modalElem = document.getElementById('createCommunityNoticeModal');
                    if (modalElem) {
                        const modalInstance = bootstrap.Modal.getInstance(modalElem);
                        modalInstance.hide();
                    }
                } else {
                    alert(data.message);
                }
            });
    },
    searchNotices: function () {
        this.loadNotices({ page: 1 });
    },

    clearSearch: function () {
        document.getElementById('community-searchKeyword').value = '';
        document.getElementById('community-startDate').value = '';
        document.getElementById('community-endDate').value = '';
        this.loadNotices({ page: 1 });
    },

    deleteNotice: function (noticeId) {
        if (confirm('确定要删除该社区公告吗？')) {
            fetch(`/api/community-notice/${noticeId}`, { method: 'DELETE' })
               .then(response => response.json())
               .then(data => {
                    if (data.code === 200) {
                        alert('社区公告删除成功');
                        this.loadNotices({
                            page: document.querySelector('#community-pagination-container .pagination .active a')?.innerText || 1
                        });
                    } else {
                        alert('社区公告删除失败：' + data.message);
                    }
                });
        }
    },

    showNoticeModal: function (noticeId) {
        fetch(`/api/community-notice/${noticeId}`)
           .then(response => response.json())
           .then(data => {
                if (data.code === 200) {
                    const modal = document.createElement('div');
                    modal.className = 'modal fade';
                    modal.id = 'communityNoticeModal';
                    let pictureHtml = data.data.NoticePicture ?
                        `<img src="${data.data.NoticePicture}" alt="配图" class="img-fluid mt-3">` : '';
                    modal.innerHTML = `
                        <div class="modal-dialog modal-lg">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">社区公告详情</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <p><strong>公告名称:</strong> ${data.data.NoticeName}</p>
                                    <p><strong>发布者:</strong> ${data.data.username}</p>
                                    <p><strong>发布日期:</strong> ${data.data.Notice_date}</p>
                                    <p><strong>内容:</strong> ${data.data.Notice_content}</p>
                                    ${pictureHtml}
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                                </div>
                            </div>
                        </div>
                    `;
                    document.body.appendChild(modal);
                    new bootstrap.Modal(modal).show();
                }
            });
    },
};

// 侧边栏点击事件处理
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function (e) {
        e.preventDefault();
        document.getElementById('welcome-card').style.display = 'none';
        document.getElementById('content-display').style.display = 'none';
        document.getElementById('comment-content').style.display = 'none';
        document.getElementById('user-content').style.display = 'none';
        document.getElementById('global-notice-content').style.display = 'none';
        document.getElementById('community-notice-content').style.display = 'none';
        const target = this.dataset.url.includes('community/posts') ? 'content-display' :
            this.dataset.url.includes('comment') ? 'comment-content' :
            this.dataset.url.includes('user') ? 'user-content' :
                this.dataset.url.includes('global-notice') ? 'global-notice-content' :
                    this.dataset.url.includes('community-notice') ? 'community-notice-content' : null;
        if (target) {
            document.getElementById(target).style.display = 'block';
            if (target === 'content-display') {
                Community.loadPosts();
            } else if (target === 'comment-content') {
                CommentManager.loadComments();
            }else if (target === 'user-content') {
                User.loadUsers();
            }  else if (target === 'global-notice-content') {
                GlobalNotice.loadNotices();
            } else if (target === 'community-notice-content') {
                CommunityNotice.loadNotices();
            }
        }
    });
});
// 添加JavaScript事件处理
document.getElementById('imageModal').addEventListener('shown.bs.modal', function () {
    const img = document.getElementById('modal-image');
    const zoomIn = document.querySelector('.zoom-in');
    const zoomOut = document.querySelector('.zoom-out');
    // 初始缩放比例
    let scale = 1;
    zoomIn.addEventListener('click', function () {
        scale = Math.min(scale + 0.2, 2);
        img.style.transform = `scale(${scale})`;
    });
    zoomOut.addEventListener('click', function () {
        scale = Math.max(scale - 0.2, 0.5);
        img.style.transform = `scale(${scale})`;
    });
    // 双击恢复默认缩放
    img.addEventListener('dblclick', function () {
        scale = 1;
        img.style.transform = 'scale(1)';
    });
});
// 初始化加载
window.addEventListener('DOMContentLoaded', function () {
    const initialUrl = window.location.pathname;
    if (initialUrl.includes('community/posts')) {
        Community.loadPosts();
    } else if (initialUrl.includes('comment')) {
        CommentManager.loadComments();
    } else if (initialUrl.includes('user')) {
        User.loadUsers();
    } else if (initialUrl.includes('global-notice')) {
        GlobalNotice.loadNotices();
    } else if (initialUrl.includes('community-notice')) {
        CommunityNotice.loadNotices();
    }
});