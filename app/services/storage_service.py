"""
Supabase Storage Service
圖片上傳與管理服務
"""
import io
import uuid
from typing import Optional
from supabase import create_client, Client
from app.config import settings


class StorageService:
    """Supabase Storage 服務"""

    def __init__(self):
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        self.bucket_name = settings.SUPABASE_STORAGE_BUCKET

    async def ensure_bucket_exists(self) -> bool:
        """確保 Bucket 存在"""
        try:
            # 檢查 Bucket 是否存在
            buckets = self.client.storage.list_buckets()
            bucket_names = [b.name for b in buckets]

            if self.bucket_name not in bucket_names:
                # 建立 Bucket
                self.client.storage.create_bucket(
                    id=self.bucket_name,
                    options={"public": True}
                )
                # 設定公開存取政策
                self.client.storage.set_public_acl(self.bucket_name)
                return True
            return True
        except Exception as e:
            print(f"檢查 Bucket 失敗: {e}")
            return False

    async def upload_image(
        self,
        image_data: bytes,
        user_id: int,
        prefix: str = "original"
    ) -> dict:
        """
        上傳圖片到 Supabase Storage

        Args:
            image_data: 圖片二進位資料
            user_id: 用戶 ID
            prefix: 檔案路徑前綴 (original/result)

        Returns:
            {
                "path": "elder-images/123/uuid.png",
                "full_url": "https://...",
                "success": True
            }
        """
        filename = f"{uuid.uuid4()}.png"
        path = f"{user_id}/{prefix}/{filename}"

        try:
            # 上傳檔案
            self.client.storage.from_(self.bucket_name).upload(
                path=path,
                file=image_data,
                file_options={"content-type": "image/png"}
            )

            # 取得公開 URL
            full_url = self.client.storage.from_(self.bucket_name).get_public_url(path)

            return {
                "success": True,
                "path": path,
                "full_url": full_url,
                "filename": filename
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": path
            }

    async def upload_image_from_url(
        self,
        image_url: str,
        user_id: int,
        prefix: str = "original"
    ) -> dict:
        """
        從 URL 下載圖片並上傳到 Supabase

        Args:
            image_url: 來源圖片 URL
            user_id: 用戶 ID
            prefix: 檔案路徑前綴

        Returns:
            上傳結果 dict
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                image_data = response.content

            return await self.upload_image(image_data, user_id, prefix)
        except Exception as e:
            return {
                "success": False,
                "error": f"下傳圖片失敗: {str(e)}"
            }

    def delete_image(self, path: str) -> bool:
        """刪除圖片"""
        try:
            self.client.storage.from_(self.bucket_name).remove([path])
            return True
        except Exception as e:
            print(f"刪除圖片失敗: {e}")
            return False

    def get_public_url(self, path: str) -> str:
        """取得圖片的公開 URL"""
        return self.client.storage.from_(self.bucket_name).get_public_url(path)


# 單例模式
storage_service = StorageService()
