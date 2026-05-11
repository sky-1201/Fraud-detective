# backend/app/tools/graph_tool.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from backend.app.core.config import settings
from backend.app.core.logger import logger
from backend.app.db.neo4j_db import neo4j_conn
import json


class FraudGraphTool:
    """
    反欺诈图谱穿透工具 (Text2Cypher)
    职责：根据嫌疑人 ID，自动生成 Cypher 提取其 2 度资金网络，并总结为 JSON 情报。
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_API_BASE,
            model_name=settings.LLM_MODEL_ANALYST,
            temperature=0  # 侦查取证必须严谨，温度设为0
        )

        # 将数据库 Schema 作为先验知识告诉 LLM
        self.schema = """
        Node properties:
        - Client {id: STRING}
        Relationship properties:
        - (Client)-[TRANSFERRED_TO {amount: FLOAT, step: INTEGER, type: STRING}]->(Client)
        """

    def investigate(self, account_id: str) -> str:
        """执行图谱侦查并返回结构化情报"""
        # 强制去除可能存在的不可见空格
        clean_id = account_id.strip()
        logger.info(f"🕵️‍♂️ 图谱探员出动！正在穿透账户 [{clean_id}] 的关系网...")

        # 使用统一的双向查询，并使用 startNode() 动态判断资金流向
        cypher_query = """
        MATCH (suspect:Client {id: $account_id})
        OPTIONAL MATCH (other:Client)-[r:TRANSFERRED_TO]-(suspect)
        RETURN 
            suspect.id AS Target,
            collect(DISTINCT {
                partner_id: other.id, 
                amount: r.amount, 
                step: r.step, 
                type: r.type,
                direction: CASE WHEN startNode(r) = suspect THEN 'OUTFLOW (汇出)' ELSE 'INFLOW (汇入)' END
            }) AS Transactions
        """

        try:
            raw_data = neo4j_conn.execute_query(cypher_query, {"account_id": clean_id})

            # 如果没查到，或者 Transactions 列表里只有 null
            if not raw_data or not raw_data[0].get('Transactions') or raw_data[0]['Transactions'][0].get(
                    'partner_id') is None:
                return f"图谱侦查结果：未能在图谱中找到账户 {clean_id} 的任何资金流转记录。"

            summary_prompt = PromptTemplate.from_template(
                """你是一名专业的反欺诈资金网络分析师。
                请根据以下从 Neo4j 图数据库中提取的资金流向 JSON 数据，用 2-3 句话总结该账户的资金特征。
                重点关注：资金是否呈现“快进快出”、“多进一出（归集）”或“一进多出（分散）”的洗钱特征。

                嫌疑人ID: {account_id}
                资金网络数据:
                {raw_data}

                请直接输出专业的分析结论："""
            )

            chain = summary_prompt | self.llm
            result = chain.invoke({
                "account_id": clean_id,
                "raw_data": json.dumps(raw_data, ensure_ascii=False)
            })

            logger.info(f"✅ 探员情报获取成功！")
            return f"【图谱侦查情报】:\n{result.content}\n\n【原始网络数据支持】:\n{json.dumps(raw_data, ensure_ascii=False)}"

        except Exception as e:
            logger.error(f"❌ 图谱穿透失败: {e}")
            return f"图谱侦查失败，错误信息: {str(e)}"