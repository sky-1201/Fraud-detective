# backend/app/models/transaction.py
from sqlalchemy import Column, Integer, String, Float, Boolean, Index
from backend.app.db.mysql import Base


class Transaction(Base):
    """
    PaySim 交易流水表模型 (雷达扫描的底层数据源)
    """
    __tablename__ = "transactions"

    # 主键 ID
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 核心交易字段
    step = Column(Integer, nullable=False, comment="交易发生的时间步(1 step = 1 hour)")
    type = Column(String(50), nullable=False, comment="交易类型(如 TRANSFER, CASH_OUT)")
    amount = Column(Float, nullable=False, comment="交易金额")

    # 账户关联字段
    nameOrig = Column(String(100), nullable=False, index=True, comment="汇款方账户 ID")
    oldbalanceOrg = Column(Float, nullable=False, comment="汇款方初始余额")
    newbalanceOrig = Column(Float, nullable=False, comment="汇款方最新余额")

    nameDest = Column(String(100), nullable=False, index=True, comment="收款方账户 ID")
    oldbalanceDest = Column(Float, nullable=False, comment="收款方初始余额")
    newbalanceDest = Column(Float, nullable=False, comment="收款方最新余额")

    # 历史遗留的风控标记 (在真实雷达中通常仅作参考)
    isFraud = Column(Boolean, default=False, comment="是否为欺诈交易")
    isFlaggedFraud = Column(Boolean, default=False, comment="是否被系统标记为高风险")

    # 复合索引：雷达系统经常需要根据“时间”和“金额”进行全表扫描
    __table_args__ = (
        Index('idx_step_amount', 'step', 'amount'),
    )