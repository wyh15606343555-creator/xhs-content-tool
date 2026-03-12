# 管理后台重设计 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将管理后台从主页面底部分离为独立视图，精简侧边栏，统一 Apple 克制风视觉风格。

**Architecture:** 仅修改 `app.py` 一个文件。通过 `st.session_state.admin_view` 布尔值切换主页面/管理视图。管理面板代码提取为 `render_admin_panel()` 独立函数，使用自定义 HTML 指标卡片 + `st.tabs` 胶囊形 Tab 切换子模块。

**Tech Stack:** Python, Streamlit, SQLite, pandas, custom HTML/CSS

**Spec:** `docs/specs/2026-03-13-xhs-admin-redesign-design.md`

---

## Chunk 1: 侧边栏重设计 + 页面切换机制

### Task 1: 初始化 admin_view session_state 变量

**Files:**
- Modify: `app.py` — session_state 初始化区域（约第 750-810 行附近，其他 session_state 初始化的位置）

- [ ] **Step 1: 找到 session_state 初始化区域，添加 admin_view 变量**

在现有 session_state 初始化代码附近（如 `if "city" not in st.session_state:` 等），添加：

```python
if "admin_view" not in st.session_state:
    st.session_state.admin_view = False
```

- [ ] **Step 2: 验证**

Run: `cd "/Volumes/4T固态/Claude Code Text/小红书/demo" && python -c "import app" 2>&1 | head -5`
Expected: 无 SyntaxError（Streamlit 应用不会在 import 时完整运行，但语法检查通过即可）

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: add admin_view session_state initialization"
```

---

### Task 2: 重设计侧边栏 — 管理后台入口按钮 + 用户须知精简

**Files:**
- Modify: `app.py:815-966` — `with st.sidebar:` 代码块

**改动概要：**
1. 欢迎信息后面（第 821 行之后），添加管理后台入口按钮（仅管理员可见）
2. 用户须知 `st.expander`（第 889-919 行）改为一行链接文字 + 折叠的 expander
3. 管理视图时，入口按钮变为「返回内容生成」

- [ ] **Step 1: 在欢迎信息和 st.divider() 之间插入管理后台入口按钮**

在 `app.py` 第 822 行 `st.divider()` **之前**，添加管理后台入口按钮（仅管理员可见）：

```python
    # ── 管理后台入口（仅管理员可见） ──
    if st.session_state.invite_code in ADMIN_CODES:
        _admin_label = "← 返回内容生成" if st.session_state.get("admin_view") else "📊 管理后台"
        if st.button(_admin_label, use_container_width=True, key="btn_admin_toggle"):
            st.session_state.admin_view = not st.session_state.get("admin_view", False)
            st.rerun()
```

- [ ] **Step 2: 精简用户须知 — 从长 expander 改为一行文字 + 折叠**

找到 `app.py` 第 889-919 行的用户须知 expander 代码：

```python
    with st.expander("📋 用户须知与免责声明"):
        st.markdown("""**一、工具定位**
        ...（约30行长文本）...""")
