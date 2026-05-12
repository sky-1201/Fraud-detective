# backend/app/api/endpoints/cases.py
from fastapi import APIRouter, HTTPException
from backend.app.schemas.payload import CaseRequest, TaskResponse
from backend.app.core.logger import logger
from backend.app.db.neo4j_db import neo4j_conn
from backend.app.worker.tasks import investigate_suspect_task
from celery.result import AsyncResult

router = APIRouter()


@router.post("/investigate", response_model=TaskResponse)
async def investigate_case_async(request: CaseRequest):
    """
    [重构版：异步分发]
    接收嫌疑人 ID，秒级返回 Task ID，具体的 LangGraph 调查推入 Celery 队列。
    """
    account_id = request.account_id
    logger.info(f"🚨 [立案网关] 收到 {account_id} 的调查请求，正在移交 Celery...")

    try:
        # 1. 触发后台任务 (使用 delay)
        task = investigate_suspect_task.delay(account_id)

        logger.info(f"🎫 已生成取件码 (Task ID): {task.id}")

        # 2. 0.01秒瞬间返回，绝不阻塞！
        return TaskResponse(
            status="processing",
            task_id=task.id,
            account_id=account_id
        )
    except Exception as e:
        logger.error(f"❌ 分发任务失败: {e}")
        raise HTTPException(status_code=500, detail="任务队列服务异常")


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """前端通过这个接口，凭借 Task ID 不断轮询案卷进度"""
    task_result = AsyncResult(task_id)

    if task_result.state == 'PENDING':
        return {"status": "processing"}
    elif task_result.state == 'SUCCESS':
        # 提取 Worker 跑完存在 Redis 里的结果
        result_data = task_result.result
        if "error" in result_data:
            return {"status": "error", "message": result_data["error"]}
        return {"status": "success", "data": result_data}
    elif task_result.state == 'FAILURE':
        return {"status": "error", "message": str(task_result.info)}
    else:
        return {"status": task_result.state}


@router.get("/network/{account_id}")
async def get_suspect_network(account_id: str):
    """专门为前端关系图谱提供真实拓扑数据的接口"""
    cypher_query = """
    MATCH (n:Client {id: $account_id})-[r:TRANSFERRED_TO]-(m:Client)
    RETURN 
        m.id AS partner_id,
        r.amount AS amount,
        CASE WHEN startNode(r) = n THEN 'OUTFLOW' ELSE 'INFLOW' END AS direction
    LIMIT 50
    """
    try:
        raw_data = neo4j_conn.execute_query(cypher_query, {"account_id": account_id.strip()})
        return {"status": "success", "data": raw_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}