import os
import re
import logging
from datetime import datetime
import pandas as pd
import networkx as nx
from collections import Counter
from itertools import combinations
import matplotlib.pyplot as plt
import jieba  # 新增：用于标题分词

from pyecharts import options as opts
from pyecharts.charts import Line, WordCloud, Bar, Pie  # 新增：词云、柱状图、饼图

# 解决 Mac 下 Matplotlib 中文显示问题
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS'] 
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 阶段一 & 阶段二：原矿入库与洗矿提纯 (Data Miner & Cleaner)
# ==========================================
class PatentMiner:
    def __init__(self, input_dir, stopwords_path=None, entity_map=None):
        self.input_dir = input_dir
        self.stopwords = set()  # 可根据需要加载停用词
        self.entity_map = entity_map or {}  # 实体对齐字典
        
        # 配置异常拦截日志
        logging.basicConfig(filename='error_log.txt', level=logging.ERROR, 
                            format='%(asctime)s - %(message)s')

    def _clean_entity(self, name):
        """实体对齐与清洗"""
        name = name.strip()
        return self.entity_map.get(name, name)

    def parse_txt(self, filepath):
        """精准抽取：根据 Web of Science (Clarivate) 格式提取数据"""
        patents = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # 按照记录结束标识 'ER' 切分每条专利记录
                records = content.split('\nER\n')
                
                for record in records:
                    if not record.strip() or record.startswith('FN '):
                        continue
                        
                    data = {}
                    # 1. 提取专利号 (PN)
                    pn_match = re.search(r'^PN\s+(.+)$', record, re.M)
                    data['patent_number'] = pn_match.group(1).strip() if pn_match else "Unknown"
                    
                    # 2. 提取标题 (TI) - 考虑跨行
                    ti_match = re.search(r'^TI\s+(.*?)(?=\n[A-Z]{2}\s|$)', record, re.S | re.M)
                    data['title'] = ti_match.group(1).replace('\n', ' ').strip() if ti_match else ""
                    
                    # 3. 提取申请人/代理机构 (AE)
                    ae_match = re.search(r'^AE\s+(.*?)(?=\n[A-Z]{2}\s|$)', record, re.S | re.M)
                    if ae_match:
                        ae_raw = ae_match.group(1)
                        # 提取括号外的名称（支持多行多机构）
                        applicants = re.findall(r'^(.*?)(?:\s\(|$)', ae_raw, re.M)
                        data['applicants'] = ';'.join([self._clean_entity(a) for a in applicants if a.strip()])
                    else:
                        data['applicants'] = ""

                    # 4. 提取公开日期 (PD) 并转换格式
                    pd_match = re.search(r'^PD\s+\S+\s+(\d{2}\s[A-Z][a-z]{2}\s\d{4})', record, re.M)
                    if pd_match:
                        date_str = pd_match.group(1)
                        try:
                            data['date'] = datetime.strptime(date_str, '%d %b %Y').strftime('%Y-%m-%d')
                        except:
                            data['date'] = ""
                    else:
                        data['date'] = ""

                    # 5. 提取国际专利分类号 (IP)
                    ip_match = re.search(r'^IP\s+(.+)$', record, re.M)
                    data['ipc'] = ip_match.group(1).strip() if ip_match else ""

                    patents.append(data)
                    
        except Exception as e:
            logging.error(f"解析文件 {filepath} 失败: {str(e)}")
            
        return pd.DataFrame(patents)

    def batch_process(self):
        """流水线：自动扫描目录下所有 TXT 文件并汇总"""
        all_data = []
        if not os.path.exists(self.input_dir):
            print(f"错误: 找不到目录 '{self.input_dir}'")
            return pd.DataFrame()

        # 获取目录下所有 .txt 结尾的文件
        files = [f for f in os.listdir(self.input_dir) if f.lower().endswith('.txt')]
        
        if not files:
            return pd.DataFrame()

        print(f"正在扫描并处理 {len(files)} 个文本文件...")
        for filename in files:
            filepath = os.path.join(self.input_dir, filename)
            df = self.parse_txt(filepath)
            if not df.empty:
                all_data.append(df)
        
        if not all_data:
            return pd.DataFrame()
            
        return pd.concat(all_data, ignore_index=True)

