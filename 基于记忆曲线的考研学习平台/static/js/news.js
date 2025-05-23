const apiUrl = `/api/news`;
        let currentPage = 1;

        function fetchNews() {
            const keyword = document.getElementById('news-keyword')?.value || '';
            const publisher = document.getElementById('news-publisher')?.value || '';
            const queryParams = new URLSearchParams({
                page: currentPage,
                keyword,
                publisher
            });
            fetch(`${apiUrl}?${queryParams}`)
              .then(response => response.json())
              .then(data => {
                    if (data.code === 200) {
                        renderNews(data.data);
                        renderPagination(data.pagination);
                    } else {
                        console.error('获取新闻失败:', data.message);
                    }
                })
              .catch(error => console.error('请求错误:', error));
        }

        function renderNews(news) {
            const newsList = document.getElementById('news-list');
            newsList.innerHTML = '';
            news.forEach(newsItem => {
                const item = document.createElement('div');
                item.className = 'news-item';
                item.innerHTML = `
                    <div class="news-title">${newsItem.Title}</div>
                    <div class="news-meta">
                        <span><i class="meta-icon"><img src="/static/imgs/日历.png" alt="时间日历" width="24" height="24"></i>
                         ${new Date(newsItem.UpdateTime).toLocaleString()}</span>
                        <span><i class="meta-icon"><img src="/static/imgs/发布者.png" alt="时间日历" width="24" height="24"></i>
                         ${newsItem.Publisher}</span>
                    </div>
                `;
                item.addEventListener('click', () => showNewsDetail(newsItem));
                newsList.appendChild(item);
            });
        }

        function renderPagination(pagination) {
            const paginationDiv = document.getElementById('news-pagination-buttons');
            paginationDiv.innerHTML = '';
            if (pagination.current_page > 1) {
                const prevButton = document.createElement('button');
                prevButton.textContent = '上一页';
                prevButton.onclick = () => { currentPage--; fetchNews(); };
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
                button.onclick = () => { currentPage = i; fetchNews(); };
                paginationDiv.appendChild(button);
            }
            if (pagination.current_page < pagination.total_pages) {
                const nextButton = document.createElement('button');
                nextButton.textContent = '下一页';
                nextButton.onclick = () => { currentPage++; fetchNews(); };
                paginationDiv.appendChild(nextButton);
            }
        }

        function formatText(text) {
            // 先去除所有空格
            const cleanedText = text.replace(/\s+/g, ''); // 替换所有空白字符为空字符串
            // 定义每段的最大字符数
            const maxCharsPerParagraph = 300;
            // 分割文本为多段
            let formattedText = '';
            let currentParagraph = '';
            for (let i = 0; i < cleanedText.length; i++) {
                currentParagraph += cleanedText[i];
                if ((i + 1) % maxCharsPerParagraph === 0) {
                    formattedText += '<p class="text-with-indent">' + currentParagraph + '</p>';
                    currentParagraph = '';
                }
            }
            // 添加最后一段（如果存在）
            if (currentParagraph) {
                formattedText += '<p class="text-with-indent">' + currentParagraph + '</p>';
            }
            return formattedText;
        }

        function showNewsDetail(newsItem) {
            const newsDetail = document.getElementById('news-detail-container');
            const paginationContainer = document.getElementById('news-pagination-buttons');
            let imageHtml = '';
            if (newsItem.WebsitePicture) {
                imageHtml = `<img src="${newsItem.WebsitePicture}" style="width: 800px; height: auto;" alt="WebsitePicture">`;
            }
            // 格式化新闻内容
            const formattedContent = formatText(newsItem.Content);
            newsDetail.innerHTML = `
                <div class="new-news-detail" style="width:100%">
                    <h1 class="news_detail-title">${newsItem.Title}</h1><br>
                    <div class="news-meta"><span class="time">发布时间：${new Date(newsItem.UpdateTime).toLocaleString()}</span>
                    <span class="publisher">发布者：${newsItem.Publisher}</span></div>
                        <div class="nav-area">${imageHtml}</div>
                    <div class="nav-area">
                        <div class="detail-content">${formattedContent}</div>
                    </div>
                    <div class="nav-area">
                        <span><a href="javascript:hideNewsDetail()" class="back-btn">返回列表</a></span>
                    </div>
                </div>
            `;
            newsDetail.style.display = 'block';
            paginationContainer.style.display = 'none'; // 隐藏分页
            document.getElementById('news-list').style.display = 'none'; // 隐藏列表
        }

        function hideNewsDetail() {
            const newsDetail = document.getElementById('news-detail-container');
            const paginationContainer = document.getElementById('news-pagination-buttons');
            newsDetail.style.display = 'none';
            paginationContainer.style.display = 'block'; // 显示分页
            document.getElementById('news-list').style.display = 'block'; // 显示列表
            fetchNews(); // 重新加载数据
        }

        // 初始化加载
        fetchNews();

        // 搜索功能
        document.getElementById('news-search-button').addEventListener('click', () => {
            currentPage = 1;
            fetchNews();
        });