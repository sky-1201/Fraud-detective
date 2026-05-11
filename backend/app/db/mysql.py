# backend/app/db/mysql.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

# 拼接 SQLAlchemy 标准格式的数据库连接 URL
# 格式: mysql+pymysql://user:password@host:port/dbname
MYSQL_URL = f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"

# 创建企业级数据库引擎 (Engine)
# pool_pre_ping: 每次连接前测试存活，防止 MySQL 经典 8 小时断线问题
# pool_size: 连接池大小
engine = create_engine(
    MYSQL_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False # 如果设为 True，会在控制台打印所有生成的 SQL 语句（调试用）
)

# 创建会话工厂 (SessionLocal)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 模型基类，所有的表模型都要继承它
Base = declarative_base()

# 依赖注入函数：供 FastAPI 路由在每次请求时获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()