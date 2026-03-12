"""
小红书通用内容 Agent — Demo v5.0
邀请码测试版 | 12大行业全部支持双模式 | 4档会员体系（体验/达人/商家/企业）
"""

import streamlit as st
import re
import json
import pandas as pd
from datetime import datetime, timedelta
from PIL import Image
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

from config import (
    INDUSTRIES, INDUSTRY_ICONS, ICON_ATTRS, DEFAULTS,
    INDUSTRY_EN_NAMES, INDUSTRY_EMOJIS,
    PRO_GEN_LIMIT, ADMIN_CODES,
    TIER_PLANS, PAYMENT_CONTACT_WECHAT,
    POST_GOALS, TONE_STYLES,
)
from utils import (
    init_db, log_event, save_generation, get_history, get_db,
    friendly_api_error, img_cols,
    get_pro_used, has_pro_quota,
    add_pro_quota, get_user_tier,
    check_invite_code, validate_phone, register_or_login, get_all_users,
    make_zip, make_batch_zip,
    save_store_profile, load_store_profile,
    try_use_pro_quota, refund_pro_quota,
)
from api import (
    try_extract_xhs, download_image_url,
    rewrite_with_deepseek, generate_original_content,
    rewrite_with_claude, generate_original_with_claude,
    generate_dynamic_image_prompt,
    edit_image_with_gemini,
    remove_watermark_and_protect,
    stealth_anti_hash,
    analyze_competitor, plan_content_strategy, polish_content,
)


EVENT_TYPE_LABELS = {
    "login": "登录",
    "generate": "生成文案",
    "extract_link": "提取链接",
    "feedback": "提交反馈",
    "admin_recharge": "管理员充值",
    "view_history": "查看历史",
    "reuse_history": "复用历史文案",
}


def _metric_card(label_cn, label_en, value, color="#1d1d1f"):
    """管理后台指标卡片 HTML"""
    return (
        f'<div style="background:#f5f5f7;border-radius:14px;padding:16px;">'
        f'<div style="font-size:11px;color:#86868b;">{label_cn} {label_en}</div>'
        f'<div style="font-size:28px;font-weight:600;color:{color};margin-top:4px;">'
        f'{value}</div></div>'
    )


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

        # ── Tab 胶囊形样式 ──
        st.markdown("""
        <style>
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

        # ── 预查询：会员配额（Tab 1 和 Tab 3 共用） ──
        _tier_labels = {k: v["name"] for k, v in TIER_PLANS.items()}
        quota_rows = conn.execute(
            "SELECT invite_code, pro_gen_used, tier, updated_at "
            "FROM quota_usage ORDER BY pro_gen_used DESC"
        ).fetchall()
        df_quota = None
        if quota_rows:
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
            if df_quota is not None:
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
            if df_quota is not None:
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
                        "成功": "✓" if r["success"] else "✗",
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


st.set_page_config(
    page_title="小红书内容Agent",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="expanded",
)

init_db()

st.markdown("""
<style>
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

/* ── 隐藏 Streamlit 默认 UI 元素 ── */
#MainMenu {visibility: hidden !important;}
header {visibility: hidden !important; height: 0 !important;}
footer {visibility: hidden !important; height: 0 !important;}
[data-testid="stToolbar"] {display: none !important;}
[data-testid="stDecoration"] {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}
.stDeployButton {display: none !important;}
.viewerBadge_container__r5tak {display: none !important;}
.styles_viewerBadge__CvC9N {display: none !important;}
[data-testid="manage-app-button"] {display: none !important;}
._profileContainer_gzau3_53 {display: none !important;}
.st-emotion-cache-ztfqz8 {display: none !important;}
[class*="stActionButton"] {display: none !important;}

/* ═══════════════════════════════════════════════
   LIGHT THEME — Apple + 小红书 Red
   Background: #FFFFFF · Text: #1D1D1F · Accent: #FF2442
═══════════════════════════════════════════════ */

/* ── Global ── */
html, body,
[data-testid="stApp"],
.stApp {
    background-color: #FFFFFF !important;
    color: #6E6E73 !important;
}
.main .block-container {
    background-color: #FFFFFF !important;
    padding-top: 1.5rem;
}

/* ── Top header / toolbar ── */
[data-testid="stHeader"],
[data-testid="stToolbar"] {
    background-color: #FFFFFF !important;
    border-bottom: 1px solid #F2F2F7 !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background-color: #F5F5F7 !important;
    border-right: 1px solid #E5E5EA !important;
}
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    color: #6E6E73 !important;
}
section[data-testid="stSidebar"] strong {
    color: #1D1D1F !important;
}
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #86868B !important;
}
section[data-testid="stSidebar"] hr {
    border-color: #E5E5EA !important;
}

/* ── Headings ── */
h1, h2, h3, h4, h5 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
}
h1 { font-size: 2.2rem !important; }
h3 { font-size: 1.1rem !important; }

/* ── Divider ── */
hr {
    border: none !important;
    border-top: 1px solid #E5E5EA !important;
    margin: 1rem 0 !important;
}

