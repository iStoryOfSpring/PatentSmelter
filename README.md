# PatentSmelter

**PatentSmelter** is a lightweight analytical pipeline that transforms raw patent export files from Web of Science (Clarivate) into structured data, insightful visualizations, and exportable reports. It supports both an interactive Streamlit UI and a headless CLI mode.

[English](#english) | [中文](#chinese)


[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Workstation-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

<div id="chinese"></div>

## 中文

### 项目简介

PatentSmelter 是一个面向专利文本批量分析与可视化的轻量化流水线工具。将杂乱、半结构化的专利 TXT 文件作为"原矿"，通过抽取、清洗、加工与全维度分析，输出涵盖技术生命周期、热点探测、动态演进的可视化成果。

### ✨ 核心特性

- **全自动流水线**：丢入 `.txt` 文件即可运行，自动遍历目录解析数据，无需手动清洗
- **双模式运行**：Streamlit 交互界面（推荐）+ 命令行批处理模式
- **技术生命周期分析**：逻辑回归 S 曲线拟合 + 四阶段识别（萌芽期 / 成长期 / 成熟期 / 衰退期）+ 阶段标注可视化
- **热点探测**：IPC 分类年分布热力图 + 突发词（Burst Term）检测
- **动态演进**：逐年关键词对比 + 技术路线图时间轴 + 成熟度气泡图
- **多维度可视化**：
  - 月度申请趋势折线图
  - 标题 & 摘要关键词云 & 词频柱状图（基于 jieba 分词）
  - 年度国家/地区分布玫瑰图
  - 申请人合作共现网络图
- **灵活筛选**：支持按年份范围、IPC 分类号筛选数据后分析
- **数据导出**：清洗后的结构化数据一键导出 CSV
- **可配置选项**：按需勾选分析模块，控制台 / 页面均可操作

### 快速上手

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 将 Web of Science 导出的 .txt 文件放入 my_patents/ 目录（先新建名称为my_patents的文件夹)

# 3a. Streamlit 界面（推荐）
streamlit run app.py
# 浏览器访问 http://localhost:8501

# 3b. 命令行模式
python main.py
```

**注意，绝大多数情况下用3a方法就够了，不得已才用3b**

#### Streamlit 界面使用

启动 `streamlit run app.py` 后，终端会显示双语提示：

```
============================================================
  PatentSmelter 正在启动...
  PatentSmelter is starting up...
  请勿关闭此窗口 / Do NOT close this window
============================================================
```

页面划分为三个区域：

| 区域 | 位置 | 功能 |
|------|------|------|
| **左侧边栏** | 左侧 | 设置输入目录、勾选分析模块、年份/IPC 筛选、点击「开始分析」 |
| **中央主区域** | 中间 | 展示选中的图表预览（HTML / PNG / CSV），分析时显示进度条 |
| **文件列表** | 右侧 | 列出所有已生成文件，点击「查看」在中央区域打开预览 |

操作步骤：

1. 左侧确认输入目录指向 `./my_patents`
2. 勾选需要分析的项目（默认开启：月度趋势、词云词频、国家分布、S 曲线、IPC 热力图、逐年关键词、摘要分析）
3. 根据需要设置年份范围 / IPC 筛选
4. 点击 **「开始分析」**
5. 观察中央区域的进度条 —— 分析完成后进度条消失
6. 点击右侧文件列表中的「查看」预览任一图表

> 分析过程中请勿刷新页面。分析耗时视专利数量而定，大量数据时可能需要几分钟。

#### 命令行模式

```bash
python main.py
```
所有图表自动生成至 `./output/` 目录，无需任何操作。

### 输出文件清单

| 文件 | 说明 |
|------|------|
| `cleaned_patent_data.csv` | 清洗后的结构化专利数据 |
| `monthly_trend.html` | 月度申请趋势折线图 |
| `title_wordcloud.html` | 标题关键词词云 |
| `title_wordfreq_bar.html` | 标题高频词柱状图（Top 20） |
| `abstract_wordcloud.html` | 摘要关键词词云 |
| `abstract_wordfreq_bar.html` | 摘要高频词柱状图（Top 20） |
| `country_distribution_YYYY.html` | 年度国家/地区分布图表（每年一份） |
| `s_curve.html` | 技术生命周期 S 曲线（含四阶段色块标注） |
| `ipc_heatmap.html` | IPC 分类年分布热力图 |
| `yearly_keywords.html` | 逐年关键词对比分组柱状图 |
| `burst_terms.html` | 技术突发词排行（Top 20） |
| `bubble_chart.html` | 技术成熟度气泡图（年份 — 成熟度 — 申请量） |
| `technology_roadmap.html` | 技术路线图自动播放时间轴 |
| `co_applicant_network.png` | 申请人合作共现网络图 |

### 项目结构

```
PatentSmelter/
├── app.py           # Streamlit 交互界面
├── patent_core.py   # 核心逻辑（数据解析、分析模型、可视化）
├── main.py          # CLI 入口（向后兼容）
├── requirements.txt # Python 依赖
├── my_patents/      # 存放专利 .txt 数据文件
└── output/          # 生成的图表（HTML / PNG / CSV）
```

### 更新日志

#### v2.0 — 技术生命周期与热点分析

新增 6 大分析模块，覆盖流程图全部 5 层：

- **生命周期分析**：`fit_s_curve()` — 逻辑回归拟合累计申请量 S 曲线；`identify_stages()` — 一阶 / 二阶导数法识别萌芽 → 成长 → 成熟 → 衰退四阶段
- **IPC 热力图**：`generate_ipc_heatmap()` — 年份 × IPC 部级分类（A–H）交叉分布热力图，直观展示技术领域变迁
- **突发词检测**：`detect_burst_terms()` — 前后半时间窗口词频对比，计算爆发强度，识别新兴技术关键词
- **逐年关键词**：`analyze_text_by_year()` + `generate_yearly_keyword_chart()` — 逐年 Top 关键词分组柱状图
- **成熟度气泡图**：`generate_bubble_chart()` — x=年份、y=S 曲线归一化成熟度、气泡=年申请量、色=生命周期阶段
- **技术路线图**：`generate_roadmap_timeline()` — 每年 Top 专利时间轴自动播放
- **摘要 NLP**：`generate_abstract_nlp_charts()` — 新增 AB（摘要）字段解析与词云词频分析
- **外部停用词表**：支持通过 `PatentMiner(stopwords_path=...)` 加载自定义停用词
- **UI 布局优化**：三栏布局（左侧控制 / 中栏图表预览 / 右侧文件列表），无需上下滚动
- **进度条支持**：实时显示分析进度，附中英文等待提示
- **终端提示**：启动时打印 "请勿关闭此窗口 / Do NOT close this window" 提示

### License

本项目基于 MIT License 开源。详情见 `LICENSE` 文件。

---

## English

### Overview

PatentSmelter ingests semi-structured patent text files exported from Web of Science (Clarivate), parses them into a clean DataFrame, and produces analytical visualizations via a modular pipeline. It runs either through an interactive Streamlit interface or as a command-line batch tool.

### Key Features

- **Fully automated pipeline** — drop `.txt` files into the input directory, run once, get all outputs
- **Dual operation modes**: Streamlit web UI (recommended) and headless CLI
- **Technology life cycle analysis**: Logistic S-curve fitting + 4-stage identification (Embryonic / Growth / Mature / Decline)
- **Hotspot detection**: IPC year×category heatmap + burst term detection
- **Evolutionary analysis**: Year-over-year keyword comparison, technology roadmap timeline, maturity bubble chart
- **Multi-dimensional visualizations**:
  - Monthly application trend line chart
  - Title & abstract keyword word cloud & frequency bar chart (jieba-based tokenization)
  - Annual country/region distribution chart
  - Applicant co-occurrence network graph
- **Flexible filtering**: filter by year range and/or IPC classification before analysis
- **Data export**: cleaned structured data to CSV with one click
- **Modular analysis**: toggle individual analysis modules on/off

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Place Web of Science .txt files into my_patents/ （create a new folder names 'my_patents' ）

# 3a. Streamlit UI (recommended)
streamlit run app.py
# Open http://localhost:8501

# 3b. CLI mode
python main.py
```

#### Streamlit UI Guide

The page is divided into three areas:

| Area | Position | Purpose |
|------|----------|---------|
| **Sidebar** | Left | Configure input directory, toggle analysis modules, set year/IPC filters, click "Start Analysis" |
| **Chart Preview** | Center | Displays the selected chart (HTML / PNG / CSV); shows progress bar during analysis |
| **File List** | Right | Lists all generated output files; click "View" to preview in the center area |

Steps:

1. In the left sidebar, confirm the input directory points to `./my_patents`
2. Check the analysis modules you need (default: trend, word cloud, country pie, S-curve, IPC heatmap, yearly keywords, abstract NLP)
3. Optionally set year range / IPC filter
4. Click **「开始分析」**
5. Watch the progress bar in the center area — it disappears when analysis completes
6. Click "View" on any file in the right column to preview it

> Do not refresh the page during analysis. Processing time depends on the number of patents; large datasets may take a few minutes.

### Output Artifacts

| File | Description |
|------|-------------|
| `cleaned_patent_data.csv` | Cleaned structured patent data |
| `monthly_trend.html` | Monthly application trend line chart |
| `title_wordcloud.html` | Title keyword word cloud |
| `title_wordfreq_bar.html` | Title keyword frequency bar chart (Top 20) |
| `abstract_wordcloud.html` | Abstract keyword word cloud |
| `abstract_wordfreq_bar.html` | Abstract keyword frequency bar chart (Top 20) |
| `country_distribution_YYYY.html` | Annual country/region distribution chart (per year) |
| `s_curve.html` | Technology life cycle S-curve with 4-stage annotations |
| `ipc_heatmap.html` | IPC section × year heatmap |
| `yearly_keywords.html` | Year-over-year keyword comparison grouped bar chart |
| `burst_terms.html` | Technology burst term ranking (Top 20) |
| `bubble_chart.html` | Technology maturity bubble chart (year — maturity — count) |
| `technology_roadmap.html` | Technology roadmap auto-playing timeline |
| `co_applicant_network.png` | Applicant co-occurrence network graph |

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

### Changelog

#### v2.0 — Technology Lifecycle & Hotspot Analysis

Six new analysis modules covering the full 5-layer pipeline:

- **S-Curve Modeling**: `fit_s_curve()` — logistic regression on cumulative patent counts; `identify_stages()` — derivative-based phase detection (Embryonic → Growth → Mature → Decline)
- **IPC Heatmap**: `generate_ipc_heatmap()` — year × IPC section (A–H) cross-distribution heatmap
- **Burst Terms**: `detect_burst_terms()` — frequency ratio between early/late time windows to identify surging keywords
- **Yearly Keywords**: `analyze_text_by_year()` + `generate_yearly_keyword_chart()` — grouped bar chart of Top keywords per year
- **Bubble Chart**: `generate_bubble_chart()` — x=year, y=S-curve normalized maturity, size=annual count, color=lifecycle stage
- **Technology Roadmap**: `generate_roadmap_timeline()` — auto-playing timeline of top patents per year
- **Abstract NLP**: `generate_abstract_nlp_charts()` — AB field parsing, word cloud & frequency charts
- **External Stopwords**: load custom stopwords via `PatentMiner(stopwords_path=...)`
- **UI Layout Update**: three-column layout (sidebar controls / center chart preview / right file list) — no more scrolling
- **Progress Bar**: real-time analysis progress with bilingual waiting hint
- **Terminal Notice**: startup prints "请勿关闭此窗口 / Do NOT close this window"

### License

This project is open-sourced under the MIT License. See the `LICENSE` file for details.

---

### Author's Note

The author upholds the One-China principle. HK, MO, and TW are classified as part of CN (region rather than country).

作者始终坚持中共中央的‘一个中国’原则。
