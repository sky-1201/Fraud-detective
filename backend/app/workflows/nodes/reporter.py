# backend/app/workflows/nodes/reporter.py
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from backend.app.workflows.state import CaseState
from backend.app.core.config import settings
from backend.app.core.logger import logger

# 实例化报告员专属大脑
# 撰写报告不需要复杂的逻辑推理，但需要极好的文笔和排版能力
llm = ChatOpenAI(
    openai_api_key=settings.OPENAI_API_KEY,
    openai_api_base=settings.OPENAI_API_BASE,
    model_name=settings.LLM_MODEL_ANALYST,
    temperature=0.3  # 稍微给点温度，让文字排版更自然
)


async def reporter_node(state: CaseState) -> dict:
    """
    结案报告员节点逻辑：
    汇总前序探员和分析师的所有成果，撰写最终的标准化《反洗钱可疑交易报告 (SAR)》。
    """
    suspect_id = state["suspect_id"]
    risk_level = state.get("risk_level", "UNKNOWN")
    risk_score = state.get("risk_score", 0)
    reasoning = state.get("reasoning", "无推理记录")

    logger.info(f"✍️ [Node: Reporter] 正在为嫌疑人 {suspect_id} 撰写最终结案报告...")

    # 如果是低风险，直接出具简易放行报告，节省 Token
    if risk_level == "LOW":
        simple_report = f"""
        # 🟢 账户自动排查放行通知
        - **核查对象**: {suspect_id}
        - **综合风险评分**: {risk_score}/100
        - **系统判定**: 正常账户，未见明显洗钱/欺诈特征。
        - **处理建议**: 自动放行，无需人工介入。
        """
        logger.info("✅ 低风险账户，已生成简易放行通知。")
        return {
            "final_report": simple_report,
            "messages": [AIMessage(content="【报告员签发】低风险简易报告已归档。")]
        }

    # 对于中高风险，撰写严谨的红头公文
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一名金融机构的资深合规官 (Compliance Officer)。
        请根据系统传入的风险参数和推理过程，撰写一份正式的《反洗钱可疑交易报告 (SAR)》。

        【排版要求】：
        必须使用 Markdown 格式，包含以下模块：
        1. 🚨 **案卷摘要** (含嫌疑人ID、风险评级、风险指数)
        2. 🕸️ **资金图谱特征** (用最简练的语言描述网络拓扑)
        3. ⚖️ **研判依据** (详细陈述为什么打这个分数)
        4. 🛡️ **处置建议** (比如：冻结账户、限制非柜面业务、上报监管等)

        文风要求：极其严肃、客观、法务化，绝不使用任何轻浮的口语。"""),
        ("user", "嫌疑人账户：{suspect_id}\n风险等级：{risk_level}\n风险分数：{risk_score}\n分析师推理：{reasoning}")
    ])

    try:
        chain = prompt | llm
        response = await chain.ainvoke({
            "suspect_id": suspect_id,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "reasoning": reasoning
        })

        final_report = response.content
        logger.info("✅ 正式 SAR 结案报告撰写完毕！")

        return {
            "final_report": final_report,
            "messages": [AIMessage(content="【报告员签发】正式反洗钱评估报告已归档。专案组侦查结束。")]
        }

    except Exception as e:
        logger.error(f"❌ [Reporter Error] 撰写报告时发生崩溃: {e}")
        return {
            "final_report": f"⚠️ 报告生成失败: {str(e)}\n\n原始分析数据：\n评分={risk_score}\n依据={reasoning}",
            "messages": [AIMessage(content=f"【系统异常】报告生成失败: {e}")]
        }