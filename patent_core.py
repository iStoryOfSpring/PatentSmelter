import os
import re
import logging
from datetime import datetime
import numpy as np
import pandas as pd
import networkx as nx
from collections import Counter
from itertools import combinations
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import jieba
jieba.setLogLevel(logging.WARNING)

from pyecharts import options as opts
from pyecharts.charts import Line, WordCloud, Bar, Pie, Timeline, Scatter
from pyecharts.commons.utils import JsCode

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 只配置一次 logging
if not logging.getLogger().hasHandlers():
    logging.basicConfig(filename='error_log.txt', level=logging.ERROR,
                        format='%(asctime)s - %(message)s')


class PatentMiner:
    def __init__(self, input_dir, stopwords_path=None, entity_map=None):
        self.input_dir = input_dir
        self.stopwords = set()
        if stopwords_path and os.path.exists(stopwords_path):
            with open(stopwords_path, 'r', encoding='utf-8') as f:
                self.stopwords = {line.strip() for line in f if line.strip()}
        self.entity_map = entity_map or {}

    def _clean_entity(self, name):
        name = name.strip()
        return self.entity_map.get(name, name)

    def parse_txt(self, filepath):
        patents = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                records = content.split('\nER\n')

                for record in records:
                    if not record.strip() or record.startswith('FN '):
                        continue

                    data = {}
                    pn_match = re.search(r'^PN\s+(.+)$', record, re.M)
                    data['patent_number'] = pn_match.group(1).strip() if pn_match else "Unknown"

                    ti_match = re.search(r'^TI\s+(.*?)(?=\n[A-Z]{2}\s|$)', record, re.S | re.M)
                    data['title'] = ti_match.group(1).replace('\n', ' ').strip() if ti_match else ""

                    ae_match = re.search(r'^AE\s+(.*?)(?=\n[A-Z]{2}\s|$)', record, re.S | re.M)
                    if ae_match:
                        ae_raw = ae_match.group(1)
                        applicants = re.findall(r'^(.*?)(?:\s\(|$)', ae_raw, re.M)
                        data['applicants'] = ';'.join([self._clean_entity(a) for a in applicants if a.strip()])
                    else:
                        data['applicants'] = ""

                    pd_match = re.search(r'^PD\s+\S+\s+(\d{2}\s[A-Z][a-z]{2}\s\d{4})', record, re.M)
                    if pd_match:
                        date_str = pd_match.group(1)
                        try:
                            data['date'] = datetime.strptime(date_str, '%d %b %Y').strftime('%Y-%m-%d')
                        except:
                            data['date'] = ""
                    else:
                        data['date'] = ""

                    ab_match = re.search(r'^AB\s+(.*?)(?=\n[A-Z]{2}\s|$)', record, re.S | re.M)
                    data['abstract'] = ab_match.group(1).replace('\n', ' ').strip() if ab_match else ""

                    ip_match = re.search(r'^IP\s+(.+)$', record, re.M)
                    data['ipc'] = ip_match.group(1).strip() if ip_match else ""

                    patents.append(data)

        except Exception as e:
            logging.error(f"解析文件 {filepath} 失败: {str(e)}")

        return pd.DataFrame(patents)

    def batch_process(self):
        all_data = []
        if not os.path.exists(self.input_dir):
            print(f"错误: 找不到目录 '{self.input_dir}'")
            return pd.DataFrame()

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


