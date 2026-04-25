"""PatentSmelter Streamlit UI
Usage: streamlit run app.py
"""

import os
import subprocess
import platform
import pandas as pd
import streamlit as st

from patent_core import PatentMiner, PatentProcessor


# --------------- Helpers ---------------

def get_output_dir():
    out = os.path.abspath("./output")
    os.makedirs(out, exist_ok=True)
    return out


def parse_patents(input_dir: str):
    miner = PatentMiner(input_dir)
    raw_df = miner.batch_process()
    if raw_df.empty:
        return pd.DataFrame(), None
    processor = PatentProcessor(raw_df)
    processor._prepare_columns()
    return raw_df, processor


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


def run_analyses(df: pd.DataFrame) -> list:
    processor = PatentProcessor(df)
    processor._prepare_columns()
    out_dir = get_output_dir()
    chart_paths = []

    if st.session_state.get("do_trend", True):
        monthly_trend, _ = processor.compute_stats()
        processor.visualize_trend(monthly_trend)
        fp = os.path.join(out_dir, "monthly_trend.html")
        if os.path.exists(fp):
            chart_paths.append(fp)

    if st.session_state.get("do_nlp", True):
        processor.generate_nlp_charts()
        for name in ("title_wordcloud.html", "title_wordfreq_bar.html"):
            fp = os.path.join(out_dir, name)
            if os.path.exists(fp):
                chart_paths.append(fp)

    if st.session_state.get("do_pie", True):
        processor.generate_country_pie_charts()
        for fname in os.listdir(out_dir):
            if fname.startswith("country_distribution_") and fname.endswith(".html"):
                chart_paths.append(os.path.join(out_dir, fname))

    if st.session_state.get("do_network", False):
        edge_weights = processor.analyze_co_occurrence()
        processor.build_network(edge_weights)
        fp = os.path.join(out_dir, "co_applicant_network.png")
        if os.path.exists(fp):
            chart_paths.append(fp)

    if st.session_state.get("do_csv", False):
        processor.save_dataframe(processor.df)
        fp = os.path.join(out_dir, "cleaned_patent_data.csv")
        if os.path.exists(fp):
            chart_paths.append(fp)

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
            "available_ipcs", "available_years", "last_input_dir"):
    if key not in st.session_state:
        st.session_state[key] = None

# --------------- Page config ---------------

st.set_page_config(
    page_title="PatentSmelter",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------- Sidebar ---------------

with st.sidebar:
    st.title("PatentSmelter")

    input_dir = st.text_input("输入专利文件夹路径", value="./my_patents", key="input_dir")

    st.divider()
    st.subheader("分析选项")

    st.checkbox("月度趋势", value=True, key="do_trend")
    st.checkbox("词云词频", value=True, key="do_nlp")
    st.checkbox("国家分布饼图", value=True, key="do_pie")
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


# --------------- Main Panel ---------------

st.header("分析结果")

if run_clicked:
    # 校验至少选了一个分析项
    if not any([
        st.session_state.do_trend,
        st.session_state.do_nlp,
        st.session_state.do_pie,
        st.session_state.do_network,
        st.session_state.do_csv,
    ]):
        st.warning("请至少选择一个分析选项")
        st.stop()

    # 解析（缓存）
    with st.spinner("正在解析专利数据..."):
        if st.session_state.last_input_dir != input_dir:
            raw_df, processor = parse_patents(input_dir)
            if raw_df.empty:
                st.error(f"目录 '{input_dir}' 中没有找到有效专利数据")
                st.stop()
            st.session_state.raw_df = raw_df
            st.session_state.processor = processor
            st.session_state.last_input_dir = input_dir
            st.session_state.available_ipcs = extract_ipc_options(raw_df)
            yrs = sorted(raw_df["year"].dropna().unique().tolist())
            st.session_state.available_years = yrs if yrs else [2020]

    # 筛选
    with st.spinner("正在筛选数据..."):
        df_filtered = apply_filters(st.session_state.raw_df)
        if df_filtered.empty:
            st.warning("筛选条件下无数据，请扩大年份范围或调整 IPC 筛选条件")
            st.stop()

    # 分析
    with st.spinner("正在生成图表..."):
        chart_files = run_analyses(df_filtered)
        st.session_state.chart_files = chart_files

    st.success(f"分析完成！共生成 {len(chart_files)} 个文件")

# --------------- Results display ---------------

chart_files = st.session_state.get("chart_files", [])
if chart_files:
    st.subheader("生成的文件列表")

    for idx, fp in enumerate(chart_files):
        fname = os.path.basename(fp)
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text(fname)
        with col2:
            if st.button("查看", key=f"view_{idx}"):
                st.session_state.selected_chart = fp

    sel = st.session_state.get("selected_chart")
    if sel and os.path.exists(sel):
        st.divider()
        st.subheader("图表预览")
        if sel.endswith(".html"):
            with open(sel, "r", encoding="utf-8") as f:
                st.components.v1.html(f.read(), height=600, scrolling=True)
        elif sel.endswith(".png"):
            st.image(sel)
        elif sel.endswith(".csv"):
            st.dataframe(pd.read_csv(sel))
            with open(sel, "rb") as f:
                st.download_button("下载 CSV", data=f, file_name=os.path.basename(sel))

    st.divider()
    st.markdown(
        f'<a href="file://{get_output_dir()}" target="_blank">打开 output 文件夹</a>',
        unsafe_allow_html=True,
    )

else:
    st.info("在左侧设置参数后点击「开始分析」")