# ==========================================
# 阶段三：逻辑加工与可视化 (Data Processor)
# ==========================================
class PatentProcessor:
    def __init__(self, df):
        self.df = df
        self.export_dir = './output'
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

    def analyze_basic(self):
        """基础统计：提取年份、月份和国家信息"""
        # 提取年份和月份
        self.df['year'] = pd.to_datetime(self.df['date'], errors='coerce').dt.year
        self.df['month'] = pd.to_datetime(self.df['date'], errors='coerce').dt.month
        
        # 提取国家代码（假设专利号前两位为国家代码，例如 CN, US, EP）
        self.df['country'] = self.df['patent_number'].astype(str).str.extract(r'^([A-Za-z]{2})')[0].fillna('Unknown').str.upper()

        # 月份统计（1-12月累计）
        monthly_trend = self.df['month'].dropna().value_counts().sort_index()
        
        # IPC 统计
        all_ipcs = []
        for codes in self.df['ipc'].dropna():
            all_ipcs.extend([code.strip()[:4] for code in codes.split(';')])
        ipc_counts = Counter(all_ipcs)
        
        return monthly_trend, ipc_counts

    def analyze_co_occurrence(self):
        """合作网络分析：申请人共现"""
        edge_weights = Counter()
        for apps in self.df['applicants'].dropna():
            app_list = [a.strip() for a in apps.split(';') if a.strip()]
            if len(app_list) >= 2:
                for combo in combinations(sorted(app_list), 2):
                    edge_weights[combo] += 1
        return edge_weights

    def visualize_trend(self, monthly_trend):
        """生成高颜值月度趋势图 (Pyecharts)"""
        # 提取 X 轴（月份）和 Y 轴（数量）
        months = [f"{int(m)}月" for m in monthly_trend.index]
        counts = [int(c) for c in monthly_trend.values]
        
        line = (
            Line(init_opts=opts.InitOpts(theme="dark", width="900px", height="500px"))
            .add_xaxis(xaxis_data=months)
            .add_yaxis(
                series_name="专利申请量",
                y_axis=counts,
                is_smooth=True,              
                label_opts=opts.LabelOpts(is_show=True), 
                linestyle_opts=opts.LineStyleOpts(width=3, color="#00BFFF"), 
                areastyle_opts=opts.AreaStyleOpts(opacity=0.3, color="#00BFFF") 
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="单年各月份专利申请热度趋势", pos_left="center"),
                xaxis_opts=opts.AxisOpts(name="月份"),
                yaxis_opts=opts.AxisOpts(name="累计申请数量"),
                legend_opts=opts.LegendOpts(is_show=False)
            )
        )
        out_path = os.path.join(self.export_dir, 'monthly_trend.html')
        line.render(out_path)
        print(f"[UI 生成] 月度趋势图已保存至: {out_path}")

    def generate_nlp_charts(self):
        """生成标题关键词的词云和词频柱状图"""
        titles = self.df['title'].dropna().tolist()
        text = " ".join(titles)
        
        # 分词
        words = jieba.lcut(text)
        
        # 定义要屏蔽的无意义词汇
        stop_words = {# 中文无关词
        "一种", "装置", "方法", "系统", "设备", "用于", "及其", "基于", "的", "和", "与", "在", "中", "其", "及", "了", "进行", "实现",
        # 英文无关词 
        "and", "of", "for", "with", "is", "in", "to", "has", "as", "at", "on", "by", "from", "which", "the", "are", "that", "whose",
        "comprises", "comprising", "provided", "used", "using", "involves", "containing", "connected", "comprising", 
        "system", "method", "device", "unit", "module", "part"}
        
        # 过滤单字和停用词
        word_counts = Counter([w for w in words if len(w) > 1 and w not in stop_words])
        
        # 取 Top 100 做词云，Top 20 做柱状图
        top_100_words = word_counts.most_common(100)
        top_20_words = word_counts.most_common(20)

        if not top_100_words:
            print("警告：没有足够的标题关键词生成词云。")
            return

        # 1. 绘制词云
        wc = (
            WordCloud()
            .add("", top_100_words, word_size_range=[15, 80], shape="circle")
            .set_global_opts(title_opts=opts.TitleOpts(title="专利标题关键词云", pos_left="center"))
        )
        wc_path = os.path.join(self.export_dir, 'title_wordcloud.html')
        wc.render(wc_path)
        print(f"[UI 生成] 标题词云已保存至: {wc_path}")

        # 2. 绘制词频柱状图
        x_data = [w[0] for w in top_20_words]
        y_data = [w[1] for w in top_20_words]
        
        bar = (
            Bar()
            .add_xaxis(x_data)
            .add_yaxis("出现频次", y_data)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="专利标题高频词 Top 20", pos_left="center"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-45)), # 标签倾斜防重叠
                legend_opts=opts.LegendOpts(is_show=False)
            )
        )
        bar_path = os.path.join(self.export_dir, 'title_wordfreq_bar.html')
        bar.render(bar_path)
        print(f"[UI 生成] 标题词频图已保存至: {bar_path}")

    def generate_country_pie_charts(self):
        """按年份单独生成国家分布饼图"""
        valid_years = self.df['year'].dropna().unique()
        
        for year in sorted(valid_years):
            year_int = int(year)
            # 筛选当年的数据
            df_year = self.df[self.df['year'] == year_int]
            country_counts = df_year['country'].value_counts()
            
            if country_counts.empty:
                continue
                
            data_pair = [list(z) for z in zip(country_counts.index.tolist(), country_counts.values.tolist())]
            
            pie = (
                Pie()
                .add(
                    "",
                    data_pair,
                    radius=["30%", "70%"], # 设为环形图更好看一点
                    rosetype="radius",     # 南丁格尔玫瑰图效果
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=f"{year_int}年 专利国家/地区分布", pos_left="center"),
                    legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%")
                )
                .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c} ({d}%)"))
            )
            
            pie_path = os.path.join(self.export_dir, f'country_distribution_{year_int}.html')
            pie.render(pie_path)
            print(f"[UI 生成] {year_int}年国家分布饼图已保存至: {pie_path}")

    def build_network(self, edge_weights):
        """生成合作网络静态图片 (Matplotlib)"""
        if not edge_weights:
            print("没有足够的合作数据来生成网络图。")
            return None

        G = nx.Graph()
        for (node1, node2), weight in edge_weights.items():
            G.add_edge(node1, node2, weight=weight)
            
        plt.figure(figsize=(12, 10))
        
        pos = nx.spring_layout(G, k=0.8, seed=42) 
        degrees = dict(G.degree())
        node_sizes = [v * 150 + 300 for v in degrees.values()]
        
        edges = G.edges(data=True)
        edge_widths = [d['weight'] * 1.5 for u, v, d in edges]
        
        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color='#FFB6C1', alpha=0.9, edgecolors='white')
        nx.draw_networkx_edges(G, pos, width=edge_widths, edge_color='#A9A9A9', alpha=0.6)
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
        
        plt.title("申请人合作网络图", fontsize=18, fontweight='bold', pad=20)
        plt.axis('off') 
        plt.tight_layout()
        
        out_path = os.path.join(self.export_dir, 'co_applicant_network.png')
        plt.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"[UI 生成] 网络图已保存至: {out_path}")
        return G

    def save_dataframe(self, df):
        """一键落盘：明细表"""
        out_path = os.path.join(self.export_dir, 'cleaned_patent_data.csv')
        df.to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f"[数据导出] 清洗明细已保存至: {out_path}")

# ==========================================
# 主控引擎 (Pipeline Execution)
# ==========================================
def main():
    print("启动专利分析流水线...")
    
    # 1. 初始化
    miner = PatentMiner(input_dir='my_patents')
    df_clean = miner.batch_process()
    
    if df_clean.empty:
        print("未提取到有效数据。请确保当前目录下存在符合格式的 .txt 文件。")
        return

    print(f"成功提取 {len(df_clean)} 条专利记录！")

    # 2. 启动数据加工
    processor = PatentProcessor(df_clean)
    
    # 执行分析流程
    monthly_trend, ipc_counts = processor.analyze_basic()
    edge_weights = processor.analyze_co_occurrence()
    
    # 结果输出
    processor.visualize_trend(monthly_trend)       # 月度趋势图
    processor.generate_nlp_charts()                # 词云与词频图
    processor.generate_country_pie_charts()        # 按年度生成的国家饼图
    processor.build_network(edge_weights)          # 合作网络
    processor.save_dataframe(df_clean)             # 落盘（此时导出的CSV也包含了新增的year, month, country列）
    
    print(f"分析完成！所有图表和数据已保存至 {processor.export_dir} 文件夹。")

if __name__ == "__main__":
    main()
