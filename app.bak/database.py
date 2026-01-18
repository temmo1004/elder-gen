"""
Database Configuration
資料庫連線設定與 Session 管理
"""
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.config import settings

# 處理資料庫 URL
if settings.DATABASE_URL:
    # 修正 Supabase Transaction Mode 的連線字串
    # Supabase 預設給的是 postgres://，需要改為 postgresql://
    db_url = settings.DATABASE_URL.replace("postgres://", "postgresql://")

    # 如果是 pooler connection，需要特殊處理
    if "pooler" in db_url and settings.ENVIRONMENT == "production":
        # Transaction mode pooler
        db_url = db_url.replace("?pgbouncer=true", "") + "?pgbouncer=true"

    # 建立 Engine
    engine = create_engine(
        db_url,
        poolclass=QueuePool,
        pool_size=5,          # 連線池大小
        max_overflow=10,      # 最大溢出連線數
        pool_pre_ping=True,   # 檢查連線有效性
        echo=settings.DEBUG,  # 開發時顯示 SQL
    )

    # 建立 Session 工廠
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
else:
    # 沒有設定資料庫時使用 null engine
    engine = None
    SessionLocal = None

# ORM Base class
Base = declarative_base()


def get_db():
    """
    Dependency Injection: 取得資料庫 Session
    用在 FastAPI 的 Depends(get_db)
    """
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="資料庫未設定")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化資料庫 Table（開發用，生產建議用 Migration）"""
    if engine is not None:
        Base.metadata.create_all(bind=engine)
