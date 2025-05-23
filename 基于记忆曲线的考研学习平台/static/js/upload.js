function doSummit(){
    var formData=new FormData($("#formId")[0]);
    $.ajax({
        url:url,
        type: 'post',
        cache: false, //上传文件不需要缓存
        async : true,
        data: formdata,
        processData: false, // 此处是关键：告诉jQuery不要去处理发送的数据
        contentType: false, // 此处是关键：告诉jQuery不要去设置Content-Type请求头
        success: function (data) {
                    //处理成功后动作，比如调转window.location.href ='/list'
                },
        error : function(XMLHttpRequest, textStatus, errorThrown) {
                  alert(errorThrown);
                }
        }); 
    }