```

替换为精简版：

```python
    # ── 用户须知（精简为一行） ──
    st.markdown(
        '<div style="font-size:11px;color:#c7c7cc;text-align:center;padding:8px 0;">'
        '用户须知 · 免责声明</div>',
        unsafe_allow_html=True,
    )
    with st.expander("查看详情", expanded=False):
        st.markdown("""**一、工具定位**

本工具是一款内容创作效率工具，帮助商家和创作者快速生成高质量的文案初稿与配图参考，降低内容创作门槛，助力账号运营。

**二、内容性质**

工具输出的所有文案和图片均为 **AI辅助生成的参考素材**，而非可直接发布的成品。我们强烈建议：
- 在AI初稿基础上融入个人风格和真实体验，进行二次创作
- 配图优先使用实拍照片，AI处理后的图片作为补充
- 发布前根据平台要求判断是否需要添加AI内容标识

**三、合规提示**

根据国家互联网信息办公室等七部门联合发布的《人工智能生成合成内容标识办法》（2025年9月1日起施行），AI生成或深度合成的内容在特定场景下需进行标识。各社交媒体平台也在持续完善AI内容的检测与管理机制。

本工具不对用户的发布行为及其后果承担责任。用户应自行关注并遵守相关法律法规及平台规则的最新要求。

**四、使用建议**

| 做法 | 推荐度 |
|------|--------|
| AI文案 + 大幅改写融入个人风格 | ⭐⭐⭐ 推荐 |
| AI文案作为灵感参考，自己重写 | ⭐⭐⭐ 推荐 |
| 实拍图 + AI辅助美化 | ⭐⭐⭐ 推荐 |
| AI文案小幅修改直接发 | ⭐⭐ 可用，建议标识 |
| AI生成图直接发 | ⭐ 建议标识或替换为实拍 |

**五、责任界定**

本工具仅提供内容生成服务，不参与、不控制、不代理用户在任何第三方平台的发布行为。用户使用本工具生成的内容进行发布、传播等行为，应自行确保符合适用法律法规及平台规则，相关责任由用户自行承担。""")
```

- [ ] **Step 3: 调整侧边栏元素顺序**

确认最终顺序从上到下为：
1. 欢迎信息（保留不变）
2. 管理后台入口按钮（新增，Step 1）
3. `st.divider()`
4. 所在城市输入（保留不变）
5. `st.divider()`
6. 会员额度显示（保留不变）
7. `st.divider()`
8. 历史记录按钮（保留不变）
9. `st.divider()`
10. 用户须知（Step 2 精简版）
11. 意见反馈 expander（保留不变）
12. `st.divider()` 前移到意见反馈之前
13. 退出登录按钮
14. 版本号 caption

将 `st.caption("Demo v5.0 · 内测版...")` 从用户须知 expander 内移到退出登录按钮之后。

- [ ] **Step 4: 手动测试侧边栏**

Run: `cd "/Volumes/4T固态/Claude Code Text/小红书/demo" && streamlit run app.py --server.port 8501`

验证：
- 管理员账号登录后，侧边栏显示「📊 管理后台」按钮
- 点击后按钮变为「← 返回内容生成」
- 用户须知只显示一行灰色文字
- 所有其他侧边栏元素正常

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat: redesign sidebar — add admin entry button, simplify user notice"
```

---

### Task 3: 添加主页面 admin_view 分支判断

**Files:**
- Modify: `app.py:969-972` — 主页面内容开始处（`# 页面2：行业选择` 之前）

- [ ] **Step 1: 在侧边栏代码结束后、主内容开始前插入分支判断**

在 `app.py` 第 969 行（`# ═══════════════ 页面2：行业选择` 注释行）**之前**，插入：

```python
# ═══════════════════════════════════════════════════════
#  页面分支：管理视图 / 内容生成
# ═══════════════════════════════════════════════════════
if st.session_state.get("admin_view") and st.session_state.invite_code in ADMIN_CODES:
    render_admin_panel()
    st.stop()
```

这样当 `admin_view=True` 时，调用管理面板函数后 `st.stop()` 阻止后续内容生成代码执行。

- [ ] **Step 2: 在文件顶部（imports 之后）添加 render_admin_panel 占位函数**

在 `app.py` 的 import 区域之后（约第 45 行附近），添加占位函数：

```python
def render_admin_panel():
    """管理后台独立视图"""
    st.info("管理后台加载中...")
```

- [ ] **Step 3: 验证分支逻辑**

