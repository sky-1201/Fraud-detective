# backend/app/workflows/state.py
import operator
from typing import Annotated, TypedDict, Optional
from langchain_core.messages import BaseMessage


class CaseState(TypedDict):
    """
     企业级 AI 专案组案卷宗 (LangGraph Global State)

    这是在图谱探员、风控分析师、结案报告员之间流转的唯一数据结构。
    """

    # ==========================================
    #  卷宗封面：案件基础信息 (立案时由调度员填入)
    # ==========================================
    suspect_id: str

    # ==========================================
    #  内部通讯录：Agent 思考与对话记录
    # LangGraph 标准规范：使用 operator.add 实现列表的 Append-Only (只追加不覆盖)
    # ==========================================
    messages: Annotated[list[BaseMessage], operator.add]    #operator.add追加信息，没有这个参数就直接覆盖了

    # ==========================================
    #  证据收集袋：各路探员取证后的存放处
    # ==========================================
    # 图谱探员使用 graph_tool 查回来的资金网络结构化情报
    graph_evidence: Optional[str]

    # (架构师预留) 未来如果需要 SQL 探员去 MySQL 查历史 KYC 资料，存放在这里
    sql_evidence: Optional[str]

    # ==========================================
    # ⚖ 法庭判决书：分析师 (Analyst) 填入的定性结论
    # ==========================================
    risk_score: Optional[int]  # 风险指数 (0-100)
    risk_level: Optional[str]  # 风险等级 (LOW, MEDIUM, HIGH, CRITICAL)
    reasoning: Optional[str]  # 判决依据的思维链 (Chain of Thought)，方便审计

    # ==========================================
    #  最终红头文件：报告员 (Reporter) 填入的对外输出
    # ==========================================
    final_report: Optional[str]  # 格式化的反洗钱可疑交易报告 (SAR)