# 小红书Agent UI 重设计 — 实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将小红书Agent的UI从当前粗糙风格重设计为Apple克制风+国际化风格，不改变业务逻辑。

**Architecture:** 纯前端重构 — 修改 `app.py` 中的 CSS 和 HTML 渲染代码，以及 `config.py` 中的行业映射数据。所有业务逻辑、API调用、数据库操作保持不变。改动集中在 CSS 样式块（~600行）和4个页面渲染区域。

**Tech Stack:** Python / Streamlit / inline CSS (`st.markdown` with `unsafe_allow_html=True`)

**Spec:** `docs/specs/2026-03-12-xhs-ui-redesign-design.md`

---

## Chunk 1: CSS 设计系统 + config.py 数据准备

### Task 1: config.py — 新增英文名映射 + 移除 industry_preview

**Files:**
- Modify: `config.py:810-848` (DEFAULTS dict)
- Modify: `config.py` (新增 INDUSTRY_EN_NAMES 和 INDUSTRY_EMOJIS 字典，在 INDUSTRIES 定义之后)

**上下文：**
- `config.py` 包含 `DEFAULTS` 字典（line 810），其中 `industry_preview` 字段（line 815）需要移除
- `INDUSTRIES` 字典（line 189-803）定义了12个行业的 key 和 label
- 需要新增两个映射字典供 `app.py` 行业选择页使用

- [ ] **Step 1: 在 config.py 中新增 INDUSTRY_EN_NAMES 字典**

在 `INDUSTRIES` 字典结束后（约 line 804）、`DEFAULTS` 之前，添加：

```python
# ═══════════════════════════════════════════════════════
#  行业英文名 & Emoji 映射（UI重设计用）
# ═══════════════════════════════════════════════════════
INDUSTRY_EN_NAMES: dict[str, str] = {
    "fitness": "Fitness",
    "beauty": "Beauty",
    "education": "Education",
    "food": "Dining",
    "medical_beauty": "Med Aesthetics",
    "fashion": "Fashion",
    "legal": "Legal",
    "photography": "Photography",
    "hotel": "Hotel & B&B",
    "jewelry": "Jewelry",
    "pet": "Pets",
    "custom": "Custom",
}

INDUSTRY_EMOJIS: dict[str, str] = {
    "fitness": "💪",
    "beauty": "💇",
    "education": "📚",
    "food": "🍜",
    "medical_beauty": "✨",
    "fashion": "👗",
    "legal": "⚖️",
    "photography": "📷",
    "hotel": "🏨",
    "jewelry": "💎",
    "pet": "🐾",
    "custom": "✨",
}
```

- [ ] **Step 2: 从 DEFAULTS 中移除 industry_preview**

找到 `config.py` 中的 DEFAULTS 字典，删除这一行：
```python
    industry_preview="",   # 第一次点击：预览选中（高亮），再次点击确认
```

- [ ] **Step 3: 在 app.py 的 import 中新增导入**

修改 `app.py` line 18-23 的 import 块，在 `from config import (...)` 中新增 `INDUSTRY_EN_NAMES, INDUSTRY_EMOJIS`：

```python
from config import (
    INDUSTRIES, INDUSTRY_ICONS, ICON_ATTRS, DEFAULTS,
    INDUSTRY_EN_NAMES, INDUSTRY_EMOJIS,
    PRO_GEN_LIMIT, ADMIN_CODES,
    TIER_PLANS, PAYMENT_CONTACT_WECHAT,
    POST_GOALS, TONE_STYLES,
)
```

- [ ] **Step 4: 验证 app 可启动**

```bash
cd "/Volumes/4T固态/Claude Code Text/小红书/demo" && python -c "from config import INDUSTRY_EN_NAMES, INDUSTRY_EMOJIS, DEFAULTS; print('EN_NAMES:', len(INDUSTRY_EN_NAMES)); print('EMOJIS:', len(INDUSTRY_EMOJIS)); print('industry_preview' in DEFAULTS)"
```

预期输出：
```
EN_NAMES: 12
EMOJIS: 12
False
```

- [ ] **Step 5: Commit**

```bash
cd "/Volumes/4T固态/Claude Code Text/小红书/demo"
git add config.py app.py
git commit -m "feat: add industry EN names/emojis, remove industry_preview from DEFAULTS"
```

---

### Task 2: CSS 设计系统重写 — 变量 + 移除渐变 + 新增类

**Files:**
- Modify: `app.py:55-603` (整个 `<style>` 块)

**上下文：**
- 当前 CSS 约 550 行，在 `st.markdown("""<style>...</style>""")` 中
- 需要：(1) 添加 `:root` CSS 变量 (2) 移除所有渐变样式 (3) 新增设计类 (4) 更新现有样式
- 侧边栏样式（line 96-116）保持不变（不在本次范围）
- 响应式 CSS（line 494-601）需要保留并更新

- [ ] **Step 1: 在 `<style>` 开头添加 CSS 变量**

在 line 56（`<style>` 标签之后）、隐藏 Streamlit 默认 UI 元素之前，插入：

```css
/* ── Design Tokens ── */
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f5f5f7;
    --bg-selected: #fff1f3;
    --text-primary: #1d1d1f;
    --text-secondary: #86868b;
    --text-tertiary: #c7c7cc;
    --accent: #ff2442;
    --accent-orange: #ff8c00;
    --success: #34c759;
    --border: #e5e5ea;
    --divider: #f0f0f0;
    --radius-lg: 16px;
    --radius-md: 14px;
    --radius-sm: 10px;
    --radius-xs: 4px;
}
```

- [ ] **Step 2: 更新 Headings 样式 + 移除 .step-num**

将 line 118-123 的 headings 共享 CSS 块（仅替换这3行，保留 line 124-125 的 `h1`/`h3` 字号声明不变）：
```css
h1, h2, h3, h4, h5 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
}
```

同时删除 line 141-152 的 `.step-num` CSS 定义（包含 `linear-gradient`，已被进度条替代）：
```css
/* 删除以下整块 */
.step-num {
    display: inline-block;
    background: linear-gradient(135deg, #FF2442, #FF6B81);
    ...
}
```

- [ ] **Step 3: 更新按钮样式 — 移除渐变**

将 line 154-184 的按钮 CSS 替换为：

