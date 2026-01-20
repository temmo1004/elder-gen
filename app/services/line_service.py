"""
LINE Bot Service
LINE 訊息處理與回覆服務
"""
import hashlib
import base64
from typing import Optional, List
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage,
    TextSendMessage, ImageSendMessage,
    QuickReply, QuickReplyButton, MessageAction,
    FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent,
    TextComponent, ButtonComponent, SeparatorComponent, URIAction
)
from app.config import settings


class LineService:
    """LINE Bot 服務"""

    def __init__(self):
        self._api = None
        self._handler = None
        self.channel_secret = settings.LINE_CHANNEL_SECRET or ""
        self._initialized = False

    def _ensure_initialized(self):
        """延遲初始化，直到環境變數設定完成"""
        if not self._initialized and settings.LINE_CHANNEL_ACCESS_TOKEN:
            self._api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
            self._handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
            self._initialized = True

    @property
    def api(self):
        self._ensure_initialized()
        return self._api

    @property
    def handler(self):
        self._ensure_initialized()
        return self._handler

    def verify_signature(self, body: bytes, signature: str) -> bool:
        """
        驗證 LINE Webhook Signature
        """
        if not self.channel_secret:
            return False
        hash_value = hashlib.sha256(self.channel_secret.encode("utf-8") + body).digest()
        calculated_signature = base64.b64encode(hash_value).decode()

        # 處理不同的 signature 格式
        received_signature = signature.replace("Bearer ", "").strip()

        return calculated_signature == received_signature

    def reply_message(self, reply_token: str, messages: List):
        """
        回覆訊息
        """
        try:
            self.api.reply_message(reply_token, messages)
            return True
        except LineBotApiError as e:
            print(f"LINE 回覆失敗: {e}")
            return False

    def push_message(self, to: str, messages: List):
        """
        主動推播訊息
        """
        try:
            self.api.push_message(to, messages)
            return True
        except LineBotApiError as e:
            print(f"LINE 推播失敗: {e}")
            return False

    def get_user_profile(self, user_id: str) -> Optional[dict]:
        """
        取得用戶資料
        """
        try:
            profile = self.api.get_profile(user_id)
            return {
                "user_id": profile.user_id,
                "display_name": profile.display_name,
                "picture_url": profile.picture_url,
                "status_message": profile.status_message,
            }
        except LineBotApiError as e:
            print(f"取得用戶資料失敗: {e}")
            return None

    # ============= 訊息模板 =============
    @staticmethod
    def text_message(text: str) -> TextSendMessage:
        """文字訊息"""
        return TextSendMessage(text=text)

    @staticmethod
    def image_message(original_url: str, preview_url: Optional[str] = None) -> ImageSendMessage:
        """圖片訊息"""
        return ImageSendMessage(
            original_content_url=original_url,
            preview_image_url=preview_url or original_url
        )

    @staticmethod
    def create_menu_flex() -> FlexSendMessage:
        """
        建立主選單 Flex Message
        """
        bubble = BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(text="長輩圖販賣機", weight="bold", size="xl"),
                    TextComponent(
                        text="選擇您要的功能",
                        size="md",
                        color="#666666",
                        margin="md"
                    ),
                    BoxComponent(
                        layout="vertical",
                        spacing="sm",
                        contents=[
                            ButtonComponent(
                                style="primary",
                                action=MessageAction(label="生成長輩圖", text="/generate"),
                                height="md"
                            ),
                            ButtonComponent(
                                action=MessageAction(label="查詢點數", text="/points"),
                                height="md"
                            ),
                            ButtonComponent(
                                action=MessageAction(label="儲值點數", text="/topup"),
                                height="md"
                            ),
                            ButtonComponent(
                                action=MessageAction(label="我的作品", text="/history"),
                                height="md"
                            ),
                        ]
                    )
                ]
            )
        )

        return FlexSendMessage(alt_text="主選單", contents=bubble)

    @staticmethod
    def create_quick_reply(buttons: List[tuple[str, str]]) -> QuickReply:
        """
        建立 Quick Reply
        buttons: [("顯示文字", "回傳文字"), ...]
        """
        items = [
            QuickReplyButton(
                action=MessageAction(label=label, text=text)
            )
            for label, text in buttons
        ]
        return QuickReply(items=items)


# 單例模式
line_service = LineService()
