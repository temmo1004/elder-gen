# Project ElderGen - 長輩圖自動販賣機

## 專案概述

LINE Bot 自動化長輩圖生成服務，用戶上傳照片 → AI 生成 → 推播結果。

## 架構

```
┌─────────────┐     Webhook     ┌──────────────┐
│  LINE User  │ ───────────────→ │  Zeabur API  │
└─────────────┘                  └──────────────┘
                                          │
                                          ▼
                                   ┌─────────────┐
                                   │   Redis     │
                                   └─────────────┘
                                          │
                                          ▼
┌─────────────┐                      ┌──────────────┐
│  LINE User  │ ←── Push Message ─── │ Zeabur Worker│
└─────────────┘                      └──────────────┘
                                          │
                              ┌───────────┼───────────┐
                              ▼           ▼           ▼
                        ┌─────────┐ ┌─────────┐ ┌──────────┐
                        │Banana Pro│ │Supabase │ │ Supabase │
                        │   AI    │ │ Storage │ │    DB    │
                        └─────────┘ └─────────┘ └──────────┘
```

## 目錄結構

```
elder-gen/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 主程式
│   ├── worker.py            # Celery Worker
│   ├── config.py            # 環境變數設定
│   ├── database.py          # 資料庫連線
│   ├── models.py            # SQLAlchemy ORM
│   ├── schemas.py           # Pydantic 驗證
│   ├── api/
│   │   └── line_handler.py  # LINE 事件處理
│   └── services/
│       ├── line_service.py
│       ├── ai_service.py
│       ├── storage_service.py
│       └── payment_service.py
├── Dockerfile.api           # API 服務 Dockerfile
├── Dockerfile.worker        # Worker 服務 Dockerfile
├── requirements.txt
├── supabase_init.sql        # 資料庫初始化腳本
└── .env.example             # 環境變數範例
```

## 部署步驟

### 1. Supabase 設定

1. 登入 Supabase Dashboard
2. 開啟 SQL Editor，執行 `supabase_init.sql`
3. 建立 Storage Bucket：
   - 名稱：`elder-images`
   - Public Bucket：開啟

### 2. LINE Developers 設定

1. 登入 [LINE Developers Console](https://developers.line.biz/)
2. 建立 Messaging Channel
3. 取得 `CHANNEL_ACCESS_TOKEN` 和 `CHANNEL_SECRET`
4. 設定 Webhook URL：`https://your-api.zeabur.app/callback/line`

### 3. Banana Pro 註冊

1. 註冊 [Banana Pro](https://banana.dev)
2. 取得 API Key

### 4. Zeabur 部署

#### 新增 Redis
```
Zeabur Dashboard → Marketplace → Redis → Deploy
```

#### 部署 API 服務
```
Zeabur Dashboard → New Service → Git
→ 選擇 GitHub Repo
→ Dockerfile 路徑：Dockerfile.api
→ 設定環境變數
→ Deploy
```

#### 部署 Worker 服務
```
Zeabur Dashboard → New Service → Git
→ 選擇同一個 GitHub Repo
→ Dockerfile 路徑：Dockerfile.worker
→ 設定環境變數
→ Deploy
```

### 5. 環境變數

在 Zeabur 各服務中設定：

| 變數名稱 | 說明 | 範例 |
|---------|------|------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot Token | `...` |
| `LINE_CHANNEL_SECRET` | LINE Secret | `...` |
| `DATABASE_URL` | Supabase 連線 | `postgresql://...` |
| `REDIS_URL` | Redis 連線 | `redis://...` |
| `SUPABASE_URL` | Supabase URL | `https://...` |
| `SUPABASE_KEY` | Service Role Key | `...` |
| `BANANA_API_KEY` | Banana Pro Key | `...` |

## 本地開發

```bash
# 安裝依賴
pip install -r requirements.txt

# 複製環境變數
cp .env.example .env
# 編輯 .env 填入設定

# 啟動 Redis (需要 Docker)
docker run -d -p 6379:6379 redis

# 啟動 API
uvicorn app.main:app --reload

# 啟動 Worker (另一個終端)
celery -A app.worker worker --loglevel=info
```

## API 端點

| 端點 | 說明 |
|------|------|
| `GET /health` | 健康檢查 |
| `POST /callback/line` | LINE Webhook |
| `POST /callback/newebpay` | 藍新金流 Webhook |
| `GET /api/user/{line_user_id}` | 取得用戶資料 |
| `GET /api/jobs/{job_id}` | 查詢任務狀態 |

## LINE Bot 指令

| 指令 | 說明 |
|------|------|
| `/menu` | 顯示主選單 |
| `/generate` | 生成長輩圖 |
| `/points` | 查詢點數 |
| `/topup` | 儲值點數 |
| `/history` | 我的作品 |
| 上傳圖片 | 開始生成任務 |

## 授權

MIT License
