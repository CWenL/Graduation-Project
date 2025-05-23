function time(){
    var vWeek,vWeek_s,vDay;
    vWeek = ["星期天","星期一","星期二","星期三","星期四","星期五","星期六"];
    var date =  new Date();
    year = date.getFullYear();
    month = date.getMonth() + 1;
    day = date.getDate();
    hours = date.getHours();
    minutes = date.getMinutes();
    seconds = date.getSeconds();
    vWeek_s = date.getDay();
    if (hours < 10)
        hours = "0" + hours
    if (minutes < 10)
        minutes = "0" + minutes
    if (seconds < 10)
        seconds = "0" + seconds
    document.getElementById("time").innerHTML = year + "年" + month + "月" + day + "日" + "\t" + hours + ":" + minutes +":" + seconds + "\t" + vWeek[vWeek_s] ;
    };
    setInterval("time()",1000);


function startCountdown(target, endTime) {
    var now = new Date();
    var end = new Date(endTime);
    var diff = end - now;

    if (diff <= 0) {
        clearInterval(interval);
        document.getElementById(target).innerHTML = "倒计时结束";
        return;
    }

    var days = Math.floor(diff / (1000 * 60 * 60 * 24));
    var hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    var minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    var seconds = Math.floor((diff % (1000 * 60)) / 1000);

    document.getElementById(target).innerHTML =
        days + "天 " + hours + "小时 " + minutes + "分钟 " + seconds + "秒";
}

var interval = setInterval(function() {
    startCountdown("countdown", "December 1, 2025 00:00:00");
}, 1000);