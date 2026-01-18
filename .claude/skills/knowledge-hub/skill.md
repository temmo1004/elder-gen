---
name: knowledge-hub
description: "知識管理工具 - 記錄 BUG 修復過程、時間點、經驗總結。Actions: record, summary, search, learn, review. 自動記錄問題分析、解決方案、預防措施。"
---

# Knowledge Hub - 知識管理工具

專為開發團隊設計的知識管理系統，記錄 BUG 修復過程、時間點、經驗總結。

---

## 功能概述

### 1. 記錄 BUG 修復 (record)
當修復 BUG 時，自動記錄：
- 問題描述
- 根本原因分析
- 解決方案
- 修改的檔案
- 時間戳
- 相關 commit

### 2. 生成知識總結 (summary)
將修復過程整理成結構化文檔：
- 問題類型分類
- 影響範圍評估
- 預防措施建議

### 3. 知識檢索 (search)
搜尋歷史問題與解決方案

### 4. 經驗回顧 (review)
定期回顧常見問題模式

---

## 使用方式

### 當修復 BUG 時

```
/knowledge record
```

自動觸發知識記錄流程：

#### Step 1: 問題分析
```markdown
## 問題描述
- 錯誤訊息: ...
- 發生場景: ...
- 影響範圍: ...

## 根本原因
- 技術原因: ...
- 設計缺陷: ...
- 人為疏失: ...
```

#### Step 2: 解決方案
```markdown
## 修復方案
- 修改檔案: ...
- 關鍵代碼: ...
- Commit ID: ...
```

#### Step 3: 經驗總結
```markdown
## 學習要點
- 如何預防: ...
- 相關知識: ...
- 後續追蹤: ...
```

### 搜尋歷史知識

```
/knowledge search <關鍵字>
```

### 生成週報/月報

```
/knowledge report [week|month]
```

---

## 知識分類

### 按類型
- 🔴 安全漏洞
- 🟡 邏輯錯誤
- 🟢 效能問題
- 🔵 相容性問題
- 🟣 部署問題

### 按影響
- P0: 阻斷性問題
- P1: 嚴重問題
- P2: 一般問題
- P3: 優化改善

### 按平台
- Frontend: 前端問題
- Backend: 後端問題
- Database: 資料庫問題
- DevOps: 部署/運維問題

---

## 知識模板

```markdown
# BUG: [標題]

**時間**: YYYY-MM-DD HH:mm:ss
**嚴重度**: P0/P1/P2/P3
**類型**: 安全/邏輯/效能/相容/部署
**平台**: Frontend/Backend/Database/DevOps

## 問題描述
[錯誤日誌或截圖]

## 根本原因
[分析原因]

## 解決方案
```javascript
// 修復代碼
```

## 影響範圍
- 影響用戶: ...
- 影響功能: ...

## 預防措施
- 代碼審查: ...
- 自動化測試: ...
- 監控告警: ...

## 相關資源
- Commit: ...
- Issue: ...
- 文檔: ...
```

---

## 知識庫位置

```
.claude/skills/knowledge-hub/
├── SKILL.md          # 本文件
├── knowledge.json    # 知識庫數據
└── reports/          # 生成的報告
    ├── weekly/
    └── monthly/
```
