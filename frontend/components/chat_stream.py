# frontend/components/chat_stream.py
import streamlit as st
import requests
import time
from config import API_BASE_URL
from components.network_view import render_money_network


def render_investigation_panel():
    st.header("🕵️‍♂️ 步骤二：AI 专案组联合审讯 (异步集群版)")
    st.markdown("任务已分发至 Celery 后台集群，通过 Task ID 实时轮询，拒绝页面卡死！")

    # 🌟 1. 初始化所有需要的全局状态
    if 'current_report' not in st.session_state:
        st.session_state.current_report = None
    if 'current_graph' not in st.session_state:
        st.session_state.current_graph = None
    if 'current_suspect' not in st.session_state:
        st.session_state.current_suspect = None

    # 新增：用于记住异步任务的凭证
    if 'current_task_id' not in st.session_state:
        st.session_state.current_task_id = None
    if 'poll_count' not in st.session_state:
        st.session_state.poll_count = 0

    default_id = st.session_state.get('selected_suspect', "")

    with st.form("investigate_form"):
        account_id = st.text_input("🎯 输入锁定的嫌疑人 ID", value=default_id, placeholder="例如: C1286084959")
        investigate_btn = st.form_submit_button("🔨 移交专案组发起定罪", use_container_width=True)

    # ==========================================
    # 动作层 1：只负责发单，领取小票存入保险箱
    # ==========================================
    if investigate_btn:
        if not account_id:
            st.warning("请先输入需要侦查的嫌疑人 ID！")
            return

        try:
            # 发单前清空旧报告
            st.session_state.current_report = None
            st.session_state.current_graph = None
            st.session_state.poll_count = 0

            res = requests.post(
                f"{API_BASE_URL}/cases/investigate",
                json={"account_id": account_id.strip()}
            )

            if res.status_code == 200:
                task_data = res.json()
                # 🚀 核心关键：把 Task ID 存进全局状态，页面怎么刷新都不怕！
                st.session_state.current_task_id = task_data.get("task_id")
                st.session_state.current_suspect = account_id.strip()

                # 顺手把图谱数据拉回来
                try:
                    graph_res = requests.get(f"{API_BASE_URL}/cases/network/{account_id.strip()}")
                    if graph_res.status_code == 200:
                        st.session_state.current_graph = graph_res.json().get("data", [])
                except:
                    pass

                # 强制 Streamlit 重新加载页面，进入下方的轮询逻辑
                st.rerun()
            else:
                st.error(f"任务分发失败: {res.text}")
        except Exception as e:
            st.error(f"前端网络请求失败: {e}")

    # ==========================================
    # 动作层 2：页面重载触发的独立轮询器
    # ==========================================
    # 只要保险箱里有 Task ID，即使你刚点了雷达刷新了页面，它也会继续执行这里！
    if st.session_state.current_task_id:
        task_id = st.session_state.current_task_id
        st.session_state.poll_count += 1

        progress_bar = st.progress(min(10 + st.session_state.poll_count * 2, 95))
        st.info(f"🎫 凭证: {task_id[:8]}... | 🧠 专案组深度推理中 (第 {st.session_state.poll_count} 次轮询)")

        try:
            status_res = requests.get(f"{API_BASE_URL}/cases/status/{task_id}")
            if status_res.status_code == 200:
                status_info = status_res.json()
                current_status = status_info.get("status")

                if current_status == "success":
                    # ✅ 任务完成，保存报告，销毁排队小票
                    st.session_state.current_report = status_info.get("data", {})
                    st.session_state.current_task_id = None
                    st.success("✅ 判决书已生成！")
                    time.sleep(1)
                    st.rerun()  # 最后重载一次，展示报告

                elif current_status == "error":
                    # ❌ 任务报错，销毁排队小票
                    error_msg = status_info.get("message", "后台执行发生未知错误")
                    st.error(f"❌ 专案组执行失败: {error_msg}")
                    st.session_state.current_task_id = None

                else:
                    # ⏳ 还在处理中，让页面睡 2 秒后强制自我重载 (实现非 while 轮询)
                    time.sleep(2)
                    if st.session_state.poll_count < 60:
                        st.rerun()
                    else:
                        st.error("⏳ AI 思考时间过长，已超时。")
                        st.session_state.current_task_id = None
        except Exception as e:
            st.error(f"查询进度失败: {e}")
            time.sleep(2)
            st.rerun()  # 遇到网络波动，重试

    # ==========================================
    # 渲染层：只要有报告且当前不在排队中，就展示
    # ==========================================
    if st.session_state.current_report and not st.session_state.current_task_id:
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

        # 渲染动态资金图谱
        render_money_network(account_id=suspect_id, raw_graph_data=graph_data)

        # 渲染最终 SAR 报告
        with st.expander("📄 查看《反洗钱可疑交易结案报告》", expanded=True):
            st.markdown(result.get("report", "报告生成失败。"))