Run: `cd "/Volumes/4T固态/Claude Code Text/小红书/demo" && python -c "
import ast
with open('app.py') as f:
    tree = ast.parse(f.read())
print('Syntax OK')
"`
Expected: `Syntax OK`

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: add admin_view page branch with placeholder function"
```

---

## Chunk 2: 管理后台独立视图实现

### Task 4: 实现管理页面页头 + 指标卡片（自定义 HTML）

**Files:**
- Modify: `app.py` — `render_admin_panel()` 函数

- [ ] **Step 1: 添加事件类型中文映射常量**

在 `render_admin_panel()` 函数之前（或函数内部顶部），添加：

```python
EVENT_TYPE_LABELS = {
    "login": "登录",
    "generate": "生成文案",
    "extract_link": "提取链接",
    "feedback": "提交反馈",
    "admin_recharge": "管理员充值",
    "view_history": "查看历史",
    "reuse_history": "复用历史文案",
}
```

- [ ] **Step 2: 实现 render_admin_panel() — 页头部分**

替换占位函数，实现完整的 `render_admin_panel()`：

```python
def render_admin_panel():
    """管理后台独立视图 — Apple 克制风"""

    # ── 页头 ──
    st.markdown(
        '<div style="margin-bottom:24px;">'
        '<div style="display:inline-block;font-size:14px;font-weight:700;color:#ff2442;'
        'background:#fff1f3;padding:4px 12px;border-radius:4px;">ADMIN</div>'
        '<div style="font-size:22px;font-weight:600;color:#1d1d1f;margin-top:6px;">数据分析</div>'
        '<div style="font-size:13px;color:#86868b;">Analytics Dashboard</div>'
        '</div>',
        unsafe_allow_html=True,
    )
```

- [ ] **Step 3: 实现指标卡片查询 + HTML 渲染**

在页头之后，添加数据查询和指标卡片：

```python
    # ── 指标卡片 ──
    conn = None
    try:
        conn = get_db()
        _today = datetime.now().strftime("%Y-%m-%d")
        _7days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        total_users = conn.execute(
            "SELECT COUNT(DISTINCT invite_code) FROM event_log"
        ).fetchone()[0]
        total_gens = conn.execute(
            "SELECT COUNT(*) FROM generation_history"
        ).fetchone()[0]
        today_gens = conn.execute(
            "SELECT COUNT(*) FROM generation_history WHERE created_at >= ?",
            (_today,)
        ).fetchone()[0]
        week_gens = conn.execute(
            "SELECT COUNT(*) FROM generation_history WHERE created_at >= ?",
            (_7days_ago,)
        ).fetchone()[0]
        total_feedbacks = conn.execute(
            "SELECT COUNT(*) FROM feedback"
        ).fetchone()[0]
        extract_total = conn.execute(
            "SELECT COUNT(*) FROM event_log WHERE event_type = 'extract_link'"
        ).fetchone()[0]
        extract_ok = conn.execute(
            "SELECT COUNT(*) FROM event_log WHERE event_type = 'extract_link' AND success = 1"
        ).fetchone()[0]
        extract_rate = f"{extract_ok / extract_total * 100:.0f}%" if extract_total > 0 else "—"

        def _metric_card(label_cn, label_en, value, color="#1d1d1f"):
            return (
                f'<div style="background:#f5f5f7;border-radius:14px;padding:16px;">'
                f'<div style="font-size:11px;color:#86868b;">{label_cn} {label_en}</div>'
                f'<div style="font-size:28px;font-weight:600;color:{color};margin-top:4px;">'
                f'{value}</div></div>'
            )

        row1 = (
            '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:12px;">'
            + _metric_card("总用户", "Users", total_users)
            + _metric_card("总生成", "Generated", total_gens)
            + _metric_card("今日", "Today", today_gens, "#ff2442")
            + '</div>'
        )
        row2 = (
            '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:20px;">'
            + _metric_card("近7日", "7-Day", week_gens)
            + _metric_card("提取成功率", "Rate", extract_rate, "#34c759")
            + _metric_card("反馈", "Feedback", total_feedbacks)
            + '</div>'
        )
        st.markdown(row1 + row2, unsafe_allow_html=True)
