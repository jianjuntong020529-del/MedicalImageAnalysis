import matplotlib.pyplot as plt
import numpy as np

# 数据
years = ['2020', '2021', '2022', '2023', '2024', '2025E']
patients = [7.04, 7.07, 7.10, 7.14, 7.18, 7.20]
colors = ['#1f77b4']  # 蓝色系配色，接近原图风格

# 创建画布
plt.figure(figsize=(8, 6))

# 绘制柱状图
bars = plt.bar(years, patients, color=colors[0])

# 添加数据标签
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height,
             f'{height}',
             ha='center', va='bottom')

# 设置标题和坐标轴
plt.title('2020-2025年中国口腔疾病患者人数预测趋势图', fontsize=14)
plt.ylabel('人数（亿）', fontsize=12)
plt.ylim(0, 8)  # 匹配原图的Y轴范围

# 隐藏顶部和右侧的边框
plt.gca().spines['top'].set_visible(False)
plt.gca().spines['right'].set_visible(False)

# 显示图表
plt.tight_layout()
plt.show()