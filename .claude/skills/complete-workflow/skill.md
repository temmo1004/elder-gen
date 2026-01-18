---
name: complete-workflow
description: "完整功能開發工作流程 - 代碼審查→代碼簡化→知識管理→Git推送。三階段品質把控：1.review檢查 2.simplify優化 3.knowledge記錄，最後自動 commit & push"
---

# Complete Workflow - 完整功能開發工作流程

功能開發完成後的標準化流程，確保代碼品質與知識沉澱。

---

## 工作流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  功能開發   │ -> │  代碼審查   │ -> │  代碼簡化   │ -> │  知識管理   │
│   完成      │    │  (review)   │    │ (simplify)  │    │ (knowledge)  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                  │
                                                                  v
                                                          ┌─────────────┐
                                                          │ Git Commit  │
                                                          │   & Push    │
                                                          └─────────────┘
```

---

## 階段一：代碼審查 (review)

### 目標
- 檢查程式碼品質
- 識別安全漏洞
- 確保最佳實踐

### 執行
```
/review
```

### 通過標準
- 🔴 高嚴重度問題：**0 個**
- 🟡 中嚴重度問題：**≤2 個**
- 🟢 低嚴重度問題：**≤5 個**
- 整體評分：**≥7/10**

### 輸出
| 項目 | 內容 |
|------|------|
| 嚴重度分布 | 🔴 X / 🟡 X / 🟢 X |
| 整體評分 | X/10 |
| 必須修復 | 問題列表 |
| 建議改善 | 優化建議 |

---

## 階段二：代碼簡化 (simplify)

### 目標
- 減少代碼重複
- 提升可讀性
- 優化效能

### 執行
使用 `code-simplifier` agent 分析並簡化代碼。

### 檢查項目
- [ ] 移除重複代碼
- [ ] 簡化複雜邏輯
- [ ] 提取共用函數
- [ ] 優化命名
- [ ] 減少嵌套層級

### 通過標準
- 無明顯代碼重複
- 函數單一職責
- 命名清晰易懂

---

## 階段三：知識管理 (knowledge)

### 目標
- 記錄修復過程
- 沉澱經驗知識
- 建立問題模式庫

### 執行
```
/knowledge record
```

### 記錄內容
```markdown
## 問題描述
- 錯誤訊息: ...
- 發生場景: ...

## 根本原因
- 技術原因: ...
- 設計問題: ...

## 解決方案
- 修改檔案: ...
- 關鍵代碼: ...

## 預防措施
- 代碼審查: ...
- 自動化測試: ...
```

---

## 最終階段：Git Commit & Push

### Commit 訊息格式
```bash
<type>: <subject>

[optional body]

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

### Type 選項
| Type | 說明 | 範例 |
|------|------|------|
| `feat` | 新功能 | feat: 新增 Threads 發文功能 |
| `fix` | 修復 BUG | fix: 修復 UUID 格式錯誤 |
| `refactor` | 重構 | refactor: 優化權限檢查邏輯 |
| `security` | 安全修復 | security: 強化內部 API 驗證 |
| `perf` | 效能優化 | perf: 減少資料庫查詢次數 |

### Push 流程
```bash
git add <files>
git commit -m "<message>"
git push origin main
```

---

## 自動化觸發

### 使用方式
完成功能開發後，執行：
```
/workflow complete
```

系統將自動執行：
1. 代碼審查 (review)
2. 代碼簡化分析 (simplify)
3. 知識記錄 (knowledge)
4. Git commit & push

### 手動執行各階段
```
/workflow review    # 只執行代碼審查
/workflow simplify   # 只執行代碼簡化
/workflow knowledge  # 只執行知識記錄
/workflow git        # 只執行 git push
```

---

## 品質門檻

任何階段失敗都需要修復後才能進入下一階段：

| 階段 | 門檻 | 失敗處理 |
|------|------|----------|
| Review | 評分 ≥7/10，無🔴問題 | 修復後重新審查 |
| Simplify | 無明顯重複/複雜度問題 | 重構後重新檢查 |
| Knowledge | 記錄完整 | 補充記錄 |
| Git | 無 merge conflict | 解決衝突後推送 |

---

## 進度追蹤

當前工作流狀態會在完成後顯示：

```
✅ 階段一：代碼審查 - 通過 (8.5/10)
✅ 階段二：代碼簡化 - 通過
✅ 階段三：知識管理 - 已記錄 BUG-003
✅ 階段四：Git Push - commit abc1234
```
