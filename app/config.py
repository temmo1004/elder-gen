"""
Configuration Management with Pydantic Settings
環境變數設定 - 使用 pydantic-settings 進行型別安全的管理
"""
import sys
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError


class Settings(BaseSettings):
    """應用設定"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ============= LINE Bot =============
    LINE_CHANNEL_ACCESS_TOKEN: str
    LINE_CHANNEL_SECRET: str

    # ============= Database (Supabase Transaction Mode) =============
    DATABASE_URL: str

    # ============= Redis (Zeabur Internal) =============
    REDIS_URL: str = "redis://localhost:6379/0"

    # ============= Supabase API =============
    SUPABASE_URL: str
    SUPABASE_KEY: str  # Service Role Key (for backend operations)
    SUPABASE_STORAGE_BUCKET: str = "elder-images"

    # ============= NewebPay (藍新金流) =============
    NEWEBPAY_MERCHANT_ID: str
    NEWEBPAY_HASH_KEY: str
    NEWEBPAY_HASH_IV: str
    NEWEBPAY_RETURN_URL: str
    NEWEBPAY_NOTIFY_URL: str
    NEWEBPAY_CLIENT_BACK_URL: str  # 用戶付款完成後返回的前端 URL

    # ============= Banana Pro AI =============
    BANANA_API_KEY: str
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


try:
    settings = Settings()
except ValidationError as e:
    print("❌ 環境變數設定錯誤：")
    for error in e.errors():
        loc = " -> ".join(str(x) for x in error["loc"])
        print(f"   缺少必填變數: {loc}")
    print("\n請在 Zeabur 環境變數中設定這些值")
    sys.exit(1)
