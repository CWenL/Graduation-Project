from bs4 import BeautifulSoup
import re
import json

import jieba
import manage_file
import draw_chart
import SQLiteOp as sp
import os
import urllib.request
from urllib.parse import urlparse
import time
import random

BASE_RAW_DATA_DIR = os.path.abspath(os.path.dirname(__file__))+"/tmp/"

# 动态获取基础路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 脚本所在目录
STATIC_DIR = os.path.join(BASE_DIR, "static", "Picture_Web")
def convert_to_web_path(file_path, base_path=None):
    """将文件系统路径转换为Web路径"""
    # 使用静态文件目录作为默认基础路径
    if base_path is None:
        base_path = STATIC_DIR
    # 统一路径大小写
    base_path = os.path.abspath(base_path).replace("\\", "/").lower()
    file_path = os.path.abspath(file_path).replace("\\", "/").lower()
    print(f"base_path: {base_path}")
    print(f"file_path: {file_path}")
    # 移除基础路径部分
    if file_path.startswith(base_path):
        web_path = file_path[len(base_path):]
    else:
        raise ValueError(f"File path does not start with the base path: {file_path}")
    web_path = "/static/Picture_Web" + web_path
    return web_path

def analysis_News(URL): # 分析最近考研新闻
    soup = BeautifulSoup(URL, 'html.parser')
    listBox2 = soup.find_all("div", class_="listBox2")
    for ldata in listBox2:
        # 找到所有的新闻项
        news_items = ldata.find_all('li')
        # 提取相关信息
        for item in news_items:
            # 标题
            title = item.find('h3').text
            # 日期
            date = item.find('p', class_='time').text
            # 链接地址
            link = "https://www.dxsbb.com/" + item.find('a')['href']
            # 使用正则表达式匹配数字部分
            match = re.search(r'/news/(\d+)\.html', link)
            web_id = match.group(1)
            res = sp.sql_execute_select("SELECT * FROM CrawlerData WHERE WebId = ?", (web_id,))
            
            # 图片下载地址
            img_url = item.find('img')['src']
            print(img_url)
            try:
                # 图片下载 返回现在存储在服务器中的地址
                load_url = convert_to_web_path(download_image(img_url))
            except Exception as e:
                load_url = "/static/imgs/Null.gif"
                print(f'下载 {img_url} 时出错: {e}')
                pass

            # 如果没有该条数据，插入数据
            if not res:
                insertdata = """
                INSERT INTO CrawlerData (WebId, Title, UpdateTime, Publisher, WebsiteLink, WebsitePicture) 
                VALUES (?, ?, ?, ?, ?, ?);
                """
                sp.sql_cursor_execute(insertdata, (web_id, title, date, "大学生必备网", link, load_url))
            else:
                # 如果已经有数据，更新数据
                update_data = """
                UPDATE CrawlerData
                SET Title = ?, UpdateTime = ?, Publisher = ?, WebsiteLink = ?, WebsitePicture = ?
                WHERE WebId = ?;
                """
                sp.sql_cursor_execute(update_data, (title, date, "大学生必备网", link, load_url, web_id))

    # 暂时不要了，要这个还要多建表
    # # 查找所有 class 为 rigthbox 的 div
    # divs = soup.find_all('div', class_='rigthbox')
    #  # 遍历每个 div
    # for div in divs:
    #     h2_text = div.find('h2').get_text(strip=True)  # 获取 h2 标签的文本内容
    #     # 查找所有 <li> 元素
    #     lis = div.find_all('li')
    #     for li in lis:
    #         a_tag = li.find('a')  # 找到 <a> 标签
    #         if a_tag:
    #             title = a_tag.get_text(strip=True)  # 获取标题文本
    #             link = a_tag['href']  # 获取链接（href 属性）
    #             # 使用正则表达式提取链接中的数字ID
    #             match = re.search(r'/news/list_(\d+).html', link)
    #             if match:
    #                 id_number = match.group(1)  # 提取 ID
    #             else:
    #                 id_number = None  # 如果没有匹配到 ID，设置为 None
    #         res=sp.sql_execute_select("select * from CrawlerData where WebId = ?",(web_id,))
    #         if res is None:
    #             insertdata="INSERT INTO CrawlerData (WebId, Title, Publisher, WebsiteLink) VALUES (?, ?, ?, ?);"
    #             sp.sql_cursor_execute(insertdata,(id_number,h2_text+"-"+title,"大学生必备网",link,))
    #         else:
    #             continue


def download_picture(anime_play_link,anime_cover_display_image,position):
    folder_path = os.path.abspath(os.path.dirname(__file__))+position  # 存放图片的文件夹路径
    if not os.path.exists(folder_path): # 确保文件夹存在，如果不存在则创建文件夹
        os.makedirs(folder_path)
    for index, url in enumerate(anime_cover_display_image): # 下载图片并保存到文件夹 # enumerate顺便获取下标
        try:
            parsed_url = urlparse(url) # 解析URL获取文件扩展名 
            filename, file_extension = os.path.splitext(parsed_url.path)
            if not file_extension:
                file_extension = '.jpg'  # 默认使用 .jpg 扩展名
            anime_id = re.search(r'\d+', anime_play_link[index]).group()
            image_name = anime_id+file_extension  # 构造图片文件名，这里使用序号作为文件名
            image_path = os.path.join(folder_path, image_name)
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            if os.path.isfile(image_path): #如果不存在就返回False
                print(image_path+"已存在")
            else:
                urllib.request.install_opener(opener)
                urllib.request.urlretrieve(url, image_path) # 使用urlretrieve下载图片到指定路径
                print(f'{image_name} 下载完成')
                time.sleep(random.uniform(0.5,1))
        except Exception as e:
            print(f'下载 {url} 时出错: {e}')

import requests

def download_image(image_url):
    try:
        # 获取文件名
        file_name = os.path.basename(urlparse(image_url).path)
        
        # 定义保存路径，确保文件夹存在
        save_dir = os.path.join(os.getcwd(), "static", "Picture_Web")  # 同一目录下的static/PictureWeb文件夹
        os.makedirs(save_dir, exist_ok=True)  # 如果文件夹不存在，创建文件夹
        
        # 保存图片的完整路径
        save_path = os.path.join(save_dir, file_name)
        
        # 发起 HTTP 请求获取图片内容
        response = requests.get(image_url)
        
        # 确保请求成功
        if response.status_code == 200:
            # 写入文件
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            print(f"图片已下载并保存为：{save_path}")
            return save_path
        else:
            print(f"下载失败，HTTP 状态码：{response.status_code}")
    except Exception as e:
        print(f"下载过程中出现错误：{e}")

# # 测试函数
# image_url = "https://img.dxsbb.com/upFiles/infoImg/2022091938716141.jpg"
# download_image(image_url)


def get_content(filename):
    soup = BeautifulSoup(filename,'html.parser')
    contentNode=soup.find("div", class_="content")
    # print(contentNode)
    content=contentNode.get_text()
    # 使用jieba进行中文分词
    content=" ".join(jieba.cut(content))
    return content