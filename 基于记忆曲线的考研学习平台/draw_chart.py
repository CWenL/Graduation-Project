import datetime
import re
import json
import manage_file
import draw_chart
import SQLiteOp
import os
import urllib.request
from urllib.parse import urlparse
import time
import random
import matplotlib.pyplot as plt
import jieba
from wordcloud import WordCloud
import pyecharts.options as opts
from pyecharts.charts import Line
from pyecharts.commons.utils import JsCode
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from pyecharts.charts import Pie
# def writeCiYun(): # 把所有评论合并制作词云
#     select_allComment_data=list(SQLiteOp.sql_execute_select_noVariable('select Comment from Comment'))
#     # print(select_allComment_data)
#     AllComment=' '.join([item[0] for item in select_allComment_data])
#     # print(AllComment)
#     cut_AllComment=jieba.cut(AllComment)
#     result=" ".join(cut_AllComment)
#     wc = WordCloud(
#         font_path='./fonts/simhei.ttf',
#         background_color='white',
#         width=800,
#         height=550,
#         max_font_size=100,
#         min_font_size=10,
#         mode='RGBA'
#     )
#     wc.generate(result)
#     wc.to_file(r"c:\\Users\\Administrator\Documents\\GitHub\\python_Crawler_course_design\\pythonProject3\webapp/static/WordCloud/allWordCloud.png")
#     plt.figure("新番")
#     plt.imshow(wc)
#     plt.axis("off")
#     # plt.show()
    

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.offline as pyo

def generate_user_tag_heatmap(unique_tags, heatmap_data):
    """
    生成用户已接触标签的热力图
    :param unique_tags: 唯一标签名称列表
    :param heatmap_data: 热力图数据矩阵
    :return: 热力图对象
    """
    # 创建热力图
    fig = make_subplots(rows=1, cols=1)
    trace = go.Heatmap(
        z=heatmap_data,
        x=unique_tags,
        y=unique_tags,
        colorscale='Blues'  # 设置颜色搭配
    )
    fig.add_trace(trace, row=1, col=1)
    fig.update_layout(title='用户标签热力图')
    return fig

# from pyecharts import options as opts
# from pyecharts.commons.utils import JsCode
# from pyecharts.charts import Pie
# def new_label_opts():
#     fn = """
#     function(params) {
#         if(params.name == '其他')
#             return '\\n\\n\\n' + params.name + ' : ' + params.value + '%';
#         return params.name + ' : ' + params.value + '%';
#     }
#     """
#     return opts.LabelOpts(formatter=JsCode(fn), position="center")
# def Get_Pie():
#     tags_list = SQLiteOp.sql_execute_select_noVariable('select anime_label from Anime')
#     tags_list = [tags[0] for tags in tags_list if tags[0]]# 将元组列表转换为字符串列表
#     tag_counts = {}# 创建一个空字典来存放标签和它们的出现次数
#     for tags in tags_list: # 遍历标签列表
#         tags_found = re.findall(r'#\w+', tags) # 使用正则表达式匹配标签
#         for tag in tags_found: # 对每个匹配到的标签进行计数
#             if tag in tag_counts:
#                 tag_counts[tag] += 1
#             else:
#                 tag_counts[tag] = 1
#     tag_counts = dict(sorted(tag_counts.items(), key=lambda item: item[1])) # 将字典按照值升序
    
#     pie = Pie()
#     count_sum=0
#     for tag,count in tag_counts.items():
#         count_sum=count_sum+count
#         pie.add(
#             "",[list(z) for z in tag_counts.items()],
#         center=["40%", "52%"],
#         radius=[140, 222],
#         )
#     pie.set_global_opts(
        
#         legend_opts=opts.LegendOpts(
#             type_="scroll", pos_top="20%", pos_left="80%", orient="vertical"
#         ),
#     )
#     pie.render(os.path.abspath(os.path.dirname(__file__))+'/static/chart/mutiple_pie.html')

def days_in_phase(phase):
    start = datetime.datetime.strptime(phase["start_date"], "%Y-%m-%d")
    end = datetime.datetime.strptime(phase["end_date"], "%Y-%m-%d")
    return (end - start).days + 1

