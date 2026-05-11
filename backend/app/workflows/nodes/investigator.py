# backend/app/workflows/nodes/investigator.py
from langchain_core.messages import AIMessage
from backend.app.workflows.state import CaseState
from backend.app.tools.graph_tool import FraudGraphTool
from backend.app.core.logger import logger

# 实例化图谱工具（在节点外部实例化，实现单例复用）
graph_tool = FraudGraphTool()


async def investigator_node(state: CaseState) -> dict:
    """
    侦查员节点逻辑：
    负责前往 Neo4j 图数据库进行资金链路穿透，并将发现的证据存入案卷。
    """
    suspect_id = state["suspect_id"]
    logger.info(f"🕵️ [Node: Investigator] 收到任务，开始审理嫌疑人: {suspect_id}")

    try:
        # 1. 调用图谱穿透工具
        # 该工具内部会完成：Cypher查询 -> LLM特征总结
        evidence = graph_tool.investigate(suspect_id)

        # 2. 准备侦查简报（添加到对话历史中）
        investigation_log = AIMessage(
            content=f"【侦查员简报】已完成对账户 {suspect_id} 的图谱穿透。发现该账户存在以下特征：\n{evidence}"
        )

        # 3. 返回更新后的状态碎片
        # 注意：在 LangGraph 中，只需返回你想要修改的字段
        return {
            "graph_evidence": evidence,
            "messages": [investigation_log]  # 触发 operator.add，实现日志追加
        }

    except Exception as e:
        error_msg = f"❌ [Investigator Error] 侦查过程中出现技术故障: {str(e)}"
        logger.error(error_msg)

        return {
            "graph_evidence": "侦查失败：内部系统错误",
            "messages": [AIMessage(content=error_msg)]
        }