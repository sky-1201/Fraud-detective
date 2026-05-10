# src/tools/graph_tool.py
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from src.config.settings import settings



class FraudGraphTool:
    def __init__(self):
        print("🔧 正在组装 Text2Cypher 探长工具箱...")

        # 1. 挂载图数据库
        self.graph = Neo4jGraph(
            url=settings.NEO4J_URI,
            username=settings.NEO4J_USERNAME,
            password=settings.NEO4J_PASSWORD
        )

        # 2. 初始化大模型大脑
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL_DEFAULT,  # 统一使用配置里的模型名称
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE
        )

        # 自定义 Cypher 生成提示词：给大模型立规矩
        cypher_template = """你是一个 Neo4j 图数据库的 Cypher 专家。
                请根据提供的 Schema 编写 Cypher 查询来回答用户的提问。

                Schema信息:
                {schema}

                ⚠️ 严格遵守以下规则:
                1. 只能使用 Schema 中提供的节点和关系类型。
                2. 【核心规则】当需要查询关系（边）上的属性（如转账金额 amount）时，绝对不要在模式匹配内部使用变量赋值（如 {{amount: amount}}）！
                3. 【核心规则】必须给关系赋予别名，并在 RETURN 语句中通过别名调用。正确示例：MATCH (a)-[r:TRANSFERRED_TO]->(b) RETURN r.amount
                4. 不要包含任何多余的解释或道歉，只输出纯 Cypher 语句。

                用户的提问是:
                {question}"""

        cypher_prompt = PromptTemplate(
            input_variables=["schema", "question"],
            template=cypher_template
        )

        # 1. 定义 QA 提示词：教大模型如何看懂数据库结果并写报告
        qa_template = """你是一位资深的金融犯罪调查专家。
                请根据用户的问题和从图数据库中查询到的原始数据，撰写一份简洁、专业的调查报告。

                原始查询结果:
                {context}

                用户原始问题:
                {question}

                ⚠️ 报告准则:
                1. 如果结果中有 id 或 amount，请务必直接引用，不要说“不知道”。
                2. 将 id 描述为“账户编号”，将 amount 描述为“转账金额”。
                3. 如果结果为空，请礼貌地说明在当前案卷库中未找到相关记录。

                调查报告:"""

        qa_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=qa_template
        )

        # 2. 更新 Chain 的配置
        self.cypher_chain = GraphCypherQAChain.from_llm(
            cypher_llm=self.llm,
            qa_llm=self.llm,
            graph=self.graph,
            verbose=True,
            return_direct=False,
            allow_dangerous_requests=True,
            cypher_prompt=cypher_prompt,
            qa_prompt=qa_prompt,
            return_intermediate_steps = True #让 Chain 吐出底层查询的真实数据
        )

    def investigate_account(self, query: str) -> dict:
        try:
            print(f"\n🕵️‍♂️ 探长下达调查指令: {query}")
            result = self.cypher_chain.invoke({"query": query})

            # 安全地遍历中间步骤，寻找真实的 context 数据
            context = []
            for step in result.get("intermediate_steps", []):
                if "context" in step:
                    context = step["context"]
                    break  # 找到了就立刻停止

            # 探长的状态码逻辑：空为0，非空为1
            status_code = 1 if len(context) > 0 else 0

            return {
                "report": result['result'],
                "status_code": status_code
            }
        except Exception as e:
            return {"report": f"❌ 调查受阻: {e}", "status_code": 0}


# ========== 测试模块 ==========
if __name__ == "__main__":
    tool = FraudGraphTool()

    # 架构师 Tips: 为了测试，你需要从你的 Neo4j 网页端随便复制一个节点(账户)的 ID 填在下面
    # 例如：帮我查一下 C12345678 这个账户向哪些账户转过钱？转了多少？
    test_query = "帮我查一下C2007599722这个账户向哪些账户转过钱？转了多少？"

    response = tool.investigate_account(test_query)
    print("\n📝 最终调查报告:")
    print(response)