```css
/* ── Buttons ── */
.stButton > button {
    background-color: #FFFFFF !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    transition: all 0.2s ease;
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background-color: var(--bg-selected) !important;
}
.stButton > button[kind="primary"] {
    background-color: var(--accent) !important;
    color: #FFFFFF !important;
    border: none !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(255,36,66,0.25);
}
.stButton > button[kind="primary"]:hover {
    filter: brightness(0.95) !important;
    color: #FFFFFF !important;
}
.stButton > button:disabled {
    background-color: var(--bg-secondary) !important;
    color: #AEAEB2 !important;
    border-color: var(--border) !important;
    box-shadow: none;
}
```

- [ ] **Step 4: 更新输入框样式 — 灰底无边框**

将 line 198-221 的输入框 CSS 替换为：

```css
/* ── Text Inputs / Text Areas ── */
.stTextInput input,
.stTextArea textarea {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    padding: 12px 16px !important;
    caret-color: var(--accent);
}
.stTextInput input:focus,
.stTextArea textarea:focus {
    border: none !important;
    box-shadow: 0 0 0 2px rgba(255,36,66,0.2) !important;
    outline: none !important;
}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: var(--text-tertiary) !important;
}
.stTextInput label,
.stTextArea label {
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
}
```

- [ ] **Step 5: 更新进度条样式 — 移除渐变**

将 line 271-279 的进度条 CSS 中的渐变改为纯色：

```css
/* ── Progress Bar ── */
[data-testid="stProgressBar"] > div {
    background-color: var(--bg-secondary) !important;
    border-radius: 4px !important;
}
[data-testid="stProgressBar"] > div > div {
    background-color: var(--accent) !important;
    border-radius: 4px !important;
}
```

- [ ] **Step 6: 更新登录页 gate 样式 — 移除渐变**

将 line 328-358 的 gate 样式替换为：

```css
/* ── Gate Box (登录页) ── */
.gate-box {
    text-align: center;
    padding: 4rem 1rem 2.5rem;
}
.gate-logo {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin-bottom: 1.2rem;
}
.gate-logo-icon {
    width: 36px; height: 36px;
    border-radius: 10px;
    background: var(--accent);
    display: inline-flex;
    align-items: center; justify-content: center;
    color: white;
    font-weight: 700;
    font-size: 18px;
}
.gate-title {
    font-size: 22px;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: -0.02em;
}
.gate-sub {
    color: var(--text-secondary);
    font-size: 13px;
    margin-top: 4px;
}
.gate-footer {
    color: var(--text-tertiary);
    font-size: 11px;
    margin-top: 20px;
}
```

- [ ] **Step 7: 更新行业卡片样式 — 灰底无边框**

将 line 365-483 的行业卡片 CSS 替换为：

```css
/* ── Industry Cards ── */

/* 同行列等高 */
[data-testid="stHorizontalBlock"]:has(.ind-card) {
    align-items: stretch !important;
    margin-bottom: 2px !important;
    row-gap: 10px !important;
}
[data-testid="stColumn"]:has(.ind-card) {
    display: flex !important;
    flex-direction: column !important;
    position: relative !important;
}
[data-testid="stColumn"]:has(.ind-card) > div,
[data-testid="stColumn"]:has(.ind-card) > div > div:first-child,
[data-testid="stColumn"]:has(.ind-card) > div > div:first-child > div,
[data-testid="stColumn"]:has(.ind-card) > div > div:first-child > div > div,
[data-testid="stColumn"]:has(.ind-card) > div > div:first-child > div > div > div {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    min-height: 0 !important;
}

.ind-card {
    border-radius: var(--radius-md);
    padding: 18px 12px;
    text-align: center;
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    overflow: hidden;
    box-sizing: border-box;
    border: none;
    background: var(--bg-secondary);
    transition: all 0.2s ease;
    cursor: pointer;
}
.ind-card.ind-sel {
    background: var(--bg-selected);
    box-shadow: 0 0 0 2px var(--accent);
}
.ind-card.ind-custom {
    border: 1px dashed #d1d1d6;
    background: var(--bg-secondary);
}
.ind-emoji {
    font-size: 28px;
    margin-bottom: 4px;
}
.ind-name {
    font-weight: 500; font-size: 13px;
    color: var(--text-primary);
    overflow-wrap: break-word; line-height: 1.3;
    transition: color 0.2s ease;
}
.ind-sel .ind-name {
    color: var(--accent);
    font-weight: 600;
}
.ind-en {
    font-size: 11px;
    color: var(--text-secondary);
    line-height: 1.3;
}
.ind-sel .ind-en {
    color: #ff8a9e;
}

/* Streamlit 按钮覆盖卡片 */
[data-testid="stColumn"]:has(.ind-card) [class*="st-key-sel_"] {
    position: absolute !important;
    inset: 0 !important;
    z-index: 10 !important;
    height: auto !important;
    min-height: 0 !important;
}
[data-testid="stColumn"]:has(.ind-card) [class*="st-key-sel_"] .stButton {
    height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}
[data-testid="stColumn"]:has(.ind-card) [class*="st-key-sel_"] .stButton > button {
    width: 100% !important;
    height: 100% !important;
    min-height: 0 !important;
    opacity: 0 !important;
    background: transparent !important;
    border: none !important;
    cursor: pointer !important;
    padding: 0 !important;
    box-shadow: none !important;
}
.ind-card:active {
    transform: scale(0.97);
    filter: brightness(0.96);
}
```

- [ ] **Step 8: 新增设计系统 CSS 类**

在行业卡片样式之后、响应式 CSS 之前，添加：

```css
/* ── New Design System Classes ── */

/* Step 标签 */
.step-tag {
    font-size: 11px; font-weight: 600;
    color: var(--accent); background: var(--bg-selected);
    padding: 2px 8px; border-radius: var(--radius-xs);
    display: inline-block;
}

/* 灰底大卡片 */
.card-gray {
    background: var(--bg-secondary);
    border-radius: var(--radius-lg);
    padding: 20px;
}

/* 选中卡片 */
.card-selected {
    background: var(--bg-selected);
    box-shadow: 0 0 0 2px var(--accent);
}

/* 功能标签 */
.tag {
    font-size: 10px; color: var(--text-secondary);
    background: #ebebed; padding: 2px 8px;
    border-radius: var(--radius-xs);
    display: inline-block;
}
.tag-pro {
    font-size: 10px;
    color: var(--accent-orange);
    background: #fff8f0;
    padding: 2px 8px;
    border-radius: var(--radius-xs);
    display: inline-block;
}
.tag-free {
    font-size: 10px;
    color: var(--success);
    background: #f0faf0;
    padding: 1px 6px;
    border-radius: 3px;
    display: inline-block;
}

/* 进度条节点 */
.progress-dot {
    width: 24px; height: 24px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 600;
    flex-shrink: 0;
}
.progress-dot-done { background: var(--success); color: white; }
.progress-dot-active { background: var(--accent); color: white; }
.progress-dot-pending { background: var(--border); color: #999; }

/* 状态栏 */
.status-bar {
    background: var(--bg-secondary);
    border-radius: var(--radius-sm);
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
}

/* 折叠摘要行 */
.completed-step-summary {
    background: var(--bg-secondary);
    border-radius: 12px;
    padding: 14px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
}
```

