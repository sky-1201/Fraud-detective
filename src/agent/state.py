# src/agent/state.py
from typing import TypedDict, Optional, Any


class FraudInvestigationState(TypedDict):
    """
    案件调查的全局状态（案卷夹）。
    LangGraph 会在不同的 Agent（节点）之间传递这个字典，每个 Agent 负责填补属于自己的空白。
    """
    # 1. 初始信息
    user_query: str  # 用户的原始指令 (例如："调查 C1590550415 账户")
    target_account: Optional[str]  # [可选] 专门提取出的嫌疑人账号ID，方便后续直接使用

    # 2. 侦查阶段
    raw_evidence: Optional[Any]  # 侦查员从 Neo4j 查回来的原始图谱数据/或者未查到的提示语
    investigation_status: str  # 状态标识："EVIDENCE_FOUND" (找到证据) 或 "NO_EVIDENCE" (查无此人)

    # 3. 分析阶段
    risk_score: Optional[int]  # 0-100 的洗钱风险评分
    risk_analysis_details: str  # 分析师写的详细推理过程（比如：发现典型资金归集特征）

    # 4. 结案阶段
    final_report: str  # 最终要呈现给前端大屏的红头结案报告