# UDA LINK 圖片存儲整合

## 日期
2026-01-20

## 問題描述
原本使用 Supabase Storage 直接存儲圖片，但需要整合到 UDA LINK 圖片託管服務，統一管理所有圖片。

## 解決方案
創建 Elder Gen 專用 VIP 用戶，使用 UDA LINK 現有的 `/upload-image` 端點上傳圖片。

### 實作步驟

1. **創建 VIP 用戶**
   - Email: `elder-gen@uda-link.internal`
   - 方案: PRO (10GB 儲存)
   - 使用 `create_elder_gen_user.py` 腳本自動創建

2. **環境變數設定**
   ```bash
   SUPABASE_URL=https://ngaiubuacbetqkxaecij.supabase.co
   ELDER_GEN_EMAIL=elder-gen@uda-link.internal
   ELDER_GEN_PASSWORD=<password>
   ```

3. **實作自動 Token 刷新**
   - 使用 `refresh_token` 刷新
   - 失敗時用 email/password 重新登入
   - 提前 5 分鐘刷新避免過期

## 修改檔案
| 檔案 | 變更 |
|------|------|
| `app/services/storage_service.py` | 改用 UDA LINK API + 自動刷新 |
| `app/config.py` | 改用 EMAIL/PASSWORD 環境變數 |
| `requirements.txt` | 移除 supabase，加入 pyjwt |
| `.env.example` | 更新環境變數說明 |

## API 端點
- 上傳: `POST /functions/v1/upload-image`
- 刪除: `POST /functions/v1/delete-image`
- 認證: `Bearer <access_token>`

## 注意事項
1. Access Token 約 1 小時過期
2. 系統會自動刷新，無需手動干預
3. 所有 Elder Gen 圖片都存在同一個 VIP 用戶下

## 相關檔案
- 腳本: `/WEB URL/image-hosting/create_elder_gen_user.py`
- 憑證: `/WEB URL/image-hosting/elder_gen_user_credentials.json`
