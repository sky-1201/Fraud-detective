# backend/scripts/import_real_data.py
import sys
import pandas as pd
from pathlib import Path
from neo4j import GraphDatabase

# 锁定项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from backend.app.core.config import settings
from backend.app.core.logger import logger
from backend.app.db.mysql import engine, Base, SessionLocal
from backend.app.models.transaction import Transaction

# --- 配置区 ---
CSV_FILE_PATH = PROJECT_ROOT / "data" / "PaySim.csv"  # 请确保文件路径正确
CHUNK_SIZE = 10000  # 每次处理 1 万行，兼顾速度与内存
LIMIT_ROWS = 100000  # 初次运行建议先导入 10 万行进行测试，全量导入请设为 None


def get_neo4j_driver():
    return GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
    )


def clean_data(df):
    """进行必要的字段映射与清洗"""
    # 确保列名与数据库模型一致（PaySim 原始列名 vs 我们的模型）
    rename_map = {
        'oldbalanceOrg': 'oldbalanceOrg',
        'newbalanceOrig': 'newbalanceOrig',
        'oldbalanceDest': 'oldbalanceDest',
        'newbalanceDest': 'newbalanceDest'
    }
    return df.rename(columns=rename_map)


def process_ingestion():
    if not CSV_FILE_PATH.exists():
        logger.error(f"❌ 未找到 CSV 文件: {CSV_FILE_PATH}")
        return

    # 1. 准备数据库
    logger.info("💾 [MySQL] 正在初始化表结构...")
    Base.metadata.create_all(bind=engine)

    # 2. 准备 Neo4j 驱动
    driver = get_neo4j_driver()

    # 3. 开启流式迭代
    logger.info(f"🚀 开始从 {CSV_FILE_PATH.name} 导入数据...")

    reader = pd.read_csv(CSV_FILE_PATH, chunksize=CHUNK_SIZE)
    total_processed = 0

    for i, chunk in enumerate(reader):
        if LIMIT_ROWS and total_processed >= LIMIT_ROWS:
            break

        chunk = clean_data(chunk)
        data_list = chunk.to_dict(orient='records') #列表

        # --- A. 写入 MySQL ---
        db = SessionLocal()
        try:
            db.bulk_insert_mappings(Transaction, data_list)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"❌ MySQL 块 {i} 写入失败: {e}")
        finally:
            db.close()

        # --- B. 写入 Neo4j ---
        cypher = """
        UNWIND $batch AS row
        MERGE (orig:Client {id: row.nameOrig})
        MERGE (dest:Client {id: row.nameDest})
        CREATE (orig)-[r:TRANSFERRED_TO {
            amount: row.amount,
            step: row.step,
            type: row.type,
            isFraud: row.isFraud
        }]->(dest)
        """
        with driver.session() as session:
            session.run(cypher, batch=data_list)

        total_processed += len(chunk)
        logger.info(f"📈 已处理: {total_processed} 行...")

    driver.close()
    logger.info(f"🎉 任务完成！共计导入 {total_processed} 条真实案卷流水。")


if __name__ == "__main__":
    process_ingestion()