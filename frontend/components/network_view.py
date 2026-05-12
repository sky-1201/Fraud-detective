# frontend/components/network_view.py
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

def render_money_network(account_id: str, raw_graph_data: list = None):
    """
    N度深层资金图谱渲染引擎：支持复杂的链状、网状、多进一出闭环渲染
    """
    nodes = []
    edges = []
    added_nodes = set()

    # 1. 核心嫌疑人节点 (红色钻石)
    nodes.append(Node(id=account_id, label=f"🎯 目标\n{account_id}", size=35, color="#FF4B4B", symbolType="diamond", font={"size": 11, "color": "white"}))
    added_nodes.add(account_id)

    if raw_graph_data:
        # 🟢 渲染 N 度拓扑关系
        for record in raw_graph_data:
            source_id = record.get("source")
            target_id = record.get("target")
            amount = record.get("amount", 0)

            # 动态添加起始节点
            if source_id and source_id not in added_nodes:
                # 嫌疑人标红，其他节点标蓝
                color = "#FF4B4B" if source_id == account_id else "#1f77b4"
                nodes.append(Node(id=source_id, label=source_id, size=15, color=color, font={"size": 8}))
                added_nodes.add(source_id)

            # 动态添加目标节点
            if target_id and target_id not in added_nodes:
                color = "#FF4B4B" if target_id == account_id else "#1f77b4"
                nodes.append(Node(id=target_id, label=target_id, size=15, color=color, font={"size": 8}))
                added_nodes.add(target_id)

            # 添加资金流动连线
            if source_id and target_id:
                edges.append(Edge(source=source_id, target=target_id, label=f"${amount}", color="#90A4AE", font={"size": 7}))
    else:
        st.warning("⚠️ 暂未获取到真实图谱数据，已切换至拓扑演示模式。")
        for i in range(1, 4):
            victim_id = f"受害者_V00{i}"
            nodes.append(Node(id=victim_id, label=victim_id, size=15, color="#1f77b4"))
            edges.append(Edge(source=victim_id, target=account_id, label="汇入 💰", color="#00C853"))

    # ⚙️ 物理引擎配置升级
    config = Config(
        width="100%", height=500, directed=True,
        physics=True,
        hierarchical=False, # 也可以设为 True 看看极其壮观的层级树状流向！
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=False,
        nodeSpacing=120,    # 撑开网状结构
        linkLength=100
    )

    st.markdown("##### 🕸️ 深层洗钱网络穿透追踪 (N-Hop)")
    return agraph(nodes=nodes, edges=edges, config=config)