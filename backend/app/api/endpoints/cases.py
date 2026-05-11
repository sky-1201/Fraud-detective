# backend/app/api/endpoints/cases.py
from fastapi import APIRouter, HTTPException
from backend.app.schemas.payload import CaseRequest, CaseResponse
from backend.app.workflows.graph import compiled_graph
from backend.app.core.logger import logger

router = APIRouter()


@router.post("/investigate", response_model=CaseResponse)
async def investigate_case(request: CaseRequest):
    """
    [显微镜深度侦查]
    接收嫌疑人 ID，启动 LangGraph AI 专案组进行深度图谱穿透与风控研判。
    """
    account_id = request.account_id
    logger.info("=" * 50)
    logger.info(f"🚨 [立案] 接收到深度侦查请求，目标账户: {account_id}")

    # 1. 初始化案卷宗 (State)
    # 根据 state.py 的定义，我们只需给调度员提供目标 ID 和一个空的聊天记录列表
    initial_state = {
        "suspect_id": account_id,
        "messages": []
    }

    try:
        # 2. 核心大招：触发工作流异步执行！
        # ainvoke 会自动按照 graph.py 里定义的顺序，驱动 Investigator -> Analyst -> Reporter
        logger.info("⚙️ 引擎启动：案卷已投入 LangGraph 流水线...")
        final_state = await compiled_graph.ainvoke(initial_state)

        # 3. 提取最终的侦查成果
        risk_level = final_state.get("risk_level", "UNKNOWN")
        risk_score = final_state.get("risk_score", 0)
        final_report = final_state.get("final_report", "生成报告失败。")

        logger.info(f"🏁 [结案] 侦查结束！最终评级: {risk_level} ({risk_score}/100)")
        logger.info("=" * 50)

        # 4. 格式化并返回给调用方 (前端或大屏)
        return CaseResponse(
            account_id=account_id,
            risk_level=risk_level,
            risk_score=risk_score,
            report=final_report
        )

    except Exception as e:
        error_msg = f"专案组执行过程中发生严重故障: {str(e)}"
        logger.error(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)