```

- [ ] **Step 4: 手动测试页头和指标卡片**

Run: `streamlit run app.py`
验证：管理员登录 → 点击管理后台 → 看到 ADMIN 标签 + 6个灰底圆角指标卡片，今日数值红色，成功率绿色

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat: implement admin panel header and metric cards"
```

---

### Task 5: 实现图表区域 + Tab 切换 + 各 Tab 内容

**Files:**
- Modify: `app.py` — `render_admin_panel()` 函数（续）

- [ ] **Step 1: 添加每日生成趋势图表**

在指标卡片之后，添加趋势图表：

```python
        # ── 每日生成趋势 ──
        st.markdown(
            '<div style="margin-bottom:4px;">'
            '<div style="font-size:14px;font-weight:600;color:#1d1d1f;">每日生成趋势</div>'
            '<div style="font-size:11px;color:#86868b;">Daily Generation Trend</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        _30days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        daily_rows = conn.execute(
            "SELECT DATE(created_at) as day, COUNT(*) as cnt "
            "FROM generation_history WHERE created_at >= ? "
            "GROUP BY DATE(created_at) ORDER BY day",
            (_30days_ago,)
        ).fetchall()
        if daily_rows:
            df_daily = pd.DataFrame([dict(r) for r in daily_rows])
            df_daily.columns = ["日期", "生成次数"]
            df_daily = df_daily.set_index("日期")
            st.line_chart(df_daily)
        else:
            st.caption("暂无数据")
```

- [ ] **Step 2: 添加 Tab 胶囊形 CSS 覆盖**

在图表之后、st.tabs 之前，注入 CSS：

```python
        # ── Tab 胶囊形样式 ──
        st.markdown("""
        <style>
        /* 胶囊形 Tab 样式覆盖 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background: transparent;
            border-bottom: none;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 10px 22px;
            border-radius: 24px;
            font-size: 15px;
            font-weight: 500;
            background: #f5f5f7;
            color: #1d1d1f;
            border: none;
            white-space: nowrap;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: #ff2442;
            color: white;
            font-weight: 600;
        }
        .stTabs [data-baseweb="tab-highlight"] {
            display: none;
        }
        .stTabs [data-baseweb="tab-border"] {
            display: none;
        }
        </style>
        """, unsafe_allow_html=True)
```

- [ ] **Step 3: 实现 5 个 Tab 及其内容**

