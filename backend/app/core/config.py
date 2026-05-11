# backend/app/core/config.py
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# 📍 绝对路径锁定：精准定位项目根目录 fraud_detective_enterprise
# 轨迹: config.py -> core -> app -> backend -> 根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """
    全局强类型配置中心。
    所有变量必须明确类型，缺失或类型错误会在启动时直接报错。
    """
    # --- API 基础配置 ---
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Fraud Detective Enterprise API"

    # --- MySQL 关系型数据库配置 ---
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str
    MYSQL_DB: str = "fraud_db"

    # --- Neo4j 图数据库配置 ---
    NEO4J_URI: str
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str

    # --- LLM 大模型配置 ---
    OPENAI_API_KEY: str
    OPENAI_API_BASE: str
    LLM_MODEL_ANALYST: str = "qwen-max"  # 复杂推理模型
    LLM_MODEL_ROUTER: str = "qwen-turbo"  # 简单路由模型 (省成本)

    # --- 日志配置 ---
    LOG_LEVEL: str = "INFO"
    LOG_DIR: Path = PROJECT_ROOT / "logs"

    # 指定去哪里读取 .env 文件
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"  # 忽略 .env 中多余的无关变量
    )


# 全局单例实例化，整个项目只需 from core.config import settings
settings = Settings()