- [ ] **Step 9: 更新响应式 CSS**

将 line 494-601 的响应式 CSS 替换为：

```css
/* ═══════════════════════════════════════════════
   MOBILE RESPONSIVE
═══════════════════════════════════════════════ */

/* ── 平板（≤768px）── */
@media (max-width: 768px) {
    .main .block-container {
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        padding-top: 1rem !important;
    }
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 0.5rem !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        min-width: 47% !important;
        flex: 1 1 47% !important;
    }
    h1 { font-size: 1.6rem !important; }
    h3 { font-size: 1rem !important; }
    .gate-box { padding: 2rem 0.5rem 1.5rem !important; }
    .gate-title { font-size: 18px !important; }
    .ind-card { padding: 14px 8px !important; }
    .ind-emoji { font-size: 24px !important; }
    .ind-name { font-size: 12px !important; }
    .ind-en { font-size: 10px !important; }
    section[data-testid="stSidebar"] {
        min-width: 260px !important;
        max-width: 280px !important;
    }
    /* 进度条：隐藏步骤名文字 */
    .progress-step-name { display: none !important; }
}

/* ── 小屏手机（≤480px）── */
@media (max-width: 480px) {
    .main .block-container {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        min-width: 100% !important;
        flex: 1 1 100% !important;
    }
    /* 行业卡片保持 2 列 */
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ind-card)
    > [data-testid="stColumn"] {
        min-width: 47% !important;
        flex: 1 1 47% !important;
    }
    h1 { font-size: 1.4rem !important; }
    .gate-title { font-size: 16px !important; }
    .gate-sub { font-size: 11px !important; }
    .gate-box { padding: 1.5rem 0.3rem 1rem !important; }
    .stButton > button {
        font-size: 0.85rem !important;
        padding: 0.5rem 0.8rem !important;
    }
    /* 模式卡片：图标缩小 */
    .mode-icon { width: 36px !important; height: 36px !important; }
    .progress-step-name { display: none !important; }
}

/* ── 极小屏（≤360px）── */
@media (max-width: 360px) {
    .gate-title { font-size: 14px !important; }
    h1 { font-size: 1.2rem !important; }
    .ind-card { padding: 10px 6px !important; }
    .ind-emoji { font-size: 20px !important; }
    .ind-name { font-size: 11px !important; }
}
```

- [ ] **Step 10: 验证 app 可启动**

```bash
cd "/Volumes/4T固态/Claude Code Text/小红书/demo" && python -c "import app" 2>&1 | head -5
```

如果有 import 错误需要修复。注意 Streamlit app 无法直接 `import app`，改用：
```bash
cd "/Volumes/4T固态/Claude Code Text/小红书/demo" && streamlit run app.py --server.headless true &
sleep 3 && curl -s http://localhost:8501 | head -20
kill %1 2>/dev/null
```

- [ ] **Step 11: Commit**

```bash
cd "/Volumes/4T固态/Claude Code Text/小红书/demo"
git add app.py
git commit -m "feat: CSS design system overhaul — tokens, no gradients, new utility classes"
```

---

## Chunk 2: 页面重写 — 登录 + 行业选择 + 模式选择

### Task 3: 登录页重写

**Files:**
- Modify: `app.py:617-680` (登录页渲染区域)

**上下文：**
- 当前登录页使用 `gate-box` / `gate-logo` / `gate-title` 渐变样式
- 新设计：红色方块 "R" Logo + "RedNote Agent" 文字 + 灰底输入框 + "开始使用" 按钮
- 表单使用 `st.columns([1, 2, 1])` 居中（保持不变）
- 登录逻辑完全不变

- [ ] **Step 1: 替换登录页品牌标识 HTML**

将 line 618-628 的品牌标识替换为：

```python
    st.markdown("""
    <div class="gate-box">
        <div class="gate-logo">
            <div class="gate-logo-icon">R</div>
            <div class="gate-title">RedNote Agent</div>
        </div>
        <div class="gate-sub">AI-powered content creation for Xiaohongshu</div>
    </div>
    """, unsafe_allow_html=True)
```

- [ ] **Step 2: 更新表单区域**

将 line 630-680 的表单区域替换为：

```python
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown(
            "<div style='font-size:12px;font-weight:500;color:#1d1d1f;margin-bottom:4px;'>"
            "手机号 <span style='color:#86868b;font-weight:400;'>Phone</span></div>",
            unsafe_allow_html=True,
        )
        _phone_input = st.text_input(
            "手机号",
            placeholder="请输入11位手机号",
            max_chars=11,
            label_visibility="collapsed",
        )

        st.markdown(
            "<div style='font-size:12px;font-weight:500;color:#1d1d1f;margin-bottom:4px;margin-top:16px;'>"
            "邀请码 <span style='color:#86868b;font-weight:400;'>Invite Code</span></div>",
            unsafe_allow_html=True,
        )
        _code_input = st.text_input(
            "邀请码",
            placeholder="请输入邀请码",
            max_chars=20,
            label_visibility="collapsed",
        )

        st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
        _login_clicked = st.button("开始使用", use_container_width=True, type="primary")

        _phone = (_phone_input or "").strip()
        _code = (_code_input or "").strip().upper()
        if _login_clicked:
            if not _phone:
                st.error("请输入手机号")
            elif not _code:
                st.error("请输入邀请码")
            elif not validate_phone(_phone):
                st.error("手机号格式不正确，请输入11位手机号")
            elif not check_invite_code(_code):
                st.error("邀请码无效，请联系 David 获取")
            else:
                result = register_or_login(_phone, _code)
                if result["ok"]:
                    st.session_state.authed = True
                    st.session_state.user_phone = _phone
                    st.session_state.invite_code = result["invite_code"]
                    log_event(result["invite_code"], "login",
                              detail=f"phone={_phone} new={result['is_new']}")
                    st.rerun()
                else:
                    st.error(result["msg"])

        st.markdown(
            "<div class='gate-footer'>内测阶段 · 仅限受邀用户</div>",
            unsafe_allow_html=True,
        )

        st.divider()
        st.caption(
            "**免责声明：** 本工具为小红书内容创作辅助工具，生成的文案和图片仅作为"
            "**创作参考素材**。根据《人工智能生成合成内容标识办法》（2025年9月施行）"
            "及平台社区规范，AI辅助生成的内容在发布时可能需要进行标识，且存在被平台"
            "算法识别的可能性。建议结合自身风格二次编辑后发布。因用户发布行为产生的"
            "任何后果，由用户自行承担。使用本工具即表示您已阅读并同意以上条款。"
        )
    st.stop()
```

