# src/agent/nodes.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import re

from src.tools.graph_tool import FraudGraphTool
from src.utils.logger import logger
from src.config.settings import settings
from src.agent.state import FraudInvestigationState

# 1. 组装全局武器库
# 侦查员的专属工具
graph_tool = FraudGraphTool()

# 分析师和报告员共用的“大脑”（LLM）
llm = ChatOpenAI(
    model=settings.LLM_MODEL_DEFAULT,
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_API_BASE,
    temperature=0.2  # 稍微给点温度，让写出来的报告更自然
)


# ==========================================
# 🕵️‍♂️ 节点 1: 侦查员 (Investigator)
# ==========================================
def investigator_node(state: FraudInvestigationState):
    logger.info("🕵️‍♂️ [侦查员] 出动：正在向图数据库下达查询指令...")
    query = state["user_query"]

    # 拿到包含 report 和 status_code 的字典
    investigation_result = graph_tool.investigate_account(query)

    evidence = investigation_result["report"]
    status_code = investigation_result["status_code"]

    logger.info(f"📝 [侦查员笔录]: {evidence}")

    # 【架构级重构】：彻底抛弃脆弱的文本匹配，使用绝对可靠的状态码路由！
    if status_code == 0:
        status = "NO_EVIDENCE"
        logger.warning(f"🕵️‍♂️ [侦查员] 报告：底层数据为空 (状态码 0)，未留下转账痕迹。")
    else:
        status = "EVIDENCE_FOUND"
        logger.info(f"🕵️‍♂️ [侦查员] 报告：发现底层资金数据 (状态码 1)，已固化证据！")

    return {"raw_evidence": evidence, "investigation_status": status}


# ==========================================
# 🧠 节点 2: 风控分析师 (Analyst)
# ==========================================
def analyst_node(state: FraudInvestigationState):
    logger.info("🧠 [分析师] 接手：正在运用反欺诈模型分析资金流向特征...")
    evidence = state.get("raw_evidence", "")

    # 注入专家风控经验的 Prompt (屏蔽作弊字段版)
    analyst_prompt = PromptTemplate.from_template(
        """你是一位资深的反洗钱(AML)与反欺诈风控分析师。
        请仔细审查以下由图数据库提取出的资金流水证据：

        【案卷证据】：{evidence}

        ⚠️ 【极其重要的风控纪律】：
        数据中可能包含 `is_fraud` 或类似标记，这是不可靠的历史遗留或测试标签。作为独立调查员，你必须**完全无视该字段**！
        你只能凭借以下三个客观维度来独立判断洗钱或欺诈风险：
        1. 拓扑结构：资金是否有异常的“归集”（多账户向一账户汇款）或“打散”（一账户向多账户汇款）特征？
        2. 金额特征：交易金额是否极其庞大、或者呈现为了避开监管而构造的不符合常理的金额？
        3. 账户特征：这批交易的参与方是否在短时间内形成了密集的网络流向？

        请给出详尽且严密的推理过程。并在回答的最后一行，严格按以下格式给出一个 0-100 的洗钱风险评分（分数越高代表嫌疑越大）：
        【风险评分：XX】"""
    )

    # LangChain 语法：把 Prompt 和 LLM 绑在一起执行
    chain = analyst_prompt | llm
    analysis_result = chain.invoke({"evidence": evidence}).content

    # 用正则提取分数，提取不到默认给个 50 分中等风险
    score_match = re.search(r"【风险评分：(\d+)】", analysis_result)
    score = int(score_match.group(1)) if score_match else 50

    logger.info(f"🧠 [分析师] 结论：已完成深度分析，评估风险得分为 {score} 分。")

    return {"risk_analysis_details": analysis_result, "risk_score": score}


# ==========================================
# ✍️ 节点 3: 报告员 (Reporter)
# ==========================================
def reporter_node(state: FraudInvestigationState):
    logger.info("✍️ [报告员] 奋笔疾书中：正在整合所有线索生成红头结案报告...")

    query = state.get("user_query", "")
    status = state.get("investigation_status", "")

    if status == "NO_EVIDENCE":
        # 走快车道的报告
        final_report = (
            f"📄 【账户核查简报】\n\n"
            f"针对请求：{query}\n"
            f"核查结果：经图谱系统穿透核查，该目标在当前案件库中无任何相关转账及拓扑关联记录。暂解除嫌疑。\n"
            f"建议：持续观望。"
        )
    else:
        # 走重案车道的报告
        evidence = state.get("raw_evidence", "")
        analysis = state.get("risk_analysis_details", "")
        score = state.get("risk_score", 0)

        reporter_prompt = PromptTemplate.from_template(
            """你是一位公安部高级文秘。请根据以下专案组提供的零散线索，撰写一份严肃、专业、排版清晰的《金融账户异常排查红头报告》。

            【原始请求】：{query}
            【图谱取证】：{evidence}
            【风控分析】：{analysis}
            【风险评分】：{score} (满分100)

            报告要求：
            1. 包含核心章节：调查背景、资金流向摘要、风险定性分析、处置建议。
            2. 口吻官方、严谨，不要使用任何语气词。
            3. 直接输出报告内容，不要说“好的”。"""
        )

        final_report = (reporter_prompt | llm).invoke({
            "query": query,
            "evidence": evidence,
            "analysis": analysis,
            "score": score
        }).content

    logger.info("✅ [报告员] 搞定：红头结案报告已签发！")
    return {"final_report": final_report}


# ==========================================
# 🔀 路由裁判 (Router)
# ==========================================
def route_investigation(state: FraudInvestigationState):
    """
    这个函数不会修改 State，它只是返回下一步该去哪个节点的“名字”
    """
    status = state.get("investigation_status")
    if status == "NO_EVIDENCE":
        logger.info("🔀 [路由裁判] 判定：无有效线索，启用绿色快车道，直达报告员！")
        return "reporter_node"  # 这里的字符串必须和我们一会儿画图时注册的节点名字一样
    else:
        logger.info("🔀 [路由裁判] 判定：发现重大资金线索，立刻移交风控分析师！")
        return "analyst_node"