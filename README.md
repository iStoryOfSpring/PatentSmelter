# PatentSmelter
PatentSmelter 是一个面向专利文本批量分析与可视化的轻量化流水线工具。将杂乱、半结构化的专利 TXT 文件作为“原矿”，通过抽取、清洗、双轨加工与可视化导出，输出可供决策参考的分析成果。

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](#license)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.0%2B-orange)](https://networkx.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-lightgrey)](https://pandas.pydata.org/)

## 📖 项目简介

**PatentSmelter** 能够批量读取原始专利 `.txt` 文件，提取关键字段（名称、日期、申请人、IPC分类号、关键词），清洗噪声数据，并生成：

- 📈 **年度申请趋势图**
- ☁️ **高频关键词词频统计**
- 🕸️ **申请人合作网络关系图**（导出为 `.gexf` 格式，可直接导入 Gephi 进行高级可视化）

最终所有结果统一打包输出至桌面文件夹 `专利分析结果_YYYYMMDD`，实现一键式科研辅助分析。

## ✨ 核心特性

| 阶段           | 模块              | 功能说明                                                                 |
| -------------- | ----------------- | ------------------------------------------------------------------------ |
| **阶段 Ⅰ & Ⅱ** | `PatentMiner`     | 原矿入库与洗矿提纯：批量扫描目录，正则解析文本，实体对齐，停用词过滤       |
| **阶段 Ⅲ**     | `PatentProcessor` | 双轨加工流水线：轨道 A（趋势分析）与轨道 B（SNA 合作网络关系提取）         |
| **阶段 Ⅳ & Ⅴ** | `PatentExporter`  | 可视化与打包发货：生成折线图、GEXF 网络文件，并将清洗后数据落盘至桌面       |

- ✅ **智能环境嗅探**：自动识别 Windows/macOS/Linux 并定位桌面路径
- ✅ **异常拦截日志**：解析失败的文件会记录至 `error_log.txt`
- ✅ **高可扩展性**：通过修改 `parse_txt` 方法中的正则表达式即可适配任何格式的专利 TXT

## 📁 目录结构

├── main.py # 主程序（包含所有类及流水线控制逻辑）

├── README.md # 项目文档

├── requirements.txt # 依赖清单（建议）

├── my_patents/ # 存放待解析的 .txt 专利原文（需自行创建）

└── error_log.txt # 自动生成的解析错误日志



## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.8 及以上版本，然后安装依赖包：

bash
`pip install pandas networkx matplotlib wordcloud jieba pyecharts numpy`

### 2. 准备数据

在项目根目录下创建文件夹 my_patents，将所有待处理的专利 TXT 文件放入其中。
**⚠️ 重要提醒：你需要根据自己 TXT 文件的实际内容格式，修改 PatentMiner.parse_txt() 方法中的正则表达式提取逻辑。当前代码仅提供占位示例。**

### 3. 运行流水线

打开 main.py，将最后一行 # main() 的注释去掉，然后在终端执行：

bash
`python main.py`
程序将自动完成以下步骤：

扫描 my_patents 文件夹，解析每个 .txt 文件
生成清洗后的 DataFrame
计算年度趋势及关键词频次
构建申请人共现网络
在桌面上创建 专利分析结果_YYYYMMDD 文件夹，输出所有结果

### 输出结果说明

运行成功后，你将在桌面看到类似 专利分析结果_当前日期 的文件夹，内含：

|文件名称|描述|
|---------------------------|-------------------------------------------------|
|cleaned_patent_data.csv|清洗后的结构化专利数据表，可用 Excel 打开|
|yearly_trend.png|专利申请年度趋势折线图|
|co_applicant_network.gexf|申请人合作网络图文件（拖入 Gephi 即可进行力导向布局分析）|
🛠️ 自定义配置

修改文本解析规则

编辑 parse_txt 方法，根据你的 TXT 样例重写正则匹配部分。例如：

python

假设你的 txt 格式为：

专利名称：一种基于人工智能的数据处理方法

申请日：2023.05.20

申请人：XX大学；YY科技有限公司

主分类号：G06F 16/00

关键词：人工智能，数据处理，机器学习

`title = re.search(r'专利名称：(.*)', content).group(1)`
`raw_date = re.search(r'申请日：(.*)', content).group(1)`

**进一步解析年、月、日...**
添加停用词与实体对齐

在实例化 PatentMiner 时传入对应参数：

python

miner = PatentMiner(

    input_dir='./my_patents',
    
    stopwords_path='stopwords.txt',          # 每行一个停用词
    
    entity_map={'XX大学(北京)': 'XX大学'}     # 名称对齐字典
    
)

## 📝 注意事项

TXT 编码：确保专利文本文件使用 UTF-8 编码，否则可能抛出解码异常。

中文显示问题：绘图时若中文显示为方框，请在 draw_trends 方法中添加中文字体设置（如 plt.rcParams['font.sans-serif'] = ['SimHei']）。

大规模数据：当处理数万条专利时，建议将 batch_process 改为生成器模式以降低内存占用。

## 🤝 贡献指南

欢迎提交 Issue 或 Pull Request 来改进这个项目！可能的改进方向包括：

支持更多专利文件格式（如 XML、JSON）

增加 IPC 共现网络分析

集成词云图生成（已导入 WordCloud，待实现）

## 📄 开源许可

本项目基于 MIT License 开源，您可以自由使用、修改和分发。
