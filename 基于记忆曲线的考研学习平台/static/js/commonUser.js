function deleteLearningRecord(button) {
    const questionId = button.dataset.questionId;
    if (confirm('确定要删除这条学习记录吗？')) {
      $.ajax({
        url: `/delete_question/${questionId}`,
        method: 'DELETE',
        success: function (response) {
          if (response.success) {
            alert('学习记录删除成功');
            window.location.href = '/userpage';
          } else {
            alert('删除失败：' + response.message);
          }
        },
        error: function () {
          alert('网络错误，请稍后重试');
        }
      });
    }
  }

  function deleteThisPost(button) {
    const postId = button.dataset.questionId;
    if (confirm('确定要删除这条帖子吗？')) {
      $.ajax({
        url: `/delete_post/${postId}`,
        method: 'DELETE',
        success: function (response) {
          if (response.success) {
            alert('删除成功');
            window.location.href = '/userpage';
          } else {
            alert('删除失败：' + response.message);
          }
        },
        error: function () {
          alert('网络错误，请稍后重试');
        }
      });
    }
  }