- [ ] **Step 3: 验证登录页渲染**

启动 app，在浏览器中查看登录页：
- 红色方块 "R" Logo + "RedNote Agent" 文字水平排列
- 灰底无边框输入框
- "开始使用" 红色按钮
- 底部 "内测阶段 · 仅限受邀用户"

- [ ] **Step 4: Commit**

```bash
cd "/Volumes/4T固态/Claude Code Text/小红书/demo"
git add app.py
git commit -m "feat: redesign login page — RedNote Agent branding, gray inputs"
```

---

### Task 4: 行业选择页重写

**Files:**
- Modify: `app.py:840-939` (行业选择渲染区域)

**上下文：**
- 当前：4列网格 + SVG图标 + 两步交互（预览→确认）+ `industry_preview` session state
- 新设计：3列网格 + emoji + 中英双语 + 单击选中 + 底部确认栏
- `industry_preview` 已在 Task 1 从 DEFAULTS 中移除
- 需要同时删除所有引用 `industry_preview` 的逻辑

- [ ] **Step 1: 替换行业选择页头部**

将 line 843-861 的头部（品牌标识 + 流程说明 + "第一步"标题）替换为：

```python
# Step 标签 + 标题 + 英文副标题
st.markdown(
    "<div class='step-tag'>Step 1</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div style='font-size:24px;font-weight:600;color:#1d1d1f;letter-spacing:-0.5px;margin-top:8px;'>"
    "选择行业</div>"
    "<div style='font-size:13px;color:#86868b;margin-top:4px;'>"
    "Choose the industry that best describes your business</div>",
    unsafe_allow_html=True,
)
```

- [ ] **Step 2: 重写行业网格 — 3列 + emoji + 中英双语 + 单击**

将 line 862-929 的行业网格替换为：

```python
industry_keys = list(INDUSTRIES.keys())
rows = [industry_keys[i:i+3] for i in range(0, len(industry_keys), 3)]

for row_keys in rows:
    cols = st.columns(3)
    for col, ikey in zip(cols, row_keys):
        info = INDUSTRIES[ikey]
        selected = st.session_state.industry_id == ikey
        emoji = INDUSTRY_EMOJIS.get(ikey, "📦")
        en_name = INDUSTRY_EN_NAMES.get(ikey, "")
        sel_cls = "ind-sel" if selected else ""
        custom_cls = "ind-custom" if ikey == "custom" and not selected else ""

        with col:
            st.markdown(
                f"""
                <div class="ind-card {sel_cls} {custom_cls}">
                    <div class="ind-emoji">{emoji}</div>
                    <div class="ind-name">{info['label']}</div>
                    <div class="ind-en">{en_name}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(info['label'], key=f"sel_{ikey}", use_container_width=True):
                # 单击直接选中
                st.session_state.industry_id = ikey
                st.session_state.selected_mode = None
                st.session_state.content_ready = False
                st.session_state.rewrite_done = False
                st.session_state.images_done = False
                st.session_state.rewrite_result = ""
                st.session_state.competitor_analysis = None
                st.session_state.content_strategy = None
                st.session_state.edited_title = ""
                st.session_state.edited_body = ""
                st.session_state.edited_images = []
                st.session_state.note_title = ""
                st.session_state.note_text = ""
                st.session_state.note_images = []
                st.session_state.store_profile = {}
                st.session_state.daily_brief = ""
                st.session_state.custom_industry_name = ""
                st.session_state.create_images = []
                st.session_state.dynamic_image_prompt = ""
                st.session_state.scene_images = []
                st.session_state.scene_prompt = ""
                st.session_state.feedback_submitted = False
                st.session_state["scene_tier"] = ""
                st.rerun()
```

- [ ] **Step 3: 替换底部提示为确认栏（带 st.stop 门控）**

将 line 931-939 的底部提示替换为。注意：单击选中后 `industry_id` 已设置，但需要用 `st.stop()` 阻止页面继续渲染，直到用户点击"下一步"。使用一个简单方案：行业选中后始终显示确认栏，页面始终 `st.stop()` 在此处，点击"下一步"时设置 `industry_confirmed=True`。

```python
# 底部确认栏（已选中行业时显示）
if not st.session_state.industry_id:
    st.info("👆 点击卡片选择你的行业")
    st.stop()

# 显示确认栏
_sel_key = st.session_state.industry_id
_sel_emoji = INDUSTRY_EMOJIS.get(_sel_key, "📦")
_sel_name = INDUSTRIES[_sel_key]["label"]
col_info, col_btn = st.columns([3, 1])
with col_info:
    st.markdown(
        f"<div class='status-bar'>"
        f"<span style='font-size:16px;'>{_sel_emoji}</span>"
        f"<span style='font-weight:500;color:#1d1d1f;'>{_sel_name}</span>"
        f"<span style='color:#86868b;'>已选择</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
with col_btn:
    if st.button("下一步 →", key="industry_next", type="primary", use_container_width=True):
        st.session_state.industry_confirmed = True
        st.rerun()

# 门控：必须点"下一步"才能继续
if not st.session_state.get("industry_confirmed", False):
    st.stop()
```

同时在 `config.py` 的 DEFAULTS 字典中（约 line 810-848）添加一行：
```python
    industry_confirmed=False,  # 行业选择确认门控
```
在 `industry=""` 行之后插入即可。

- [ ] **Step 4: 删除所有 industry_preview 残留引用**

