# backend/app/main.py

from fastapi import FastAPI
from backend.app.api.endpoints import scan,cases
from backend.app.core.config import settings
from backend.app.core.logger import logger

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs" # 开启 Swagger 文档
)

# 挂载雷达扫描路由
app.include_router(
    scan.router,
    prefix=f"{settings.API_V1_STR}/radar",
    tags=["Radar"]
)

# 挂载 AI 专案组案件调查路由 (深度穿透)
app.include_router(
    cases.router,
    prefix=f"{settings.API_V1_STR}/cases",
    tags=["Cases"]
)

@app.on_event("startup")
async def startup_event():
    logger.info("="*50)
    logger.info(f"🚀 {settings.PROJECT_NAME} 启动成功！")
    logger.info(f"📚 API 文档地址: http://127.0.0.1:8000/docs")
    logger.info("="*50)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
    #http://127.0.0.1:8000/docs

# neo4j数据库可视化：http://localhost:7474/
# 进入项目根目录后，启动 FastAPI 服务
# uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
# streamlit run frontend/app.py