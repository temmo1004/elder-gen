"""
Celery Worker - 圖片生成背景任務
處理非同步的 AI 圖片生成工作
"""
import os
import uuid
from datetime import datetime
from celery import Celery
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal, Base, engine
from app import models
from app.services import ai_service, storage_service, line_service


# 初始化 Celery
celery_app = Celery(
    "elder_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery 設定
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Taipei",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 分鐘超時
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)


def get_db():
    """取得資料庫 Session"""
    return SessionLocal()


@celery_app.task(name="tasks.process_elder_image", bind=True, max_retries=3)
def process_elder_image(self, job_id: str, user_line_id: int, prompt: str, original_url: str = None):
    """
    處理長輩圖生成任務

    Args:
        job_id: 任務 ID
        user_line_id: 用戶 LINE User ID
        prompt: 文字提示
        original_url: 原圖 URL（可選）
    """
    import asyncio
    import httpx

    db = get_db()
    job = None

    try:
        # 1. 查詢任務記錄
        job = db.query(models.ElderImageJob).filter(
            models.ElderImageJob.job_id == job_id
        ).first()

        if not job:
            raise ValueError(f"找不到任務: {job_id}")

        # 2. 更新狀態為 PROCESSING
        job.status = "PROCESSING"
        db.commit()

        # 3. 呼叫 AI 生成圖片 (使用 asyncio.run 包裹異步函數)
        async def _process_image():
            ai_result = await ai_service.generate_from_url(
                image_url=original_url,
                prompt=prompt
            )

            if not ai_result["success"]:
                raise Exception(f"AI 生成失敗: {ai_result.get('error')}")

            # 4. 取得生成的圖片資料
            image_bytes = ai_result.get("image_bytes")
            result_url = ai_result.get("image_url")

            # 如果回傳的是 URL，需要下載
            if result_url and not image_bytes:
                async with httpx.AsyncClient() as client:
                    response = await client.get(result_url)
                    image_bytes = response.content

            # 5. 上傳到 UDA LINK Storage
            upload_result = await storage_service.upload_image(
                image_data=image_bytes,
                user_id=user_line_id,
                prefix="result"
            )

            if not upload_result["success"]:
                raise Exception(f"上傳失敗: {upload_result.get('error')}")

            return upload_result

        upload_result = asyncio.run(_process_image())
        final_url = upload_result["full_url"]

        # 6. 更新任務狀態為 COMPLETED
        job.result_url = final_url
        job.result_image_path = upload_result["path"]
        job.status = "COMPLETED"
        job.completed_at = datetime.now()
        db.commit()

        # 7. 推播結果到 LINE
        # 需要取得用戶的 LINE User ID
        user = db.query(models.ElderUser).filter(
            models.ElderUser.id == user_line_id
        ).first()

        if user:
            line_service.push_message(
                user.line_user_id,
                [
                    line_service.text_message("✅ 您的長輩圖生成完成！"),
                    line_service.image_message(final_url)
                ]
            )

        return {
            "success": True,
            "job_id": job_id,
            "result_url": final_url
        }

    except Exception as e:
        # 錯誤處理
        error_msg = str(e)

        if job:
            job.status = "FAILED"
            job.error_message = error_msg
            job.completed_at = datetime.now()

            # 退還點數
            user = db.query(models.ElderUser).filter(
                models.ElderUser.id == user_line_id
            ).first()

            if user:
                user.points += job.cost_points
                db.commit()

                # 通知用戶
                line_service.push_message(
                    user.line_user_id,
                    line_service.text_message(f"❌ 圖片生成失敗，點數已退還。\n錯誤: {error_msg}")
                )

        db.commit()

        # 重試邏輯
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

        return {
            "success": False,
            "error": error_msg
        }

    finally:
        db.close()


@celery_app.task(name="tasks.send_notification")
def send_notification(user_line_id: str, message: str):
    """
    發送 LINE 通知
    """
    try:
        line_service.push_message(
            user_line_id,
            [line_service.text_message(message)]
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# 啟動時建立資料表（如果不存在）
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """設定定時任務"""
    # 可以在這裡加入定時清理任務等
    pass


if __name__ == "__main__":
    # 啟動 Worker
    celery_app.start()