在 `app.py` 全文搜索 `industry_preview`，确保以下位置已清理：
- 原 line 869-871：`previewed` / `has_preview` 变量 — 已在 Step 2 中移除
- 原 line 926-928：`st.session_state.industry_preview = ikey` — 已移除
- 原 line 903：`st.session_state.industry_preview = ""` — 已移除
- 原 line 932-935：预览底部提示 — 已在 Step 3 中移除

搜索确认无残留：
```bash
grep -n "industry_preview" "/Volumes/4T固态/Claude Code Text/小红书/demo/app.py"
```
预期：无输出

- [ ] **Step 5: 验证行业选择页**

启动 app，登录后查看行业选择页：
- 3列网格，emoji + 中文 + 英文
- 单击选中，底部显示确认栏
- "下一步 →" 按钮可点击

- [ ] **Step 6: Commit**

```bash
cd "/Volumes/4T固态/Claude Code Text/小红书/demo"
git add app.py
git commit -m "feat: redesign industry selection — 3-col emoji grid, single-click, bilingual"
```

---

### Task 5: 模式选择页重写

**Files:**
- Modify: `app.py:989-1090` (模式选择渲染区域)

**上下文：**
- 当前：两列并排卡片，功能清单式，渐变图标
- 新设计：纵向堆叠的横向卡片（左图标 + 中内容 + 右箭头）
- 选中后状态栏也在此区域（line 1083-1089）

- [ ] **Step 1: 替换模式选择页头部和卡片**

将 line 992-1080 的模式选择区域替换为：

```python
if not st.session_state.selected_mode:
    st.divider()
    st.markdown("<div class='step-tag'>Step 2</div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:24px;font-weight:600;color:#1d1d1f;letter-spacing:-0.5px;margin-top:8px;'>"
        "选择模式</div>"
        "<div style='font-size:13px;color:#86868b;margin-top:4px;'>"
        "How would you like to create content?</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # 竞品参考模式卡片
    st.markdown(
        """
        <div class="card-gray" style="padding:20px;display:flex;align-items:flex-start;gap:16px;cursor:pointer;margin-bottom:12px;">
            <div class="mode-icon" style="width:44px;height:44px;border-radius:12px;background:#ff2442;
                        display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                <span style="font-size:22px;">🔄</span>
            </div>
            <div style="flex:1;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    <span style="font-size:15px;font-weight:600;color:#1d1d1f;">竞品参考</span>
                    <span style="font-size:11px;color:#86868b;">Rewrite</span>
                    <span class="tag-free">FREE</span>
                </div>
                <div style="font-size:12px;color:#86868b;line-height:1.5;">
                    粘贴竞品链接 → AI分析爆文结构 → 改写为你的风格
                </div>
                <div style="display:flex;gap:8px;margin-top:8px;">
                    <span class="tag">文案改写</span>
                    <span class="tag">去水印</span>
                    <span class="tag">防查重</span>
                </div>
            </div>
            <div style="color:#c7c7cc;font-size:18px;align-self:center;">›</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("选择竞品参考模式", key="mode_sel_a", type="primary", use_container_width=True):
        st.session_state.selected_mode = "rewrite"
        st.rerun()

    # 原创生成模式卡片
    st.markdown(
        """
        <div class="card-gray" style="padding:20px;display:flex;align-items:flex-start;gap:16px;cursor:pointer;">
            <div class="mode-icon" style="width:44px;height:44px;border-radius:12px;background:#ff8c00;
                        display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                <span style="font-size:22px;">✨</span>
            </div>
            <div style="flex:1;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    <span style="font-size:15px;font-weight:600;color:#1d1d1f;">原创生成</span>
                    <span style="font-size:11px;color:#86868b;">Create</span>
                    <span class="tag-free">FREE</span>
                </div>
                <div style="font-size:12px;color:#86868b;line-height:1.5;">
                    填写店铺信息 → AI创作专属文案 → 美化照片或生成配图
                </div>
                <div style="display:flex;gap:8px;margin-top:8px;">
                    <span class="tag">AI文案</span>
                    <span class="tag">照片美化</span>
                    <span class="tag-pro">AI配图 Pro</span>
                </div>
            </div>
            <div style="color:#c7c7cc;font-size:18px;align-self:center;">›</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("选择原创生成模式", key="mode_sel_b", use_container_width=True):
        st.session_state.selected_mode = "create"
        st.rerun()

    st.stop()
```

- [ ] **Step 2: 更新选中后的状态栏 + 保留切换按钮**

将 line 1083-1123 的状态栏 + 切换按钮区域替换为（原代码有"切换模式"按钮在 line 1101-1123，必须保留其 state reset 逻辑）：

```python
# 已选择模式后的状态栏
mode = st.session_state.selected_mode
mode_label = "竞品参考" if mode == "rewrite" else "原创生成"
_sel_emoji = INDUSTRY_EMOJIS.get(st.session_state.industry_id, "📦")
_sel_industry = INDUSTRIES[st.session_state.industry_id]["label"]
_city_label = st.session_state.city or "通用"

col_status, col_switch = st.columns([5, 1])
with col_status:
    st.markdown(
        f"<div class='status-bar'>"
        f"<span style='color:#34c759;'>●</span>"
        f"<span style='font-size:14px;'>{_sel_emoji}</span>"
        f"<span style='font-weight:500;color:#1d1d1f;'>{_sel_industry}</span>"
        f"<span style='color:#86868b;'>·</span>"
        f"<span style='color:#86868b;'>{mode_label}</span>"
        f"<span style='color:#86868b;'>·</span>"
        f"<span style='color:#86868b;'>{_city_label}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
with col_switch:
    st.markdown(
        "<div style='text-align:right;padding-top:12px;'>"
        "<span id='switch-mode-label' style='font-size:11px;color:#ff2442;font-weight:500;cursor:pointer;'>切换</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    if st.button("切换", key="switch_mode_btn", use_container_width=True):
        st.session_state.selected_mode = None
        st.session_state.content_ready = False
        st.session_state.rewrite_done = False
        st.session_state.images_done = False
        st.session_state.rewrite_result = ""
        st.session_state.competitor_analysis = None
        st.session_state.content_strategy = None
        st.session_state.edited_title = ""
        st.session_state.edited_body = ""
        st.session_state.edited_images = []
        st.session_state.note_title = ""
        st.session_state.note_text = ""
        st.session_state.note_images = []
        st.session_state.batch_results = []
        st.session_state.store_profile = {}
        st.session_state.daily_brief = ""
        st.session_state.scene_images = []
        st.session_state.scene_prompt = ""
        st.session_state.feedback_submitted = False
        st.session_state["scene_tier"] = ""
        st.rerun()
```

