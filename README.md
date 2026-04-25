# PatentSmelter

**PatentSmelter** is a lightweight analytical pipeline that transforms raw patent export files from Web of Science (Clarivate) into structured data, insightful visualizations, and exportable reports. It supports both an interactive Streamlit UI and a headless CLI mode.

[English](#english) | [中文](#chinese)

---

<div id="chinese"></div>

## 中文

### 项目简介

PatentSmelter 是一个面向专利文本批量分析与可视化的轻量化流水线工具。将杂乱、半结构化的专利 TXT 文件作为"原矿"，通过抽取、清洗、加工与可视化导出，输出可供决策参考的分析成果。

### ✨ 核心特性

- **全自动流水线**：丢入 `.txt` 文件即可运行，自动遍历目录解析数据，无需手动清洗
- **双模式运行**：Streamlit 交互界面（推荐） + 命令行批处理模式
- **多维度可视化**：
  - 月度申请趋势折线图（支持跨年逐月展示）
  - 标题关键词词云 & 词频柱状图（基于 jieba 分词）
  - 年度国家/地区分布玫瑰图
  - 申请人合作共现网络图
- **灵活筛选**：支持按年份范围、IPC 分类号筛选数据后分析
- **数据导出**：清洗后的结构化数据一键导出 CSV
- **可配置选项**：按需勾选分析模块，控制台/页面均可操作

### 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 将 Web of Science 导出的 .txt 文件放入 my_patents/ 目录

# 3a. Streamlit 界面（推荐）
streamlit run app.py
# 访问 http://localhost:8501

# 3b. 命令行模式
python main.py
```

### 项目结构

```
PatentSmelter/
├── app.py           # Streamlit UI
├── patent_core.py   # 核心逻辑（解析、分析、可视化）
├── main.py          # CLI 入口（向后兼容）
├── requirements.txt
├── my_patents/      # 存放 .txt 专利数据
└── output/          # 生成的图表和 CSV
```

### License

本项目基于 MIT License 开源。详情见 `LICENSE` 文件。

---

<div id="english"></div>

## English

### Overview

PatentSmelter ingests semi-structured patent text files exported from Web of Science (Clarivate), parses them into a clean DataFrame, and produces analytical visualizations via a modular pipeline. It runs either through an interactive Streamlit interface or as a command-line batch tool.

### Key Features

- **Fully automated pipeline** — drop `.txt` files into the input directory, run once, get all outputs
- **Dual operation modes**: Streamlit web UI (recommended) and headless CLI
- **Multi-dimensional visualizations**:
  - Monthly application trend line chart (supports cross-year data)
  - Title keyword word cloud & frequency bar chart (jieba-based tokenization)
  - Annual country/region distribution donut chart
  - Applicant co-occurrence network graph
- **Flexible filtering**: filter by year range and/or IPC classification before analysis
- **Data export**: cleaned structured data to CSV with one click
- **Modular analysis**: toggle individual analysis modules on/off

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Place Web of Science .txt files into my_patents/

# 3a. Streamlit UI (recommended)
streamlit run app.py
# Open http://localhost:8501

# 3b. CLI mode
python main.py
```

### Project Structure

```
PatentSmelter/
├── app.py           # Streamlit UI
├── patent_core.py   # Core logic (parsing, analysis, visualization)
├── main.py          # CLI entry point (backward-compatible)
├── requirements.txt
├── my_patents/      # Directory for .txt patent data files
└── output/          # Generated charts and CSV output
```

### Output Artifacts

| File | Description |
|------|-------------|
| `cleaned_patent_data.csv` | Structured patent data after cleaning |
| `monthly_trend.html` | Interactive monthly trend chart |
| `title_wordcloud.html` | Title keyword word cloud |
| `title_wordfreq_bar.html` | Title keyword frequency bar chart (top 20) |
| `country_distribution_YYYY.html` | Annual country/region distribution chart (per year) |
| `co_applicant_network.png` | Applicant co-occurrence network visualization |

### License

This project is open-sourced under the MIT License. See the `LICENSE` file for details.

---

### Author's Note

The author upholds the One-China principle. HK, MO, and TW are classified as part of CN (region rather than country).
