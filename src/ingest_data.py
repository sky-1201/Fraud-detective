# src/ingest_data.py
import pandas as pd
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
AUTH = (os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD", "password123"))


def clean_and_prepare_data(csv_path: str, limit: int = 1000):
    """
    数据清洗与预处理：把二维表格变成图谱认识的字典列表
    """
    print("🕵️ 探长，正在从本地 CSV 提取转账案卷...")
    # 架构师 Tips：用 chunksize 或者 nrows 限制读取量，避免开发期内存爆炸
    df = pd.read_csv(csv_path, nrows=limit)

    # 在反欺诈中，我们最关心的是 "TRANSFER" (转账) 行为
    df_transfers = df[df['type'] == 'TRANSFER'].copy()

    records = []
    for _, row in df_transfers.iterrows():
        records.append({
            "source_id": row['nameOrig'],  # 汇款人
            "target_id": row['nameDest'],  # 收款人
            "amount": float(row['amount']),  # 金额
            "is_fraud": int(row['isFraud'])  # 是否是确定的欺诈记录
        })
    print(f"✅ 成功提取 {len(records)} 条核心转账记录！")
    return records


def ingest_to_neo4j(records: list):
    """
    将数据批量写入 Neo4j 图数据库
    """
    # 架构师 Tips: Neo4j 的 Cypher 语句。
    # 这里我们使用 MERGE 而不是 CREATE，MERGE 的意思是“有则匹配，无则创建”，防止节点重复。
    # UNWIND 是批量处理的神器，它能一次性把数百条数据压入数据库，大幅提升写入性能。
    cypher_query = """
    UNWIND $records AS record
    // 1. 刻画资金源头节点
    MERGE (source:Client {id: record.source_id})

    // 2. 刻画资金去向节点
    MERGE (target:Client {id: record.target_id})

    // 3. 建立转账关系（边），并将金额和是否欺诈作为属性附着在“动作”上
    MERGE (source)-[r:TRANSFERRED_TO {amount: record.amount}]->(target)
    SET r.is_fraud = record.is_fraud
    """

    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            # 执行写入事务
            driver.execute_query(
                cypher_query,
                records=records,
                database_="neo4j"
            )
        print("✅ 报告探长！所有嫌疑人节点和资金流向已成功导入图数据库！")
    except Exception as e:
        print(f"❌ 写入失败，请检查: {e}")


if __name__ == "__main__":
    csv_file_path = "../data/paysim.csv"  # 确保你下载的 csv 放在这里

    # 我们先读取 5000 行原始数据，清洗后大约会得到几百条 TRANSFER 记录
    transfer_records = clean_and_prepare_data(csv_file_path, limit=5000)

    if transfer_records:
        ingest_to_neo4j(transfer_records)
    else:
        print("⚠️ 没有在前 5000 行中找到 'TRANSFER' 类型的记录，请调大读取范围。")