- [ ] **Step 3: 验证模式选择页**

启动 app，选择行业后查看模式选择页：
- 两张横向卡片纵向堆叠
- 左侧图标 + 中间内容 + 右侧箭头
- 功能标签标识
- 选中后状态栏显示完整上下文

- [ ] **Step 4: Commit**

```bash
cd "/Volumes/4T固态/Claude Code Text/小红书/demo"
git add app.py
git commit -m "feat: redesign mode selection — vertical cards, tags, bilingual"
```

---

## Chunk 3: 内容生成区域 + 反馈区域 + 最终验证

### Task 6: 进度条组件

**Files:**
- Modify: `app.py` (在模式选中后、内容步骤开始前的位置)

**上下文：**
- 当前无进度条，使用 `.step-num` 渐变圆圈数字
- 新设计：水平进度条，4个节点+连接线，使用单个 `st.markdown` HTML 块
- 进度条出现在选模式后、具体步骤之前
- Mode A 步骤名：提取、文案、图片、下载
- Mode B 步骤名：信息、文案、图片、下载

- [ ] **Step 1: 创建进度条渲染函数**

在 `app.py` 的 imports 之后、`st.set_page_config()` 之前（约 line 44-45），添加辅助函数（模块级定义，不在执行流中）：

```python
def render_progress_bar(steps: list[str], current_step: int):
    """渲染水平进度条。current_step 从 0 开始。"""
    nodes_html = []
    for i, name in enumerate(steps):
        if i < current_step:
            dot_cls = "progress-dot-done"
            dot_content = "✓"
            text_color = "#34c759"
        elif i == current_step:
            dot_cls = "progress-dot-active"
            dot_content = str(i + 1)
            text_color = "#ff2442"
        else:
            dot_cls = "progress-dot-pending"
            dot_content = str(i + 1)
            text_color = "#86868b"

        node = (
            f"<div style='display:flex;align-items:center;'>"
            f"<div class='progress-dot {dot_cls}'>{dot_content}</div>"
            f"<div class='progress-step-name' style='font-size:11px;color:{text_color};font-weight:500;margin-left:4px;'>{name}</div>"
            f"</div>"
        )
        nodes_html.append(node)

        # 连接线（最后一个节点后不加）
        if i < len(steps) - 1:
            line_color = "#34c759" if i < current_step else "#e5e5ea"
            nodes_html.append(
                f"<div style='flex:1;height:2px;background:{line_color};margin:0 8px;'></div>"
            )

    html = (
        "<div style='display:flex;align-items:center;gap:0;margin-bottom:24px;'>"
        + "".join(nodes_html)
        + "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)
```

- [ ] **Step 2: 在内容步骤区域开始处调用进度条**

在模式选中后、具体步骤渲染之前（搜索现有的步骤数字标记位置），添加进度条调用。

确定当前步骤索引的逻辑（根据 session state 判断）：
```python
# 确定当前步骤
if mode == "rewrite":
    _progress_steps = ["提取", "文案", "图片", "下载"]
else:
    _progress_steps = ["信息", "文案", "图片", "下载"]

# 判断当前在哪一步
if st.session_state.images_done:
    _current_step = 3  # 下载
elif st.session_state.rewrite_done or st.session_state.get("create_done", False):
    _current_step = 2  # 图片
elif st.session_state.content_ready:
    _current_step = 1  # 文案
else:
    _current_step = 0  # 提取/信息

render_progress_bar(_progress_steps, _current_step)
```

注意：需要根据实际 session state 变量名确认步骤判断逻辑。阅读 `app.py` 中 `content_ready`、`rewrite_done`、`images_done` 等变量的使用。

- [ ] **Step 3: 移除旧的 .step-num 渐变圆圈**

在 `app.py` 中搜索所有 `step-num` 引用，找到类似的 HTML：
```python
st.markdown('<span class="step-num">1</span> ...', ...)
```
将这些替换为不带 `.step-num` 的简单标题或移除。

```bash
grep -n "step-num" "/Volumes/4T固态/Claude Code Text/小红书/demo/app.py"
```

- [ ] **Step 4: Commit**

```bash
cd "/Volumes/4T固态/Claude Code Text/小红书/demo"
git add app.py
git commit -m "feat: add horizontal progress bar, remove step-num badges"
```

---

### Task 7: 步骤标题替换 — step-num → 中英双语标题

**Files:**
- Modify: `app.py` (7处 `step-num` 引用: lines 1134, 1395, 1502, 1583, 1867, 2353, 2466)

**上下文：**
- 每个步骤都有 `<span class="step-num">N</span> **步骤名**` 格式
- 需要替换为中英双语标题格式
- `.step-num` CSS 已在 Task 2 Step 2 中移除

- [ ] **Step 1: 替换 Step 1 标题（Mode A: 粘贴链接）**

line 1134:

```python
# 原: st.markdown('<span class="step-num">1</span> **粘贴竞品小红书笔记链接**', unsafe_allow_html=True)
# 新:
st.markdown(
    "<div style='font-size:18px;font-weight:600;color:#1d1d1f;'>粘贴竞品笔记链接</div>"
    "<div style='font-size:12px;color:#86868b;'>Paste Competitor Note Links</div>",
    unsafe_allow_html=True,
)
```

- [ ] **Step 2: 替换 Step 1 标题（Mode B: 填写信息）**

line 1395:

```python
# 原: st.markdown('<span class="step-num">1</span> **填写店铺信息 + 今日主题**', unsafe_allow_html=True)
# 新:
st.markdown(
    "<div style='font-size:18px;font-weight:600;color:#1d1d1f;'>店铺信息 + 今日主题</div>"
    "<div style='font-size:12px;color:#86868b;'>Store Info & Daily Topic</div>",
    unsafe_allow_html=True,
)
```

- [ ] **Step 3: 替换 Step 1.5 标题（发帖需求）**

line 1502:

```python
# 原: '<span class="step-num">1.5</span> **发帖需求**（可选，提升内容质量）'
# 新:
st.markdown(
    "<div style='font-size:18px;font-weight:600;color:#1d1d1f;'>发帖需求 "
    "<span style='font-size:12px;color:#86868b;font-weight:400;'>Optional</span></div>"
    "<div style='font-size:12px;color:#86868b;'>Post Requirements</div>",
    unsafe_allow_html=True,
)
```

- [ ] **Step 4: 替换 Step 2 标题（AI 文案处理）**

