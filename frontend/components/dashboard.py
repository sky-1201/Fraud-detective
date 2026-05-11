# frontend/components/dashboard.py
import streamlit as st
import requests
import pandas as pd
from config import API_BASE_URL


def render_radar_dashboard():
    st.header("📡 步骤一：雷达预警扫描")
    st.markdown("通过 MySQL 交易底座，扫描高频异常资金枢纽。")

    with st.form("radar_form"):
        col_t, col_l = st.columns(2)
        with col_t:
            threshold = st.number_input("扫描阈值 (最少交易笔数)", min_value=1, value=10, step=1)
        with col_l:
            limit = st.number_input("最大展示数量", min_value=1, value=50, step=1)

        scan_btn = st.form_submit_button("🚀 启动全景雷达", use_container_width=True)

    if scan_btn:
        with st.spinner("雷达深度扫描中..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/radar/scan",
                    json={"threshold": threshold, "limit": limit}
                )
                if response.status_code == 200:
                    data = response.json()
                    suspects = data.get("suspects", [])

                    if not suspects:
                        st.success("✅ 当前阈值下未发现高危异常账户。")
                    else:
                        st.warning(f"⚠️ 警报！锁定 {len(suspects)} 个高危目标！")
                        df = pd.DataFrame(suspects)
                        df.columns = ["嫌疑人 ID", "总交易笔数", "涉案总金额 ($)"]

                        # 核心联动逻辑：把第一个高危目标的 ID 存入全局状态，方便右侧组件直接读取
                        st.session_state['selected_suspect'] = df.iloc[0]["嫌疑人 ID"]

                        st.dataframe(df, use_container_width=True)
                        st.info("💡 提示：排名第一的嫌疑人 ID 已自动填入右侧审讯面板。")
                else:
                    st.error(f"雷达系统异常: {response.text}")
            except Exception as e:
                st.error(f"无法连接到后端服务器: {e}")