# backend/app/db/neo4j_db.py
from neo4j import GraphDatabase
from backend.app.core.config import settings
from backend.app.core.logger import logger

class Neo4jConnectionManager:
    """企业级 Neo4j 连接池管理器"""
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
            )
            # 启动时进行一次连通性测试
            self.driver.verify_connectivity()
            logger.info("🕸️ Neo4j 图数据库连接池初始化成功！")
        except Exception as e:
            logger.error(f"❌ Neo4j 连接失败，请检查配置或 Docker 状态: {e}")
            raise e

    def close(self):
        if self.driver:
            self.driver.close()

    def execute_query(self, query: str, parameters: dict = None) -> list:
        """执行 Cypher 语句并返回字典列表"""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

# 全局单例，供 Tool 工具调用
neo4j_conn = Neo4jConnectionManager()