"""
NewebPay Payment Service
藍新金流加密/解密與整合服務
"""
import hashlib
import urllib.parse
import binascii
import time
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from app.config import settings


class NewebPayService:
    """藍新金流服務"""

    def __init__(self):
        self.key = (settings.NEWEBPAY_HASH_KEY or "").encode("utf-8")
        self.iv = (settings.NEWEBPAY_HASH_IV or "").encode("utf-8")
        self.merchant_id = settings.NEWEBPAY_MERCHANT_ID or ""

    def _is_configured(self) -> bool:
        """檢查是否已設定"""
        return bool(self.key and self.iv and self.merchant_id)

    def _encrypt(self, data_dict: dict) -> str:
        """
        AES-256-CBC 加密
        1. 轉成 Query String
        2. AES Padding & Encrypt
        3. 轉 Hex
        """
        # 1. 轉成 Query String (排除空值)
        filtered_data = {k: v for k, v in data_dict.items() if v is not None and v != ""}
        raw_data = urllib.parse.urlencode(filtered_data)

        # 2. AES Padding & Encrypt
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        encrypted = cipher.encrypt(pad(raw_data.encode("utf-8"), AES.block_size))

        # 3. 轉 Hex (大寫)
        return binascii.hexlify(encrypted).decode("utf-8").upper()

    def _decrypt(self, trade_info_hex: str) -> dict:
        """
        AES-256-CBC 解密
        1. Hex 轉 Binary
        2. Decrypt & Unpad
        3. 解析 Query String 轉 Dict
        """
        try:
            # 1. Hex 轉 Binary
            encrypted_data = binascii.unhexlify(trade_info_hex)

            # 2. Decrypt & Unpad
            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)

            # 3. 解析 Query String 轉 Dict
            return dict(urllib.parse.parse_qsl(decrypted.decode("utf-8")))
        except Exception as e:
            raise ValueError(f"解密失敗: {e}")

    def create_checksum(self, trade_info: str) -> str:
        """
        建立 SHA256 Checksum
        格式: HashKey + TradeInfo + HashIV
        """
        # 藍新金流的 Checkbox 規則
        # HashKey + TradeInfo + HashIV → SHA256 → 轉大寫
        hash_key = settings.NEWEBPAY_HASH_KEY or ""
        hash_iv = settings.NEWEBPAY_HASH_IV or ""
        raw = f"{hash_key}{trade_info}{hash_iv}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()

    def create_payment_data(
        self,
        order_no: str,
        amount: int,
        product_name: str,
        user_email: str = "",
        user_name: str = ""
    ) -> dict:
        """
        建立付款資料（MPG 付款）
        """
        # 時間戳記
        timestamp = int(time.time())

        # 交易資料
        trade_data = {
            "MerchantOrderNo": order_no,
            "Amt": amount,
            "ItemDesc": product_name,
            "Email": user_email,
            "TimeStamp": timestamp,
        }

        # 加密交易資料
        trade_info = self._encrypt(trade_data)

        # 建立 Checksum
        trade_sha = self.create_checksum(trade_info)

        return {
            "MerchantID": self.merchant_id,
            "TradeInfo": trade_info,
            "TradeSha": trade_sha,
            "Version": "1.6",
        }

    def decrypt_notify_data(self, trade_info_hex: str) -> dict:
        """
        解密藍新金流的 Notify 資料
        回傳包含 Status, MerchantOrderNo 等欄位的 dict
        """
        return self._decrypt(trade_info_hex)

    def verify_checksum(self, trade_info: str, received_sha: str) -> bool:
        """
        驗證 Checksum 是否正確
        """
        calculated_sha = self.create_checksum(trade_info)
        return calculated_sha == received_sha

    def generate_order_no(self, user_id: int) -> str:
        """
        生成訂單號
        格式: EG + 年月日時 + 用戶ID後4碼 + 4位隨機數
        例: EG2501180112345678
        """
        now = datetime.now()
        date_str = now.strftime("%y%m%d%H")
        user_suffix = str(user_id)[-4:].zfill(4)
        import random
        random_suffix = random.randint(1000, 9999)
        return f"EG{date_str}{user_suffix}{random_suffix}"
