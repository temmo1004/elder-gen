"""
LINE Event Handler
處理 LINE Bot 的各種事件
"""
import json
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage,
    PostbackEvent, FollowEvent, UnfollowEvent
)

from app.config import settings
from app.database import SessionLocal
from app import models
from app.services import line_service
from app.worker import process_elder_image
from app.utils import get_or_create_user_in_db


def handle_line_events(body: str, signature: str):
    """
    處理 LINE Webhook 事件

    Args:
        body: 請求 body (JSON string)
        signature: LINE 簽章 (X-Line-Signature header)
    """
    from linebot import WebhookHandler
    from app.config import settings

    handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)

    # 註冊事件處理器
    handler.add(MessageEvent, message=TextMessage, handle_text_message)
    handler.add(MessageEvent, message=ImageMessage, handle_image_message)
    handler.add(PostbackEvent, handle_postback)
    handler.add(FollowEvent, handle_follow)
    handler.add(UnfollowEvent, handle_unfollow)

    # 解析並處理事件（handler 會自動驗證簽章）
    handler.handle(body, signature)


def get_or_create_user(line_user_id: str, profile: dict = None) -> models.ElderUser:
    """
    取得或建立用戶（使用共用函數）

    Args:
        line_user_id: LINE User ID
        profile: LINE 用戶資料 (可選)

    Returns:
        ElderUser 物件
    """
    db: Session = SessionLocal()
    try:
        return get_or_create_user_in_db(db, line_user_id, profile)
    finally:
        db.close()


def handle_text_message(event: MessageEvent):
    """處理文字訊息"""
    line_user_id = event.source.user_id
    text = event.message.text.strip()

    # 取得或建立用戶
    profile = line_service.get_user_profile(line_user_id)
    user = get_or_create_user(line_user_id, profile)

    # 指令處理
    if text == "/menu" or text == "選單":
        line_service.reply_message(
            event.reply_token,
            [line_service.create_menu_flex()]
        )
        return

    elif text == "/points" or text == "點數":
        line_service.reply_message(
            event.reply_token,
            [line_service.text_message(f"💰 您的點數: {user.points}")]
        )
        return

    elif text == "/topup" or text == "儲值":
        # 建立儲值連結
        topup_url = f"{settings.NEWEBPAY_CLIENT_BACK_URL}/topup?user_id={user.id}"
        line_service.reply_message(
            event.reply_token,
            [line_service.text_message(f"💳 點擊下方連結儲值\n{topup_url}")]
        )
        return

    elif text == "/history" or text == "我的作品":
        # 查詢最近的生成記錄
        db: Session = SessionLocal()
        jobs = db.query(models.ElderImageJob).filter(
            models.ElderImageJob.user_id == user.id,
            models.ElderImageJob.status == "COMPLETED"
        ).order_by(models.ElderImageJob.created_at.desc()).limit(5).all()
        db.close()

        if jobs:
            text_msg = "📸 最近的作品:\n\n"
            for i, job in enumerate(jobs, 1):
                text_msg += f"{i}. {job.created_at.strftime('%m/%d %H:%M')}\n"
            line_service.reply_message(
                event.reply_token,
                [line_service.text_message(text_msg)]
            )
        else:
            line_service.reply_message(
                event.reply_token,
                [line_service.text_message("還沒有作品哦，快來生成一張吧！")]
            )
        return

    elif text.startswith("/generate ") or text.startswith("生成 "):
        # 處理生成指令 (例如: /generate 可愛的老人)
        prompt = text.replace("/generate ", "").replace("生成 ", "")
        # 繼續請用戶上傳圖片
        line_service.reply_message(
            event.reply_token,
            [line_service.text_message("請上傳一張照片，我會根據您的提示生成長輩圖")]
        )
        return

    # 預設回應
    line_service.reply_message(
        event.reply_token,
        [
            line_service.text_message(
                "👋 歡迎來到長輩圖販賣機！\n\n"
                "指令列表:\n"
                "📸 /generate - 生成長輩圖\n"
                "💰 /points - 查詢點數\n"
                "💳 /topup - 儲值點數\n"
                "📚 /history - 我的作品\n"
                "📋 /menu - 主選單"
            )
        ]
    )


