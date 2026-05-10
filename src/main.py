# src/main.py
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
from src.agent.graph import build_fraud_investigation_graph
from src.utils.logger import logger

# 初始化 FastAPI 应用
app = FastAPI(title="智能反欺诈追踪 API", version="1.0")

# 全局挂载我们之前写好的 LangGraph 工作流
logger.info("🚀 正在启动 FastAPI 后端引擎...")
agent_app = build_fraud_investigation_graph()

# 定义前端传过来的请求体格式
class InvestigationRequest(BaseModel):
    query: str

@app.post("/api/investigate")
async def run_investigation(request: InvestigationRequest):
    """
    核心接口：接收前端指令，使用数据流 (Streaming) 动态返回案卷状态
    """
    # 架构师黑科技：定义一个生成器函数，让 LangGraph 每完成一个节点，就 yield 一次数据
    def event_stream():
        initial_state = {"user_query": request.query}
        try:
            for event in agent_app.stream(initial_state):
                # 将字典转为 JSON 字符串，加上换行符，变成数据流
                yield f"{json.dumps(event, ensure_ascii=False)}\n"
        except Exception as e:
            logger.error(f"工作流执行异常: {e}")
            yield f"{json.dumps({'error': str(e)})}\n"

    # 使用 StreamingResponse 返回流式数据，前端就可以像读聊天记录一样一行行读取
    return StreamingResponse(event_stream(), media_type="application/x-ndjson")

if __name__ == "__main__":
    import uvicorn
    # 在 8000 端口启动后端服务
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)