def generate_pie_charts(username, study_plan, app):
    try:
        from pyecharts import options as opts
        from pyecharts.charts import Pie
        with app.app_context():
            phase1_days = days_in_phase(study_plan["phase1"])
            phase2_days = days_in_phase(study_plan["phase2"])
            phase3_days = days_in_phase(study_plan["phase3"])
            total_days_data = [
                ("一轮复习", phase1_days),
                ("二轮强化", phase2_days),
                ("三轮冲刺", phase3_days),
            ]
            phase1_data = [
                ("数学", study_plan["phase1"]["math_hours"]),
                ("英语", study_plan["phase1"]["english_hours"]),
                ("政治", study_plan["phase1"]["politics_hours"]),
                ("专业课", study_plan["phase1"]["professional_hours"]),
            ]
            phase2_data = [
                ("数学", study_plan["phase2"]["math_hours"]),
                ("英语", study_plan["phase2"]["english_hours"]),
                ("政治", study_plan["phase2"]["politics_hours"]),
                ("专业课", study_plan["phase2"]["professional_hours"]),
            ]
            phase3_data = [
                ("数学", study_plan["phase3"]["math_hours"]),
                ("英语", study_plan["phase3"]["english_hours"]),
                ("政治", study_plan["phase3"]["politics_hours"]),
                ("专业课", study_plan["phase3"]["professional_hours"]),
            ]
            def create_pie(title, data, unit="小时"):
                return (
                    Pie()
                    .add(
                        "",
                        data,
                        radius=["30%", "75%"],
                    )
                    .set_global_opts(
                        title_opts=opts.TitleOpts(title=title),
                        legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%"),
                        toolbox_opts=opts.ToolboxOpts(is_show=False)
                    )
                    .set_series_opts(
                        label_opts=opts.LabelOpts(formatter="{b}: {c} "+unit+" ({d}%)")
                    )
                )
            phase1_pie = create_pie("一轮复习每日学习时间安排", phase1_data)
            phase2_pie = create_pie("二轮强化每日学习时间安排", phase2_data)
            phase3_pie = create_pie("三轮冲刺每日学习时间安排", phase3_data)
            total_days_pie = create_pie("一轮、二轮、三轮各占的时间", total_days_data, unit="天")
            chart_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'chart'))
            os.makedirs(chart_dir, exist_ok=True)
            # 生成相对路径
            phase1_path = f"chart/{username}_phase1_pie.html"
            phase2_path = f"chart/{username}_phase2_pie.html"
            phase3_path = f"chart/{username}_phase3_pie.html"
            total_days_path = f"chart/{username}_total_days_pie.html"
            # 转换为绝对路径保存
            phase1_abs_path = os.path.join(chart_dir, f"{username}_phase1_pie.html")
            phase2_abs_path = os.path.join(chart_dir, f"{username}_phase2_pie.html")
            phase3_abs_path = os.path.join(chart_dir, f"{username}_phase3_pie.html")
            total_days_abs_path = os.path.join(chart_dir, f"{username}_total_days_pie.html")
            phase1_pie.render(phase1_abs_path)
            phase2_pie.render(phase2_abs_path)
            phase3_pie.render(phase3_abs_path)
            total_days_pie.render(total_days_abs_path)
            return [
                (phase1_path, "一轮复习每日学习时间安排"),
                (phase2_path, "二轮强化每日学习时间安排"),
                (phase3_path, "三轮冲刺每日学习时间安排"),
                (total_days_path, "一轮、二轮、三轮各占的时间")
            ], True, ""
    except Exception as e:
        return [], False, f"图表生成失败: {str(e)}"

from pyecharts.charts import Line
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode

def ZheXian(x_data, y_data, title):
    background_color_js = (
        "new echarts.graphic.LinearGradient(0, 0, 0, 1, "
        "[{offset: 0, color: '#c86589'}, {offset: 1, color: '#06a7ff'}], false)"
    )
    area_color_js = (
        "new echarts.graphic.LinearGradient(0, 0, 0, 1, "
        "[{offset: 0, color: '#eb64fb'}, {offset: 1, color: '#3fbbff0d'}], false)"
    )
    
    line = (
        Line(init_opts=opts.InitOpts(bg_color=JsCode(background_color_js)))
        .add_xaxis(xaxis_data=x_data)
        .add_yaxis(
            series_name="数量",
            y_axis=y_data,
            is_smooth=True,
            is_symbol_show=True,
            symbol="circle",
            symbol_size=6,
            linestyle_opts=opts.LineStyleOpts(color="#fff"),
            label_opts=opts.LabelOpts(is_show=True, position="top", color="white"),
            itemstyle_opts=opts.ItemStyleOpts(
                color="red", border_color="#fff", border_width=3
            ),
            tooltip_opts=opts.TooltipOpts(is_show=True),  # 显示tooltip
            areastyle_opts=opts.AreaStyleOpts(color=JsCode(area_color_js), opacity=1),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title=title,
                pos_top="5%",
                pos_left="center",
                title_textstyle_opts=opts.TextStyleOpts(color="#fff", font_size=16),
            ),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                boundary_gap=False,
                axislabel_opts=opts.LabelOpts(rotate=30, color="#ffffff63"),
                axisline_opts=opts.AxisLineOpts(is_show=False),
                axistick_opts=opts.AxisTickOpts(
                    is_show=True,
                    length=25,
                    linestyle_opts=opts.LineStyleOpts(color="#ffffff1f"),
                ),
                splitline_opts=opts.SplitLineOpts(
                    is_show=True, linestyle_opts=opts.LineStyleOpts(color="#ffffff1f")
                ),
                interval=5,  # 设置x轴标签的显示间隔
            ),
            yaxis_opts=opts.AxisOpts(
                type_="value",
                position="right",
                axislabel_opts=opts.LabelOpts(margin=20, color="#ffffff63"),
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(width=2, color="#fff")
                ),
                axistick_opts=opts.AxisTickOpts(
                    is_show=True,
                    length=15,
                    linestyle_opts=opts.LineStyleOpts(color="#ffffff1f"),
                ),
                splitline_opts=opts.SplitLineOpts(
                    is_show=True, linestyle_opts=opts.LineStyleOpts(color="#ffffff1f")
                ),
                split_number=5,  # 设置y轴刻度线的数量
            ),
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(
                is_show=True,
                trigger="axis",  # 按轴触发tooltip
                axis_pointer_type="cross",  # 十字准星指示器
                background_color="rgba(255, 255, 255, 0.8)",
                textstyle_opts=opts.TextStyleOpts(color="#000"),
            ),
        )
    )
    return line

