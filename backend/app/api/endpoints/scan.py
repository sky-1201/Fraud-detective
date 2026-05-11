# backend/app/api/endpoints/scan.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.mysql import get_db
from backend.app.schemas.payload import ScanRequest, ScanResponse
from backend.app.services.radar import RadarService

router = APIRouter()


@router.post("/scan", response_model=ScanResponse)
async def trigger_radar_scan(
        request: ScanRequest,
        db: Session = Depends(get_db)
):
    """
    触发雷达主动扫描。
    输入：阈值 (threshold)
    输出：锁定嫌疑人 ID 列表
    """
    suspects = RadarService.scan_high_frequency_accounts(
        db=db,
        threshold=request.threshold,
        limit=request.limit
    )

    return {
        "suspects": suspects,
        "total_found": len(suspects)
    }