# backend/app/workflows/graph.py
from langgraph.graph import StateGraph, START, END
from backend.app.workflows.state import CaseState
from backend.app.workflows.nodes.investigator import investigator_node
from backend.app.workflows.nodes.analyst import analyst_node
from backend.app.workflows.nodes.reporter import reporter_node
from backend.app.core.logger import logger

# 1. 铺设案卷宗流转轨道
# 声明这个图纸中流转的数据结构必须严格遵守 CaseState 规范
workflow = StateGraph(CaseState)

# 2. 将探员配置到对应的工作站 (添加节点)
workflow.add_node("Investigator", investigator_node)
workflow.add_node("Analyst", analyst_node)
workflow.add_node("Reporter", reporter_node)

# 3. 规划标准的流水线流转路径 (添加有向边)
# 无论多少个嫌疑人，都必须严格遵守这套法定侦查程序
workflow.add_edge(START, "Investigator")    # 调度员派单 -> 图谱探员查证
workflow.add_edge("Investigator", "Analyst")# 图谱探员查证完毕 -> 提交给分析师定性
workflow.add_edge("Analyst", "Reporter")    # 分析师定性完毕 -> 提交给报告员写公文
workflow.add_edge("Reporter", END)          # 报告撰写完毕 -> 案卷封存 (END)

# 4. 熔铸成型，编译成可执行的 AI 引擎实例
# 在企业级应用中，图谱一旦编译完成，就可以被高并发调用
compiled_graph = workflow.compile()

logger.info("🗺️ LangGraph AI 专案组图纸拼装完毕并编译成功！流水线已通电准备就绪。")