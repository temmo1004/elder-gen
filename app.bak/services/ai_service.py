"""
Banana Pro AI Service
AI 圖片生成服務
"""
import httpx
from typing import Optional, Literal
from app.config import settings


class BananaProService:
    """Banana Pro AI 服務"""

    def __init__(self):
        self.api_key = settings.BANANA_API_KEY or ""
        self.model_key = settings.BANANA_MODEL_KEY or ""
        self.base_url = "https://api.banana.dev"

    def _is_configured(self) -> bool:
        """檢查是否已設定"""
        return bool(self.api_key)

    async def generate_image(
        self,
        prompt: str,
        image_url: Optional[str] = None,  # 如果有提供圖片，做 img2img
        style: Literal["realistic", "anime", "sketch", "painting"] = "realistic",
        strength: float = 0.7,
    ) -> dict:
        """
        生成長輩圖

        Args:
            prompt: 文字提示
            image_url: 來源圖片 URL (img2img)
            style: 風格
            strength: 變化強度 (0.1-1.0)

        Returns:
            {
                "success": True/False,
                "image_url": "...",
                "image_bytes": b"...",
                "error": "..."
            }
        """
        try:
            # Banana Pro API 呼叫
            # 注意: 這裡需要根據實際的 Banana Pro API 文件調整
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # 建構請求 payload
            payload = self._build_payload(prompt, image_url, style, strength)

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

            # 處理回傳結果
            if "image_url" in result:
                return {
                    "success": True,
                    "image_url": result["image_url"]
                }
            elif "image_base64" in result:
                import base64
                image_bytes = base64.b64decode(result["image_base64"])
                return {
                    "success": True,
                    "image_bytes": image_bytes
                }
            else:
                return {
                    "success": False,
                    "error": "未知的回應格式"
                }

        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"API 呼叫失敗: {e.response.status_code}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _build_payload(
        self,
        prompt: str,
        image_url: Optional[str],
        style: str,
        strength: float
    ) -> dict:
        """
        建構 API Payload
        """
        # 根據風格調整 prompt
        style_prompts = {
            "realistic": "realistic photo, high quality, detailed, 8k",
            "anime": "anime style, vibrant colors, detailed illustration",
            "sketch": "pencil sketch, artistic, hand-drawn",
            "painting": "oil painting style, classic art, masterpiece"
        }

        enhanced_prompt = f"{prompt}, {style_prompts.get(style, style_prompts['realistic'])}"

        payload = {
            "model": self.model_key or "stable-diffusion-xl",
            "prompt": enhanced_prompt,
            "negative_prompt": "ugly, blurry, low quality, distorted, deformed",
            "width": 1024,
            "height": 1024,
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
        }

        # 如果有來源圖片，做 img2img
        if image_url:
            payload["init_image"] = image_url
            payload["strength"] = strength

        return payload

    async def generate_from_url(self, image_url: str, prompt: str = "") -> dict:
        """
        從 URL 下載圖片並生成長輩圖

        Args:
            image_url: 用戶上傳的圖片 URL
            prompt: 額外的文字提示

        Returns:
            生成結果 dict
        """
        # 預設長輩圖 prompt
        default_prompt = (
            "elderly person meme, funny expression, "
            "exaggerated facial features, humorous, "
            "social media meme style"
        )

        final_prompt = f"{prompt} {default_prompt}" if prompt else default_prompt

        return await self.generate_image(
            prompt=final_prompt,
            image_url=image_url,
            style="realistic",
            strength=0.6
        )


# 單例模式
ai_service = BananaProService()
