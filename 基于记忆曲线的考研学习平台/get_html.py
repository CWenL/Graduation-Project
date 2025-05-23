# 基础爬虫库
import asyncio
from pyppeteer import launch
import urllib.request
import analysis_html as ah
import behind_port as bp
# 数据处理
import os
# 导入文件管理器
import manage_file
# 管理数据库
import SQLiteOp as sp
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_htmlCode_Selenium(url, sleepTime, should_wait_for_js, wait_class_name=None):
    # 设置 Chrome 驱动选项
    options = Options()
    # Test
    options.add_argument('--headless')  # 无头模式
    options.add_argument('--disable-gpu')
    options.add_argument('window-size=1920x1080')
    # 忽略证书错误
    options.add_argument('--ignore-certificate-errors')
    # 忽略 Bluetooth: bluetooth_adapter_winrt.cc:1075 Getting Default Adapter failed. 错误
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    # 忽略 DevTools listening on ws://127.0.0.1... 提示
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.binary_location ="D:\chrome-win64\chrome.exe"
    service = Service("D:\chromedriver-win64\chromedriver.exe")
    # 创建浏览器实例
    driver = webdriver.Chrome(service=service,options=options)
    # 打开网页
    driver.get(url)
    # 如果需要等待 JS 渲染的元素加载完成
    if should_wait_for_js and wait_class_name:
        try:
            # 等待直到目标元素加载完成
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, wait_class_name))
            )
        except Exception as e:
            print(f"等待元素时出错: {e}")
    # 获取页面的高度
    last_height = driver.execute_script("return document.body.scrollHeight")
    # print(last_height)
    new_height=0
    while True:
        # 滚动小步长（每次滚动 200px）
        driver.execute_script("window.scrollBy(0, 200);")
        # 等待页面加载完成，给图片时间加载
        time.sleep(0.3)  # 这里可以调整等待的时间，根据页面加载的速度来设置
        # 获取新的页面高度
        new_height = new_height+200   
        # print(new_height)
        # 如果页面高度没有变化，表示已经滚动到底部
        if new_height >= last_height:
            time.sleep(sleepTime)
            new_height=0
            break
    # 获取页面内容
    rendered_html = driver.page_source
    # 关闭浏览器
    driver.quit()
    return rendered_html

def startCraw():
    wait_class_name = "listareaL"
    html_code = get_htmlCode_Selenium("https://www.dxsbb.com/news/list_86.html",0.3, should_wait_for_js=True, wait_class_name=wait_class_name)
    manage_file.raw_file_writefile("News_Home.txt", html_code)
    # 分析源码提取数据并存入数据库中
    ah.analysis_News(manage_file.raw_file_readfile("News_Home.txt"))
    # 继续爬取数据库中每行数据的链接的网页
    # 循环获取数据库中的记录
    sql_get_data="select * from CrawlerData"
    CrawlerData=sp.sql_execute_select_noVariable(sql_get_data)
    for Cdata in CrawlerData:
        # 判断是否已被爬取
        if Cdata[4] is None:
            inner_html_code = get_htmlCode_Selenium(Cdata[5],0.1, should_wait_for_js=False)
            filename="News-"+str(Cdata[0])+".txt"
            manage_file.raw_file_writefile(filename, inner_html_code)
            # 数据分析，更新内容数据
            content=ah.get_content(manage_file.raw_file_readfile(filename))
            update_content="update CrawlerData set Content = ? where WebId = ?"
            sp.sql_cursor_execute(update_content,(content,Cdata[0]))
            print("WebId:"+str(Cdata[0])+"-内容更新完成")
        else:
            print("WebId:"+str(Cdata[0])+"-内容无需更新")
            continue