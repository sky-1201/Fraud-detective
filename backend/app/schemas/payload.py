# backend/app/schemas/payload.py
from pydantic import BaseModel, Field
from typing import List, Optional

class ScanRequest(BaseModel):
    """雷达扫描请求参数"""
    threshold: int = Field(default=10, description="交易笔数阈值，超过此值将被视为嫌疑人")
    limit: int = Field(default=100, description="最多返回的嫌疑人数量")

class SuspectAccount(BaseModel):
    """嫌疑账户简要信息"""
    account_id: str
    transaction_count: int
    total_amount: float

class ScanResponse(BaseModel):
    """雷达扫描结果响应"""
    status: str = "success"
    suspects: List[SuspectAccount]
    total_found: int


class CaseRequest(BaseModel):
    """案件侦查请求参数"""
    account_id: str = Field(..., description="需要专案组彻查的嫌疑人账户 ID (如: C_BOSS_999)")

class CaseResponse(BaseModel):
    """案件侦查最终响应"""
    status: str = "success"
    account_id: str
    risk_level: str
    risk_score: int
    report: str = Field(description="Markdown 格式的最终结案报告")

class TaskResponse(BaseModel):
    """异步任务排队小票响应"""
    status: str = "processing"
    task_id: str = Field(description="Celery 生成的全局唯一任务 ID")
    account_id: str