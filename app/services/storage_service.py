"""
UDA LINK Image Hosting Service for Elder Gen
圖片上傳與管理服務 - 使用 Supabase Edge Functions + R2
支援自動 Token 刷新
"""
import uuid
import asyncio
from typing import Optional
from datetime import datetime, timedelta
import httpx
from app.config import settings


class StorageService:
    """UDA LINK 圖片託管服務 (使用 VIP 用戶，支援自動刷新 Token)"""

    # Supabase Auth API endpoint
    def __init__(self):
        self.base_url = settings.SUPABASE_URL
        self.email = settings.ELDER_GEN_EMAIL
        self.password = settings.ELDER_GEN_PASSWORD

        # Token 狀態
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._lock = asyncio.Lock()

    async def _get_valid_token(self) -> str:
        """取得有效的 access_token，必要時自動刷新"""
        async with self._lock:
            # 檢查是否需要刷新
            if self._access_token and self._token_expires_at:
                # 提前 5 分鐘刷新
                if datetime.now() + timedelta(minutes=5) < self._token_expires_at:
                    return self._access_token

            # 需要刷新或首次獲取
            await self._refresh_access_token()
            return self._access_token

    async def _refresh_access_token(self) -> bool:
        """刷新 access_token"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 嘗試用 refresh_token 刷新
                if self._refresh_token:
                    response = await client.post(
                        f"{self.base_url}/auth/v1/token?grant_type=refresh_token",
                        json={
                            "refresh_token": self._refresh_token
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()
                        self._access_token = data.get("access_token")
                        self._refresh_token = data.get("refresh_token", self._refresh_token)

                        # 解析過期時間
                        expires_in = data.get("expires_in", 3600)
                        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

                        print("✅ Token 刷新成功")
                        return True

            # refresh_token 失敗或不存在，重新登入
            if self.email and self.password:
                return await self._relogin()

            print("❌ 無法刷新 Token：缺少 email/password")
            return False

        except Exception as e:
            print(f"❌ Token 刷新失敗: {e}")
            # 嘗試重新登入
            if self.email and self.password:
                return await self._relogin()
            return False

    async def _relogin(self) -> bool:
        """重新登入獲取新的 token"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/auth/v1/token?grant_type=password",
                    json={
                        "email": self.email,
                        "password": self.password,
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    self._access_token = data.get("access_token")
                    self._refresh_token = data.get("refresh_token")

                    # 解析過期時間
                    expires_in = data.get("expires_in", 3600)
                    self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

                    print("✅ 重新登入成功")
                    return True
                else:
                    print(f"❌ 重新登入失敗: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            print(f"❌ 重新登入錯誤: {e}")
            return False

    @property
    def is_available(self) -> bool:
        """檢查服務是否可用"""
        return bool(self.base_url and self.email and self.password)

    async def upload_image(
        self,
        image_data: bytes,
        user_id: int,
        prefix: str = "original"
    ) -> dict:
        """
        上傳圖片到 UDA LINK (R2)
        使用現有的 /upload-image 端點，透過 Elder Gen VIP 用戶

        Args:
            image_data: 圖片二進位資料
            user_id: 用戶 ID (用於檔案命名)
            prefix: 檔案路徑前綴 (original/result)

        Returns:
            {
                "success": True,
                "path": "elder-gen/{user_id}/{prefix}/{filename}",
                "full_url": "https://r2...",
                "r2_path": "..."
            }
        """
        if not self.is_available:
            return {
                "success": False,
                "error": "UDA LINK 服務未設定 (缺少 ELDER_GEN_EMAIL 或 ELDER_GEN_PASSWORD)"
            }

        filename = f"{uuid.uuid4()}.png"
        path = f"elder-gen/{user_id}/{prefix}/{filename}"

        # 嘗試上傳，失敗時自動刷新 token 重試
        for attempt in range(2):  # 最多重試 1 次
            try:
                token = await self._get_valid_token()

                # 準備 multipart form data
                files = {
                    "file": (filename, image_data, "image/png")
                }

                headers = {
                    "Authorization": f"Bearer {token}"
                }

                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self.base_url}/functions/v1/upload-image",
                        files=files,
                        headers=headers
                    )

                    # 401 表示 token 過期，刷新後重試
                    if response.status_code == 401 and attempt == 0:
                        await self._refresh_access_token()
                        continue

                    response.raise_for_status()
                    result = response.json()

                if result.get("success"):
                    return {
                        "success": True,
                        "path": path,
                        "full_url": result["data"]["url"],
                        "filename": result["data"].get("fileName", filename),
                        "r2_path": result["data"].get("fileName", path)
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "上傳失敗"),
                        "path": path
                    }

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401 and attempt == 0:
                    await self._refresh_access_token()
                    continue
                return {
                    "success": False,
                    "error": f"HTTP 錯誤: {e.response.status_code}",
                    "path": path
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "path": path
                }

        return {
            "success": False,
            "error": "上傳失敗：無法獲取有效 token",
            "path": path
        }

    async def upload_image_from_url(
        self,
        image_url: str,
        user_id: int,
        prefix: str = "original"
    ) -> dict:
        """
        從 URL 下載圖片並上傳到 UDA LINK

        Args:
            image_url: 來源圖片 URL
            user_id: 用戶 ID
            prefix: 檔案路徑前綴

        Returns:
            上傳結果 dict
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                image_data = response.content

            return await self.upload_image(image_data, user_id, prefix)
        except Exception as e:
            return {
                "success": False,
                "error": f"下載圖片失敗: {str(e)}"
            }

    async def delete_image(self, image_id: str) -> bool:
        """
        刪除圖片

        Args:
            image_id: 圖片 ID (UUID)

        Returns:
            是否刪除成功
        """
        if not self.is_available:
            print("⚠️  UDA LINK 服務未設定，跳過刪除")
            return False

        # 嘗試刪除，失敗時自動刷新 token 重試
        for attempt in range(2):
            try:
                token = await self._get_valid_token()

                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }

                payload = {"imageId": image_id}

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.base_url}/functions/v1/delete-image",
                        headers=headers,
                        json=payload
                    )

                    # 401 表示 token 過期，刷新後重試
                    if response.status_code == 401 and attempt == 0:
                        await self._refresh_access_token()
                        continue

                    response.raise_for_status()
                    result = response.json()

                return result.get("success", False)

            except Exception as e:
                if attempt == 0:
                    await self._refresh_access_token()
                    continue
                print(f"刪除圖片失敗: {e}")
                return False

        return False

    def get_public_url(self, r2_path: str) -> str:
        """
        取得圖片的公開 URL
        (R2 URL 由上傳回應返回，這裡只作備用)

        Args:
            r2_path: R2 檔案路徑

        Returns:
            公開 URL
        """
        # R2 的公開 URL 應該由上傳回應返回
        if hasattr(settings, 'R2_PUBLIC_URL') and settings.R2_PUBLIC_URL:
            return f"{settings.R2_PUBLIC_URL}/{r2_path}"
        return r2_path


# 單例模式
storage_service = StorageService()
