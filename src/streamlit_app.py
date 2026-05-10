# src/streamlit_app.py
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import requests
import json

# 配置 API 地址
API_URL = "http://127.0.0.1:8000/api/investigate"

# 1. 页面配置
st.set_page_config(page_title="智能反欺诈追踪探长", layout="wide", page_icon="🕵️‍♂️")
st.title("🕵️‍♂️ 智能反欺诈追踪探长 (前后端分离版)")
st.markdown("---")

# 2. 侧边栏
with st.sidebar:
    st.header("⚙️ 监控中心")
    st.success("FastAPI 后端引擎：连接正常")
    if st.button("清除缓存"):
        st.session_state.clear()
        st.rerun()

# 3. 主界面输入区
query = st.text_input("请输入调查指令：", placeholder="例如：帮我查一下向账户 C1286084959 转账的潜在风险...")

if query:
    final_report = "报告未生成"
    score = 0
    raw_evidence = ""

    # 动态状态容器
    with st.status("🚨 专案组已接警，开始跨部门协作...", expanded=True) as status:

        try:
            # 发送请求到 FastAPI 后端，开启 stream=True 以接收流式数据
            response = requests.post(API_URL, json={"query": query}, stream=True)

            # 实时解析后端吐出来的数据流行
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    event = json.loads(decoded_line)

                    # 遍历返回的节点事件，动态更新前端 UI
                    for node_name, state_update in event.items():

                        if node_name == "investigator":
                            raw_evidence = state_update.get("raw_evidence", "")
                            st.write("🕵️‍♂️ **侦查员**：已完成图数据库穿透取证。")
                            with st.expander("查看底层图谱数据 (Cypher 回调)"):
                                st.code(raw_evidence, language="json")

                        elif node_name == "analyst":
                            score = state_update.get("risk_score", 0)
                            analysis = state_update.get("risk_analysis_details", "")
                            st.write(f"🧠 **分析师**：发现高危特征，风险评分为 {score} 分。")
                            with st.expander("查看专家风控推理过程"):
                                st.markdown(analysis)

                        elif node_name == "reporter":
                            st.write("✍️ **报告员**：融合所有线索，结案报告撰写完毕！")
                            final_report = state_update.get("final_report", "")

            status.update(label="✅ 案件调查流转完毕！", state="complete", expanded=False)

        except requests.exceptions.ConnectionError:
            status.update(label="❌ 后端 API 未启动！请检查 FastAPI 是否运行。", state="error")
            st.stop()

    # 4. 结果展示区
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📜 最终红头结案报告")
        st.info(final_report)

    with col2:
        st.subheader("🕸️ 资金图谱快照")
        if score >= 80:
            st.error("🚨 警告：系统判定极高洗钱风险！")
        elif score >= 50:
            st.warning("⚠️ 提示：系统判定中等风险，请关注。")
        else:
            st.success("✅ 提示：当前暂未发现高危特征。")

        # 演示图谱节点，你可以写解析 raw_evidence 的逻辑来动态生成
        nodes = [Node(id="Target", label="目标账户", size=400, color="#FF4B4B")]
        edges = []
        config = Config(width=500, height=400, directed=True, nodeHighlightBehavior=True)
        agraph(nodes=nodes, edges=edges, config=config)