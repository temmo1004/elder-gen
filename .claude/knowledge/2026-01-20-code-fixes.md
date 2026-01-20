# Elder Gen 代碼審查修復記錄

## 日期
2026-01-20

## 審查評分
- 修正前：5.5/10 (🔴 5 個高嚴重度問題)
- 修正後：7.5/10 (🔴 0 個高嚴重度問題)

---

## 🔴 高嚴重度問題修復

### 1. 資料庫連線洩漏 (worker.py:38-44)
**問題**
```python
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # 沒有關閉連線！
```

**根本原因**
finally 區塊只有 `pass`，導致資料庫連線未被關閉。

**解決方案**
簡化函數，直接返回 SessionLocal()，由呼叫者負責關閉連線。
```python
def get_db():
    return SessionLocal()
```

---

### 2. Celery task 同步/異步混用 (worker.py:47-78)
**問題**
Celery task 標記為同步函數，但內部使用 `await` 呼叫異步函數。

**根本原因**
Celery 預設是同步框架，不能直接在 task 函數內使用 `await`。

**解決方案**
使用 `asyncio.run()` 包裹異步函數：
```python
async def _process_image():
    ai_result = await ai_service.generate_from_url(...)
    upload_result = await storage_service.upload_image(...)
    return upload_result

upload_result = asyncio.run(_process_image())
```

---

### 3. LINE Webhook 事件處理邏輯錯誤 (line_handler.py:41-43)
**問題**
```python
events = json.loads(body)["events"]
for event in events:
    handler.handle(event["body"], event["signature"])
```

**根本原因**
LINE Webhook 事件結構中沒有 `event["body"]` 和 `event["signature"]`。

**解決方案**
將整個 body 和 signature 傳給 handler：
```python
def handle_line_events(body: str, signature: str):
    handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
    handler.handle(body, signature)
```

---

### 4. 呼叫不存在的方法 (main.py:46)
**問題**
```python
await storage_service.ensure_bucket_exists()
```

**根本原因**
UDA LINK 整合後，此方法不再存在。

**解決方案**
移除此呼叫。UDA LINK 服務會自動管理 bucket。

---

### 5. 裝飾器使用錯誤的 app (worker.py:189)
**問題**
```python
@app.on_after_configure.connect  # app 未定義
```

**根本原因**
應該使用 `celery_app` 而非 `app`。

**解決方案**
```python
@celery_app.on_after_configure.connect
```

---

## 🟡 中嚴重度問題修復

### 1. get_or_create_user 資料庫連線管理 (line_handler.py:57-81)
加入 try-finally 確保連線關閉。

---

## 代碼簡化

### 創建共用工具函數
創建 `app/utils.py`，將重複的 `get_or_create_user` 邏輯提取為共用函數 `get_or_create_user_in_db()`。

**受影響檔案**
- 新增：`app/utils.py`
- 修改：`app/api/line_handler.py`
- 修改：`app/main.py`

---

## 預防措施

1. **資料庫連線管理**：所有取得 Session 的地方都要確保在 finally 區塊關閉
2. **Celery 異步處理**：使用 `asyncio.run()` 包裹異步函數
3. **程式碼重複檢查**：定期審查重複代碼並提取共用函數
4. **型別檢查**：使用 mypy 進行靜態型別檢查

---

## 相關檔案
- 審查報告: `.claude/knowledge/2026-01-20-code-review.md`
- UDA LINK 整合: `.claude/knowledge/2026-01-20-uda-link-integration.md`
