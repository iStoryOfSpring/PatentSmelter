"""PatentSmelter Streamlit UI
Usage: streamlit run app.py
"""

import os
import subprocess
import platform
import time
import pandas as pd
import streamlit as st

from patent_core import PatentMiner, PatentProcessor

# ── 终端提示 ──────────────────────────────────────────────────────────
print("=" * 60)
print("  PatentSmelter 正在启动...")
print("  PatentSmelter is starting up...")
print("  请勿关闭此窗口 / Do NOT close this window")
print("=" * 60)

# --------------- Helpers ---------------

def get_output_dir():
    out = os.path.abspath("./output")
    os.makedirs(out, exist_ok=True)
    return out


def parse_patents(input_dir: str, stopwords_path=None):
    miner = PatentMiner(input_dir, stopwords_path=stopwords_path)
    raw_df = miner.batch_process()
    if raw_df.empty:
        return pd.DataFrame(), None, set()
    processor = PatentProcessor(raw_df)
    processor._prepare_columns()
    return raw_df, processor, miner.stopwords


def extract_ipc_options(df: pd.DataFrame) -> list:
    codes = set()
    for val in df["ipc"].dropna():
        for code in val.split(";"):
            c = code.strip()[:4]
            if c:
                codes.add(c)
    return sorted(codes)


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    y_start = st.session_state.get("year_start")
    y_end = st.session_state.get("year_end")
    if y_start is not None:
        df = df[df["year"] >= y_start]
    if y_end is not None:
        df = df[df["year"] <= y_end]

    ipc_sel = st.session_state.get("ipc_filter", [])
    if ipc_sel:
        mask = df["ipc"].apply(
            lambda x: any(ipc in str(x) for ipc in ipc_sel) if pd.notna(x) else False
        )
        df = df[mask]
    return df


# Mapping: session_state key → (display name, output filenames to check)
ANALYSIS_STEPS = [
    ("do_trend",         "月度趋势折线图",    ["monthly_trend.html"]),
    ("do_nlp",           "标题词云 & 词频",   ["title_wordcloud.html", "title_wordfreq_bar.html"]),
    ("do_pie",           "国家分布饼图",       None),  # dynamic: per year
    ("do_scurve",        "S 曲线生命周期",     ["s_curve.html"]),
    ("do_ipc_heatmap",   "IPC 热力图",         ["ipc_heatmap.html"]),
    ("do_yearly_keywords","逐年关键词对比",    ["yearly_keywords.html"]),
    ("do_abstract_nlp",  "摘要词云 & 词频",    ["abstract_wordcloud.html", "abstract_wordfreq_bar.html"]),
    ("do_burst",         "突发词检测",         ["burst_terms.html"]),
    ("do_bubble",        "成熟度气泡图",       ["bubble_chart.html"]),
    ("do_roadmap",       "技术路线图",         ["technology_roadmap.html"]),
    ("do_network",       "合作网络图",         ["co_applicant_network.png"]),
    ("do_csv",           "CSV 数据导出",       ["cleaned_patent_data.csv"]),
]


