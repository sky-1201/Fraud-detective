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
        clean_id = account_id.strip()
        logger.info(f"🕵️‍♂️ 图谱探员出动！正在进行 N度 深度穿透 [{clean_id}]...")

        # 🌟 核心升级：查询 2 度资金链路，将原本的星状结构打平为链路明细
        cypher_query = """
        MATCH path = (suspect:Client {id: $account_id})-[*1..2]-(other:Client)
        UNWIND relationships(path) AS r
        WITH DISTINCT r
        RETURN 
            startNode(r).id AS source,
            endNode(r).id AS target,
            r.amount AS amount,
            r.step AS step,
            r.type AS type
        LIMIT 100
        """

        try:
            raw_data = neo4j_conn.execute_query(cypher_query, {"account_id": clean_id})

            if not raw_data:
                return f"图谱侦查结果：未能在图谱中找到账户 {clean_id} 的任何资金流转记录。"

            # 🌟 Prompt 升维：教导 LLM 如何看懂 2 度资金链
            summary_prompt = PromptTemplate.from_template(
                """你是一名专业的反欺诈资金网络分析师。
                请根据以下从 Neo4j 提取的【2度资金链路数据】，总结嫌疑人的洗钱特征。
                数据格式为多行转账记录：`source(汇款方) -> target(收款方) | amount(金额)`。

                【侦查重点】：
                1. 链式转移：是否存在 A 打给 B，B 又迅速打给嫌疑人？(资金中转)
                2. 资金归集：是否出现大量外围边缘节点，将资金汇聚到中间节点，再流入嫌疑人？
                3. 资金打散：嫌疑人的钱是否又被分发给了大量其他不同节点？

                嫌疑人ID: {account_id}
                2度链路数据:
                {raw_data}

                请输出极其专业的分析结论（不超过 4 句话）："""
            )

            chain = summary_prompt | self.llm
            result = chain.invoke({
                "account_id": clean_id,
                "raw_data": json.dumps(raw_data, ensure_ascii=False)
            })

            logger.info(f"✅ N度探员情报获取成功！")
            return f"【深层图谱侦查情报】:\n{result.content}\n\n【原始链路数据支持】:\n{json.dumps(raw_data, ensure_ascii=False)}"

        except Exception as e:
            logger.error(f"❌ 图谱穿透失败: {e}")
            return f"图谱侦查失败，错误信息: {str(e)}"