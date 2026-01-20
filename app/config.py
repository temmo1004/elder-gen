"""
Configuration Management with Pydantic Settings
環境變數設定 - 使用 pydantic-settings 進行型別安全的管理
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """應用設定"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ============= LINE Bot =============
    LINE_CHANNEL_ACCESS_TOKEN: Optional[str] = None
    LINE_CHANNEL_SECRET: Optional[str] = None

    # ============= Database (Supabase Transaction Mode) =============
    DATABASE_URL: Optional[str] = None

    # ============= Redis (Zeabur Internal) =============
    REDIS_URL: str = "redis://localhost:6379/0"

    # ============= UDA LINK Image Hosting (Elder Gen) =============
    SUPABASE_URL: Optional[str] = None
    ELDER_GEN_EMAIL: Optional[str] = None  # Elder Gen VIP 用戶 Email
    ELDER_GEN_PASSWORD: Optional[str] = None  # Elder Gen VIP 用戶 Password
    R2_PUBLIC_URL: Optional[str] = None  # R2 公開 URL (可選，上傳回應已包含完整 URL)

    # ============= NewebPay (藍新金流) =============
    NEWEBPAY_MERCHANT_ID: Optional[str] = None
    NEWEBPAY_HASH_KEY: Optional[str] = None
    NEWEBPAY_HASH_IV: Optional[str] = None
    NEWEBPAY_RETURN_URL: Optional[str] = None
    NEWEBPAY_NOTIFY_URL: Optional[str] = None
    NEWEBPAY_CLIENT_BACK_URL: Optional[str] = None  # 用戶付款完成後返回的前端 URL

    # ============= Banana Pro AI =============
    BANANA_API_KEY: Optional[str] = None
    BANANA_MODEL_KEY: str = ""

    # ============= App Settings =============
    APP_NAME: str = "ElderGen API"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"  # development, staging, production

    # Points system
    POINTS_PER_IMAGE: int = 10  # 每次生成消耗點數
    FREE_INITIAL_POINTS: int = 50  # 新用戶免費點數

    # Celery
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 如果沒有單獨設定 Celery URL，使用 Redis
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL

    def is_configured(self) -> bool:
        """檢查必要的環境變數是否已設定"""
        required = [
            self.LINE_CHANNEL_ACCESS_TOKEN,
            self.LINE_CHANNEL_SECRET,
            self.DATABASE_URL,
            self.SUPABASE_URL,
            self.ELDER_GEN_EMAIL,
            self.ELDER_GEN_PASSWORD,
            self.BANANA_API_KEY,
        ]
        return all(required)


settings = Settings()