def run_analyses(df: pd.DataFrame, stopwords, progress_bar, status_text, time_warning) -> list:
    """Run all selected analyses and return paths of generated files."""
    processor = PatentProcessor(df, stopwords=stopwords)
    processor._prepare_columns()
    out_dir = get_output_dir()
    chart_paths = []

    # Count how many steps are enabled
    total_steps = sum(1 for key, _, _ in ANALYSIS_STEPS if st.session_state.get(key, False))
    if total_steps == 0:
        return []
    step_idx = 0

    def advance(msg):
        nonlocal step_idx
        step_idx += 1
        pct = int(step_idx / total_steps * 100)
        progress_bar.progress(pct)
        status_text.text(f"⏳ [{step_idx}/{total_steps}] {msg}")
        time.sleep(0.05)  # give Streamlit a chance to re-render

    # ── 1. 月度趋势 ──
    if st.session_state.get("do_trend", True):
        advance("生成月度趋势图...")
        monthly_trend, _ = processor.compute_stats()
        processor.visualize_trend(monthly_trend)
        fp = os.path.join(out_dir, "monthly_trend.html")
        if os.path.exists(fp):
            chart_paths.append(fp)

    # ── 2. 标题 NLP ──
    if st.session_state.get("do_nlp", True):
        advance("生成标题词云 & 词频...")
        processor.generate_nlp_charts()
        for name in ("title_wordcloud.html", "title_wordfreq_bar.html"):
            fp = os.path.join(out_dir, name)
            if os.path.exists(fp):
                chart_paths.append(fp)

    # ── 3. 国家分布饼图 ──
    if st.session_state.get("do_pie", True):
        advance("生成国家分布饼图...")
        processor.generate_country_pie_charts()
        for fname in os.listdir(out_dir):
            if fname.startswith("country_distribution_") and fname.endswith(".html"):
                chart_paths.append(os.path.join(out_dir, fname))

    # ── 4. S 曲线 ──
    if st.session_state.get("do_scurve", True):
        advance("拟合 S 曲线 & 识别生命周期阶段...")
        s_result = processor.fit_s_curve()
        stages = processor.identify_stages(s_result)
        processor.visualize_s_curve(s_result, stages)
        fp = os.path.join(out_dir, "s_curve.html")
        if os.path.exists(fp):
            chart_paths.append(fp)
    else:
        s_result = processor.fit_s_curve()
        stages = processor.identify_stages(s_result)

    # ── 5. IPC 热力图 ──
    if st.session_state.get("do_ipc_heatmap", True):
        advance("生成 IPC 热力图...")
        processor.generate_ipc_heatmap()
        fp = os.path.join(out_dir, "ipc_heatmap.html")
        if os.path.exists(fp):
            chart_paths.append(fp)

    # ── 6. 逐年关键词 ──
    if st.session_state.get("do_yearly_keywords", True):
        advance("分析逐年关键词...")
        yk = processor.analyze_text_by_year(processor.df, text_col='title', top_n=10)
        processor.generate_yearly_keyword_chart(yk)
        fp = os.path.join(out_dir, "yearly_keywords.html")
        if os.path.exists(fp):
            chart_paths.append(fp)

    # ── 7. 摘要 NLP ──
    if st.session_state.get("do_abstract_nlp", True):
        advance("生成摘要词云 & 词频...")
        processor.generate_abstract_nlp_charts()
        for name in ("abstract_wordcloud.html", "abstract_wordfreq_bar.html"):
            fp = os.path.join(out_dir, name)
            if os.path.exists(fp):
                chart_paths.append(fp)

    # ── 8. 突发词 ──
    if st.session_state.get("do_burst", False):
        advance("检测技术突发词...")
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
        fp = os.path.join(out_dir, "burst_terms.html")
        if os.path.exists(fp):
            chart_paths.append(fp)

    # ── 9. 气泡图 ──
    if st.session_state.get("do_bubble", False):
        advance("生成成熟度气泡图...")
        processor.generate_bubble_chart(s_result, stages)
        fp = os.path.join(out_dir, "bubble_chart.html")
        if os.path.exists(fp):
            chart_paths.append(fp)

    # ── 10. 技术路线图 ──
    if st.session_state.get("do_roadmap", False):
        advance("生成技术路线图时间轴...")
        processor.generate_roadmap_timeline(top_n_per_year=3)
        fp = os.path.join(out_dir, "technology_roadmap.html")
        if os.path.exists(fp):
            chart_paths.append(fp)

    # ── 11. 合作网络 ──
    if st.session_state.get("do_network", False):
        advance("构建申请人合作网络...")
        edge_weights = processor.analyze_co_occurrence()
        processor.build_network(edge_weights)
        fp = os.path.join(out_dir, "co_applicant_network.png")
        if os.path.exists(fp):
            chart_paths.append(fp)

    # ── 12. CSV 导出 ──
    if st.session_state.get("do_csv", False):
        advance("导出清洗数据 CSV...")
        processor.save_dataframe(processor.df)
        fp = os.path.join(out_dir, "cleaned_patent_data.csv")
        if os.path.exists(fp):
            chart_paths.append(fp)

    status_text.text("✅ 分析完成！")
    time_warning.empty()
    return chart_paths


def open_output_folder():
    path = get_output_dir()
    if platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    elif platform.system() == "Windows":
        os.startfile(path)  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", path])


# --------------- Session state defaults ---------------

for key in ("raw_df", "processor", "chart_files", "selected_chart",
            "available_ipcs", "available_years", "last_input_dir", "stopwords"):
    if key not in st.session_state:
        st.session_state[key] = None

# --------------- Page config ---------------

