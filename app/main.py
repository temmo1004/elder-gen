"""
FastAPI Main Application
Project ElderGen - 長輩圖自動販賣機
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from linebot.exceptions import InvalidSignatureError

from app.config import settings
from app.database import engine, get_db, init_db
from app import models, schemas
from app.services import line_service, storage_service, payment_service


# ============= Lifespan Events =============
@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用啟動/關閉時的生命週期管理"""
    # 啟動時執行
    print(f"🚀 {settings.APP_NAME} 啟動中...")
    print(f"📦 環境: {settings.ENVIRONMENT}")

    # 檢查是否已設定環境變數
    if not settings.is_configured():
        print("⚠️  警告: 環境變數未完全設定，部分功能將無法使用")
        print("⚠️  請在 Zeabur 設定以下環境變數:")
        print("   - LINE_CHANNEL_ACCESS_TOKEN")
        print("   - LINE_CHANNEL_SECRET")
        print("   - DATABASE_URL")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_KEY")
        print("   - BANANA_API_KEY")
    else:
        # 確保資料表存在
        init_db()
        print("✅ 資料庫初始化完成")

        # 確保 Storage Bucket 存在
        await storage_service.ensure_bucket_exists()
        print("✅ Storage Bucket 準備完成")

    yield

    # 關閉時執行
    print("👋 應用關閉中...")


# ============= FastAPI App =============
app = FastAPI(
    title=settings.APP_NAME,
    description="長輩圖自動販賣機 API",
    version="1.0.0",
    lifespan=lifespan,
)


# ============= Health Check =============
@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "timestamp": datetime.now().isoformat()
    }


# ============= LINE Webhook =============
@app.post("/callback/line")
async def line_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    LINE Bot Webhook
    處理來自 LINE 的訊息事件
    """
    # 取得請求內容
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    # 驗證簽章
    if not line_service.verify_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 解析事件
    from app.api.line_handler import handle_line_events
    background_tasks.add_task(handle_line_events, body.decode("utf-8"))

    return {"status": "ok"}


# ============= NewebPay Webhook =============
@app.post("/callback/newebpay")
async def newebpay_notify(request: Request, db: Session = Depends(get_db)):
    """
    藍新金流 Webhook (Notify URL)
    處理付款完成通知
    """
    form_data = await request.form()
    status = form_data.get("Status")
    trade_info = form_data.get("TradeInfo")
    trade_sha = form_data.get("TradeSha")

    if not trade_info:
        raise HTTPException(status_code=400, detail="Missing TradeInfo")

    # 解密資料
    try:
        data = payment_service.decrypt_notify_data(trade_info)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解密失敗: {e}")

    # 驗證 Checksum
    if not payment_service.verify_checksum(trade_info, trade_sha):
        raise HTTPException(status_code=400, detail="Checksum 驗證失敗")

    # 處理付款結果
    if status == "SUCCESS":
        order_no = data.get("MerchantOrderNo")
        await handle_payment_success(db, order_no, data)

    return "OK"


async def handle_payment_success(db: Session, order_no: str, payment_data: dict):
    """處理付款成功邏輯"""
    order = db.query(models.ElderOrder).filter(
        models.ElderOrder.order_no == order_no
    ).first()

    if not order:
        print(f"找不到訂單: {order_no}")
        return

    if order.status == "PAID":
        print(f"訂單 {order_no} 已經處理過了")
        return

    # 更新訂單狀態
    order.status = "PAID"
    order.neweb_trade_no = payment_data.get("TradeNo")
    order.neweb_payment_type = payment_data.get("PaymentType")
    order.pay_time = datetime.now()

    # 加點數
    user = db.query(models.ElderUser).filter(
        models.ElderUser.id == order.user_id
    ).first()

    if user:
        user.points += order.points_added

    db.commit()

    # 通知用戶
    line_service.push_message(
        user.line_user_id,
        [line_service.text_message(f"💰 儲值成功！獲得 {order.points_added} 點")]
    )


# ============= API Routes =============
@app.get("/api/user/{line_user_id}", response_model=schemas.UserResponse)
async def get_user(line_user_id: str, db: Session = Depends(get_db)):
    """取得用戶資料"""
    user = db.query(models.ElderUser).filter(
        models.ElderUser.line_user_id == line_user_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="找不到用戶")

    return user


@app.post("/api/user", response_model=schemas.UserResponse)
async def create_or_get_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """建立或取得用戶"""
    user = db.query(models.ElderUser).filter(
        models.ElderUser.line_user_id == user_data.line_user_id
    ).first()

    if user:
        # 更新顯示名稱
        user.display_name = user_data.display_name
        user.picture_url = user_data.picture_url
    else:
        # 建立新用戶
        user = models.ElderUser(
            line_user_id=user_data.line_user_id,
            display_name=user_data.display_name,
            picture_url=user_data.picture_url,
            points=settings.FREE_INITIAL_POINTS,  # 新用戶免費點數
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    return user


@app.get("/api/jobs/{job_id}", response_model=schemas.ImageJobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """查詢圖片生成任務狀態"""
    job = db.query(models.ElderImageJob).filter(
        models.ElderImageJob.job_id == job_id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="找不到任務")

    return job


@app.get("/api/user/{user_id}/jobs", response_model=list[schemas.ImageJobResponse])
async def get_user_jobs(
    user_id: int,
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0
):
    """取得用戶的圖片生成記錄"""
    jobs = db.query(models.ElderImageJob).filter(
        models.ElderImageJob.user_id == user_id
    ).order_by(models.ElderImageJob.created_at.desc()).offset(offset).limit(limit).all()

    return jobs


# ============= Error Handlers =============
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    print(f"未預期的錯誤: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "內部伺服器錯誤"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
