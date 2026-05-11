# backend/app/core/logger.py
import logging
import sys
from logging.handlers import RotatingFileHandler
from backend.app.core.config import settings


def setup_logger(name: str = "FraudDetective") -> logging.Logger:
    """
    配置并返回企业级全局日志记录器。
    包含：控制台彩色高亮输出 + 按大小自动轮转的文件存档。
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(settings.LOG_LEVEL)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. 控制台输出 (Stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. 文件输出 (带自动轮转)
    # 确保 logs 文件夹存在
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file_path = settings.LOG_DIR / "backend.log"

    # maxBytes=10MB, backupCount=5 (最多保留5个历史日志文件，防止磁盘打满)
    file_handler = RotatingFileHandler(
        filename=str(log_file_path),
        mode='a',
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# 全局暴露 logger 实例
logger = setup_logger()