st.set_page_config(
    page_title="PatentSmelter",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------- Sidebar (left) — Controls ---------------

with st.sidebar:
    st.title("⚙️ PatentSmelter")

    input_dir = st.text_input("输入专利文件夹路径", value="./my_patents", key="input_dir")

    st.divider()
    st.subheader("分析选项")

    st.checkbox("月度趋势", value=True, key="do_trend")
    st.checkbox("词云词频", value=True, key="do_nlp")
    st.checkbox("国家分布饼图", value=True, key="do_pie")
    st.checkbox("S曲线生命周期", value=True, key="do_scurve")
    st.checkbox("IPC热力图", value=True, key="do_ipc_heatmap")
    st.checkbox("逐年关键词对比", value=True, key="do_yearly_keywords")
    st.checkbox("摘要词云词频", value=True, key="do_abstract_nlp")
    st.checkbox("突发词检测", value=False, key="do_burst")
    st.checkbox("成熟度气泡图", value=False, key="do_bubble")
    st.checkbox("技术路线图", value=False, key="do_roadmap")
    st.checkbox("合作网络", value=False, key="do_network")
    st.checkbox("导出CSV", value=False, key="do_csv")

    st.divider()
    st.subheader("筛选条件")

    years = st.session_state.get("available_years") or [2020]
    year_start = st.number_input("起始年份", 1900, 2039,
                                 value=int(min(years)), key="year_start")
    year_end = st.number_input("终止年份", 1900, 2039,
                               value=int(max(years)), key="year_end")

    ipc_opts = st.session_state.get("available_ipcs") or []
    st.multiselect("IPC 分类筛选（留空为全部）",
                   options=ipc_opts, default=[], key="ipc_filter")

    st.divider()
    run_clicked = st.button("开始分析", type="primary", use_container_width=True)


# --------------- Main Panel — Two column layout: center + right ---------------

st.header("📊 分析结果")

# Create the center (chart) + right (file list) columns
col_chart, col_files = st.columns([3, 1], gap="large")

# ── Right column: file list ──
with col_files:
    st.subheader("生成的文件")
    file_container = st.container()
    with file_container:
        chart_files = st.session_state.get("chart_files", [])
        if chart_files:
            for idx, fp in enumerate(chart_files):
                fname = os.path.basename(fp)
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.caption(fname)
                with col_b:
                    if st.button("查看", key=f"fview_{idx}", use_container_width=True):
                        st.session_state.selected_chart = fp
        else:
            st.info("分析完成后\n文件列表将出现在这里")

    st.divider()
    st.markdown(
        f'<a href="file://{get_output_dir()}" target="_blank">📂 打开 output 文件夹</a>',
        unsafe_allow_html=True,
    )

# ── Center column: chart preview ──
with col_chart:
    sel = st.session_state.get("selected_chart")
    if sel and os.path.exists(sel):
        st.subheader(f"📈 {os.path.basename(sel)}")
        if sel.endswith(".html"):
            with open(sel, "r", encoding="utf-8") as f:
                st.components.v1.html(f.read(), height=650, scrolling=True)
        elif sel.endswith(".png"):
            st.image(sel, use_container_width=True)
        elif sel.endswith(".csv"):
            st.dataframe(pd.read_csv(sel))
            with open(sel, "rb") as f:
                st.download_button("下载 CSV", data=f, file_name=os.path.basename(sel))
    else:
        st.info("在左侧设置参数后点击「开始分析」，\n然后在右侧文件列表中点击「查看」预览图表")

# --------------- Run Analysis Flow ---------------

if run_clicked:
    # Validate at least one option selected
    if not any([
        st.session_state.do_trend,
        st.session_state.do_nlp,
        st.session_state.do_pie,
        st.session_state.do_scurve,
        st.session_state.do_ipc_heatmap,
        st.session_state.do_yearly_keywords,
        st.session_state.do_abstract_nlp,
        st.session_state.do_burst,
        st.session_state.do_bubble,
        st.session_state.do_roadmap,
        st.session_state.do_network,
        st.session_state.do_csv,
    ]):
        st.warning("请至少选择一个分析选项")
        st.stop()

    # ── 解析（显示在 center 区域顶部） ──
    with col_chart:
        parse_placeholder = st.empty()

    with parse_placeholder.container():
        st.info("📖 正在解析专利数据...")

    if st.session_state.last_input_dir != input_dir:
        with parse_placeholder.container():
            with st.spinner("正在解析专利数据..."):
                raw_df, processor, stopwords = parse_patents(input_dir)
            if raw_df.empty:
                st.error(f"目录 '{input_dir}' 中没有找到有效专利数据")
                st.stop()
            st.session_state.raw_df = raw_df
            st.session_state.processor = processor
            st.session_state.stopwords = stopwords
            st.session_state.last_input_dir = input_dir
            st.session_state.available_ipcs = extract_ipc_options(raw_df)
            yrs = sorted(raw_df["year"].dropna().unique().tolist())
            st.session_state.available_years = yrs if yrs else [2020]

    # ── 筛选 ──
    with parse_placeholder.container():
        with st.spinner("正在筛选数据..."):
            df_filtered = apply_filters(st.session_state.raw_df)
        if df_filtered.empty:
            st.warning("筛选条件下无数据，请扩大年份范围或调整 IPC 筛选条件")
            st.stop()

    # ── 显示分析进度（center 区域） ──
    with col_chart:
        parse_placeholder.empty()

        time_warning = st.warning(
            "⏳ 分析可能需要几分钟，视专利数量而定。\n"
            "Analysis may take a few minutes, depending on the number of patents.\n"
            "请耐心等待，请勿刷新页面。"
        )
        progress_bar = st.progress(0, text="准备开始...")
        status_text = st.empty()

        chart_files = run_analyses(
            df_filtered,
            stopwords=st.session_state.stopwords,
            progress_bar=progress_bar,
            status_text=status_text,
            time_warning=time_warning,
        )
        st.session_state.chart_files = chart_files

        progress_bar.empty()
        status_text.empty()

    st.success(f"✅ 分析完成！共生成 {len(chart_files)} 个文件")

    # Re-run to refresh the file list in the right column
    st.rerun()