```python
        # ── Tab 切换 ──
        tab_users, tab_industry, tab_recharge, tab_feedback, tab_logs = st.tabs(
            ["👥 用户", "🏆 行业", "💰 充值", "💬 反馈", "🔍 日志"]
        )

        # ── Tab 1: 用户 ──
        with tab_users:
            st.markdown(
                '<div style="font-size:14px;font-weight:600;color:#1d1d1f;">注册用户</div>'
                '<div style="font-size:11px;color:#86868b;margin-bottom:8px;">Registered Users</div>',
                unsafe_allow_html=True,
            )
            all_users = get_all_users()
            if all_users:
                df_reg = pd.DataFrame([
                    {
                        "手机号": u["phone"],
                        "邀请码": u["invite_code"],
                        "生成次数": u["gen_count"],
                        "登录次数": u["login_count"],
                        "注册时间": u["created_at"][:16] if u["created_at"] else "—",
                        "最后登录": u["last_login"][:16] if u["last_login"] else "—",
                        "最后生成": u["last_gen"][:16] if u["last_gen"] else "—",
                    }
                    for u in all_users
                ])
                st.dataframe(df_reg, use_container_width=True, hide_index=True)
                st.caption(f"共 {len(all_users)} 个注册用户")
            else:
                st.caption("暂无注册用户")

            # 用户活跃排行
            st.markdown(
                '<div style="font-size:14px;font-weight:600;color:#1d1d1f;margin-top:16px;">用户活跃排行</div>'
                '<div style="font-size:11px;color:#86868b;margin-bottom:8px;">User Activity Ranking</div>',
                unsafe_allow_html=True,
            )
            user_rows = conn.execute(
                "SELECT g.invite_code, COUNT(*) as gen_count, "
                "MAX(g.created_at) as last_active, "
                "COUNT(DISTINCT g.industry_id) as industry_count, "
                "COALESCE(u.phone, '—') as phone "
                "FROM generation_history g "
                "LEFT JOIN users u ON g.invite_code = u.invite_code "
                "GROUP BY g.invite_code "
                "ORDER BY gen_count DESC LIMIT 20"
            ).fetchall()
            if user_rows:
                df_users = pd.DataFrame([
                    {
                        "手机号": r["phone"],
                        "邀请码": r["invite_code"],
                        "生成次数": r["gen_count"],
                        "涉及行业数": r["industry_count"],
                        "最后活跃": r["last_active"][:16] if r["last_active"] else "—",
                    }
                    for r in user_rows
                ])
                st.dataframe(df_users, use_container_width=True, hide_index=True)
            else:
                st.caption("暂无数据")

            # 会员配额使用
            st.markdown(
                '<div style="font-size:14px;font-weight:600;color:#1d1d1f;margin-top:16px;">会员配额使用</div>'
                '<div style="font-size:11px;color:#86868b;margin-bottom:8px;">Membership Quota Usage</div>',
                unsafe_allow_html=True,
            )
            quota_rows = conn.execute(
                "SELECT invite_code, pro_gen_used, tier, updated_at "
                "FROM quota_usage ORDER BY pro_gen_used DESC"
            ).fetchall()
            if quota_rows:
                _tier_labels = {k: v["name"] for k, v in TIER_PLANS.items()}
                df_quota = pd.DataFrame([
                    {
                        "邀请码": q["invite_code"],
                        "会员等级": _tier_labels.get(q["tier"] or "free", "体验版"),
                        "已使用": q["pro_gen_used"],
                        "总额度": PRO_GEN_LIMIT,
                        "剩余": max(PRO_GEN_LIMIT - q["pro_gen_used"], 0),
                        "最后使用": q["updated_at"][:16] if q["updated_at"] else "—",
                    }
                    for q in quota_rows
                ])
                st.dataframe(df_quota, use_container_width=True, hide_index=True)
            else:
                st.caption("暂无数据")

        # ── Tab 2: 行业 ──
        with tab_industry:
            st.markdown(
                '<div style="font-size:14px;font-weight:600;color:#1d1d1f;">行业热度排行</div>'
                '<div style="font-size:11px;color:#86868b;margin-bottom:8px;">Industry Popularity</div>',
                unsafe_allow_html=True,
            )
            industry_rows = conn.execute(
                "SELECT industry_id, COUNT(*) as cnt FROM generation_history "
                "GROUP BY industry_id ORDER BY cnt DESC"
            ).fetchall()
            if industry_rows:
                labels = []
                counts = []
                for row in industry_rows:
                    lbl = INDUSTRIES.get(row["industry_id"], {}).get("label", row["industry_id"])
                    labels.append(lbl)
                    counts.append(row["cnt"])
                df_ind = pd.DataFrame({"行业": labels, "使用次数": counts}).set_index("行业")
                st.bar_chart(df_ind)
            else:
                st.caption("暂无数据")

            col_mode, col_tier = st.columns(2)
            with col_mode:
                st.markdown(
                    '<div style="font-size:14px;font-weight:600;color:#1d1d1f;">模式分布</div>'
                    '<div style="font-size:11px;color:#86868b;margin-bottom:8px;">Mode Distribution</div>',
                    unsafe_allow_html=True,
                )
                mode_rows = conn.execute(
                    "SELECT mode, COUNT(*) as cnt FROM generation_history GROUP BY mode"
                ).fetchall()
                if mode_rows:
                    mode_map = {"rewrite": "竞品参考", "original": "原创生成"}
                    df_mode = pd.DataFrame([
                        {"模式": mode_map.get(r["mode"], r["mode"]), "次数": r["cnt"]}
                        for r in mode_rows
                    ]).set_index("模式")
                    st.bar_chart(df_mode)
                else:
                    st.caption("暂无数据")

            with col_tier:
                st.markdown(
                    '<div style="font-size:14px;font-weight:600;color:#1d1d1f;">图片档位</div>'
                    '<div style="font-size:11px;color:#86868b;margin-bottom:8px;">Image Tier</div>',
                    unsafe_allow_html=True,
                )
                tier_rows = conn.execute(
                    "SELECT image_tier, COUNT(*) as cnt FROM generation_history "
                    "WHERE image_tier != '' GROUP BY image_tier ORDER BY cnt DESC"
                ).fetchall()
                if tier_rows:
                    tier_map = {"free": "免费", "pro": "Pro"}
                    df_tier = pd.DataFrame([
                        {"档位": tier_map.get(r["image_tier"], r["image_tier"]), "次数": r["cnt"]}
                        for r in tier_rows
                    ]).set_index("档位")
                    st.bar_chart(df_tier)
                else:
                    st.caption("暂无数据")

            # 自定义行业统计
            st.markdown(
                '<div style="font-size:14px;font-weight:600;color:#1d1d1f;margin-top:16px;">自定义行业使用统计</div>'
                '<div style="font-size:11px;color:#86868b;margin-bottom:8px;">Custom Industry Usage</div>',
                unsafe_allow_html=True,
            )
            custom_rows = conn.execute(
                "SELECT input_profile, COUNT(*) as cnt, MAX(created_at) as last_used "
                "FROM generation_history WHERE industry_id = 'custom' AND input_profile != '' "
                "GROUP BY input_profile ORDER BY cnt DESC"
            ).fetchall()
            if custom_rows:
                _custom_data = []
                for cr in custom_rows:
                    try:
                        _prof = json.loads(cr["input_profile"])
                        _ind_name = _prof.get("industry_name", "未填写")
                    except (json.JSONDecodeError, TypeError):
                        _ind_name = "未填写"
                    _custom_data.append({
                        "行业名称": _ind_name,
                        "使用次数": cr["cnt"],
                        "最近使用": cr["last_used"][:16] if cr["last_used"] else "—",
                    })
                _merged = {}
                for d in _custom_data:
                    name = d["行业名称"]
                    if name in _merged:
                        _merged[name]["使用次数"] += d["使用次数"]
                        if d["最近使用"] > _merged[name]["最近使用"]:
                            _merged[name]["最近使用"] = d["最近使用"]
                    else:
                        _merged[name] = d
                df_custom = pd.DataFrame(list(_merged.values()))
                df_custom = df_custom.sort_values("使用次数", ascending=False).reset_index(drop=True)
                st.dataframe(df_custom, use_container_width=True, hide_index=True)
                st.caption("💡 如果某个行业被频繁使用，可以考虑将其升级为正式行业模板")
            else:
                st.caption("暂无自定义行业使用记录")

        # ── Tab 3: 充值 ──
        with tab_recharge:
            st.markdown(
                '<div style="font-size:14px;font-weight:600;color:#1d1d1f;">充值管理</div>'
                '<div style="font-size:11px;color:#86868b;margin-bottom:8px;">Recharge Management</div>',
                unsafe_allow_html=True,
            )
            st.caption("用户付款后，在此为其增加额度并设置会员等级")
            with st.form("admin_recharge_form"):
                _rc_code = st.text_input("用户邀请码", placeholder="输入用户的邀请码")
                _rc_tier = st.selectbox(
                    "会员等级",
                    options=["plus", "pro", "promax"],
                    format_func=lambda t: {
                        "plus": "达人版（¥99/50次）",
                        "pro": "商家版（¥99/月/100次）",
                        "promax": "企业版（¥399/月/300次 · 顶级文案）",
                    }.get(t, t),
                )
                _tier_quota = TIER_PLANS[_rc_tier]["quota"]
                _rc_amount = st.number_input(
                    "充值额度（次数）", min_value=1, max_value=1000,
                    value=_tier_quota, step=10,
                )
                _rc_note = st.text_input("备注（可选）", placeholder="如：商家版 3月")
                _rc_submit = st.form_submit_button("确认充值", type="primary")
                if _rc_submit:
                    if not _rc_code.strip():
                        st.error("请输入用户邀请码")
                    else:
                        _rc_code_upper = _rc_code.strip().upper()
                        _before = get_pro_used(_rc_code_upper)
                        if add_pro_quota(_rc_code_upper, _rc_amount, tier=_rc_tier):
                            _after = get_pro_used(_rc_code_upper)
                            _tier_name = TIER_PLANS[_rc_tier]["name"]
                            st.success(
                                f"充值成功！ 邀请码 **{_rc_code_upper}** "
                                f"升级为 **{_tier_name}**，增加 {_rc_amount} 次额度\n\n"
                                f"已使用：{_before} → {_after}"
                            )
                            log_event(
                                st.session_state.invite_code, "admin_recharge",
                                detail=f"target={_rc_code_upper} tier={_rc_tier} amount={_rc_amount} note={_rc_note}",
                            )
                        else:
                            st.error("充值失败，请重试")

            # 会员配额概览
            st.markdown(
                '<div style="font-size:14px;font-weight:600;color:#1d1d1f;margin-top:16px;">会员配额概览</div>'
                '<div style="font-size:11px;color:#86868b;margin-bottom:8px;">Quota Overview</div>',
                unsafe_allow_html=True,
            )
            if quota_rows:
                st.dataframe(df_quota, use_container_width=True, hide_index=True)
            else:
                st.caption("暂无数据")

        # ── Tab 4: 反馈 ──
        with tab_feedback:
            st.markdown(
                '<div style="font-size:14px;font-weight:600;color:#1d1d1f;">最近反馈</div>'
                '<div style="font-size:11px;color:#86868b;margin-bottom:8px;">Recent Feedback</div>',
                unsafe_allow_html=True,
            )
            recent_fb = conn.execute(
                "SELECT * FROM feedback ORDER BY created_at DESC LIMIT 15"
            ).fetchall()
            if recent_fb:
                df_fb = pd.DataFrame([
                    {
                        "评分": fb["rating"],
                        "反馈内容": fb["feedback_text"] or "（无文字）",
                        "邀请码": fb["invite_code"],
                        "行业": INDUSTRIES.get(fb["industry_id"] or "", {}).get("label", fb["industry_id"] or "—"),
                        "时间": fb["created_at"][:16] if fb["created_at"] else "—",
                    }
                    for fb in recent_fb
                ])
                st.dataframe(df_fb, use_container_width=True, hide_index=True)
            else:
                st.caption("暂无反馈")

        # ── Tab 5: 日志 ──
        with tab_logs:
            st.markdown(
                '<div style="font-size:14px;font-weight:600;color:#1d1d1f;">事件日志</div>'
                '<div style="font-size:11px;color:#86868b;margin-bottom:8px;">Event Log</div>',
                unsafe_allow_html=True,
            )
            event_rows = conn.execute(
                "SELECT e.*, COALESCE(u.phone, '—') as phone "
                "FROM event_log e "
                "LEFT JOIN users u ON e.invite_code = u.invite_code "
                "ORDER BY e.created_at DESC LIMIT 50"
            ).fetchall()
            if event_rows:
                df_events = pd.DataFrame([
                    {
                        "手机号": r["phone"],
                        "操作": EVENT_TYPE_LABELS.get(r["event_type"], r["event_type"]),
                        "行业": r["industry_id"] or "—",
                        "模式": r["mode"] or "—",
                        "成功": "✅" if r["success"] else "❌",
                        "详情": (r["detail"] or "")[:60],
                        "时间": r["created_at"][:19] if r["created_at"] else "—",
                    }
                    for r in event_rows
                ])
                st.dataframe(df_events, use_container_width=True, hide_index=True)
            else:
                st.caption("暂无事件")

            # 每小时活跃分布
            st.markdown(
                '<div style="font-size:14px;font-weight:600;color:#1d1d1f;margin-top:16px;">每小时活跃分布</div>'
                '<div style="font-size:11px;color:#86868b;margin-bottom:8px;">Hourly Activity</div>',
                unsafe_allow_html=True,
            )
            hourly_rows = conn.execute(
                "SELECT CAST(strftime('%H', created_at) AS INTEGER) as hour, COUNT(*) as cnt "
                "FROM generation_history GROUP BY hour ORDER BY hour"
            ).fetchall()
            if hourly_rows:
                hour_data = {r["hour"]: r["cnt"] for r in hourly_rows}
                df_hour = pd.DataFrame([
                    {"时段": f"{h:02d}:00", "生成次数": hour_data.get(h, 0)}
                    for h in range(24)
                ]).set_index("时段")
                st.bar_chart(df_hour)
            else:
                st.caption("暂无数据")

    except Exception as e:
        st.error(f"数据库读取失败：{e}")
    finally:
        if conn:
            conn.close()
```

