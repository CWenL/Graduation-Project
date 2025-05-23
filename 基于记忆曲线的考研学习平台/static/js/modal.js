// 获取模态框元素
var modal = document.getElementById("myModal");

// 获取图片元素
var modalImg = document.getElementById("modalImage");

// 获取所有图片元素 除了有data-no-modal属性的
var imgs = document.querySelectorAll("img:not([data-no-modal])");

// 点击图片时显示模态框并更新图片
imgs.forEach(function(img) {
  img.onclick = function(){
    modal.style.display = "block";
    modalImg.src = this.src;
  }
});
// 获取关闭按钮元素
var span = document.getElementsByClassName("close")[0];

// 点击关闭按钮时隐藏模态框
span.onclick = function() { 
  modal.style.display = "none";
}