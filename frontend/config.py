# frontend/config.py
import os

# 后端 FastAPI 的基础服务地址
# 在 Docker 部署时，可以通过环境变量覆盖这个值
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api")

# UI 全局文案配置
APP_TITLE = "🚨  - AI 全链路反欺诈风控中枢"
APP_ICON = "🚨"