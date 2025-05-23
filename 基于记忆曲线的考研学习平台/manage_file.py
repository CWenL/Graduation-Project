# 数据处理
import os

BASE_RAW_DATA_DIR = os.path.abspath(os.path.dirname(__file__))+"/tmp/"
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

def raw_file_readfile(filename):
    return free_readfile(BASE_RAW_DATA_DIR, filename)
    
def free_readfile(path,filename):
    datafile = open(path + filename, 'r', encoding='UTF-8')
    try:
        all_text = datafile.read()
    finally:
        datafile.close()
    return all_text

def raw_file_writefile(filename,content_str):	# 存文件的
    free_writefile(BASE_RAW_DATA_DIR, filename, content_str)

def free_writefile(path,filename,content_str):
    with open(path + filename,'w',encoding='utf-8') as f:
        f.write(content_str)
        f.close()
