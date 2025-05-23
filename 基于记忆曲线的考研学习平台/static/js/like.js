$(document).ready(function () {
    $(".like-btn").click(function () {
        let postId = $(this).data("id"); // 获取帖子 ID
        let likeCountElem = $(this).find('.like-count'); // 正确选择器
        let isLiked = $(this).data("liked"); // 是否已点赞
        let action = isLiked ? "unlike" : "like"; // 取消 or 点赞

        $.ajax({
            url: "/like",
            type: "POST",
            data: JSON.stringify({ post_id: postId, action: action }),
            contentType: "application/json",
            success: function (response) {
                if (response.success) {
                    likeCountElem.text(response.likes); // 更新点赞数
                    $(this).data("liked", !isLiked); // 切换点赞状态
                    $(this).find('.heart').html(!isLiked ? '❤️' : '🤍');

                } else {
                    alert(response.error || "操作失败，请稍后重试！");
                }
            }.bind(this),
            error: function () {
                alert("网络错误，请稍后再试！");
            }
        });
    });
});
