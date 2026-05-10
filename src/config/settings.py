# src/config/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

# ==========================================
# 🧠 架构师黑科技：绝对路径锁定
# ==========================================
# __file__ 指向当前的 settings.py
# .parent 指向 config 文件夹
# .parent.parent 指向 src 文件夹
# .parent.parent.parent 指向 fraud_detective 根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 精准锁定根目录下的 .env 文件，彻底无视执行环境和多进程干扰
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    # --- Neo4j 图数据库配置 ---
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

    # --- 大模型 (LLM) 配置 ---
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
    # 我们将复杂推理（分析师）和简单翻译（侦查员）的模型分开配置，方便后期做成本优化
    LLM_MODEL_DEFAULT = "qwen-max"

    # --- 工程配置 ---
    LOG_LEVEL = "INFO"

    # 🚨 同理修复：将日志文件也绑定到绝对路径，防止多进程下日志文件乱跑到其他目录
    LOG_FILE = str(BASE_DIR / "fraud_detective.log")


# 实例化一个全局配置对象供其他模块导入
settings = Config()