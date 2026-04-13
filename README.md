# PatentSmelter
PatentSmelter 是一个面向专利文本批量分析与可视化的轻量化流水线工具。将杂乱、半结构化的专利 TXT 文件作为“原矿”，通过抽取、清洗、双轨加工与可视化导出，输出可供决策参考的分析成果。

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](#license)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.0%2B-orange)](https://networkx.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-lightgrey)](https://pandas.pydata.org/)

## 📖 项目简介

**Patent Mining Pipeline** 将专利文本分析过程类比为矿物加工流水线——**"原矿入库 → 洗矿提纯 → 双轨加工 → 打包发货"**。它能够批量读取原始专利 `.txt` 文件，提取关键字段（名称、日期、申请人、IPC分类号、关键词），清洗噪声数据，并生成：

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
