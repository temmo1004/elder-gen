"""
Pydantic Schemas for Request/Response Validation
API 請求/回應的資料驗證模型
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal


# ============= User Schemas =============
class UserBase(BaseModel):
    """用戶基本資料"""
    line_user_id: str = Field(..., max_length=64)


class UserCreate(UserBase):
    """建立用戶"""
    display_name: Optional[str] = Field(None, max_length=100)
    picture_url: Optional[str] = None


class UserResponse(BaseModel):
    """用戶回應"""
    id: int
    line_user_id: str
    display_name: Optional[str]
    points: int
    is_vip: bool
    total_images_generated: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Order Schemas =============
class OrderCreate(BaseModel):
    """建立訂單"""
    user_id: int
    amount: int = Field(..., gt=0, description="金額（分）")
    points_added: int = Field(..., gt=0)


class OrderResponse(BaseModel):
    """訂單回應"""
    id: int
    order_no: str
    user_id: int
    amount: int
    points_added: int
    status: Literal["PENDING", "PAID", "FAILED", "EXPIRED"]
    neweb_trade_no: Optional[str]
    pay_time: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Payment Schemas =============
class NewebPayPaymentRequest(BaseModel):
    """藍新金流付款請求"""
    order_no: str
    amount: int
    product_name: str = "長輩圖點數"
    return_url: str


class NewebPayPaymentResponse(BaseModel):
    """藍新金流付款回應"""
    merchant_id: str
    trade_info: str
    trade_sha: str
    version: str


# ============= Image Job Schemas =============
class ImageJobCreate(BaseModel):
    """建立圖片生成任務"""
    user_id: int
    prompt: Optional[str] = None
    original_url: Optional[str] = None
    original_image_path: Optional[str] = None


class ImageJobResponse(BaseModel):
    """圖片任務回應"""
    job_id: str
    user_id: int
    prompt_used: Optional[str]
    original_url: Optional[str]
    result_url: Optional[str]
    status: Literal["QUEUED", "PROCESSING", "COMPLETED", "FAILED"]
    error_message: Optional[str]
    cost_points: int
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============= LINE Webhook Schemas =============
class LineEventBase(BaseModel):
    """LINE Event 基礎"""
    type: str
    timestamp: int
    source: dict
    replyToken: Optional[str] = None


class LineMessageEvent(LineEventBase):
    """LINE 訊息 Event"""
    message: dict


class LinePostbackEvent(LineEventBase):
    """LINE Postback Event（按鈕互動）"""
    postback: dict


class LineWebhookRequest(BaseModel):
    """LINE Webhook 請求"""
    destination: str
    events: list[dict]


# ============= API Response Wrappers =============
class ApiResponse(BaseModel):
    """API 統一回應格式"""
    success: bool
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """錯誤回應"""
    success: bool = False
    error: str
    detail: Optional[str] = None