- [ ] **Step 4: 手动测试所有 Tab**

Run: `streamlit run app.py`
验证：
- 管理后台显示 5 个胶囊形 Tab
- 每个 Tab 内容正常显示
- 日志 Tab 显示完整手机号和中文操作类型
- 时间精确到秒

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat: implement admin panel with charts, tabs, and enhanced logs"
```

---

### Task 6: 移除旧管理面板代码

**Files:**
- Modify: `app.py:2795-3127` — 旧管理面板代码区域

- [ ] **Step 1: 定位并删除旧管理面板代码**

先用搜索定位旧代码的起止位置：

Run: `grep -n "管理后台（仅 ADMIN 邀请码可见）" app.py`

删除从该注释行的上一行（`# ═══════` 分隔线）开始，到对应的 `finally: if conn: conn.close()` 结束的整个代码块。标志性的结束位置是：

Run: `grep -n "# ─── 页脚 ───" app.py`

删除两个标记之间的全部代码（不含「页脚」行）。

- [ ] **Step 2: 验证语法正确**

Run: `cd "/Volumes/4T固态/Claude Code Text/小红书/demo" && python -c "
import ast
with open('app.py') as f:
    tree = ast.parse(f.read())
print('Syntax OK')
"`
Expected: `Syntax OK`

- [ ] **Step 3: 端到端测试**

Run: `streamlit run app.py`
验证：
- 普通用户登录：正常生成内容流程，页面底部**不再**有管理面板
- 管理员登录：侧边栏「管理后台」按钮可见 → 点击进入独立管理视图 → 所有数据和功能正常
- 管理视图点击「返回内容生成」→ 正常回到内容生成页面

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "refactor: remove old admin panel code from main page bottom"
```

---

## 实施注意事项

1. **不要修改任何业务逻辑或数据查询** — 只是把现有代码从页面底部移到独立函数
2. **所有查询语句直接复制** — 不要"优化"SQL，保持与旧代码一致（日志查询除外，需 JOIN users 表）
3. **CSS 覆盖要谨慎** — Tab 样式覆盖只用 `.stTabs` 选择器，不要影响其他组件
4. **conn 生命周期** — `render_admin_panel()` 内自己管理 `conn = get_db()` 和 `conn.close()`
5. **`quota_rows` 变量** — 在 Tab 1 用户 Tab 中查询，Tab 3 充值 Tab 中复用。确保变量在 try 块内可见
