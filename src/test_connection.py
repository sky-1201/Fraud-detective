# src/test_connection.py
from neo4j import GraphDatabase

# Neo4j 数据库连接配置 (与 docker-compose 对应)
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password123")

def check_connection():
    print("正在尝试连接到 Neo4j 探长指挥中心...")
    try:
        # 建立连接驱动
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            print("✅ 报告探长！Neo4j 数据库连接成功！图谱基座已全面就绪。")
    except Exception as e:
        print(f"❌ 连接失败，请检查报错信息: {e}")

if __name__ == "__main__":
    check_connection()