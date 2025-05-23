import SQLiteOp as sp
import get_html
import ahead_port
import analysis_html
import asyncio
import draw_chart

def flashdata():
    sp.Sql_start() # 初始化建表
    get_html.Getstart() # 获取页面源码
    draw_chart.writeCiYun() # 创建词云
    draw_chart.Get_AnimeHeatMap() # 绘制相关系数热力图
    draw_chart.Get_Pie() # 绘制标签占比饼图
    draw_chart.Get_ZheXian() # 绘制四个榜单热度的折线图
 
flashdata()