def create_study_type_pie(study_type_counts):
    # 准备数据
    data = [(item.type, item.count) for item in study_type_counts]
    # 创建饼图
    pie = (
        Pie()
        .add(
            "",
            data,
            radius=["40%", "70%"],
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="各科目题目的占比"),
            legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%"),
        )
        .set_series_opts(
            label_opts=opts.LabelOpts(formatter="{b}: {c} ({d}%)")
        )
    )
    return pie

from pyecharts.charts import Bar
from pyecharts import options as opts

# 创建柱状图和折线图
def create_label_chart(label_stats,PicTitle):
    label_counts, label_weight_sum, label_review_counts = label_stats
    # 准备数据
    labels = list(label_counts.keys())
    counts = [label_counts[label] for label in labels]
    weights = [label_weight_sum.get(label, 0) for label in labels]
    reviews = [label_review_counts.get(label, 0) for label in labels]

    # 计算右边y轴（权重总和）的合理间隔和最大值
    max_weight = max(weights)
    weight_range = max_weight
    if weight_range < 100:
        interval_weight = 10
    elif weight_range < 1000:
        interval_weight = 50
    else:
        interval_weight = 100
    max_weight = ((max_weight + interval_weight - 1) // interval_weight) * interval_weight

    # 计算左边y轴（出现次数和复习次数）的合理间隔和最大值
    max_count_review = max(counts + reviews)
    count_review_range = max_count_review
    if count_review_range < 20:
        interval_count_review = 5
    elif count_review_range < 50:
        interval_count_review = 10
    else:
        interval_count_review = 20
    max_count_review = ((max_count_review + interval_count_review - 1) // interval_count_review) * interval_count_review

    # 创建柱状图
    bar = (
        Bar()
        .add_xaxis(labels)
        .add_yaxis("标签出现次数", counts, label_opts=opts.LabelOpts(is_show=False))
        .add_yaxis("复习次数", reviews, label_opts=opts.LabelOpts(is_show=False))
        .extend_axis(
            yaxis=opts.AxisOpts(
                name="权重总和",
                type_="value",
                min_=0,
                max_=max_weight,
                interval=interval_weight,
                axislabel_opts=opts.LabelOpts(formatter="{value}"),
            )
        )
        .set_global_opts(
            tooltip_opts=opts.TooltipOpts(
                is_show=True, trigger="axis", axis_pointer_type="cross"
            ),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                axispointer_opts=opts.AxisPointerOpts(is_show=True, type_="shadow"),
            ),
            yaxis_opts=opts.AxisOpts(
                name="次数",
                type_="value",
                min_=0,
                max_=max_count_review,
                interval=interval_count_review,
                axislabel_opts=opts.LabelOpts(formatter="{value}"),
                axistick_opts=opts.AxisTickOpts(is_show=True),
                splitline_opts=opts.SplitLineOpts(is_show=True),
            ),
            legend_opts=opts.LegendOpts(pos_top="5%"),
            title_opts=opts.TitleOpts(title=PicTitle)
        )
    )
    # 创建折线图
    line = (
        Line()
        .add_xaxis(labels)
        .add_yaxis(
            series_name="权重总和",
            yaxis_index=1,
            y_axis=weights,
            label_opts=opts.LabelOpts(is_show=False),
        )
    )
    # 重叠柱状图和折线图
    chart = bar.overlap(line)
    return chart


def create_correct_rate_line(df):
    """
    创建正确率折线图
    """
    if df is None or df.empty:
        return None
    # 提取数据
    dates = df['date'].tolist()
    correct_rates = df['correct_rate'].tolist()
    # 创建折线图
    line = (
        Line()
        .add_xaxis(dates)
        .add_yaxis(
            series_name="正确率 (%)",
            y_axis=correct_rates,
            label_opts=opts.LabelOpts(is_show=True),
            is_smooth=True  # 平滑曲线
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="复习题目正确率"),
            xaxis_opts=opts.AxisOpts(type_="category", name="日期"),
            yaxis_opts=opts.AxisOpts(type_="value", name="正确率 (%)", min_=0, max_=100),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross")
        )
    )
    return line