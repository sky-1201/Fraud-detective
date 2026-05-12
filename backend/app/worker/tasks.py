# backend/app/worker/tasks.py
import asyncio
from celery import Celery
from backend.app.core.config import settings
from backend.app.workflows.graph import compiled_graph
from backend.app.core.logger import logger

# 实例化 Celery 应用，指定 Redis 作为 Broker 和 Backend
celery_app = Celery(
    "fraud_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)


@celery_app.task(bind=True, name="investigate_suspect")
def investigate_suspect_task(self, account_id: str):
    """
    后台异步运行 LangGraph 专案组的 Worker
    """
    logger.info(f"👷 [Celery Worker] 开始处理嫌疑人 {account_id} 的调查任务...")

    initial_state = {
        "suspect_id": account_id,
        "messages": []
    }

    try:
        # ⚠️ 核心考点：Celery 是同步框架，而我们的 Graph 是异步的
        # 所以必须手动创建一个事件循环来运行 ainvoke
        final_state = asyncio.run(compiled_graph.ainvoke(initial_state))

        risk_level = final_state.get("risk_level", "UNKNOWN")
        risk_score = final_state.get("risk_score", 0)
        final_report = final_state.get("final_report", "生成报告失败。")

        logger.info(f"🏁 [Celery Worker] 任务完成！{account_id} 评级: {risk_level}")

        # 将结果存回 Redis，供前端轮询提取
        return {
            "account_id": account_id,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "report": final_report
        }

    except Exception as e:
        logger.error(f"❌ [Celery Worker] 任务失败: {e}")
        # 失败时也会把错误信息写回 Redis
        return {"error": str(e)}