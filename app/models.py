"""
SQLAlchemy ORM Models
資料庫模型定義
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.sql import func
from app.database import Base


class ElderUser(Base):
    """長輩圖用戶表"""
    __tablename__ = "elder_users"

    id = Column(Integer, primary_key=True, index=True)
    line_user_id = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(100))
    picture_url = Column(String(500))  # LINE 大頭貼 URL

    # 點數系統
    points = Column(Integer, default=0, nullable=False)
    is_vip = Column(Boolean, default=False, nullable=False)

    # 統計
    total_images_generated = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ElderOrder(Base):
    """訂單表（紀錄藍新金流交易）"""
    __tablename__ = "elder_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False, index=True)  # 我們生成的訂單號
    user_id = Column(Integer, ForeignKey("elder_users.id", ondelete="CASCADE"))

    # 金額資訊
    amount = Column(Integer, nullable=False)  # 单位：分
    points_added = Column(Integer, nullable=False)

    # 狀態
    status = Column(String(20), default="PENDING")  # PENDING, PAID, FAILED, EXPIRED

    # 藍新回傳資訊
    neweb_trade_no = Column(String(50))  # 藍新交易序號
    neweb_payment_type = Column(String(50))  # 付款方式
    pay_time = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ElderImageJob(Base):
    """圖片生成任務表"""
    __tablename__ = "elder_image_jobs"

    # 使用字串主 key (Celery Task ID)
    job_id = Column(String(50), primary_key=True)
    user_id = Column(Integer, ForeignKey("elder_users.id", ondelete="CASCADE"))

    # 輸入
    prompt_used = Column(Text)
    original_url = Column(Text)  # 用戶上傳的原圖 URL
    original_image_path = Column(String(500))  # Supabase Storage path

    # 輸出
    result_url = Column(Text)  # 生成後的成品 URL
    result_image_path = Column(String(500))  # Supabase Storage path

    # 狀態
    status = Column(String(20), default="QUEUED")  # QUEUED, PROCESSING, COMPLETED, FAILED
    error_message = Column(Text)

    # 成本
    cost_points = Column(Integer, default=0)

    # 追蹤
    celery_task_id = Column(String(100))  # Celery 實際 task ID
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))


# 建立索引
Index("idx_elder_users_line", ElderUser.line_user_id)
Index("idx_elder_orders_no", ElderOrder.order_no)
Index("idx_elder_orders_user", ElderOrder.user_id)
Index("idx_elder_jobs_user", ElderImageJob.user_id)
Index("idx_elder_jobs_status", ElderImageJob.status)