class PatentProcessor:
    def __init__(self, df, stopwords=None):
        self.df = df
        self.export_dir = './output'
        self.stopwords = stopwords or set()
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

    def _prepare_columns(self):
        self.df['year'] = pd.to_datetime(self.df['date'], errors='coerce').dt.year
        self.df['month'] = pd.to_datetime(self.df['date'], errors='coerce').dt.month
        self.df['country'] = self.df['patent_number'].astype(str).str.extract(r'^([A-Za-z]{2})')[0].fillna('Unknown').str.upper()

    def compute_stats(self):
        monthly_trend = (
            self.df.groupby(['year', 'month']).size()
            .reset_index(name='count')
            .sort_values(['year', 'month'])
        )
        all_ipcs = []
        for codes in self.df['ipc'].dropna():
            all_ipcs.extend([code.strip()[:4] for code in codes.split(';')])
        ipc_counts = Counter(all_ipcs)
        return monthly_trend, ipc_counts

    def analyze_co_occurrence(self):
        edge_weights = Counter()
        for apps in self.df['applicants'].dropna():
            app_list = [a.strip() for a in apps.split(';') if a.strip()]
            if len(app_list) >= 2:
                for combo in combinations(sorted(app_list), 2):
                    edge_weights[combo] += 1
        return edge_weights

    def visualize_trend(self, monthly_trend):
        labels = [f"{int(r['year'])}-{int(r['month']):02d}" for _, r in monthly_trend.iterrows()]
        counts = [int(r['count']) for _, r in monthly_trend.iterrows()]

        line = (
            Line(init_opts=opts.InitOpts(theme="dark", width="900px", height="500px"))
            .add_xaxis(xaxis_data=labels)
            .add_yaxis(
                series_name="专利申请量",
                y_axis=counts,
                is_smooth=True,
                label_opts=opts.LabelOpts(is_show=True),
                linestyle_opts=opts.LineStyleOpts(width=3, color="#00BFFF"),
                areastyle_opts=opts.AreaStyleOpts(opacity=0.3, color="#00BFFF")
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="各年份月份专利申请热度趋势", pos_left="center"),
                xaxis_opts=opts.AxisOpts(name="月份"),
                yaxis_opts=opts.AxisOpts(name="累计申请数量"),
                legend_opts=opts.LegendOpts(is_show=False)
            )
        )
        out_path = os.path.join(self.export_dir, 'monthly_trend.html')
        line.render(out_path)
        print(f"[UI 生成] 月度趋势图已保存至: {out_path}")

    def generate_nlp_charts(self):
        titles = self.df['title'].dropna().tolist()
        text = " ".join(titles)

        words = jieba.lcut(text)

        stop_words = {
            "一种", "装置", "方法", "系统", "设备", "用于", "及其", "基于", "的", "和", "与", "在", "中", "其", "及", "了", "进行", "实现",
            "and", "of", "for", "with", "is", "in", "to", "has", "as", "at", "on", "by", "from", "which", "the", "are", "that", "whose",
            "comprises", "comprising", "provided", "used", "using", "involves", "containing", "connected", "comprising",
            "system", "method", "device", "unit", "module", "part"
        }
        # merge external stopwords
        if self.stopwords:
            stop_words |= self.stopwords

        word_counts = Counter([w for w in words if len(w) > 1 and w not in stop_words])

        top_100_words = word_counts.most_common(100)
        top_20_words = word_counts.most_common(20)

        if not top_100_words:
            print("警告：没有足够的标题关键词生成词云。")
            return

        wc = (
            WordCloud()
            .add("", top_100_words, word_size_range=[15, 80], shape="circle")
            .set_global_opts(title_opts=opts.TitleOpts(title="专利标题关键词云", pos_left="center"))
        )
        wc_path = os.path.join(self.export_dir, 'title_wordcloud.html')
        wc.render(wc_path)
        print(f"[UI 生成] 标题词云已保存至: {wc_path}")

        x_data = [w[0] for w in top_20_words]
        y_data = [w[1] for w in top_20_words]

        bar = (
            Bar()
            .add_xaxis(x_data)
            .add_yaxis("出现频次", y_data)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="专利标题高频词 Top 20", pos_left="center"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-45)),
                legend_opts=opts.LegendOpts(is_show=False)
            )
        )
        bar_path = os.path.join(self.export_dir, 'title_wordfreq_bar.html')
        bar.render(bar_path)
        print(f"[UI 生成] 标题词频图已保存至: {bar_path}")

    def generate_country_pie_charts(self):
        valid_years = self.df['year'].dropna().unique()

        for year in sorted(valid_years):
            year_int = int(year)
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
                    radius=["30%", "70%"],
                    rosetype="radius",
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

    # ─── S-Curve Modeling ───────────────────────────────────────────────
    def fit_s_curve(self):
        """Fit logistic growth curve to cumulative patent counts per year."""
        yearly = self.df.groupby('year').size().reset_index(name='count')
        yearly = yearly.sort_values('year')
        years = yearly['year'].values
        counts = yearly['count'].values
        cumulative = np.cumsum(counts)

        # Logistic model: L / (1 + exp(-k*(x - x0)))
        def logistic(x, L, k, x0):
            return L / (1 + np.exp(-k * (x - x0)))

        # Normalize years for fitting stability
        year_norm = (years - years.mean()) / years.std()
        try:
            popt, _ = curve_fit(logistic, year_norm, cumulative,
                                p0=[cumulative[-1]*1.2, 1.0, 0.0],
                                maxfev=10000)
            fitted = logistic(year_norm, *popt)
        except (RuntimeError, ValueError):
            popt = None
            fitted = cumulative.copy()

        return {
            'years': years,
            'counts': counts,
            'cumulative': cumulative,
            'fitted': fitted,
            'params': popt,
        }

    def identify_stages(self, s_result):
        """Identify technology life cycle stages from S-curve data."""
        years = s_result['years']
        fitted = s_result['fitted']
        min_year = int(years.min())
        max_year = int(years.max())
        total = max_year - min_year

        # Compute approximate slope
        slopes = np.gradient(fitted)
        accel = np.gradient(slopes)

        # Heuristic thresholds
        cum = fitted
        max_cum = cum[-1] if cum[-1] > 0 else 1

        stages = []
        for i, y in enumerate(years):
            ratio = cum[i] / max_cum
            if ratio < 0.15 and slopes[i] < max(slopes) * 0.3:
                stages.append('萌芽期')
            elif ratio < 0.5 and slopes[i] > max(slopes) * 0.5:
                stages.append('成长期')
            elif ratio < 0.85 and slopes[i] > max(slopes) * 0.1:
                stages.append('成熟期')
            else:
                stages.append('衰退期')

        # Merge consecutive same-stage ranges
        ranges = []
        prev = None
        start = None
        for i, s in enumerate(stages):
            if s != prev:
                if prev is not None:
                    ranges.append((prev, int(years[start]), int(years[i-1])))
                start = i
                prev = s
        if prev is not None:
            ranges.append((prev, int(years[start]), int(years[-1])))

        return ranges

    def visualize_s_curve(self, s_result, stages):
        """Pyecharts line+scatter chart of S-curve with stage annotations."""
        from pyecharts.charts import Scatter, Line, EffectScatter
        years = [str(int(y)) for y in s_result['years']]
        cum = [round(c, 0) for c in s_result['cumulative']]
        fitted = [round(f, 0) for f in s_result['fitted']]

        # Build scatter for actual data
        scatter = (
            Scatter(init_opts=opts.InitOpts(theme="dark", width="900px", height="500px"))
            .add_xaxis(years)
            .add_yaxis("实际累计量", cum,
                       symbol_size=10,
                       label_opts=opts.LabelOpts(is_show=False))
        )

        line = (
            Line()
            .add_xaxis(years)
            .add_yaxis("S曲线拟合", fitted,
                       is_smooth=True,
                       linestyle_opts=opts.LineStyleOpts(width=3, color="#FFD700"),
                       label_opts=opts.LabelOpts(is_show=False))
        )

        stage_colors = {
            '萌芽期': '#87CEEB',
            '成长期': '#32CD32',
            '成熟期': '#FFA500',
            '衰退期': '#FF6B6B',
        }

        # Add stage annotations as mark areas
        mark_areas = []
        for stage_name, sy, ey in stages:
            color = stage_colors.get(stage_name, '#888888')
            mark_areas.append(
                opts.MarkAreaItem(
                    name=stage_name,
                    x=(str(sy), str(ey)),
                    itemstyle_opts=opts.ItemStyleOpts(
                        color=color, opacity=0.15,
                    ),
                    label_opts=opts.LabelOpts(
                        position='top',
                        formatter=stage_name,
                        color=color,
                        font_weight='bold',
                    )
                )
            )

        if mark_areas:
            line.set_series_opts(
                markarea_opts=opts.MarkAreaOpts(
                    data=mark_areas,
                )
            )

        chart = (
            scatter
            .overlap(line)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="技术生命周期 S 曲线", pos_left="center"),
                xaxis_opts=opts.AxisOpts(name="年份", type_="category"),
                yaxis_opts=opts.AxisOpts(name="累计专利申请量"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                legend_opts=opts.LegendOpts(pos_top="bottom"),
            )
        )
        out_path = os.path.join(self.export_dir, 's_curve.html')
        chart.render(out_path)
        print(f"[UI 生成] S曲线已保存至: {out_path}")

    # ─── IPC Heatmap ────────────────────────────────────────────────────
    def generate_ipc_heatmap(self):
        """Year × IPC section heatmap using pyecharts."""
        from pyecharts.charts import HeatMap

        ipc_data = []
        for _, row in self.df.iterrows():
            year = row.get('year')
            ipc_str = row.get('ipc', '')
            if pd.isna(year) or not ipc_str:
                continue
            # Extract top-level IPC sections (first character before hyphen)
            for code in str(ipc_str).split(';'):
                section = code.strip()[0] if code.strip() else ''
                if section and section.isalpha():
                    ipc_data.append((int(year), section))

        if not ipc_data:
            print("[跳过] 没有足够的 IPC 数据生成热力图")
            return

        df_ipc = pd.DataFrame(ipc_data, columns=['year', 'section'])
        pivot = df_ipc.pivot_table(index='year', columns='section',
                                    aggfunc='size', fill_value=0)

        # Build heatmap data
        years_sorted = sorted(pivot.index.tolist())
        sections_sorted = sorted(pivot.columns.tolist())
        heat_data = []
        for y in years_sorted:
            for s in sections_sorted:
                heat_data.append([str(y), s, int(pivot.loc[y, s])])

        max_val = max(v[2] for v in heat_data) if heat_data else 1

        heat = (
            HeatMap(init_opts=opts.InitOpts(theme="dark", width="900px", height="500px"))
            .add_xaxis([str(y) for y in years_sorted])
            .add_yaxis(
                "IPC 分类",
                sections_sorted,
                heat_data,
                label_opts=opts.LabelOpts(is_show=True, position="inside",
                                           formatter="{c}", font_size=10)
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="IPC 分类年分布热力图", pos_left="center"),
                xaxis_opts=opts.AxisOpts(name="年份", type_="category", splitarea_opts=opts.SplitAreaOpts(is_show=True)),
                yaxis_opts=opts.AxisOpts(name="IPC 部", type_="category", splitarea_opts=opts.SplitAreaOpts(is_show=True)),
                visualmap_opts=opts.VisualMapOpts(
                    min_=0, max_=max_val,
                    range_color=["#F5F5F5", "#C6E48B", "#7BC96F", "#239A3B", "#196127"]
                ),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )
        out_path = os.path.join(self.export_dir, 'ipc_heatmap.html')
        heat.render(out_path)
        print(f"[UI 生成] IPC热力图已保存至: {out_path}")

    # ─── Burst Terms Detection ──────────────────────────────────────────
    def detect_burst_terms(self, yearly_texts, top_n=20):
        """Detect burst terms — words with abnormally increasing frequency."""
        years = sorted(yearly_texts.keys())
        if len(years) < 3:
            print("[跳过] 年份不足，无法检测突发词（至少需要3年数据）")
            return []

        mid = len(years) // 2
        early_years = years[:mid]
        late_years = years[mid:]

        def tokenize_and_count(text):
            words = jieba.lcut(text.lower())
            # Filter short and stopwords
            sw = {'的', '了', '在', '和', '与', '及', '或', '是', '有', '不',
                  '中', 'the', 'a', 'an', 'and', 'of', 'to', 'in', 'for',
                  'with', 'is', 'at', 'on', 'by', 'from', 'that', 'which',
                  'comprises', 'comprising', 'provided', 'used', 'using',
                  'method', 'system', 'device', 'apparatus'}
            return Counter([w for w in words if len(w) > 2 and w not in sw])

        early_text = ' '.join(str(yearly_texts.get(y, '')) for y in early_years)
        late_text = ' '.join(str(yearly_texts.get(y, '')) for y in late_years)

        early_counts = tokenize_and_count(early_text)
        late_counts = tokenize_and_count(late_text)

        total_early = sum(early_counts.values()) or 1
        total_late = sum(late_counts.values()) or 1

        scores = []
        all_words = set(list(early_counts.keys()) + list(late_counts.keys()))
        for word in all_words:
            ef = early_counts.get(word, 0) / total_early * 1e6
            lf = late_counts.get(word, 0) / total_late * 1e6
            burst = (lf + 1) / (ef + 1)  # add smoothing
            scores.append((word, burst, ef, lf))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_n]

    def visualize_burst_terms(self, burst_data):
        """Pyecharts horizontal bar chart of burst terms."""
        if not burst_data:
            return

        from pyecharts.charts import Bar

        terms = [b[0] for b in burst_data][::-1]
        scores = [b[1] for b in burst_data][::-1]

        bar = (
            Bar(init_opts=opts.InitOpts(theme="dark", width="900px", height="600px"))
            .add_xaxis(terms)
            .add_yaxis(
                "突发强度",
                [round(s, 2) for s in scores],
                label_opts=opts.LabelOpts(position="right", formatter="{c}"),
                itemstyle_opts=opts.ItemStyleOpts(color="#FF4500"),
            )
            .reversal_axis()
            .set_global_opts(
                title_opts=opts.TitleOpts(title="技术突发词 Top 20", pos_left="center"),
                xaxis_opts=opts.AxisOpts(name="突发强度"),
                yaxis_opts=opts.AxisOpts(name="关键词", type_="category"),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )
        out_path = os.path.join(self.export_dir, 'burst_terms.html')
        bar.render(out_path)
        print(f"[UI 生成] 突发词图已保存至: {out_path}")

    # ─── Yearly Keyword Comparison ──────────────────────────────────────
    def analyze_text_by_year(self, df, text_col='title', top_n=10):
        """Return {year: [(word, count), ...]} for top keywords per year."""
        from collections import defaultdict
        yearly = defaultdict(list)
        stop_words = {
            "一种", "装置", "方法", "系统", "设备", "用于", "及其", "基于",
            "的", "和", "与", "在", "中", "其", "及", "了", "进行", "实现",
            "and", "of", "for", "with", "is", "in", "to", "has", "as",
            "at", "on", "by", "from", "which", "the", "are", "that", "whose",
            "comprises", "comprising", "provided", "used", "using",
            "involves", "containing", "connected", "comprising",
            "system", "method", "device", "unit", "module", "part"
        }

        for _, row in df.iterrows():
            year = row.get('year')
            text = row.get(text_col, '')
            if pd.isna(year) or not text:
                continue
            words = jieba.lcut(str(text).lower())
            filtered = [w for w in words if len(w) > 1 and w not in stop_words]
            yearly[int(year)].extend(filtered)

        result = {}
        for year, words in sorted(yearly.items()):
            result[year] = Counter(words).most_common(top_n)
        return result

    def generate_yearly_keyword_chart(self, yearly_counts):
        """Pyecharts grouped bar chart comparing top keywords across selected years."""
        if not yearly_counts:
            return

        from pyecharts.charts import Bar

        years = sorted(yearly_counts.keys())

        # Collect all unique top keywords across selected years
        all_keywords = set()
        for y in years:
            for word, _ in yearly_counts[y]:
                all_keywords.add(word)
        all_keywords = sorted(all_keywords)

        bar = (
            Bar(init_opts=opts.InitOpts(theme="dark", width="1000px", height="500px"))
            .add_xaxis(all_keywords if len(all_keywords) <= 15 else all_keywords[:15])
        )

        colors = ['#00BFFF', '#FFD700', '#32CD32', '#FF6347', '#9370DB',
                  '#FF69B4', '#20B2AA', '#FFA500', '#87CEEB', '#98FB98']
        for i, year in enumerate(years):
            wdict = dict(yearly_counts[year])
            vals = [wdict.get(w, 0) for w in (all_keywords if len(all_keywords) <= 15 else all_keywords[:15])]
            bar.add_yaxis(
                str(year), vals,
                color=colors[i % len(colors)],
                label_opts=opts.LabelOpts(is_show=False),
            )

        bar.set_global_opts(
            title_opts=opts.TitleOpts(title="逐年关键词对比 (Top 15)", pos_left="center"),
            xaxis_opts=opts.AxisOpts(name="关键词", axislabel_opts=opts.LabelOpts(rotate=-45)),
            yaxis_opts=opts.AxisOpts(name="频次"),
            legend_opts=opts.LegendOpts(pos_top="bottom"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
        )
        out_path = os.path.join(self.export_dir, 'yearly_keywords.html')
        bar.render(out_path)
        print(f"[UI 生成] 逐年关键词对比图已保存至: {out_path}")

    # ─── Bubble Chart ───────────────────────────────────────────────────
    def generate_bubble_chart(self, s_result, stages):
        """Bubble chart: x=year, y=maturity, size=count, color=stage."""
        from pyecharts.charts import Scatter
        from pyecharts.commons.utils import JsCode

        years = s_result['years']
        counts = s_result['counts']
        fitted = s_result['fitted']
        max_fitted = fitted[-1] if fitted[-1] > 0 else 1
        maturity = fitted / max_fitted

        stage_colors = {
            '萌芽期': '#87CEEB',
            '成长期': '#32CD32',
            '成熟期': '#FFA500',
            '衰退期': '#FF6B6B',
        }

        # Build per-year stage lookup
        year_stage = {}
        for stage_name, sy, ey in stages:
            for y in range(sy, ey + 1):
                year_stage[y] = stage_name

        data = []
        for i, y in enumerate(years):
            stage = year_stage.get(int(y), '未知')
            color = stage_colors.get(stage, '#888888')
            data.append([
                int(y),
                round(float(maturity[i]), 3),
                int(counts[i]),
                stage,
                color,
            ])

        scatter = (
            Scatter(init_opts=opts.InitOpts(theme="dark", width="900px", height="500px"))
            .add_xaxis([d[0] for d in data])
            .add_yaxis(
                "专利气泡",
                [d[1] for d in data],
                symbol_size=JsCode(
                    "function(val) { return Math.max(5, val[2] / 2); }"
                ),
                label_opts=opts.LabelOpts(
                    is_show=True,
                    formatter=JsCode(
                        "function(p) { return p.value[0] + ': ' + p.data[3]; }"
                    ),
                    position="top",
                ),
                itemstyle_opts=opts.ItemStyleOpts(
                    color=JsCode(
                        "function(p) { return p.data[4]; }"
                    ),
                ),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="技术成熟度气泡图", pos_left="center"),
                xaxis_opts=opts.AxisOpts(name="年份", type_="value"),
                yaxis_opts=opts.AxisOpts(
                    name="技术成熟度",
                    min_=0, max_=1,
                    splitarea_opts=opts.SplitAreaOpts(is_show=True)
                ),
                legend_opts=opts.LegendOpts(is_show=False),
                tooltip_opts=opts.TooltipOpts(
                    formatter=JsCode(
                        "function(p) { return '年份: ' + p.value[0] + '<br/>成熟度: ' + p.value[1] + '<br/>申请量: ' + p.data[2] + '<br/>阶段: ' + p.data[3]; }"
                    ),
                ),
            )
        )
        out_path = os.path.join(self.export_dir, 'bubble_chart.html')
        scatter.render(out_path)
        print(f"[UI 生成] 气泡图已保存至: {out_path}")

    # ─── Technology Roadmap Timeline ────────────────────────────────────
    def generate_roadmap_timeline(self, top_n_per_year=3):
        """Pyecharts Timeline showing top patents per year."""
        df = self.df.copy()
        df['year'] = pd.to_datetime(df['date'], errors='coerce').dt.year

        years = sorted(df['year'].dropna().unique())
        if not len(years):
            print("[跳过] 没有年份数据生成技术路线图")
            return

        timeline = Timeline(
            init_opts=opts.InitOpts(theme="dark", width="1000px", height="500px")
        )

        for year in years:
            df_year = df[df['year'] == year].head(top_n_per_year)
            patents = df_year['patent_number'].tolist()
            titles = [str(t)[:60] + '...' if len(str(t)) > 60 else str(t)
                      for t in df_year['title'].tolist()]

            if not titles:
                continue

            # Build label data as paired text
            label_texts = [f"{p}: {t}" for p, t in zip(patents, titles)]

            bar = (
                Bar()
                .add_xaxis(label_texts[::-1])
                .add_yaxis(
                    "核心专利",
                    list(range(len(titles), 0, -1)),
                    label_opts=opts.LabelOpts(
                        is_show=True,
                        position="right",
                        formatter="{b}",
                        font_size=10,
                    ),
                    itemstyle_opts=opts.ItemStyleOpts(color="#00BFFF"),
                )
                .reversal_axis()
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=f"{int(year)} 年核心技术专利"),
                    xaxis_opts=opts.AxisOpts(is_show=False),
                    yaxis_opts=opts.AxisOpts(name="专利", type_="category"),
                    legend_opts=opts.LegendOpts(is_show=False),
                )
            )
            timeline.add(bar, str(int(year)))

        timeline.add_schema(
            is_auto_play=True,
            play_interval=2000,
            pos_left="center",
        )
        out_path = os.path.join(self.export_dir, 'technology_roadmap.html')
        timeline.render(out_path)
        print(f"[UI 生成] 技术路线图已保存至: {out_path}")

    # ─── Abstract NLP ──────────────────────────────────────────────────
    def generate_abstract_nlp_charts(self):
        """Generate word cloud and bar chart from AB (abstract) field."""
        abstracts = self.df['abstract'].dropna().tolist()
        if not abstracts:
            print("[跳过] 没有摘要数据")
            return

        text = " ".join(abstracts)
        words = jieba.lcut(text)

        stop_words = {
            "一种", "装置", "方法", "系统", "设备", "用于", "及其", "基于",
            "的", "和", "与", "在", "中", "其", "及", "了", "进行", "实现",
            "and", "of", "for", "with", "is", "in", "to", "has", "as",
            "at", "on", "by", "from", "which", "the", "are", "that", "whose",
            "comprises", "comprising", "provided", "used", "using",
            "involves", "containing", "connected",
            "system", "method", "device", "unit", "module", "part",
            "novelty", "use", "advantage", "description", "claim", "drawing",
            "independent", "preferred", "including", "comprising", "example",
        }

        word_counts = Counter([w for w in words if len(w) > 1 and w not in stop_words])
        top_100 = word_counts.most_common(100)
        top_20 = word_counts.most_common(20)

        if not top_100:
            return

        wc = (
            WordCloud()
            .add("", top_100, word_size_range=[15, 80], shape="circle")
            .set_global_opts(title_opts=opts.TitleOpts(title="摘要关键词云", pos_left="center"))
        )
        wc_path = os.path.join(self.export_dir, 'abstract_wordcloud.html')
        wc.render(wc_path)
        print(f"[UI 生成] 摘要词云已保存至: {wc_path}")

        bar = (
            Bar()
            .add_xaxis([w[0] for w in top_20])
            .add_yaxis("出现频次", [w[1] for w in top_20])
            .set_global_opts(
                title_opts=opts.TitleOpts(title="摘要高频词 Top 20", pos_left="center"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-45)),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )
        bar_path = os.path.join(self.export_dir, 'abstract_wordfreq_bar.html')
        bar.render(bar_path)
        print(f"[UI 生成] 摘要词频图已保存至: {bar_path}")

    def build_network(self, edge_weights):
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
        out_path = os.path.join(self.export_dir, 'cleaned_patent_data.csv')
        df.to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f"[数据导出] 清洗明细已保存至: {out_path}")


