# frontend/components/chat_stream.py
import streamlit as st
import requests
import time
from config import API_BASE_URL

def render_investigation_panel():
    st.header("🕵️‍♂️ 步骤二：AI 专案组联合审讯")
    st.markdown("调用 LangGraph 探员，穿透 Neo4j 图谱网络并生成定罪报告。")

    # 从 session_state 中获取默认 ID（如果雷达已经扫描到了的话）
    default_id = st.session_state.get('selected_suspect', "")

    with st.form("investigate_form"):
        account_id = st.text_input("🎯 输入锁定的嫌疑人 ID", value=default_id, placeholder="例如: C1286084959")
        investigate_btn = st.form_submit_button("🔨 移交专案组发起定罪", use_container_width=True)

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
            response = requests.post(
                f"{API_BASE_URL}/cases/investigate",
                json={"account_id": account_id.strip()}
            )

            status_text.text("🧠 首席分析师正在生成判决书...")
            progress_bar.progress(90)

            if response.status_code == 200:
                result = response.json()
                progress_bar.progress(100)
                status_text.empty()

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

                with st.expander("📄 查看《反洗钱可疑交易结案报告》", expanded=True):
                    st.markdown(result.get("report", "报告生成失败。"))

            else:
                progress_bar.empty()
                status_text.error(f"专案组执行失败: {response.text}")

        except Exception as e:
            progress_bar.empty()
            status_text.error(f"请求失败: {e}")