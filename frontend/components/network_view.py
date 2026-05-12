# frontend/components/network_view.py
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config


def render_money_network(account_id: str, raw_graph_data: list = None):
    """
    将资金流水渲染为极其酷炫的动态物理关系图谱 (支持真实数据注入)
    """
    nodes = []
    edges = []
    added_nodes = set()

    # 1. 核心嫌疑人节点 (瘦身到 size=35，依然保持最醒目)
    nodes.append(Node(id=account_id, label=f"嫌疑人\n{account_id}", size=35, color="#FF4B4B", symbolType="diamond",font={"size": 11, "color": "white"}))
    added_nodes.add(account_id)

    if raw_graph_data:
        for record in raw_graph_data:
            partner_id = record.get("partner_id")
            amount = record.get("amount", 0)
            direction = record.get("direction")

            if partner_id and partner_id not in added_nodes:
                color = "#1f77b4" if direction == "INFLOW" else "#FFA000"
                # 关联节点 (瘦身到 size=15)
                nodes.append(Node(id=partner_id, label=partner_id, size=15, color=color,font={"size": 8}))
                added_nodes.add(partner_id)


            if direction == "INFLOW":
                edges.append(
                    Edge(source=partner_id, target=account_id, label=f"${amount}", color="#00C853", font={"size": 7}))
            elif direction == "OUTFLOW":
                edges.append(
                    Edge(source=account_id, target=partner_id, label=f"${amount}", color="#D50000", font={"size": 7}))

    else:
        st.warning("⚠️ 暂未获取到真实图谱数据，已切换至拓扑演示模式。")
        for i in range(1, 4):
            victim_id = f"受害者_V00{i}"
            nodes.append(Node(id=victim_id, label=victim_id, size=15, color="#1f77b4"))
            edges.append(Edge(source=victim_id, target=account_id, label="汇入 💰", color="#00C853"))

        for i in range(1, 3):
            mule_id = f"地下钱庄_M00{i}"
            nodes.append(Node(id=mule_id, label=mule_id, size=20, color="#FFA000"))
            edges.append(Edge(source=account_id, target=mule_id, label="转移 💸", color="#D50000"))

    # ⚙️ 优化物理引擎配置
    config = Config(
        width="100%", height=500, directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=False,
        # 增加一些节点间距，防止文字重叠
        nodeSpacing=100
    )

    st.markdown("##### 🕸️ 资金流向拓扑网络追踪")
    return agraph(nodes=nodes, edges=edges, config=config)