# backend/app/workflows/nodes/analyst.py
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from backend.app.workflows.state import CaseState
from backend.app.core.config import settings
from backend.app.core.logger import logger


# 1. 严格定义分析师的“判决书”格式 (Pydantic 约束)
class RiskAssessment(BaseModel):
    risk_score: int = Field(description="风险指数，范围 0-100。100表示确凿的洗钱行为。")
    risk_level: str = Field(description="风险等级，仅限以下四个值：LOW, MEDIUM, HIGH, CRITICAL")
    reasoning: str = Field(description="一步步的逻辑推理过程 (Chain of Thought)，解释为什么打这个分数。")


# 2. 实例化分析师大脑 (使用高级模型，并绑定结构化输出)
# 注意：这里调用的是 .with_structured_output()，这是 LangChain 0.1+ 的核心杀手锏
llm = ChatOpenAI(
    openai_api_key=settings.OPENAI_API_KEY,
    openai_api_base=settings.OPENAI_API_BASE,
    model_name=settings.LLM_MODEL_ANALYST,
    temperature=0.1  # 分析师必须极度理智，温度设低
).with_structured_output(RiskAssessment)


async def analyst_node(state: CaseState) -> dict:
    """
    风控分析师节点逻辑：
    审查侦查员提交的 graph_evidence，进行逻辑推理，并给出定量打分与定性结论。
    """
    suspect_id = state["suspect_id"]
    evidence = state.get("graph_evidence", "无图谱证据")

    logger.info(f"🧠 [Node: Analyst] 正在审查嫌疑人 {suspect_id} 的案卷...")

    # 如果侦查员什么都没查到，直接给出无罪推论
    if "未能在图谱中找到" in evidence or "侦查失败" in evidence:
        logger.warning(f"⚠️ 证据不足，分析师终止推理。")
        return {
            "risk_score": 0,
            "risk_level": "LOW",
            "reasoning": "由于侦查阶段未能获取有效的图谱资金网络证据，按照疑罪从无原则，暂定为低风险。",
            "messages": [AIMessage(content="【分析师批示】证据不足，无法定罪，建议结案或人工复核。")]
        }

    # 3. 编写极其专业的反洗钱 (AML) 提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一名供职于全球顶尖金融机构的资深反洗钱(AML)与反欺诈分析师。
            你的任务是审查系统提供的资金图谱证据，并给出极其严谨的定性与打分。

            【评判核心法则】：
            - 正常交易 (LOW 0-20)：普通的日常转账、消费。
            - 疑似异常 (MEDIUM 21-60)：金额较大且频率异常，但无明显闭环。
            - 高危特征 (HIGH 61-89)：出现明显的“快进快出”或“资金汇聚”。
            - 确凿洗钱 (CRITICAL 90-100)：出现极其典型的“多进一出（归集）”且金额巨大的黑老大特征。

            请务必保持客观，严格按照上述法则进行研判。

            【强制输出格式】：
            必须且只能输出一个合法的 JSON 对象，绝不能包含 markdown 标记。
            必须严格使用以下 3 个英文键名（绝对不允许修改键名）：
            {{
                "risk_score": <整数，范围 0-100>,
                "risk_level": "<必须是 LOW/MEDIUM/HIGH/CRITICAL 之一>",
                "reasoning": "<详细的中文逻辑推理过程，解释为什么打这个分数>"
            }}"""),
        ("user", "嫌疑人账户ID：{suspect_id}\n\n【前线探员提交的证据】\n{evidence}")
    ])
    try:
        # 4. 执行链条：Prompt -> LLM (带结构化输出约束)
        chain = prompt | llm
        assessment: RiskAssessment = await chain.ainvoke({
            "suspect_id": suspect_id,
            "evidence": evidence
        })

        # 5. 组装分析师简报
        analyst_log = AIMessage(
            content=f"【分析师研判结论】\n风险等级: {assessment.risk_level}\n风险分数: {assessment.risk_score}/100\n推理过程: {assessment.reasoning}"
        )

        logger.info(f"✅ 研判完成！评级: {assessment.risk_level}, 分数: {assessment.risk_score}")

        # 6. 返回案卷更新碎片
        return {
            "risk_score": assessment.risk_score,
            "risk_level": assessment.risk_level,
            "reasoning": assessment.reasoning,
            "messages": [analyst_log]
        }

    except Exception as e:
        logger.error(f"❌ [Analyst Error] 分析师推理崩溃: {e}")
        return {
            "risk_score": 0,
            "risk_level": "LOW",
            "reasoning": "AI 分析引擎发生内部错误，未能完成评估。",
            "messages": [AIMessage(content=f"【系统异常】分析引擎推理失败: {e}")]
        }