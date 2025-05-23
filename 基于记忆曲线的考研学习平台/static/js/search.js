document.addEventListener('DOMContentLoaded', function () {
    const searchForm = document.querySelector('form.d-flex');
    searchForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const keyword = document.querySelector('input.form-control').value;
        if (!keyword) {
            alert('请输入搜索关键词');
            return;
        }
        window.location.href = `/search?keyword=${encodeURIComponent(keyword)}`;
    });
});