def main():
    print("启动专利分析流水线...")

    miner = PatentMiner(input_dir='my_patents')
    df_clean = miner.batch_process()

    if df_clean.empty:
        print("未提取到有效数据。请确保当前目录下存在符合格式的 .txt 文件。")
        return

    print(f"成功提取 {len(df_clean)} 条专利记录！")

    processor = PatentProcessor(df_clean, stopwords=miner.stopwords)
    processor._prepare_columns()

    monthly_trend, ipc_counts = processor.compute_stats()
    edge_weights = processor.analyze_co_occurrence()

    processor.visualize_trend(monthly_trend)
    processor.generate_nlp_charts()
    processor.generate_country_pie_charts()

    # ── 新增分析 ──
    # S-Curve
    s_result = processor.fit_s_curve()
    stages = processor.identify_stages(s_result)
    processor.visualize_s_curve(s_result, stages)

    # IPC Heatmap
    processor.generate_ipc_heatmap()

    # Yearly keywords
    yk = processor.analyze_text_by_year(processor.df, text_col='title', top_n=10)
    processor.generate_yearly_keyword_chart(yk)

    # Burst terms
    yearly_texts = {}
    for _, row in processor.df.iterrows():
        yr = row.get('year')
        title = row.get('title', '')
        ab = row.get('abstract', '')
        if pd.notna(yr):
            yr_int = int(yr)
            yearly_texts.setdefault(yr_int, '')
            yearly_texts[yr_int] += f" {title} {ab}"
    burst = processor.detect_burst_terms(yearly_texts, top_n=20)
    processor.visualize_burst_terms(burst)

    # Bubble chart
    processor.generate_bubble_chart(s_result, stages)

    # Technology roadmap
    processor.generate_roadmap_timeline(top_n_per_year=3)

    # Abstract NLP
    processor.generate_abstract_nlp_charts()

    processor.build_network(edge_weights)
    processor.save_dataframe(df_clean)

    print(f"分析完成！所有图表和数据已保存至 {processor.export_dir} 文件夹。")


if __name__ == "__main__":
    main()
