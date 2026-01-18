-- ============================================
-- Project ElderGen - Supabase 初始化腳本
-- 在 Supabase SQL Editor 中執行此腳本
-- ============================================

-- 1. 建立用戶表
CREATE TABLE IF NOT EXISTS public.elder_users (
    id SERIAL PRIMARY KEY,
    line_user_id VARCHAR(64) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    picture_url VARCHAR(500),
    points INTEGER DEFAULT 50,           -- 預設給 50 點
    is_vip BOOLEAN DEFAULT FALSE,
    total_images_generated INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 建立訂單表（紀錄藍新金流）
CREATE TABLE IF NOT EXISTS public.elder_orders (
    id SERIAL PRIMARY KEY,
    order_no VARCHAR(50) NOT NULL UNIQUE,
    user_id INTEGER REFERENCES public.elder_users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,              -- 單位：分
    points_added INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, PAID, FAILED, EXPIRED
    neweb_trade_no VARCHAR(50),
    neweb_payment_type VARCHAR(50),
    pay_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 建立圖片生成任務表
CREATE TABLE IF NOT EXISTS public.elder_image_jobs (
    job_id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER REFERENCES public.elder_users(id) ON DELETE CASCADE,
    prompt_used TEXT,
    original_url TEXT,
    original_image_path VARCHAR(500),
    result_url TEXT,
    result_image_path VARCHAR(500),
    status VARCHAR(20) DEFAULT 'QUEUED',  -- QUEUED, PROCESSING, COMPLETED, FAILED
    error_message TEXT,
    cost_points INTEGER DEFAULT 0,
    celery_task_id VARCHAR(100),
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- 4. 建立索引加速查詢
CREATE INDEX IF NOT EXISTS idx_elder_users_line ON public.elder_users(line_user_id);
CREATE INDEX IF NOT EXISTS idx_elder_orders_no ON public.elder_orders(order_no);
CREATE INDEX IF NOT EXISTS idx_elder_orders_user ON public.elder_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_elder_jobs_user ON public.elder_image_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_elder_jobs_status ON public.elder_image_jobs(status);

-- 5. 建立 Storage Bucket (手動在 Dashboard 操作或使用 API)
--    Bucket 名稱: elder-images
--    設定為 Public Bucket

-- 6. (可選) 建立 RLS Policies - 如果需要從前端直接存取
-- ALTER TABLE public.elder_users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.elder_orders ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.elder_image_jobs ENABLE ROW LEVEL SECURITY;

-- 7. 查詢確認
SELECT 'elder_users' as table_name, COUNT(*) as row_count FROM public.elder_users
UNION ALL
SELECT 'elder_orders', COUNT(*) FROM public.elder_orders
UNION ALL
SELECT 'elder_image_jobs', COUNT(*) FROM public.elder_image_jobs;