line 1583:

```python
# 原: f'<span class="step-num">2</span> **{label_2}**'
# 新:
st.markdown(
    f"<div style='font-size:18px;font-weight:600;color:#1d1d1f;'>{label_2}</div>"
    f"<div style='font-size:12px;color:#86868b;'>AI Content Processing</div>",
    unsafe_allow_html=True,
)
```

- [ ] **Step 5: 替换 Step 3 标题（图片处理）**

line 1867:

```python
# 原: st.markdown('<span class="step-num">3</span> **图片处理**', unsafe_allow_html=True)
# 新:
st.markdown(
    "<div style='font-size:18px;font-weight:600;color:#1d1d1f;'>图片处理</div>"
    "<div style='font-size:12px;color:#86868b;'>Image Processing</div>",
    unsafe_allow_html=True,
)
```

- [ ] **Step 6: 替换 Step 4 标题（打包下载）**

line 2353:

```python
# 原: st.markdown('<span class="step-num">4</span> **打包下载**', unsafe_allow_html=True)
# 新:
st.markdown(
    "<div style='font-size:18px;font-weight:600;color:#1d1d1f;'>打包下载</div>"
    "<div style='font-size:12px;color:#86868b;'>Download</div>",
    unsafe_allow_html=True,
)
```

- [ ] **Step 7: 替换 Step 5 标题（一键准备发布）**

line 2466:

```python
# 原: st.markdown('<span class="step-num">5</span> **一键准备发布**', unsafe_allow_html=True)
# 新:
st.markdown(
    "<div style='font-size:18px;font-weight:600;color:#1d1d1f;'>一键准备发布</div>"
    "<div style='font-size:12px;color:#86868b;'>Quick Publish Prep</div>",
    unsafe_allow_html=True,
)
```

- [ ] **Step 8: 验证无残留 step-num 引用**

```bash
grep -n "step-num" "/Volumes/4T固态/Claude Code Text/小红书/demo/app.py"
```

预期：无输出（CSS 定义和 HTML 引用都已移除）

- [ ] **Step 9: Commit**

```bash
cd "/Volumes/4T固态/Claude Code Text/小红书/demo"
git add app.py
git commit -m "feat: replace step-num badges with bilingual section titles"
```

---

### Task 8: 灰底卡片包裹 + 标题/正文双语标签 + 下载按钮灰底

**Files:**
- Modify: `app.py` (文案结果区 line 1816-1819；下载区 line 2349-2460；各步骤内容区)

**上下文：**
- 标题/正文已经是纵向排列（line 1818-1819: `st.text_area("标题")` + `st.text_area("正文")`），无需改 columns
- 需要：(1) 各步骤内容包裹灰底卡片 (2) 标题/正文加双语标签 (3) 下载按钮改灰底
- 下载区当前用 `st.columns(2)` 或 `st.columns(3)` 排列 `st.download_button`

- [ ] **Step 1: 为标题/正文添加双语标签**

在 `app.py` line 1817，将：
```python
            st.markdown("**改写结果** （可直接编辑修改）")
            edited_title = st.text_area("标题", key="edited_title", height=68)
            edited_body = st.text_area("正文", key="edited_body", height=300)
```

替换为：
```python
            st.markdown(
                "<div style='font-size:12px;font-weight:500;color:var(--text-primary);margin-bottom:4px;'>"
                "标题 <span style='color:var(--text-tertiary);font-weight:400;'>Title</span></div>",
                unsafe_allow_html=True,
            )
            edited_title = st.text_area("标题", key="edited_title", height=68, label_visibility="collapsed")
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            st.markdown(
                "<div style='font-size:12px;font-weight:500;color:var(--text-primary);margin-bottom:4px;'>"
                "正文 <span style='color:var(--text-tertiary);font-weight:400;'>Body</span></div>",
                unsafe_allow_html=True,
            )
            edited_body = st.text_area("正文", key="edited_body", height=300, label_visibility="collapsed")
```

- [ ] **Step 2: 为每个活跃步骤内容添加灰底卡片包裹**

在各步骤标题后、内容前，插入灰底卡片开启 div；内容结束后关闭 div。

具体位置（用 grep 找到各步骤起始）：
```bash
grep -n "step-num" "/Volumes/4T固态/Claude Code Text/小红书/demo/app.py"
```

预期结果：line 1134, 1395, 1502, 1583, 1867, 2353, 2466（已在 Task 7 中被替换为双语标题）

在每个步骤标题的 `st.markdown` 之后，内容开始前，插入：
```python
st.markdown('<div class="card-gray">', unsafe_allow_html=True)
```

在该步骤内容结束处（下一个步骤开始前或 `st.divider()` 前），插入：
```python
st.markdown('</div>', unsafe_allow_html=True)
```

注意：Streamlit 会将每个 `st.markdown` 包裹在独立 div 中，所以开/关 div 可能不生效。
**替代方案**：如果 Streamlit 拆分了 div，改用 CSS 选择器方案——在步骤标题下方直接放一个带 `card-gray` class 的完整 HTML 块，包含纯展示内容。交互组件（`st.text_area`, `st.button`）仍用 Streamlit 原生，在外层用 `st.container()` + 自定义 CSS 背景。

实际实施时测试哪种方式有效即可。

- [ ] **Step 3: 下载按钮改灰底样式**

下载区（line 2353-2460）的 `st.download_button` 已经通过 CSS 统一样式。在 Task 2 的 CSS 中确认以下规则存在：

```css
.stDownloadButton > button {
    background: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
}
```

如果 Task 2 CSS 中已包含此规则，则无需额外修改 Python 代码。
验证：启动 app 确认下载按钮显示灰底无边框。

- [ ] **Step 4: Commit**

```bash
cd "/Volumes/4T固态/Claude Code Text/小红书/demo"
git add app.py
git commit -m "feat: bilingual labels, gray card wrap, gray download buttons"
```

---

### Task 9: 已完成步骤折叠 + "继续"按钮

**Files:**
- Modify: `app.py` (在 `render_progress_bar` 之后添加折叠渲染函数，并在各步骤衔接处调用)

**上下文：**
- Spec 要求已完成的步骤折叠为摘要行 + 可展开详情
- Spec 要求每个步骤底部有"继续 · [下一步名称] →"按钮
- Streamlit 的 `st.expander` header 不支持任意 HTML

- [ ] **Step 1: 创建折叠摘要渲染函数**

