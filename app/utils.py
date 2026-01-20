"""
共用工具函數
"""
from typing import Optional
from sqlalchemy.orm import Session
from app import models
from app.config import settings


def get_or_create_user_in_db(
    db: Session,
    line_user_id: str,
    profile: Optional[dict] = None
) -> models.ElderUser:
    """
    取得或建立用戶（共用函數）

    Args:
        db: 資料庫 Session
        line_user_id: LINE User ID
        profile: LINE 用戶資料 (可選)

    Returns:
        ElderUser 物件
    """
    user = db.query(models.ElderUser).filter(
        models.ElderUser.line_user_id == line_user_id
    ).first()

    if not user:
        user = models.ElderUser(
            line_user_id=line_user_id,
            display_name=profile.get("display_name") if profile else None,
            picture_url=profile.get("picture_url") if profile else None,
            points=settings.FREE_INITIAL_POINTS,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    elif profile:
        # 更新資料
        user.display_name = profile.get("display_name")
        user.picture_url = profile.get("picture_url")
        db.commit()
        db.refresh(user)

    return user
