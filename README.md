# PatentSmelter

专利文献分析工具，自动解析 Web of Science (Clarivate) 格式的专利导出文件，生成可视化图表。

基于本地重构版本，核心逻辑拆分至 `patent_core.py`，新增 Streamlit 交互界面。

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](#license)

## 功能

- **月度趋势图** — 按年月统计专利申请量，跨年数据逐月展示
- **标题关键词云 & 词频柱状图** — 使用 jieba 分词，提取标题高频词
- **国家分布饼图** — 按年度生成专利国家/地区分布环形图
- **申请人合作网络** — 基于申请人共现关系生成网络图
- **数据导出** — 清洗后的结构化数据导出 CSV

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 准备数据

将 Web of Science 导出的 `.txt` 文件放入 `my_patents/` 目录（默认路径），可在 UI 中指定其他路径。

### 3. 启动

**Streamlit 界面（推荐）：**

```bash
streamlit run app.py
```

打开浏览器访问 http://localhost:8501，在左侧栏设置参数后点击"开始分析"。

**命令行模式：**

```bash
python main.py
```

结果输出到 `output/` 目录。

## 项目结构

```
PatentSmelter/
├── app.py           # Streamlit 界面
├── patent_core.py   # 核心逻辑（解析、分析、可视化）
├── main.py          # 命令行入口（向后兼容）
├── requirements.txt
├── my_patents/      # 存放 .txt 专利数据
└── output/          # 生成的图表和CSV
```

## License

本项目基于 MIT License 开源。详情见 LICENSE 文件。

## 作者声明

作者始终坚持一个中国原则，HK、MO、TW均被视为CN的一部分。