在 `render_progress_bar` 函数之后（模块级），添加：

```python
def render_completed_step(step_name: str, summary: str, detail_content_fn=None):
    """渲染已完成步骤的折叠摘要。detail_content_fn 是一个回调函数，在展开时调用。"""
    st.markdown(
        f"<div class='completed-step-summary'>"
        f"<div style='display:flex;align-items:center;gap:8px;'>"
        f"<span style='color:#34c759;font-size:14px;'>✓</span>"
        f"<span style='font-size:12px;color:#86868b;'>{step_name}</span>"
        f"<span style='font-size:11px;color:#c7c7cc;'>· {summary}</span>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    if detail_content_fn:
        with st.expander("查看详情"):
            detail_content_fn()


def render_continue_button(next_step_name: str, button_key: str):
    """渲染'继续'按钮。返回 True 如果被点击。"""
    return st.button(
        f"继续 · {next_step_name} →",
        key=button_key,
        type="primary",
        use_container_width=True,
    )
```

- [ ] **Step 2: 在步骤 1 完成后添加折叠摘要**

步骤 1 完成的标志是 `content_ready=True`（设置于 line 1230, 1316, 1465）。
在 line 1495（`if st.session_state.content_ready:`）之前，插入折叠摘要：

```python
# 步骤 1 已完成时，显示折叠摘要
if st.session_state.content_ready:
    _note_count = len(st.session_state.batch_results) if st.session_state.batch_results else 1
    _img_count = len(st.session_state.note_images)
    render_completed_step("提取完成", f"{_note_count} 条笔记 · {_img_count} 张图片")
```

- [ ] **Step 3: 在步骤 2 完成后添加折叠摘要**

步骤 2 完成的标志是 `rewrite_done=True`（设置于 line 1741）。
在 line 1755（`if st.session_state.rewrite_done:`）之后的内容展示前，当 `images_done` 已为 True 时，折叠步骤 2：

```python
if st.session_state.rewrite_done and st.session_state.images_done:
    render_completed_step("文案处理完成", "AI 改写已完成")
```

- [ ] **Step 4: 在各步骤底部添加"继续"按钮**

三个关键位置：

**步骤 1 → 2**：在 line 1495（`if st.session_state.content_ready:`）内部，文案处理 UI 开始前：
```python
# 如果还没开始文案处理，显示继续按钮
if st.session_state.content_ready and not st.session_state.rewrite_done:
    if not render_continue_button("AI 文案处理", "btn_continue_to_rewrite"):
        st.stop()
```

**步骤 2 → 3**：在 line 1865（`if st.session_state.rewrite_done and (_has_any_images or mode == "create"):`）之前：
```python
if st.session_state.rewrite_done and not st.session_state.images_done:
    if not render_continue_button("图片处理", "btn_continue_to_images"):
        st.stop()
```

**步骤 3 → 4**：在 line 2351（`if st.session_state.rewrite_done:`，下载区块）之前：
```python
if st.session_state.images_done:
    if not render_continue_button("打包下载", "btn_continue_to_download"):
        st.stop()
```

注意：这些继续按钮需要和已有的代码流整合。如果已有步骤间逻辑（如自动流转），需判断是否保留继续按钮还是保持自动流转。建议：先加按钮，如果用户反馈体验不好再改为自动。

- [ ] **Step 4: 验证折叠和继续按钮**

启动 app，走过每个步骤，确认：
- 已完成步骤显示绿色 ✓ 摘要
- 可展开查看详情
- 底部有红色"继续"按钮

- [ ] **Step 5: Commit**

```bash
cd "/Volumes/4T固态/Claude Code Text/小红书/demo"
git add app.py
git commit -m "feat: add completed step folding and continue buttons"
```

---

### Task 10: 反馈区域样式更新

**Files:**
- Modify: `app.py` (反馈区域，约 line 2563-2608)

- [ ] **Step 1: 更新反馈区域标题和样式**

将反馈区域的标题格式更新为中英双语：

```python
st.markdown(
    "<div style='font-size:18px;font-weight:600;color:#1d1d1f;'>使用反馈 "
    "<span style='font-size:12px;color:#86868b;font-weight:400;'>Feedback</span></div>",
    unsafe_allow_html=True,
)
```

输入框和按钮已经通过 CSS 变量统一更新，无需额外修改。

- [ ] **Step 2: Commit**

```bash
cd "/Volumes/4T固态/Claude Code Text/小红书/demo"
git add app.py
git commit -m "feat: update feedback section title to bilingual format"
```

---

### Task 11: 最终验证 + 清理

**Files:**
- Review: `app.py` (全文)
- Review: `config.py`

- [ ] **Step 1: 搜索并清理残留的渐变引用**

```bash
grep -n "linear-gradient" "/Volumes/4T固态/Claude Code Text/小红书/demo/app.py"
```

CSS `<style>` 块中不应再有 `linear-gradient`（侧边栏除外，侧边栏不在本次范围）。
非 CSS 区域（如行业卡片渲染代码中）的 `linear-gradient` 引用也应已被移除。

- [ ] **Step 2: 搜索并清理残留的 industry_preview 引用**

```bash
grep -rn "industry_preview" "/Volumes/4T固态/Claude Code Text/小红书/demo/"
```

预期：无结果

- [ ] **Step 3: 搜索旧样式类名残留**

```bash
grep -n "gate-accent\|ind-desc\|ind-action\|ind-icon\b" "/Volumes/4T固态/Claude Code Text/小红书/demo/app.py"
```

如果在 HTML 渲染代码中仍有引用旧类名，但 CSS 中已移除定义，需要清理。

- [ ] **Step 4: 完整启动测试**

```bash
cd "/Volumes/4T固态/Claude Code Text/小红书/demo" && streamlit run app.py
```

手动检查：
1. 登录页：RedNote Agent 品牌，灰底输入框
2. 行业选择：3列 emoji 网格，单击选中，底部确认栏
3. 模式选择：纵向堆叠卡片，功能标签
4. 进度条：水平节点+连接线
5. 内容步骤：灰底卡片包裹，标题正文纵向
6. 下载区域：灰底按钮
7. 反馈区域：中英双语标题
8. 响应式：缩小浏览器窗口检查移动端适配

- [ ] **Step 5: 最终 Commit**

```bash
cd "/Volumes/4T固态/Claude Code Text/小红书/demo"
git add -A
git commit -m "chore: cleanup residual old styles and verify UI redesign"
```
