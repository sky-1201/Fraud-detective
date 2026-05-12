# frontend/components/chat_stream.py
import streamlit as st
import requests
import time
from config import API_BASE_URL
from components.network_view import render_money_network


def render_investigation_panel():
    st.header("🕵️‍♂️ 步骤二：AI 专案组联合审讯")
    st.markdown("调用 LangGraph 探员，穿透 Neo4j 图谱网络并生成定罪报告。")

    # 🌟 初始化专属档案袋，防止刷新丢失
    if 'current_report' not in st.session_state:
        st.session_state.current_report = None
    if 'current_graph' not in st.session_state:
        st.session_state.current_graph = None
    if 'current_suspect' not in st.session_state:
        st.session_state.current_suspect = None

    default_id = st.session_state.get('selected_suspect', "")

    with st.form("investigate_form"):
        account_id = st.text_input("🎯 输入锁定的嫌疑人 ID", value=default_id, placeholder="例如: C1286084959")
        investigate_btn = st.form_submit_button("🔨 移交专案组发起定罪", use_container_width=True)

    # ==========================================
    # 动作层：只负责请求数据并存入档案袋
    # ==========================================
    if investigate_btn:
        if not account_id:
            st.warning("请先输入需要侦查的嫌疑人 ID！")
            return

        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("系统立案中...")
        progress_bar.progress(20)
        time.sleep(0.5)

        status_text.text("🕵️ 图谱探员正在穿透资金网络...")
        progress_bar.progress(50)

        try:
            # 1. 获取 AI 案件报告
            response = requests.post(
                f"{API_BASE_URL}/cases/investigate",
                json={"account_id": account_id.strip()}
            )

            # 2. 获取 Neo4j 真实网络数据
            graph_data = []
            try:
                graph_res = requests.get(f"{API_BASE_URL}/cases/network/{account_id.strip()}")
                if graph_res.status_code == 200:
                    graph_data = graph_res.json().get("data", [])
            except Exception as e:
                st.toast(f"图谱数据加载失败: {e}")

            status_text.text("🧠 首席分析师正在生成判决书...")
            progress_bar.progress(90)

            if response.status_code == 200:
                result = response.json()
                # 🌟 关键点：将成功获取的数据存入全局状态！
                st.session_state.current_report = result
                st.session_state.current_graph = graph_data
                st.session_state.current_suspect = account_id.strip()

                progress_bar.progress(100)
                status_text.empty()
                progress_bar.empty()
            else:
                progress_bar.empty()
                status_text.error(f"专案组执行失败: {response.text}")

        except Exception as e:
            progress_bar.empty()
            status_text.error(f"请求失败: {e}")

    # ==========================================
    # 渲染层：脱离按钮控制，只要档案袋有数据就渲染
    # ==========================================
    if st.session_state.current_report:
        result = st.session_state.current_report
        suspect_id = st.session_state.current_suspect
        graph_data = st.session_state.current_graph

        risk_level = result.get("risk_level", "UNKNOWN")
        risk_score = result.get("risk_score", 0)

        st.subheader("⚖️ 最终判决结果")
        if risk_level == "CRITICAL":
            st.error(f"**极高危 (CRITICAL)** | 危险指数: {risk_score}/100")
        elif risk_level == "HIGH":
            st.warning(f"**高危 (HIGH)** | 危险指数: {risk_score}/100")
        elif risk_level == "MEDIUM":
            st.info(f"**疑似异常 (MEDIUM)** | 危险指数: {risk_score}/100")
        else:
            st.success(f"**安全 (LOW)** | 危险指数: {risk_score}/100")

        # 渲染图谱
        render_money_network(account_id=suspect_id, raw_graph_data=graph_data)

        # 渲染报告
        with st.expander("📄 查看《反洗钱可疑交易结案报告》", expanded=True):
            st.markdown(result.get("report", "报告生成失败。"))