# PatentSmelter
PatentSmelter 是一个面向专利文本批量分析与可视化的轻量化流水线工具。将杂乱、半结构化的专利 TXT 文件作为“原矿”，通过抽取、清洗、双轨加工与可视化导出，输出可供决策参考的分析成果。

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](#license)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.0%2B-orange)](https://networkx.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-lightgrey)](https://pandas.pydata.org/)


## ✨ 核心特性

*    **全自动流水线**：丢入 `.txt` 即走，自动遍历目录解析数据，无需手动清洗。
*    **智能实体对齐**：内置实体归一化映射，解决“XX公司”、“XX有限公司”等别名不统一问题。
*   **深度情报可视化**：
    *   **时间序列**：月度申请趋势折线图
    *   **地域洞察**：年度国家/地区分布玫瑰图
    *   **技术解码**：标题关键词词云与词频统计
    *   **竞争图谱**：申请人合作共现网络图
*    **工业级鲁棒性**：集成异常捕获与日志记录，坏数据不影响整体流程。


| 阶段           | 模块              | 功能说明                                                                 |
| -------------- | ----------------- | ------------------------------------------------------------------------ |
| **阶段 Ⅰ & Ⅱ** | `PatentMiner`     | 原矿入库与洗矿提纯：批量扫描目录，正则解析文本，实体对齐，停用词过滤       |
| **阶段 Ⅲ**     | `PatentProcessor` | 双轨加工流水线：轨道 A（趋势分析）与轨道 B（SNA 合作网络关系提取）         |
| **阶段 Ⅳ & Ⅴ** | `PatentExporter`  | 可视化与打包发货：生成折线图、GEXF 网络文件，并将清洗后数据落盘至桌面       |

- ✅ **智能环境嗅探**：自动识别 Windows/macOS/Linux 并定位桌面路径
- ✅ **异常拦截日志**：解析失败的文件会记录至 `error_log.txt`

## 📁 目录结构

├── main.py # 主程序（包含所有类及流水线控制逻辑）

├── README.md # 项目文档

├── requirements.txt # 依赖清单（建议）

├── my_patents/ # 存放待解析的 .txt 专利原文（需自行创建）

├── output/ #存放输出文件

└── error_log.txt # 自动生成的解析错误日志


---

## 🛠️ 技术栈

*   **数据处理**：Pandas, NumPy
*   **正则引擎**：Re
*   **NLP分词**：Jieba
*   **复杂网络**：NetworkX
*   **可视化**：Pyecharts (交互式HTML), Matplotlib (静态拓扑图)

---

## 🚀 极速开始

### 环境准备

```bash
git clone https://github.com/yourusername/PatentSmelter.git
cd PatentSmelter
pip install -r requirements.txt
```

### 放入数据
将您的 Web of Science 纯文本专利数据（`*.txt`）放置于项目my_patent目录下。

### 点燃熔炉
```bash
python main.py
```
运行完毕后，查看 `./output/` 文件夹，所有图表与清洗后的 CSV 已就绪！

---

## 📁 产出物一览

运行后你将获得：

| 文件 | 描述 |
|------|------|
| `cleaned_patent_data.csv` | 清洗后的结构化明细表 |
| `monthly_trend.html` | 月度申请量动态趋势图 |
| `title_wordcloud.html` | 核心技术关键词云 |
| `country_distribution_2024.html` | 指定年份专利地域布局图 |
| `co_applicant_network.png` | 竞对合作关系网络拓扑 |

---

## 🤝 贡献代码

我们热爱开源协作！欢迎提交 Issue 报告 Bug 或提出新 Feature，也接受经过测试的 Pull Request。

---

## 📄 License

本项目基于 MIT License 开源。详情见 LICENSE 文件。