def handle_image_message(event: MessageEvent):
    """處理圖片訊息 - 用戶上傳要處理的照片"""
    line_user_id = event.source.user_id
    message_id = event.message.id

    # 取得或建立用戶
    profile = line_service.get_user_profile(line_user_id)
    user = get_or_create_user(line_user_id, profile)

    # 檢查點數
    if user.points < settings.POINTS_PER_IMAGE:
        line_service.reply_message(
            event.reply_token,
            [line_service.text_message(
                f"❌ 點數不足！\n"
                f"需要 {settings.POINTS_PER_IMAGE} 點，您目前有 {user.points} 點\n"
                f"請使用 /topup 儲值"
            )]
        )
        return

    # 取得圖片內容
    image_content = line_service.api.get_message_content(message_id)
    image_data = image_content.content

    # 上傳原圖到 Supabase
    import asyncio
    from app.services import storage_service

    upload_result = asyncio.run(storage_service.upload_image(
        image_data=image_data,
        user_id=user.id,
        prefix="original"
    ))

    if not upload_result["success"]:
        line_service.reply_message(
            event.reply_token,
            [line_service.text_message("❌ 圖片上傳失敗，請稍後再試")]
        )
        return

    # 扣除點數
    user.points -= settings.POINTS_PER_IMAGE
    db: Session = SessionLocal()
    db.commit()
    db.close()

    # 建立任務記錄
    job_id = str(uuid.uuid4())
    db: Session = SessionLocal()
    job = models.ElderImageJob(
        job_id=job_id,
        user_id=user.id,
        original_url=upload_result["full_url"],
        original_image_path=upload_result["path"],
        status="QUEUED",
        cost_points=settings.POINTS_PER_IMAGE,
    )
    db.add(job)
    db.commit()
    db.close()

    # 提交 Celery 任務
    process_elder_image.delay(
        job_id=job_id,
        user_line_id=user.id,
        prompt="elderly person meme",
        original_url=upload_result["full_url"]
    )

    # 回覆用戶
    line_service.reply_message(
        event.reply_token,
        [line_service.text_message(
            f"✅ 圖片已上傳！\n"
            f"消耗 {settings.POINTS_PER_IMAGE} 點，剩餘 {user.points} 點\n"
            f"預計 30 秒內完成，請稍候..."
        )]
    )


def handle_postback(event: PostbackEvent):
    """處理 Postback 事件（用戶點擊按鈕）"""
    data = event.postback.data

    if data == "menu":
        line_service.reply_message(
            event.reply_token,
            [line_service.create_menu_flex()]
        )
    elif data == "generate":
        line_service.reply_message(
            event.reply_token,
            [line_service.text_message("請上傳一張照片，我會生成長輩圖")]
        )
    elif data == "points":
        line_service.reply_message(
            event.reply_token,
            [line_service.text_message("查詢點數中...")]
        )


def handle_follow(event: FollowEvent):
    """處理用戶加入好友"""
    line_user_id = event.source.user_id
    profile = line_service.get_user_profile(line_user_id)
    user = get_or_create_user(line_user_id, profile)

    line_service.reply_message(
        event.reply_token,
        [
            line_service.text_message(
                f"👋 歡迎 {user.display_name or '您'}！\n\n"
                f"送您 {settings.FREE_INITIAL_POINTS} 點免費點數\n"
                f"現在就可以生成長輩圖了！"
            ),
            line_service.create_menu_flex()
        ]
    )


def handle_unfollow(event: UnfollowEvent):
    """處理用戶刪除好友"""
    # 可以選擇保留或清理用戶資料
    pass
