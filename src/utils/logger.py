# src/utils/logger.py
import logging
import sys
from src.config.settings import settings


def setup_logger(name="FraudDetective"):
    """配置全局日志记录器"""
    logger = logging.getLogger(name)

    # 如果已经配置过，直接返回（防止重复打印）
    if logger.handlers:
        return logger

    logger.setLevel(settings.LOG_LEVEL)

    # 日志输出格式
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. 输出到控制台
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. 输出到文件
    file_handler = logging.FileHandler(settings.LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# 暴露出一个实例化好的 logger 供全局使用
logger = setup_logger()