/* ── Paragraphs / captions ── */
p, .stMarkdown p { color: #6E6E73 !important; }
.stCaption, [data-testid="stCaptionContainer"],
.stCaption > p, [data-testid="stCaptionContainer"] > p {
    color: #86868B !important;
}

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

/* ── Download Button ── */
[data-testid="stDownloadButton"] > button {
    background-color: #FFFFFF !important;
    color: #1D1D1F !important;
    border: 1px solid #E5E5EA !important;
    border-radius: 10px !important;
}
[data-testid="stDownloadButton"] > button:hover {
    border-color: #FF2442 !important;
    color: #FF2442 !important;
}

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

/* ── Selectbox ── */
.stSelectbox > div > div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #1D1D1F !important;
    border: 1px solid #E5E5EA !important;
    border-radius: 10px !important;
}
.stSelectbox label { color: #86868B !important; }
.stSelectbox svg { fill: #86868B !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    border: 1px solid #E5E5EA !important;
    border-radius: 10px !important;
    overflow: hidden;
    background-color: #FAFAFA !important;
}
[data-testid="stExpander"] summary {
    background-color: #FAFAFA !important;
    color: #6E6E73 !important;
    padding: 10px 14px !important;
}
[data-testid="stExpander"] summary:hover {
    color: #FF2442 !important;
}
[data-testid="stExpander"] svg { fill: #86868B !important; }
.streamlit-expanderContent {
    background-color: #FAFAFA !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    border-width: 0 0 0 3px !important;
    border-style: solid !important;
    background-color: #FAFAFA !important;
    color: #6E6E73 !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] div,
[data-testid="stAlert"] span {
    color: inherit !important;
}
/* success */
[data-testid="stAlert"][data-baseweb="notification"] {
    background-color: #FAFAFA !important;
}

/* ── Progress Bar ── */
[data-testid="stProgressBar"] > div {
    background-color: var(--bg-secondary) !important;
    border-radius: 4px !important;
}
[data-testid="stProgressBar"] > div > div {
    background-color: var(--accent) !important;
    border-radius: 4px !important;
}

/* ── Code / Pre ── */
.stCode, [data-testid="stCode"],
code, pre {
    background-color: #F5F5F7 !important;
    color: #1D1D1F !important;
    border: 1px solid #E5E5EA !important;
    border-radius: 6px !important;
}

/* ── File Uploader ── */
[data-testid="stFileUploader"],
[data-testid="stFileUploaderDropzone"] {
    background-color: #FAFAFA !important;
    border: 1px dashed #D1D1D6 !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploader"] label {
    color: #86868B !important;
}

/* File uploader 汉化 */
[data-testid="stFileUploaderDropzoneInstructions"] > div > span {
    font-size: 0 !important;
    line-height: 0;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div > span::after {
    content: "拖拽图片到此处";
    font-size: 0.875rem;
    line-height: 1.4;
    color: #86868B;
}
[data-testid="stFileUploaderDropzoneInstructions"] small {
    font-size: 0 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] small::after {
    content: "支持 JPG / JPEG / PNG / WEBP，单文件最大 20MB";
    font-size: 0.75rem;
    color: #AEAEB2;
}
[data-testid="stFileUploaderDropzone"] button span {
    font-size: 0 !important;
}
[data-testid="stFileUploaderDropzone"] button span::after {
    content: "选择文件";
    font-size: 0.875rem;
}

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

/* ── Spinner ── */
[data-testid="stSpinner"] > div {
    border-top-color: #FF2442 !important;
}

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

/* ── Image captions ── */
[data-testid="stImage"] p { color: #86868B !important; font-size: 0.75rem !important; }

/* ── New Design System Classes ── */

/* Step 标签 */
.step-tag {
    font-size: 16px; font-weight: 700;
    color: var(--accent); background: var(--bg-selected);
    padding: 4px 12px; border-radius: var(--radius-xs);
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

/* ── Download Buttons ── */
.stDownloadButton > button {
    background: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #F5F5F7; }
::-webkit-scrollbar-thumb { background: #D1D1D6; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #AEAEB2; }

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
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  Session State 初始化
# ═══════════════════════════════════════════════════════
for _k, _v in DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

if "admin_view" not in st.session_state:
    st.session_state.admin_view = False


# ═══════════════════════════════════════════════════════
#  页面1：邀请码 + 手机号登录
# ═══════════════════════════════════════════════════════
if not st.session_state.authed:
    st.markdown("""
    <div class="gate-box">
        <div class="gate-logo">
            <div class="gate-logo-icon" style="font-weight:800;">R</div>
            <div class="gate-title">红薯特工</div>
        </div>
        <div class="gate-sub">面向小红书的 AI 内容创作助手</div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown(
            "<div style='font-size:12px;font-weight:500;color:#1d1d1f;margin-bottom:4px;'>"
            "手机号 <span style='color:#86868b;font-weight:400;'>Phone</span></div>",
            unsafe_allow_html=True,
        )
        _phone_input = st.text_input(
            "phone",
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
            "invite_code",
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


# ═══════════════════════════════════════════════════════
#  侧边栏
# ═══════════════════════════════════════════════════════
with st.sidebar:
    _phone_display = st.session_state.get("user_phone", "")
    if _phone_display:
        _phone_masked = _phone_display[:3] + "****" + _phone_display[7:]
        st.markdown(f"**欢迎！** {_phone_masked} · `{st.session_state.invite_code}`")
    else:
        st.markdown(f"**欢迎测试！** `{st.session_state.invite_code}`")

    # ── 管理后台入口（仅管理员可见） ──
    if st.session_state.invite_code in ADMIN_CODES:
        _admin_label = "← 返回内容生成" if st.session_state.get("admin_view") else "📊 管理后台"
        if st.button(_admin_label, use_container_width=True, key="btn_admin_toggle"):
            st.session_state.admin_view = not st.session_state.get("admin_view", False)
            st.rerun()

    st.divider()

    st.markdown("**📍 所在城市/区域**")
    _city_input = st.text_input(
        "城市区域",
        value=st.session_state.city,
        placeholder="如：北京·朝阳区 / 上海·徐汇区 / 济南·历下区",
        label_visibility="collapsed",
        max_chars=30,
    )
    if _city_input.strip():
        st.session_state.city = _city_input.strip()
    if st.session_state.city:
        st.caption(f"✓ 已设置：{st.session_state.city}")
    else:
        st.caption("填写后，AI 生成的文案会自动融入本地元素")

    st.divider()

    # 会员额度显示
    _code = st.session_state.invite_code
    _user_tier_now = get_user_tier(_code)
    _tier_label_now = TIER_PLANS.get(_user_tier_now, TIER_PLANS["free"])["name"]
    _pro_used = get_pro_used(_code)
    _pro_left = PRO_GEN_LIMIT - _pro_used
    st.markdown(f"**💎 {_tier_label_now}** · 配图额度")
    if _pro_left > 10:
        st.success(f"剩余 **{_pro_left}** 次")
    elif _pro_left > 0:
        st.warning(f"剩余 **{_pro_left}** 次（快用完了）")
    else:
        st.error("体验额度已用完")
        st.caption("👇 升级会员，解锁更多额度")
        _plus = TIER_PLANS["plus"]
        st.markdown(f"**{_plus['name']}** ¥{_plus['price']}/{_plus['quota']}次")
        st.caption(f"微信联系充值：{PAYMENT_CONTACT_WECHAT}")

    st.caption("")

    # ── 历史记录 ──
    st.divider()
    if st.button("📜 查看历史记录", use_container_width=True):
        st.session_state["show_history"] = not st.session_state.get("show_history", False)
        st.rerun()

    if st.session_state.get("show_history"):
        history = get_history(st.session_state.invite_code, limit=10)
        if history:
            for h in history:
                ind_label = INDUSTRIES.get(h["industry_id"], {}).get("label", h["industry_id"])
                mode_label = "竞品参考" if h["mode"] == "rewrite" else "原创生成"
                time_str = h["created_at"][:16].replace("T", " ") if h["created_at"] else ""
                with st.expander(f"{ind_label} · {mode_label} · {time_str}"):
                    st.text_area("生成的文案", value=h["output_text"], height=150,
                                 disabled=True, key=f"hist_{h['id']}")
                    if st.button("复用这篇", key=f"reuse_{h['id']}"):
                        st.session_state.rewrite_result = h["output_text"]
                        st.session_state.rewrite_done = True
                        st.session_state.industry_id = h["industry_id"]
                        st.session_state.selected_mode = h["mode"]
                        st.session_state.content_ready = True
                        st.session_state["show_history"] = False
                        st.rerun()
        else:
            st.caption("还没有生成记录")

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

    # ── 意见反馈入口（侧边栏，随时可见） ──
    st.divider()
    with st.expander("📝 意见反馈"):
        _fb_text = st.text_area(
            "你的建议",
            placeholder="功能建议、使用问题、想要的新行业模板……都可以写在这里",
            height=100,
            label_visibility="collapsed",
            key="sidebar_feedback_text",
        )
        _fb_rating = st.select_slider(
            "体验评分",
            options=["😣 很差", "😕 一般", "😐 还行", "😊 不错", "🤩 很棒"],
            value="😊 不错",
            key="sidebar_feedback_rating",
        )
        if st.button("提交反馈", key="sidebar_feedback_btn", type="primary", use_container_width=True):
            if _fb_text.strip():
                _fb_conn = None
                try:
                    _fb_conn = get_db()
                    _fb_rating_text = _fb_rating.split(" ", 1)[-1] if " " in _fb_rating else _fb_rating
                    _fb_conn.execute(
                        "INSERT INTO feedback (invite_code, rating, feedback_text, industry_id, mode) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (st.session_state.invite_code, _fb_rating_text, _fb_text.strip(),
                         st.session_state.get("industry_id", ""), "sidebar"),
                    )
                    _fb_conn.commit()
                except Exception:
                    pass
                finally:
                    if _fb_conn:
                        _fb_conn.close()
                log_event(st.session_state.invite_code, "feedback",
                          st.session_state.get("industry_id", ""), "sidebar",
                          detail=_fb_text.strip()[:100])
                st.success("感谢反馈！David 会认真看每一条 🙏")
            else:
                st.warning("请输入反馈内容")

    if st.button("退出登录", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    st.caption("Demo v5.0 · 内测版\n\n遇到问题请截图反馈给 David 15606343555")


# ═══════════════════════════════════════════════════════
#  页面分支：管理视图 / 内容生成
# ═══════════════════════════════════════════════════════
if st.session_state.get("admin_view") and st.session_state.invite_code in ADMIN_CODES:
    render_admin_panel()
    st.stop()


# ═══════════════════════════════════════════════════════
#  页面2：行业选择（3列网格 + emoji + 中英双语）
# ═══════════════════════════════════════════════════════
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
                st.session_state.industry_confirmed = False
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

industry = dict(INDUSTRIES[st.session_state.industry_id])  # 浅拷贝，避免修改原模板

# ── 自定义行业：让用户输入行业名称，动态生成 AI 提示词 ─────────────────────
if st.session_state.industry_id == "custom":
    st.markdown("#### 告诉我你的行业")
    _custom_name = st.text_input(
        "你的行业名称",
        value=st.session_state.custom_industry_name,
        placeholder="如：花艺工作室 / 汽车改装 / 瑜伽馆 / 摄影工作室",
        key="custom_industry_input",
    )
    st.session_state.custom_industry_name = _custom_name

    if not _custom_name.strip():
        st.info("请先输入你的行业名称")
        st.stop()

    # 动态重建 AI 提示词，把通用模板里注入行业名
    industry["label"] = _custom_name.strip()
    industry["system_prompt"] = (
        f"你是专业的{_custom_name}小红书文案改写专家。\n\n"
        "改写规则：\n"
        f"1. 保留原文关于{_custom_name}的核心卖点（效果数据、产品亮点、真实反馈）\n"
        "2. 完全更换表达方式，改写率 > 70%\n"
        f"3. 风格：符合{_custom_name}行业调性，专业可信+亲切真实，口语化，适当使用 emoji\n"
        "4. 融入城市本地元素（地标、商圈、区域名）\n"
        "5. 保留并优化话题标签（#xxx）\n"
        f"6. 强调{_custom_name}行业的核心卖点和差异化优势\n\n"
        "请严格按以下格式输出：\n"
        "【标题】改写后的标题\n"
        "【正文】改写后的正文"
    )
    industry["create_system_prompt"] = (
        f"你是专业的{_custom_name}小红书文案创作专家。\n\n"
        f"根据{_custom_name}店铺/品牌信息和今日主题，创作一篇原创小红书笔记。\n\n"
        "创作要求：\n"
        f"1. 风格：符合{_custom_name}行业调性，专业可信+真实亲切，口语化，适当使用 emoji\n"
        "2. 结构：吸引眼球的标题 + 痛点/需求共鸣 + 产品/服务介绍 + 效果/案例展示 + 行动引导\n"
        f"3. 围绕{_custom_name}行业特点使用高转化种草词\n"
        "4. 加入真实案例或数据对比，增强可信度\n"
        "5. 结尾加话题标签（5-8个）\n"
        "6. 字数：正文300-500字\n\n"
        "请严格按以下格式输出：\n"
        "【标题】原创标题（含emoji，突出卖点）\n"
        "【正文】原创正文"
    )


# ═══════════════════════════════════════════════════════
#  页面3：工作方式选择（竞品参考 vs 原创生成）
# ═══════════════════════════════════════════════════════
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

st.divider()

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


# ═══════════════════════════════════════════════════════
#  Step 1：输入内容（根据模式分流）
# ═══════════════════════════════════════════════════════

# ─── Mode A：粘贴竞品链接（支持批量）───
if mode == "rewrite":
    st.markdown(
        "<div style='font-size:18px;font-weight:600;color:#1d1d1f;'>粘贴竞品笔记链接</div>"
        "<div style='font-size:12px;color:#86868b;'>Paste Competitor Note Links</div>",
        unsafe_allow_html=True,
    )
    st.caption("支持批量：每行粘贴一条分享内容，最多同时处理 10 条")

    paste_input = st.text_area(
        "粘贴分享内容",
        height=120,
        max_chars=3000,
        placeholder="每行粘贴一条，例如：\n宝藏健身房推荐🔥 http://xhslink.com/xxx\n超绝私教课 http://xhslink.com/yyy\n（也可以只粘贴一条）",
        label_visibility="collapsed",
    )

    col_btn, col_up = st.columns([1, 2])
    with col_btn:
        btn_extract = st.button("🚀 一键提取", type="primary", use_container_width=True)
    with col_up:
        extra_imgs = st.file_uploader(
            "补充上传图片（可选，仅单条模式生效）",
            type=["jpg", "jpeg", "png", "webp", "heic", "heif", "bmp", "tiff", "gif"],
            accept_multiple_files=True,
        )

    if btn_extract:
        if not paste_input.strip():
            st.warning("请先粘贴小红书分享内容")
        else:
            # --- 解析输入中的所有 URL ---
            _all_urls = re.findall(r'https?://[^\s，,、!！\]】]+', paste_input)
            _all_urls = [u.rstrip('.,;:!?。，；：！？') for u in _all_urls]
            # 去重并保持顺序
            _seen = set()
            urls = []
            for u in _all_urls:
                if u not in _seen:
                    _seen.add(u)
                    urls.append(u)
            if len(urls) > 10:
                st.warning("最多同时处理 10 条链接，已截取前 10 条")
                urls = urls[:10]

            if not urls:
                # 没解析出 URL，走原来的单条逻辑
                urls = [paste_input.strip()]

            is_batch = len(urls) > 1
            prog = st.progress(0, text=f"开始提取（共 {len(urls)} 条）…")
            batch = []
            all_logs = []

            for idx, raw_url in enumerate(urls):
                base_pct = idx / len(urls)
                step_pct = 1.0 / len(urls)

                def _cb(pct, msg):
                    prog.progress(min(base_pct + pct * step_pct * 0.7, 0.99),
                                  text=f"[{idx+1}/{len(urls)}] {msg}")

                title, text, img_urls, logs = try_extract_xhs(raw_url, _cb)
                all_logs.append(f"── 第 {idx+1} 条 ──\n" + "\n".join(logs))

                prog.progress(min(base_pct + step_pct * 0.7, 0.99),
                              text=f"[{idx+1}/{len(urls)}] 下载图片…")
                downloaded = []
                for i, u in enumerate(img_urls or []):
                    im = download_image_url(u)
                    if im:
                        downloaded.append(im)

                # 单条模式：追加用户手动上传的图片
                if not is_batch and extra_imgs:
                    for f in extra_imgs:
                        try:
                            downloaded.append(Image.open(f).convert("RGB"))
                        except (OSError, ValueError):
                            pass

                batch.append({
                    "url": raw_url,
                    "title": title or "",
                    "text": text or "",
                    "images": downloaded,
                    "rewrite": "",
                    "edited_images": [],
                })

            prog.progress(1.0, text="提取完成！")
            st.session_state.extract_log = "\n\n".join(all_logs)

            # 过滤掉完全失败的（无标题无正文）
            ok_batch = [b for b in batch if b["title"] or b["text"]]

            if ok_batch:
                st.session_state.batch_results = ok_batch
                # 兼容旧变量（单条时同步写入）
                st.session_state.note_title = ok_batch[0]["title"]
                st.session_state.note_text = ok_batch[0]["text"]
                st.session_state.note_images = ok_batch[0]["images"]
                st.session_state.content_ready = True
                st.session_state.rewrite_done = False
                st.session_state.images_done = False
                st.session_state.rewrite_result = ""
                st.session_state.competitor_analysis = None
                st.session_state.content_strategy = None
                st.session_state.edited_title = ""
                st.session_state.edited_body = ""
                st.session_state.edited_images = []

                if is_batch:
                    failed = len(batch) - len(ok_batch)
                    msg = f"批量提取完成！成功 {len(ok_batch)} 条"
                    if failed:
                        msg += f"，失败 {failed} 条"
                    st.success(msg)
                else:
                    b = ok_batch[0]
                    parts = []
                    if b["title"]:
                        parts.append("标题 ✓")
                    if b["text"]:
                        parts.append(f"正文 ✓（{len(b['text'])}字）")
                    if b["images"]:
                        parts.append(f"{len(b['images'])}张图片 ✓")
                    st.success(f"提取成功！{' | '.join(parts)}")

                    if not b["text"] and b["title"]:
                        st.info(
                            "💡 **正文未提取到**（小红书反爬限制）\n\n"
                            "操作：小红书 App 打开该笔记 → 长按正文 → 全选复制 → 粘贴到下方「正文」框 → 点击「更新内容」"
                        )
                    if not b["images"] and b["title"]:
                        st.info("💡 **图片未提取到**，可在下方手动上传原图")
                st.rerun()
            else:
                st.error("提取失败 — 小红书限制了自动访问")
                st.markdown(
                    "**手动补救（30秒搞定）**：\n"
                    "1. 在小红书 App 打开这篇笔记\n"
                    "2. 长按标题 → 复制\n"
                    "3. 长按正文 → 全选 → 复制\n"
                    "4. 粘贴到下方对应的框里"
                )
                st.session_state["_show_manual_fallback"] = True

    if st.session_state.extract_log:
        with st.expander("查看提取详情", expanded=False):
            st.code(st.session_state.extract_log, language=None)

    # ── 手动输入兜底（提取失败时自动展开）──
    if st.session_state.get("_show_manual_fallback") and not st.session_state.content_ready:
        with st.expander("手动粘贴笔记内容", expanded=True):
            manual_title = st.text_input("笔记标题", placeholder="从小红书App复制标题粘贴到这里", key="manual_title")
            manual_text = st.text_area(
                "笔记正文",
                height=200,
                placeholder="从小红书App长按正文 → 全选 → 复制 → 粘贴到这里",
                key="manual_text",
            )
            manual_imgs = st.file_uploader(
                "笔记图片（可选，截图或保存的图片）",
                type=["jpg", "jpeg", "png", "webp", "heic", "heif", "bmp", "tiff", "gif"],
                accept_multiple_files=True,
                key="manual_imgs",
            )
            if st.button("确认手动内容", type="primary", key="btn_manual_confirm"):
                if manual_title.strip() or manual_text.strip():
                    st.session_state.note_title = manual_title.strip()
                    st.session_state.note_text = manual_text.strip()
                    imgs = []
                    if manual_imgs:
                        for f in manual_imgs:
                            try:
                                imgs.append(Image.open(f).convert("RGB"))
                            except (OSError, ValueError):
                                pass
                    st.session_state.note_images = imgs
                    st.session_state.batch_results = [{
                        "url": "",
                        "title": manual_title.strip(),
                        "text": manual_text.strip(),
                        "images": imgs,
                        "rewrite": "",
                        "edited_images": [],
                    }]
                    st.session_state.content_ready = True
                    st.session_state.rewrite_done = False
                    st.session_state.images_done = False
                    st.session_state.competitor_analysis = None
                    st.session_state.content_strategy = None
                    st.session_state.edited_title = ""
                    st.session_state.edited_body = ""
                    st.session_state["_show_manual_fallback"] = False
                    st.rerun()
                else:
                    st.warning("至少填写标题或正文")

    _is_batch = len(st.session_state.batch_results) > 1

    if st.session_state.content_ready and not _is_batch:
        # 单条模式：显示可编辑的内容
        with st.expander("📋 已提取的内容（可手动补充编辑）", expanded=True):
            edit_title = st.text_input("标题", value=st.session_state.note_title)
            edit_text = st.text_area(
                "正文",
                value=st.session_state.note_text,
                height=150,
                placeholder="如果正文未提取到，从小红书 App 复制正文粘贴到这里…",
            )
            add_imgs = st.file_uploader(
                "补充/替换图片",
                type=["jpg", "jpeg", "png", "webp", "heic", "heif", "bmp", "tiff", "gif"],
                accept_multiple_files=True,
                key="add_imgs_edit",
            )
            if st.button("💾 更新内容"):
                st.session_state.note_title = edit_title.strip()
                st.session_state.note_text = edit_text.strip()
                if add_imgs:
                    new_imgs = [Image.open(f).convert("RGB") for f in add_imgs]
                    if new_imgs:
                        st.session_state.note_images = new_imgs
                # 同步到 batch_results
                if st.session_state.batch_results:
                    st.session_state.batch_results[0]["title"] = edit_title.strip()
                    st.session_state.batch_results[0]["text"] = edit_text.strip()
                    if add_imgs and new_imgs:
                        st.session_state.batch_results[0]["images"] = new_imgs
                st.session_state.rewrite_done = False
                st.session_state.images_done = False
                st.session_state.competitor_analysis = None
                st.session_state.content_strategy = None
                st.session_state.edited_title = ""
                st.session_state.edited_body = ""
                st.success("内容已更新！")
                st.rerun()

            if st.session_state.note_images:
                _nc = img_cols(len(st.session_state.note_images))
                _columns = st.columns(_nc)
                for i, img in enumerate(st.session_state.note_images):
                    with _columns[i % _nc]:
                        st.image(img, caption=f"原图 {i+1}", use_container_width=True)

    elif st.session_state.content_ready and _is_batch:
        # 批量模式：用 tabs 展示每条提取结果
        with st.expander(f"📋 已提取 {len(st.session_state.batch_results)} 条内容（点击查看）", expanded=False):
            _tab_names = [f"笔记 {i+1}" for i in range(len(st.session_state.batch_results))]
            _tabs = st.tabs(_tab_names)
            for i, (tab, br) in enumerate(zip(_tabs, st.session_state.batch_results)):
                with tab:
                    st.markdown(f"**标题**：{br['title'] or '（未提取到）'}")
                    if br["text"]:
                        st.caption(br["text"][:200] + ("…" if len(br["text"]) > 200 else ""))
                    else:
                        st.caption("（正文未提取到）")
                    if br["images"]:
                        st.caption(f"图片：{len(br['images'])} 张")
                    else:
                        st.caption("图片：无")


# ─── Mode B：店铺名片 + 今日主题 ───
else:
    st.markdown(
        "<div style='font-size:18px;font-weight:600;color:#1d1d1f;'>店铺信息 + 今日主题</div>"
        "<div style='font-size:12px;color:#86868b;'>Store Info & Daily Topic</div>",
        unsafe_allow_html=True,
    )
    st.caption("填写一次，每次只需更新「今日主题」，AI 为你生成专属原创文案")

    with st.expander("🏪 店铺名片（填写后长期使用）", expanded=not bool(st.session_state.store_profile)):
        profile = dict(st.session_state.store_profile)
        for field in industry["profile_fields"]:
            profile[field["key"]] = st.text_input(
                field["label"],
                value=profile.get(field["key"], ""),
                placeholder=field["placeholder"],
                key=f"pf_{field['key']}",
            )

        if st.button("💾 保存店铺信息"):
            st.session_state.store_profile = profile
            st.success("店铺信息已保存！")

    st.markdown("**✏️ 今日发什么？**")
    brief = st.text_area(
        "今日主题/卖点",
        value=st.session_state.daily_brief,
        height=100,
        placeholder=industry.get("brief_placeholder", "描述你今天想发的内容…"),
        label_visibility="collapsed",
    )
    st.session_state.daily_brief = brief

    st.markdown("**📷 上传你的图片**")
    with st.expander("📌 拍摄要求（点击查看）", expanded=False):
        st.markdown(
            "- **竖拍为主**：9:16 比例最佳，与小红书全屏浏览一致\n"
            "- **光线充足**：自然光最佳，避免过暗或逆光模糊\n"
            "- **突出主体**：食物/产品/环境/人物居中，背景尽量简洁\n"
            "- **保持真实**：无需提前加滤镜，AI 会自动根据文案氛围美化\n"
            "- **清晰不模糊**：避免手抖，可借助三脚架或靠墙稳定\n"
            "- **建议数量**：3~9 张，覆盖不同角度或细节\n\n"
            "⚠️ 必须是自己店铺/产品的真实照片，不可使用竞品或网络图片"
        )
    uploaded_imgs = st.file_uploader(
        "上传图片",
        type=["jpg", "jpeg", "png", "webp", "heic", "heif", "bmp", "tiff", "gif"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="create_img_upload",
    )
    if uploaded_imgs:
        imgs = []
        for f in uploaded_imgs:
            try:
                imgs.append(Image.open(f).convert("RGB"))
            except (OSError, ValueError):
                pass
        if imgs:
            st.session_state.create_images = imgs
            _nc = img_cols(len(imgs))
            _columns = st.columns(_nc)
            for i, img in enumerate(imgs):
                with _columns[i % _nc]:
                    st.image(img, caption=f"图片 {i+1}", use_container_width=True)

    if st.button("✅ 确认，开始生成", type="primary"):
        if not brief.strip():
            st.warning("请填写今日主题")
        else:
            if not any(v.strip() for v in profile.values() if isinstance(v, str)):
                st.warning("💡 建议填写店铺信息，AI 会生成更精准的文案")
            if not st.session_state.store_profile:
                st.session_state.store_profile = profile
            st.session_state.daily_brief = brief
            st.session_state.note_images = st.session_state.create_images
            st.session_state.content_ready = True
            st.session_state.rewrite_done = False
            st.session_state.images_done = False
            st.session_state.rewrite_result = ""
            st.session_state.competitor_analysis = None
            st.session_state.content_strategy = None
            st.session_state.edited_title = ""
            st.session_state.edited_body = ""
            st.session_state.edited_images = []
            st.session_state.dynamic_image_prompt = ""
            st.session_state.scene_images = []
            st.session_state.scene_prompt = ""
            st.rerun()

    if st.session_state.content_ready and mode == "create":
        store_filled = {k: v for k, v in st.session_state.store_profile.items() if v}
        parts = []
        if store_filled:
            parts.append(f"店铺信息 ✓（{len(store_filled)}项）")
        if st.session_state.daily_brief:
            parts.append("今日主题 ✓")
        if st.session_state.note_images:
            parts.append(f"{len(st.session_state.note_images)}张图片 ✓")
        if parts:
            st.success(f"内容已确认：{' | '.join(parts)}")


# ─── 已完成步骤折叠：Step 1 ───
if st.session_state.content_ready and st.session_state.rewrite_done:
    _note_count = len(st.session_state.batch_results) if st.session_state.batch_results else 1
    _img_count = len(st.session_state.note_images)
    render_completed_step("提取完成", f"{_note_count} 条笔记 · {_img_count} 张图片")

# ═══════════════════════════════════════════════════════
#  Step 2：AI 文案处理
# ═══════════════════════════════════════════════════════
if st.session_state.content_ready:
    st.divider()

    # ─── Mode A 需求输入面板（仅单条模式） ───
    _is_batch_check = mode == "rewrite" and len(st.session_state.batch_results) > 1
    if mode == "rewrite" and not _is_batch_check and (st.session_state.note_title or st.session_state.note_text):
        st.markdown(
            "<div style='font-size:18px;font-weight:600;color:#1d1d1f;'>发帖需求 "
            "<span style='font-size:12px;color:#86868b;font-weight:400;'>Optional</span></div>"
            "<div style='font-size:12px;color:#86868b;'>Post Requirements</div>",
            unsafe_allow_html=True,
        )

        # 店铺资料（可折叠）
        with st.expander("填写店铺资料（可选，提升差异化效果）", expanded=False):
            # 自动加载已保存的资料
            _saved_profile = load_store_profile(
                st.session_state.user_phone,
                st.session_state.industry_id or "",
            )
            _sp_name = st.text_input(
                "店铺名称",
                value=_saved_profile.get("store_name", ""),
                key="sp_store_name",
            )
            _sp_selling = st.text_area(
                "核心卖点",
                value=_saved_profile.get("core_selling_points", ""),
                max_chars=200,
                key="sp_core_selling",
                placeholder="如：10年老店、进口材料、明星同款…",
            )
            _sp_audience = st.text_input(
                "目标客群",
                value=_saved_profile.get("target_audience", ""),
                key="sp_target_audience",
                placeholder="如：25-35岁女性、宝妈、健身爱好者…",
            )
            if st.button("保存店铺资料", key="btn_save_profile"):
                _profile = {
                    "store_name": _sp_name,
                    "core_selling_points": _sp_selling,
                    "target_audience": _sp_audience,
                }
                save_store_profile(
                    st.session_state.user_phone,
                    st.session_state.industry_id or "",
                    _profile,
                )
                st.success("已保存！下次自动加载")

        # 发帖目的 + 语气风格
        _req_col1, _req_col2 = st.columns(2)
        with _req_col1:
            st.session_state.post_goal = st.selectbox(
                "发帖目的",
                POST_GOALS,
                index=POST_GOALS.index(st.session_state.get("post_goal", "种草案例")),
                key="sel_post_goal",
            )
        with _req_col2:
            st.session_state.tone_style = st.selectbox(
                "语气风格",
                TONE_STYLES,
                index=TONE_STYLES.index(st.session_state.get("tone_style", "温暖亲切")),
                key="sel_tone_style",
            )

        st.session_state.extra_requirements = st.text_area(
            "补充要求（可选）",
            value=st.session_state.get("extra_requirements", ""),
            key="ta_extra_req",
            placeholder="例如：突出性价比、提到新店开业、强调限时优惠…",
            height=68,
        )

        st.divider()

    _batch = st.session_state.batch_results
    _is_batch_mode = mode == "rewrite" and len(_batch) > 1

    if mode == "rewrite":
        _n_label = f"（{len(_batch)} 条）" if _is_batch_mode else ""
        label_2 = f"AI 文案改写{_n_label}（{industry['label']} · {_city_label}风格）"
        btn_label = f"✨ 一键改写全部文案（{len(_batch)} 条）" if _is_batch_mode else "✨ 一键改写文案"
    else:
        label_2 = f"AI 原创文案生成（{industry['label']} · {_city_label}风格）"
        btn_label = "✨ 一键生成文案"

    st.markdown(
        f"<div style='font-size:18px;font-weight:600;color:#1d1d1f;'>{label_2}</div>"
        f"<div style='font-size:12px;color:#86868b;'>AI Content Processing</div>",
        unsafe_allow_html=True,
    )
    st.caption("🆓 免费功能 · 由语言模型驱动")

    if st.button(btn_label, type="primary", key="btn_rewrite"):
        if mode == "rewrite" and not _is_batch_mode and not st.session_state.note_title and not st.session_state.note_text:
            st.error("标题和正文都为空，请先补充内容")
        elif mode == "create" and not st.session_state.daily_brief.strip():
            st.error("请填写今日主题")
        else:
            with st.status("AI 正在创作…", expanded=True) as _gen_status:
                try:
                    # 检查用户等级，企业版用 Claude
                    _user_tier = get_user_tier(st.session_state.invite_code)
                    _use_claude = (_user_tier == "promax")
                    _brain_name = "高级语言模型" if _use_claude else "语言模型"
                    _rewrite_fn = rewrite_with_claude if _use_claude else rewrite_with_deepseek
                    _create_fn = generate_original_with_claude if _use_claude else generate_original_content

                    if mode == "rewrite" and _is_batch_mode:
                        # --- 批量改写 ---
                        for bi, br in enumerate(_batch):
                            _gen_status.update(label=f"{_brain_name} 正在改写第 {bi+1}/{len(_batch)} 条…")
                            result = _rewrite_fn(
                                br["title"], br["text"], industry, st.session_state.city,
                            )
                            br["rewrite"] = result
                            save_generation(
                                invite_code=st.session_state.invite_code,
                                industry_id=st.session_state.industry_id,
                                mode="rewrite",
                                input_title=br["title"],
                                input_text=br["text"],
                                input_profile="",
                                output_text=result,
                                image_count=len(br["images"]),
                                city=st.session_state.city,
                            )
                        log_event(st.session_state.invite_code, "generate_text",
                                   st.session_state.industry_id, "rewrite",
                                   detail=json.dumps({"batch_count": len(_batch), "brain": _brain_name}))
                        # 兼容：第一条同步到旧变量
                        st.session_state.rewrite_result = _batch[0]["rewrite"]
                    elif mode == "rewrite":
                        # ── 三步链式生成 ──
                        _step1_ok = False
                        _step2_ok = False

                        # Step 1: 竞品分析
                        _gen_status.update(label="Step 1/3：分析竞品笔记…")
                        try:
                            analysis = analyze_competitor(
                                st.session_state.note_title,
                                st.session_state.note_text,
                                use_claude=_use_claude,
                            )
                            if analysis:
                                st.session_state.competitor_analysis = analysis
                                _step1_ok = True
                        except Exception:
                            pass  # Step1 失败 → 降级为单步

                        # Step 2: 差异化策略
                        if _step1_ok:
                            _gen_status.update(label="Step 2/3：制定差异化策略…")
                            # 构建店铺资料
                            _store_data = None
                            _sp_name = st.session_state.get("sp_store_name", "").strip()
                            _sp_selling = st.session_state.get("sp_core_selling", "").strip()
                            _sp_audience = st.session_state.get("sp_target_audience", "").strip()
                            if _sp_name or _sp_selling or _sp_audience:
                                _store_data = {
                                    "store_name": _sp_name,
                                    "core_selling_points": _sp_selling,
                                    "target_audience": _sp_audience,
                                }
                            try:
                                strategy = plan_content_strategy(
                                    analysis=st.session_state.competitor_analysis,
                                    store_profile=_store_data,
                                    post_goal=st.session_state.get("post_goal", "种草案例"),
                                    tone_style=st.session_state.get("tone_style", "温暖亲切"),
                                    extra_requirements=st.session_state.get("extra_requirements", ""),
                                    use_claude=_use_claude,
                                )
                                if strategy:
                                    st.session_state.content_strategy = strategy
                                    _step2_ok = True
                            except Exception:
                                pass  # Step2 失败 → 跳过策略

                        # Step 3: 生成内容
                        _gen_status.update(label="Step 3/3：生成改写内容…" if _step1_ok else f"{_brain_name} 正在改写文案…")
                        # 降级逻辑：Step2失败但Step1成功时，将分析结果转为简化策略注入
                        _strategy_param = None
                        if _step2_ok:
                            _strategy_param = st.session_state.get("content_strategy")
                        elif _step1_ok and st.session_state.get("competitor_analysis"):
                            # Step2 失败降级：用 Step1 分析结果构造简化策略
                            _analysis = st.session_state.competitor_analysis
                            _strategy_param = {
                                "angle": f"针对竞品弱点改进：{'、'.join(_analysis.get('weaknesses', [])[:2])}",
                                "differentiators": [],
                                "structure_plan": _analysis.get("structure", ""),
                                "tone_guide": f"借鉴竞品的情绪触发点：{'、'.join(_analysis.get('emotional_triggers', [])[:3])}",
                            }
                        try:
                            result = _rewrite_fn(
                                st.session_state.note_title,
                                st.session_state.note_text,
                                industry,
                                st.session_state.city,
                                content_strategy=_strategy_param,
                            )
                        except Exception as step3_err:
                            # Step3 失败：不消耗配额，提示重试
                            refund_pro_quota(st.session_state.invite_code)
                            raise step3_err  # 交给外层 except 处理
                        st.session_state.rewrite_result = result
                        if _batch:
                            _batch[0]["rewrite"] = result
                        save_generation(
                            invite_code=st.session_state.invite_code,
                            industry_id=st.session_state.industry_id,
                            mode="rewrite",
                            input_title=st.session_state.note_title,
                            input_text=st.session_state.note_text,
                            input_profile="",
                            output_text=result,
                            image_count=len(st.session_state.note_images),
                            city=st.session_state.city,
                        )
                        log_event(st.session_state.invite_code, "generate_text",
                                   st.session_state.industry_id, mode,
                                   detail=json.dumps({"chain": _step1_ok, "strategy": _step2_ok, "brain": _brain_name}))
                    else:
                        _gen_status.update(label=f"{_brain_name} 正在创作文案…")
                        result = _create_fn(
                            st.session_state.store_profile,
                            st.session_state.daily_brief,
                            industry,
                            st.session_state.city,
                        )
                        st.session_state.rewrite_result = result
                        save_generation(
                            invite_code=st.session_state.invite_code,
                            industry_id=st.session_state.industry_id,
                            mode=mode,
                            input_title="",
                            input_text=st.session_state.daily_brief,
                            input_profile=json.dumps(st.session_state.store_profile, ensure_ascii=False),
                            output_text=result,
                            image_count=len(st.session_state.note_images),
                            city=st.session_state.city,
                        )
                        log_event(st.session_state.invite_code, "generate_text",
                                   st.session_state.industry_id, mode)
                    st.session_state.rewrite_done = True
                    if mode == "create":
                        _gen_status.update(label="正在生成图片优化指令…")
                        try:
                            dp = generate_dynamic_image_prompt(st.session_state.rewrite_result, industry)
                            st.session_state.dynamic_image_prompt = dp
                        except Exception:
                            st.session_state.dynamic_image_prompt = ""
                    _gen_status.update(label="生成完成！", state="complete", expanded=False)
                    st.rerun()
                except Exception as e:
                    _gen_status.update(label="生成失败", state="error")
                    st.error(friendly_api_error(e))

    if st.session_state.rewrite_done:
        if mode == "rewrite" and _is_batch_mode:
            # --- 批量结果展示 ---
            _tab_names = [f"笔记 {i+1}" for i in range(len(_batch))]
            _rw_tabs = st.tabs(_tab_names)
            for i, (tab, br) in enumerate(zip(_rw_tabs, _batch)):
                with tab:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**原文**")
                        st.info(f"**{br['title']}**\n\n{br['text']}")
                    with c2:
                        st.markdown("**改写后** （右上角可复制）")
                        st.code(br["rewrite"], language=None)
        elif mode == "rewrite":
            # --- 单条 Mode A 结果展示（升级版）---

            # Step 1/2 分析结果（折叠展示）
            if st.session_state.get("competitor_analysis"):
                with st.expander("竞品分析结果", expanded=False):
                    _analysis = st.session_state.competitor_analysis
                    if isinstance(_analysis, dict):
                        if _analysis.get("hooks"):
                            st.markdown("**Hook 手法：** " + "、".join(_analysis["hooks"]))
                        if _analysis.get("structure"):
                            st.markdown(f"**内容结构：** {_analysis['structure']}")
                        if _analysis.get("emotional_triggers"):
                            st.markdown("**情绪触发：** " + "、".join(_analysis["emotional_triggers"]))
                        if _analysis.get("weaknesses"):
                            st.markdown("**可改进：** " + "、".join(_analysis["weaknesses"]))

            if st.session_state.get("content_strategy"):
                with st.expander("内容策略", expanded=False):
                    _strat = st.session_state.content_strategy
                    if isinstance(_strat, dict):
                        if _strat.get("angle"):
                            st.markdown(f"**切入角度：** {_strat['angle']}")
                        if _strat.get("differentiators"):
                            st.markdown("**差异化：** " + "、".join(_strat["differentiators"]))
                        if _strat.get("structure_plan"):
                            st.markdown(f"**结构建议：** {_strat['structure_plan']}")
                        if _strat.get("tone_guide"):
                            st.markdown(f"**语气指导：** {_strat['tone_guide']}")

            # 解析标题和正文（从 【标题】【正文】 格式中提取）
            _raw_result = st.session_state.rewrite_result or ""
            _parsed_title = ""
            _parsed_body = _raw_result
            _title_match = re.search(r'【标题】\s*(.+?)(?:\n|【正文】)', _raw_result, re.DOTALL)
            _body_match = re.search(r'【正文】\s*(.+)', _raw_result, re.DOTALL)
            if _title_match:
                _parsed_title = _title_match.group(1).strip()
            if _body_match:
                _parsed_body = _body_match.group(1).strip()

            # 初始化编辑框（仅首次）
            if st.session_state.get("edited_title") == "" and _parsed_title:
                st.session_state["edited_title"] = _parsed_title
            if st.session_state.get("edited_body") == "" and _parsed_body:
                st.session_state["edited_body"] = _parsed_body

            # 可编辑文本框
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

            # AI 润色按钮
            if st.button("✨ AI 润色一下（消耗1次配额）", key="btn_polish"):
                if not try_use_pro_quota(st.session_state.invite_code):
                    st.error("配额不足，无法润色")
                else:
                    with st.spinner("AI 正在润色…"):
                        try:
                            _user_tier = get_user_tier(st.session_state.invite_code)
                            polished = polish_content(
                                title=st.session_state.get("edited_title", ""),
                                body=st.session_state.get("edited_body", ""),
                                tone_style=st.session_state.get("tone_style", "温暖亲切"),
                                use_claude=(_user_tier == "promax"),
                            )
                            if polished and polished.get("title") and polished.get("body"):
                                st.session_state["edited_title"] = polished["title"]
                                st.session_state["edited_body"] = polished["body"]
                                # 同步更新 rewrite_result 用于后续流程
                                st.session_state.rewrite_result = f"【标题】{polished['title']}\n\n【正文】{polished['body']}"
                                st.rerun()
                            else:
                                refund_pro_quota(st.session_state.invite_code)
                                st.warning("润色失败，可直接使用当前内容")
                        except Exception:
                            refund_pro_quota(st.session_state.invite_code)
                            st.warning("润色失败，可直接使用当前内容")
        else:
            st.markdown("**生成结果** （右上角可复制）")
            st.code(st.session_state.rewrite_result, language=None)


# ═══════════════════════════════════════════════════════
#  Step 3：图片处理
#  Mode A：去水印 + 隐形防查重（Gemini去水印 + PIL隐形处理）
#  Mode B：方案A 美化原图（Gemini，免费）+ 方案B AI配图（体验版 / 精品版）
# ═══════════════════════════════════════════════════════
# 单条 Mode A 时，使用用户编辑后的内容
if mode == "rewrite" and st.session_state.rewrite_done and len(st.session_state.batch_results) <= 1:
    _final_title = st.session_state.get("edited_title", "")
    _final_body = st.session_state.get("edited_body", "")
    if _final_title or _final_body:
        st.session_state.rewrite_result = f"【标题】{_final_title}\n\n【正文】{_final_body}"

# ─── 已完成步骤折叠：Step 2 ───
if st.session_state.rewrite_done and st.session_state.images_done:
    render_completed_step("文案处理完成", "AI 改写已完成")

_has_any_images = st.session_state.note_images or any(br.get("images") for br in st.session_state.batch_results)
if st.session_state.rewrite_done and (_has_any_images or mode == "create"):
    st.divider()
    st.markdown(
        "<div style='font-size:18px;font-weight:600;color:#1d1d1f;'>图片处理</div>"
        "<div style='font-size:12px;color:#86868b;'>Image Processing</div>",
        unsafe_allow_html=True,
    )

    _batch = st.session_state.batch_results
    _is_batch_mode = mode == "rewrite" and len(_batch) > 1

    # ─── Mode A：竞品参考 → 去水印 + 隐形防查重 ───
    if mode == "rewrite":
        st.caption("🆓 免费功能 · AI去除小红书水印 + 隐形防查重（不翻转、不变色）")

        with st.expander("处理说明", expanded=False):
            st.markdown(
                "**两步处理**，去水印 + 避免平台判定为搬运：\n\n"
                "**第1步 — AI 去水印**\n"
                "- 图片引擎识别并去除「小红书」水印文字\n"
                "- 自动修复水印区域，还原原始画面\n\n"
                "**第2步 — 隐形防查重**（肉眼看不出变化）\n"
                "- 清除图片元数据\n"
                "- 微裁边 2-3%\n"
                "- 微缩放 ±2%\n"
                "- 隐形噪点（±2像素值，不可见）\n\n"
                "💡 不翻转图片、不改变商品颜色，确保商品展示效果不受影响"
            )

        # 计算总图片数
        if _is_batch_mode:
            _total_imgs = sum(len(br.get("images", [])) for br in _batch)
            _btn_img_label = f"🧹 一键去水印 + 防查重（{_total_imgs} 张）"
        else:
            _total_imgs = len(st.session_state.note_images)
            _btn_img_label = "🧹 一键去水印 + 防查重"

        if _total_imgs > 0 and st.button(_btn_img_label, type="primary", key="btn_img"):
            if _is_batch_mode:
                # --- 批量处理 ---
                _warnings = []
                with st.spinner(f"正在处理 {_total_imgs} 张图片（AI去水印 + 隐形防查重）..."):
                    for bi, br in enumerate(_batch):
                        imgs = br.get("images", [])
                        edited_list = []
                        for img in imgs:
                            result_img, err = remove_watermark_and_protect(img)
                            edited_list.append(result_img if result_img else stealth_anti_hash(img))
                            if err:
                                _warnings.append(err)
                        br["edited_images"] = edited_list
                if _batch:
                    st.session_state.edited_images = _batch[0].get("edited_images", [])
                st.session_state.images_done = True
                log_event(st.session_state.invite_code, "edit_image",
                           st.session_state.industry_id, mode,
                           detail=json.dumps({"count": _total_imgs, "type": "watermark_batch"}))
                if _warnings:
                    st.warning(f"部分图片去水印未成功，已完成隐形防查重：{_warnings[0]}")
                else:
                    st.success(f"全部 {_total_imgs} 张处理完成！")
                st.rerun()
            else:
                # --- 单条处理 ---
                _warnings = []
                with st.spinner("正在处理图片（AI去水印 + 隐形防查重）..."):
                    edited = []
                    for img in st.session_state.note_images:
                        result_img, err = remove_watermark_and_protect(img)
                        edited.append(result_img if result_img else stealth_anti_hash(img))
                        if err:
                            _warnings.append(err)
                st.session_state.edited_images = edited
                if _batch:
                    _batch[0]["edited_images"] = edited
                st.session_state.images_done = True
                n = len(edited)
                log_event(st.session_state.invite_code, "edit_image",
                           st.session_state.industry_id, mode,
                           detail=json.dumps({"count": n, "type": "watermark"}))
                if _warnings:
                    st.warning(f"部分图片去水印未成功，已完成隐形防查重：{_warnings[0]}")
                else:
                    st.success(f"全部 {n} 张处理完成！")
                st.rerun()

        if st.session_state.images_done:
            if _is_batch_mode:
                _img_tab_names = [f"笔记 {i+1}" for i in range(len(_batch))]
                _img_tabs = st.tabs(_img_tab_names)
                for bi, (tab, br) in enumerate(zip(_img_tabs, _batch)):
                    with tab:
                        _ed = br.get("edited_images", [])
                        _orig = br.get("images", [])
                        if not _orig:
                            st.caption("此笔记无图片")
                            continue
                        for i, (orig, ed) in enumerate(zip(_orig, _ed)):
                            c1, c2 = st.columns(2)
                            with c1:
                                st.image(orig, caption=f"原图 {i+1}", use_container_width=True)
                            with c2:
                                st.image(ed, caption=f"处理后 {i+1}", use_container_width=True)
                                _ec1, _ec2 = st.columns([3, 1])
                                with _ec1:
                                    _req = st.text_input("修改", key=f"edit_bwm_{bi}_{i}",
                                                         placeholder="不满意？描述修改要求…",
                                                         label_visibility="collapsed")
                                with _ec2:
                                    _ebtn = st.button("✏️ 修改", key=f"edit_bwm_btn_{bi}_{i}",
                                                      use_container_width=True)
                                if _ebtn and _req:
                                    with st.spinner(f"正在修改笔记{bi+1}第{i+1}张…"):
                                        _new, _err = edit_image_with_gemini(ed, _req)
                                    if _new:
                                        st.session_state.batch_results[bi]["edited_images"][i] = _new
                                        del st.session_state[f"edit_bwm_{bi}_{i}"]
                                        st.success("修改成功！")
                                        st.rerun()
                                    else:
                                        st.error(f"修改失败：{_err}")
            else:
                for i, (orig, ed) in enumerate(
                    zip(st.session_state.note_images, st.session_state.edited_images)
                ):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.image(orig, caption=f"原图 {i+1}", use_container_width=True)
                    with c2:
                        st.image(ed, caption=f"处理后 {i+1}", use_container_width=True)
                        _ec1, _ec2 = st.columns([3, 1])
                        with _ec1:
                            _req = st.text_input("修改", key=f"edit_wm_{i}",
                                                 placeholder="不满意？描述修改要求…",
                                                 label_visibility="collapsed")
                        with _ec2:
                            _ebtn = st.button("✏️ 修改", key=f"edit_wm_btn_{i}",
                                              use_container_width=True)
                        if _ebtn and _req:
                            with st.spinner(f"正在修改第 {i+1} 张…"):
                                _new, _err = edit_image_with_gemini(ed, _req)
                            if _new:
                                st.session_state.edited_images[i] = _new
                                del st.session_state[f"edit_wm_{i}"]
                                st.success("修改成功！")
                                st.rerun()
                            else:
                                st.error(f"修改失败：{_err}")

    # ─── Mode B：原创模式 → 方案A 美化 + 方案B AI配图（免费/Pro）───
    else:
        st.caption("两种方案可单独使用，也可都做——最终选最好看的发布")

        # ── 方案A：美化原图（仅当用户已上传图片时显示）──
        if st.session_state.note_images:
            st.markdown("**📸 方案A：美化原图** — 🆓 免费 · 保持商品原样，仅优化光线/色调/氛围")

            _beautify_options = {
                "智能匹配": "根据文案情绪自动匹配最佳美化效果",
                "暖调氛围": "温暖柔和的光线，适合美食、家居、生活类",
                "清新明亮": "高亮度、低饱和，适合护肤、穿搭、日系风格",
                "高级质感": "低对比、高质感，适合奢侈品、数码、商务类",
                "鲜艳活力": "高饱和度、强对比，适合运动、户外、潮牌类",
                "自定义": "输入你自己的美化需求",
            }
            _beautify_choice = st.radio(
                "选择美化风格",
                list(_beautify_options.keys()),
                horizontal=True,
                key="beautify_style",
                help="所有方案都会保持商品原样不变，仅调整光线和氛围",
            )
            st.caption(_beautify_options[_beautify_choice])

            _preserve_rule = (
                "CRITICAL RULE: Do NOT change, alter, or replace the main product/subject. "
                "Keep the exact same product shape, color, design, logo, packaging, and all visual details intact. "
                "Only enhance the surrounding lighting, background atmosphere, and color grading. "
                "Remove any text overlays or watermarks."
            )

            if _beautify_choice == "智能匹配":
                img_prompt_a = (
                    st.session_state.dynamic_image_prompt
                    if st.session_state.dynamic_image_prompt
                    else industry["image_prompt"]
                )
                img_prompt_a = f"{_preserve_rule}\n\nStyle direction: {img_prompt_a}"
            elif _beautify_choice == "暖调氛围":
                img_prompt_a = (
                    f"{_preserve_rule}\n\n"
                    "Apply warm golden-hour lighting. Add soft warm tones (amber, honey). "
                    "Create a cozy, inviting atmosphere. Slightly soften shadows for a gentle feel."
                )
            elif _beautify_choice == "清新明亮":
                img_prompt_a = (
                    f"{_preserve_rule}\n\n"
                    "Increase brightness and add airy, light atmosphere. Use cool-neutral white balance. "
                    "Reduce saturation slightly for a clean, fresh Japanese-style look. Soft even lighting."
                )
            elif _beautify_choice == "高级质感":
                img_prompt_a = (
                    f"{_preserve_rule}\n\n"
                    "Apply low-contrast, muted luxury toning. Use subtle shadow detail and refined highlights. "
                    "Create an editorial, premium feel. Slightly desaturate for sophisticated elegance."
                )
            elif _beautify_choice == "鲜艳活力":
                img_prompt_a = (
                    f"{_preserve_rule}\n\n"
                    "Boost color saturation and vibrancy. Increase contrast for a punchy, energetic look. "
                    "Enhance blue skies, green foliage, and vivid product colors. Dynamic, eye-catching lighting."
                )
            else:
                _custom_prompt = st.text_area(
                    "输入你的美化需求",
                    placeholder="例如：背景虚化一点，光线柔和一些，整体偏粉色调…",
                    key="custom_beautify_prompt",
                    height=80,
                )
                img_prompt_a = (
                    f"{_preserve_rule}\n\n"
                    f"User request: {_custom_prompt}"
                ) if _custom_prompt else ""

            with st.expander("查看美化指令", expanded=False):
                st.code(img_prompt_a or "请输入自定义需求", language=None)

            _can_beautify = bool(img_prompt_a)
            if st.button("🎨 一键美化原图", type="primary", key="btn_img", disabled=not _can_beautify):
                n = len(st.session_state.note_images)
                prog2 = st.progress(0, text="准备处理…")
                edited, errors = [], []
                for i, img in enumerate(st.session_state.note_images):
                    prog2.progress(i / n, text=f"正在处理第 {i+1}/{n} 张…")
                    result_img, err_msg = edit_image_with_gemini(img, img_prompt_a)
                    edited.append(result_img)
                    if err_msg:
                        errors.append(f"图片 {i+1}：{err_msg}")
                prog2.progress(1.0, text="处理完成！")
                st.session_state.edited_images = edited
                st.session_state.images_done = True
                log_event(st.session_state.invite_code, "edit_image",
                           st.session_state.industry_id, mode,
                           detail=json.dumps({"count": n, "type": "beautify"}))
                ok = sum(1 for x in edited if x)
                if ok == n:
                    st.success(f"全部 {n} 张美化成功！")
                elif ok:
                    st.warning(f"{ok}/{n} 张成功，{n-ok} 张失败")
                else:
                    st.error("美化全部失败，可用原图下载")
                if errors:
                    with st.expander("查看错误详情"):
                        for e in errors:
                            st.caption(e)
                st.rerun()

            if st.session_state.images_done:
                for i, (orig, ed) in enumerate(
                    zip(st.session_state.note_images, st.session_state.edited_images)
                ):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.image(orig, caption=f"原图 {i+1}", use_container_width=True)
                    with c2:
                        if ed:
                            st.image(ed, caption=f"美化后 {i+1}", use_container_width=True)
                            _ec1, _ec2 = st.columns([3, 1])
                            with _ec1:
                                _req = st.text_input("修改", key=f"edit_bt_{i}",
                                                     placeholder="不满意？描述修改要求…",
                                                     label_visibility="collapsed")
                            with _ec2:
                                _ebtn = st.button("✏️ 修改", key=f"edit_bt_btn_{i}",
                                                  use_container_width=True)
                            if _ebtn and _req:
                                with st.spinner(f"正在修改第 {i+1} 张…"):
                                    _new, _err = edit_image_with_gemini(ed, _req)
                                if _new:
                                    st.session_state.edited_images[i] = _new
                                    del st.session_state[f"edit_bt_{i}"]
                                    st.success("修改成功！")
                                    st.rerun()
                                else:
                                    st.error(f"修改失败：{_err}")
                        else:
                            st.warning(f"图片 {i+1} 处理失败")
                            st.caption("可跳过，下载时使用原图")

                if any(x is None for x in st.session_state.edited_images):
                    if st.button("🔄 重试失败的图片", key="btn_retry"):
                        prog3 = st.progress(0, text="重试中…")
                        for i, (img, ed) in enumerate(
                            zip(st.session_state.note_images, st.session_state.edited_images)
                        ):
                            if ed is None:
                                prog3.progress(i / len(st.session_state.note_images),
                                               text=f"重试第 {i+1} 张…")
                                new_img, _ = edit_image_with_gemini(img, img_prompt_a)
                                if new_img:
                                    st.session_state.edited_images[i] = new_img
                        prog3.progress(1.0, text="重试完成")
                        st.rerun()

            st.divider()

        # ── 方案B：AI 场景换装（基于用户上传的商品照片）──
        if st.session_state.note_images:
            st.markdown("**🖼️ 方案B：AI 场景换装** — 保持商品原样，更换场景风格")

            _scene_styles = {
                "实景摄影": {
                    "desc": "真实场景拍摄效果，自然光线、环境道具",
                    "prompt": (
                        "Transform the background into a realistic professional product photography scene. "
                        "Use natural lighting, real-world props and surfaces (marble, wood, fabric). "
                        "Create depth with bokeh background. Studio-quality commercial photography look."
                    ),
                },
                "油画风格": {
                    "desc": "经典油画笔触，艺术感强烈",
                    "prompt": (
                        "Transform the background and atmosphere into a classical oil painting style. "
                        "Apply visible brushstroke textures, rich warm color palette, dramatic chiaroscuro lighting. "
                        "Renaissance or Impressionist painting feel. The product remains photorealistic."
                    ),
                },
                "水彩插画": {
                    "desc": "清新水彩晕染，文艺柔美",
                    "prompt": (
                        "Transform the background into a delicate watercolor illustration style. "
                        "Soft color washes, gentle bleeding edges, hand-painted floral or nature elements. "
                        "Light pastel tones, dreamy and artistic. The product remains photorealistic."
                    ),
                },
                "赛博朋克": {
                    "desc": "霓虹灯光、未来科技感",
                    "prompt": (
                        "Transform the background into a cyberpunk neon-lit scene. "
                        "Vibrant neon pink, cyan, and purple lighting. Futuristic cityscape or tech environment. "
                        "Reflective wet surfaces, holographic elements. The product remains photorealistic."
                    ),
                },
                "自然户外": {
                    "desc": "山水花草、阳光沙滩等自然环境",
                    "prompt": (
                        "Place the product in a beautiful natural outdoor scene. "
                        "Lush greenery, golden sunlight, or serene beach/mountain landscape. "
                        "Natural elements like flowers, leaves, pebbles as props. Organic and refreshing atmosphere."
                    ),
                },
                "极简纯色": {
                    "desc": "纯色背景、干净利落，突出商品本身",
                    "prompt": (
                        "Place the product on a clean minimalist solid-color background. "
                        "Soft gradient or pure white/grey/pastel backdrop. Professional studio lighting. "
                        "No distractions, maximum focus on the product. Apple-style product photography."
                    ),
                },
                "节日氛围": {
                    "desc": "春节、圣诞、情人节等节日场景",
                    "prompt": (
                        "Place the product in a festive holiday celebration scene. "
                        "Warm fairy lights, gift boxes, ribbons, confetti, seasonal decorations. "
                        "Cozy and celebratory atmosphere. Rich warm colors."
                    ),
                },
                "中国风": {
                    "desc": "水墨山水、古典元素、国潮美学",
                    "prompt": (
                        "Place the product in a Chinese traditional aesthetic scene. "
                        "Ink wash painting mountains, classical architecture elements, red and gold accents. "
                        "Guochao (national trend) style with modern flair. Elegant and culturally rich."
                    ),
                },
                "自定义场景": {
                    "desc": "输入你想要的任何场景描述",
                    "prompt": "",
                },
            }

            _scene_choice = st.radio(
                "选择场景风格",
                list(_scene_styles.keys()),
                horizontal=True,
                key="scene_style_b",
                help="AI 会保持你的商品完全不变，只更换周围的场景和氛围",
            )
            st.caption(_scene_styles[_scene_choice]["desc"])

            _scene_preserve_rule = (
                "CRITICAL RULE: Do NOT change, alter, or replace the main product/subject in any way. "
                "Keep the EXACT same product shape, color, design, logo, packaging, and all visual details 100% intact. "
                "Only change the background, surrounding scene, lighting environment, and decorative elements. "
                "The product must remain photorealistic even if the background style changes. "
                "Remove any text overlays or watermarks."
            )

            if _scene_choice == "自定义场景":
                _custom_scene = st.text_area(
                    "描述你想要的场景",
                    placeholder="例如：放在樱花树下的木桌上，阳光透过花瓣洒下来…",
                    key="custom_scene_prompt_b",
                    height=80,
                )
                _scene_prompt_b = (
                    f"{_scene_preserve_rule}\n\n"
                    f"Scene description: {_custom_scene}"
                ) if _custom_scene else ""
            else:
                _scene_prompt_b = (
                    f"{_scene_preserve_rule}\n\n"
                    f"{_scene_styles[_scene_choice]['prompt']}"
                )

            with st.expander("查看场景指令", expanded=False):
                st.code(_scene_prompt_b or "请输入自定义场景描述", language=None)

            _can_scene = bool(_scene_prompt_b)
            if st.button("🎬 一键场景换装", type="primary", key="btn_scene_b", disabled=not _can_scene):
                n = len(st.session_state.note_images)
                prog_b = st.progress(0, text="准备场景换装…")
                scene_results, scene_errors = [], []
                for i, img in enumerate(st.session_state.note_images):
                    prog_b.progress(i / n, text=f"正在为第 {i+1}/{n} 张换装场景…")
                    result_img, err_msg = edit_image_with_gemini(img, _scene_prompt_b)
                    scene_results.append(result_img)
                    if err_msg:
                        scene_errors.append(f"图片 {i+1}：{err_msg}")
                prog_b.progress(1.0, text="场景换装完成！")
                st.session_state.scene_images = scene_results
                st.session_state.scene_prompt = _scene_prompt_b
                st.session_state["scene_tier"] = "scene_b"
                log_event(st.session_state.invite_code, "scene_change_b",
                           st.session_state.industry_id, mode,
                           detail=json.dumps({"count": n, "style": _scene_choice}))
                ok = sum(1 for x in scene_results if x)
                if ok == n:
                    st.success(f"全部 {n} 张场景换装成功！")
                elif ok:
                    st.warning(f"{ok}/{n} 张成功，{n-ok} 张失败")
                else:
                    st.error("场景换装全部失败，请重试")
                if scene_errors:
                    with st.expander("查看错误详情"):
                        for e in scene_errors:
                            st.caption(e)
                st.rerun()

            if st.session_state.scene_images and st.session_state.get("scene_tier") == "scene_b":
                for i, (orig, sc) in enumerate(
                    zip(st.session_state.note_images, st.session_state.scene_images)
                ):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.image(orig, caption=f"原图 {i+1}", use_container_width=True)
                    with c2:
                        if sc:
                            st.image(sc, caption=f"场景换装 {i+1}", use_container_width=True)
                            _ec1, _ec2 = st.columns([3, 1])
                            with _ec1:
                                _req = st.text_input("修改", key=f"edit_sc_{i}",
                                                     placeholder="不满意？描述修改要求…",
                                                     label_visibility="collapsed")
                            with _ec2:
                                _ebtn = st.button("✏️ 修改", key=f"edit_sc_btn_{i}",
                                                  use_container_width=True)
                            if _ebtn and _req:
                                with st.spinner(f"正在修改第 {i+1} 张…"):
                                    _new, _err = edit_image_with_gemini(sc, _req)
                                if _new:
                                    st.session_state.scene_images[i] = _new
                                    del st.session_state[f"edit_sc_{i}"]
                                    st.success("修改成功！")
                                    st.rerun()
                                else:
                                    st.error(f"修改失败：{_err}")
                        else:
                            st.warning(f"图片 {i+1} 换装失败")
                st.caption("✏️ 修改图片不消耗额度")

                with st.expander("查看场景描述提示词", expanded=False):
                    st.info(st.session_state.scene_prompt)
        else:
            st.info("**🖼️ 方案B：AI 场景换装** — 请先在上方上传商品照片，即可使用场景换装功能")


# ═══════════════════════════════════════════════════════
#  Step 4：打包下载
# ═══════════════════════════════════════════════════════
if st.session_state.rewrite_done:
    st.divider()
    st.markdown(
        "<div style='font-size:18px;font-weight:600;color:#1d1d1f;'>打包下载</div>"
        "<div style='font-size:12px;color:#86868b;'>Download</div>",
        unsafe_allow_html=True,
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    _batch = st.session_state.batch_results
    _is_batch_mode = mode == "rewrite" and len(_batch) > 1

    if _is_batch_mode:
        # ─── 批量下载 ───
        c1, c2 = st.columns(2)
        with c1:
            # 全部文案合并为一个 TXT
            _all_texts = []
            for i, br in enumerate(_batch):
                _all_texts.append(f"{'=' * 40}\n第 {i+1} 条 — {br.get('title', '无标题')}\n{'=' * 40}\n\n{br.get('rewrite') or br.get('text', '')}")
            _txt_header = (
                f"行业: {industry['label']}\n"
                f"城市: {st.session_state.city or '未指定'}\n"
                f"时间: {ts}\n"
                f"共 {len(_batch)} 条笔记\n"
                f"{'=' * 40}\n\n"
            )
            st.download_button(
                f"📝 下载全部文案（{len(_batch)} 条 TXT）",
                data=(_txt_header + "\n\n".join(_all_texts)).encode("utf-8"),
                file_name=f"批量文案_{ts}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with c2:
            # 全部内容打包 ZIP（含子目录）
            _has_edited = st.session_state.images_done and any(br.get("edited_images") for br in _batch)
            zip_batch = make_batch_zip(_batch, use_edited=_has_edited)
            _zip_label = "📦 批量下载全部（文案+处理图 ZIP）" if _has_edited else "📦 批量下载全部（文案+原图 ZIP）"
            st.download_button(
                _zip_label,
                data=zip_batch,
                file_name=f"批量内容_{ts}.zip",
                mime="application/zip",
                use_container_width=True,
            )
    else:
        # ─── 单条下载（原逻辑）───
        c1, c2, c3 = st.columns(3)

        _txt_header = (
            f"行业: {industry['label']}\n"
            f"城市: {st.session_state.city or '未指定'}\n"
            f"时间: {ts}\n"
            f"{'=' * 30}\n\n"
        )
        with c1:
            st.download_button(
                "📝 下载文案（TXT）",
                data=(_txt_header + st.session_state.rewrite_result).encode("utf-8"),
                file_name=f"文案_{ts}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with c2:
            if st.session_state.images_done:
                good_imgs = [x for x in st.session_state.edited_images if x]
                if good_imgs:
                    zip_data = make_zip(
                        st.session_state.rewrite_result[:60],
                        st.session_state.rewrite_result,
                        good_imgs,
                    )
                    st.download_button(
                        "📦 文案+处理图（ZIP）",
                        data=zip_data,
                        file_name=f"小红书内容_{ts}.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )

        with c3:
            if st.session_state.note_images:
                zip_orig = make_zip(
                    st.session_state.rewrite_result[:60],
                    st.session_state.rewrite_result,
                    st.session_state.note_images,
                )
                st.download_button(
                    "📦 文案+原图（ZIP）",
                    data=zip_orig,
                    file_name=f"文案加原图_{ts}.zip",
                    mime="application/zip",
                    use_container_width=True,
                )

    # Mode B：AI生成配图额外下载行
    if mode == "create" and st.session_state.scene_images:
        ca, _, _ = st.columns(3)
        with ca:
            zip_scene = make_zip(
                st.session_state.rewrite_result[:60],
                st.session_state.rewrite_result,
                st.session_state.scene_images,
            )
            tier_label = "精品版" if st.session_state.get("scene_tier") == "pro" else "体验版"
            st.download_button(
                f"🖼️ 文案+AI配图·{tier_label}（ZIP）",
                data=zip_scene,
                file_name=f"AI配图_{tier_label}_{ts}.zip",
                mime="application/zip",
                use_container_width=True,
            )

    # ═══════════════════════════════════════════════════════
    #  Step 5：一键准备发布
    # ═══════════════════════════════════════════════════════
    st.divider()
    st.markdown(
        "<div style='font-size:18px;font-weight:600;color:#1d1d1f;'>一键准备发布</div>"
        "<div style='font-size:12px;color:#86868b;'>Quick Publish Prep</div>",
        unsafe_allow_html=True,
    )

    def _split_title_body(text: str) -> tuple:
        """从文案中拆分标题（第一行）和正文（其余部分）"""
        lines = text.strip().split("\n")
        title = ""
        body_start = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped:
                title = re.sub(r'^#+\s*', '', stripped)
                body_start = i + 1
                break
        body = "\n".join(lines[body_start:]).strip()
        return title, body

    def _render_publish_block(full_text: str, block_key: str = ""):
        """渲染单条笔记的发布准备区：可编辑标题/正文 + 复制按钮"""
        pub_title, pub_body = _split_title_body(full_text)
        _bk = block_key or "main"

        # ── 可编辑标题 ──
        st.markdown("**📌 标题**（可直接编辑修改）")
        st.text_input(
            "标题", value=pub_title, key=f"pub_title_{_bk}",
            label_visibility="collapsed",
        )
        st.markdown(
            f'<button onclick="'
            f"var t=document.getElementById('pub_title_{_bk}');"
            f"if(!t)t=this.closest('.stVerticalBlock').querySelector('input');"
            f"var v=t?t.value:'{pub_title.replace(chr(39), '')}';"
            f"navigator.clipboard.writeText(v).then(()=>this.textContent='✅ 已复制标题')"
            f'"'
            f' style="width:100%;padding:10px;font-size:16px;font-weight:bold;border-radius:8px;'
            f'border:2px solid #ff2442;color:#fff;background:#ff2442;cursor:pointer;'
            f'margin-bottom:16px"'
            f'>📋 复制标题</button>',
            unsafe_allow_html=True,
        )

        # ── 可编辑正文 ──
        st.markdown("**📝 正文**（可直接编辑修改）")
        st.text_area(
            "正文", value=pub_body, key=f"pub_body_{_bk}",
            height=300, label_visibility="collapsed",
        )
        st.markdown(
            f'<button onclick="'
            f"var t=this.closest('.stVerticalBlock').querySelector('textarea');"
            f"var v=t?t.value:'';"
            f"navigator.clipboard.writeText(v).then(()=>this.textContent='✅ 已复制正文')"
            f'"'
            f' style="width:100%;padding:10px;font-size:16px;font-weight:bold;border-radius:8px;'
            f'border:2px solid #ff2442;color:#fff;background:#ff2442;cursor:pointer;'
            f'margin-bottom:8px"'
            f'>📋 复制正文</button>',
            unsafe_allow_html=True,
        )

    if _is_batch_mode:
        # 批量模式：每条笔记一个 tab
        _pub_tab_names = [f"笔记 {i+1}" for i in range(len(_batch))]
        _pub_tabs = st.tabs(_pub_tab_names)
        for i, (tab, br) in enumerate(zip(_pub_tabs, _batch)):
            with tab:
                _text = br.get("rewrite") or br.get("text", "")
                if _text:
                    _render_publish_block(_text, block_key=f"pub_{i}")
                else:
                    st.caption("该条无文案内容")
    else:
        # 单条模式
        _render_publish_block(st.session_state.rewrite_result)

    st.info(
        "**发布步骤：**\n"
        "1. 复制标题和正文（点上方红色按钮）\n"
        "2. 长按保存图片到手机相册（或电脑下载ZIP）\n"
        "3. 打开**小红书APP** → 点底部「+」发布\n"
        "4. 选择图片 → 粘贴标题和正文 → 发布\n\n"
        "💡 建议用小红书APP发布，网页版在手机上体验不佳",
        icon="📱",
    )
    with st.expander("电脑端发布（网页版）"):
        st.link_button(
            "🔗 打开小红书创作中心",
            url="https://creator.xiaohongshu.com/publish/publish",
            use_container_width=True,
        )
        st.caption("网页版适合电脑端使用，可直接拖入图片发布")
    st.caption(
        "⚠️ 温馨提示：本工具生成的内容为AI辅助创作参考，建议融入个人风格后发布。"
        "根据相关法规，AI生成内容可能需要标识，详见侧边栏「用户须知」。"
    )


# ═══════════════════════════════════════════════════════
#  反馈区
# ═══════════════════════════════════════════════════════
if st.session_state.rewrite_done and not st.session_state.feedback_submitted:
    st.divider()
    st.markdown(
        "<div style='font-size:18px;font-weight:600;color:#1d1d1f;'>使用反馈 "
        "<span style='font-size:12px;color:#86868b;font-weight:400;'>Feedback</span></div>",
        unsafe_allow_html=True,
    )
    st.caption("你的反馈直接影响产品下一版迭代方向")

    with st.form("feedback_form"):
        rating = st.select_slider(
            "整体体验评分",
            options=["😣 很差", "😕 一般", "😐 还行", "😊 不错", "🤩 很棒"],
            value="😊 不错",
        )
        feedback_text = st.text_area(
            "具体反馈（可选）",
            placeholder="哪个功能最有用？哪里用起来最麻烦？最希望增加什么功能？",
            height=100,
        )
        submitted = st.form_submit_button("提交反馈", type="primary")
        if submitted:
            conn = None
            try:
                conn = get_db()
                rating_text = rating.split(" ", 1)[-1] if " " in rating else rating
                conn.execute(
                    "INSERT INTO feedback (invite_code, rating, feedback_text, industry_id, mode) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (st.session_state.invite_code, rating_text, feedback_text,
                     st.session_state.get("industry_id", ""), st.session_state.get("selected_mode", "")),
                )
                conn.commit()
            except Exception:
                pass
            finally:
                if conn:
                    conn.close()
            log_event(st.session_state.invite_code, "feedback",
                       st.session_state.get("industry_id", ""), st.session_state.get("selected_mode", ""))
            st.session_state.feedback_submitted = True
            st.rerun()

elif st.session_state.feedback_submitted:
    st.divider()
    st.success("感谢反馈！David 会认真查看每一条，下一版见 👋")

# (旧管理面板已迁移至 render_admin_panel() 独立视图)
# ─── 页脚 ───
st.divider()
st.caption("📱 小红书内容 Agent · Demo v5.0 · 12大行业全双模式 · 免费+Pro双档AI配图")
