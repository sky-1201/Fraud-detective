# backend/app/services/radar.py
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from backend.app.models.transaction import Transaction
from backend.app.schemas.payload import SuspectAccount
from backend.app.core.logger import logger
from sqlalchemy import func, desc, union_all


class RadarService:
    @staticmethod
    def scan_high_frequency_accounts(db: Session, threshold: int, limit: int):
        """
        [雷达主动出击] 扫描 MySQL，找出交易笔数超过阈值的账户。
        使用数据库原生聚合，性能极高。
        """
        logger.info(f"📡 雷达正在扫描... 寻找交易笔数 > {threshold} 的账户")

        # 1. 定义两个子查询：一个取汇款方，一个取收款方
        # 我们统一给列起好 label (别名)，这样合并时才能对齐
        q1 = db.query(
            Transaction.nameOrig.label("account_id"),
            Transaction.amount.label("amount")
        )

        q2 = db.query(
            Transaction.nameDest.label("account_id"),
            Transaction.amount.label("amount")
        )

        # 2. 使用 union_all 将两个查询合并
        # .alias() 非常关键，它把合并后的数据集包装成一个可以被后续 group_by 的虚拟表
        combined_tx = union_all(q1, q2).alias("combined_tx")

        # 3. 执行最终的全景聚合查询
        results = db.query(
            combined_tx.c.account_id,
            func.count(combined_tx.c.account_id).label("transaction_count"),
            func.sum(combined_tx.c.amount).label("total_amount")
        ).group_by(
            combined_tx.c.account_id
        ).having(
            func.count(combined_tx.c.account_id) >= threshold
        ).order_by(
            desc("transaction_count")
        ).limit(limit).all()

        # 转化为 Pydantic 模型返回
        suspects = [
            SuspectAccount(
                account_id=r.account_id,
                transaction_count=r.transaction_count,
                total_amount=round(r.total_amount, 2)
            ) for r in results
        ]

        logger.info(f"✅ 雷达扫描完成，共锁定 {len(suspects)} 个高危目标。")
        return suspects