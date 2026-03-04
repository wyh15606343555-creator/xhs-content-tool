"""
小红书通用内容 Agent — Demo v5.0
邀请码测试版 | 12大行业全部支持双模式 | 免费+Pro双档AI配图
"""

import streamlit as st
import re
import json
import pandas as pd
from datetime import datetime, timedelta
from PIL import Image

from config import (
    INDUSTRIES, INDUSTRY_ICONS, ICON_ATTRS, DEFAULTS,
    PRO_GEN_LIMIT, ADMIN_CODES,
)
from utils import (
    init_db, log_event, save_generation, get_history, get_db,
    friendly_api_error, img_cols,
    get_pro_used, has_pro_quota, try_use_pro_quota, refund_pro_quota,
    check_invite_code, make_zip, make_batch_zip,
)
from api import (
    try_extract_xhs, download_image_url,
    rewrite_with_deepseek, generate_original_content,
    generate_dynamic_image_prompt,
    generate_scene_nano_banana, generate_scene_with_imagen4,
    edit_image_with_gemini,
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
    color: #1D1D1F !important;
    font-weight: 700 !important;
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

/* ── Step Number Badge ── */
.step-num {
    display: inline-block;
    background: linear-gradient(135deg, #FF2442, #FF6B81);
    color: #FFFFFF !important;
    border-radius: 50%;
    width: 26px; height: 26px;
    text-align: center; line-height: 26px;
    font-size: 0.85rem; font-weight: 900;
    margin-right: 8px;
    vertical-align: middle;
}

/* ── Buttons ── */
.stButton > button {
    background-color: #FFFFFF !important;
    color: #1D1D1F !important;
    border: 1px solid #E5E5EA !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    transition: all 0.2s ease;
}
.stButton > button:hover {
    border-color: #FF2442 !important;
    color: #FF2442 !important;
    background-color: #FFF1F3 !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #FF2442, #FF6B81) !important;
    color: #FFFFFF !important;
    border: none !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 8px rgba(255,36,66,0.25);
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #FF6B81, #FF8FA0) !important;
    color: #FFFFFF !important;
}
.stButton > button:disabled {
    background-color: #F5F5F7 !important;
    color: #AEAEB2 !important;
    border-color: #E5E5EA !important;
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
    background-color: #FFFFFF !important;
    color: #1D1D1F !important;
    border: 1px solid #E5E5EA !important;
    border-radius: 10px !important;
    caret-color: #FF2442;
}
.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: #FF2442 !important;
    box-shadow: 0 0 0 3px rgba(255,36,66,0.1) !important;
    outline: none !important;
}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #AEAEB2 !important;
}
.stTextInput label,
.stTextArea label {
    color: #86868B !important;
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
    background-color: #F2F2F7 !important;
    border-radius: 4px !important;
}
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #FF2442, #FF6B81) !important;
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

/* ── Gate Box (邀请码页) ── */
.gate-box {
    text-align: center;
    padding: 4rem 1rem 2.5rem;
}
.gate-logo {
    width: 56px; height: 56px;
    border-radius: 14px;
    background: linear-gradient(135deg, #FF2442, #FF6B81);
    display: inline-flex;
    align-items: center; justify-content: center;
    margin-bottom: 1.2rem;
}
.gate-title {
    font-size: 2.8rem;
    font-weight: 900;
    margin-bottom: 0.5rem;
    color: #1D1D1F;
    letter-spacing: -0.04em;
    line-height: 1.1;
}
.gate-accent {
    color: #FF2442;
}
.gate-sub {
    color: #86868B;
    font-size: 0.85rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 0.5rem;
}

/* ── Spinner ── */
[data-testid="stSpinner"] > div {
    border-top-color: #FF2442 !important;
}

/* ── Industry Cards 3D hover ── */
.ind-card {
    border-radius: 16px;
    padding: 20px 12px;
    text-align: center;
    min-height: 124px;
    overflow: hidden;
    box-sizing: border-box;
    transition: transform 0.3s cubic-bezier(.34,1.56,.64,1),
                box-shadow 0.3s ease,
                border-color 0.3s ease;
    cursor: default;
    perspective: 800px;
}
.ind-card:hover {
    transform: translateY(-6px) scale(1.03);
    box-shadow: 0 12px 28px rgba(0,0,0,0.10), 0 2px 6px rgba(0,0,0,0.04);
}
.ind-card.ind-sel {
    border: 2px solid #FF2442;
    background: #FFF1F3;
    box-shadow: 0 0 0 3px rgba(255,36,66,0.12), 0 4px 14px rgba(255,36,66,0.18);
}
.ind-card.ind-sel:hover {
    transform: translateY(-6px) scale(1.03);
    box-shadow: 0 0 0 3px rgba(255,36,66,0.18), 0 14px 32px rgba(255,36,66,0.22);
}
.ind-card:not(.ind-sel) {
    border: 1px solid #E5E5EA;
    background: #FFFFFF;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.ind-icon {
    width: 46px; height: 46px; border-radius: 13px;
    display: inline-flex; align-items: center; justify-content: center;
    margin-bottom: 10px;
    transition: transform 0.3s ease;
}
.ind-card:hover .ind-icon {
    transform: rotateY(12deg) scale(1.08);
}
.ind-name {
    font-weight: 650; font-size: 0.9rem;
    overflow-wrap: break-word;
    transition: color 0.2s ease;
}
.ind-desc {
    font-size: 0.72rem; color: #86868B; margin-top: 5px;
    overflow-wrap: break-word;
}

/* ── Image captions ── */
[data-testid="stImage"] p { color: #86868B !important; font-size: 0.75rem !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #F5F5F7; }
::-webkit-scrollbar-thumb { background: #D1D1D6; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #AEAEB2; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  Session State 初始化
# ═══════════════════════════════════════════════════════
for _k, _v in DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ═══════════════════════════════════════════════════════
#  页面1：邀请码门禁
# ═══════════════════════════════════════════════════════
if not st.session_state.authed:
    st.markdown("""
    <div class="gate-box">
        <div class="gate-logo">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 013 3L7 19l-4 1 1-4z"/>
            </svg>
        </div>
        <div class="gate-title"><span class="gate-accent">小红书</span>内容 Agent</div>
        <div class="gate-sub">内测版本 · 请输入邀请码进入</div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("### 输入邀请码")
        code_input = st.text_input(
            "邀请码",
            placeholder="如：TEST01",
            label_visibility="collapsed",
            max_chars=20,
        )
        if st.button("进入 →", type="primary", use_container_width=True):
            if check_invite_code(code_input):
                st.session_state.authed = True
                st.session_state.invite_code = code_input.strip().upper()
                log_event(code_input.strip().upper(), "login")
                st.rerun()
            else:
                st.error("邀请码无效，请联系 David 获取")

        st.caption("没有邀请码？联系 David 申请测试资格")
    st.stop()


# ═══════════════════════════════════════════════════════
#  侧边栏
# ═══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"**欢迎测试！** `{st.session_state.invite_code}`")
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

    # Pro 配额显示
    _code = st.session_state.invite_code
    _pro_used = get_pro_used(_code)
    _pro_left = PRO_GEN_LIMIT - _pro_used
    st.markdown("**⭐ Pro 精品配图额度**")
    if _pro_left > 10:
        st.success(f"剩余 **{_pro_left}** / {PRO_GEN_LIMIT} 次")
    elif _pro_left > 0:
        st.warning(f"剩余 **{_pro_left}** / {PRO_GEN_LIMIT} 次（快用完了）")
    else:
        st.error("Pro 额度已用完")
        st.caption("联系 David 获取新额度")

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

    st.divider()
    st.caption("Demo v5.0 · 内测版\n\n遇到问题请截图反馈给 David 15606343555")

    if st.button("退出登录", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ═══════════════════════════════════════════════════════
#  页面2：行业选择（12个，3行×4列）
# ═══════════════════════════════════════════════════════
st.markdown(
    "<div style='display:flex; align-items:center; gap:12px; margin-bottom:4px;'>"
    "<div style='width:40px; height:40px; border-radius:10px; "
    "background:linear-gradient(135deg,#FF2442,#FF6B81); "
    "display:flex; align-items:center; justify-content:center; flex-shrink:0;'>"
    "<svg width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='#fff' "
    "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
    "<path d='M12 20h9'/><path d='M16.5 3.5a2.12 2.12 0 013 3L7 19l-4 1 1-4z'/>"
    "</svg></div>"
    "<div style='font-size:1.6rem; font-weight:800; letter-spacing:-0.03em; color:#1D1D1F;'>"
    "<span style='color:#FF2442;'>小红书</span>内容 Agent"
    "</div></div>",
    unsafe_allow_html=True,
)
st.caption("选择行业 → 选择工作方式 → AI 生成专业笔记 → 图片处理 → 一键下载")
st.divider()

st.markdown("### 第一步：选择你的行业")

industry_keys = list(INDUSTRIES.keys())
rows = [industry_keys[i:i+4] for i in range(0, len(industry_keys), 4)]

for row_keys in rows:
    cols = st.columns(4)
    for col, ikey in zip(cols, row_keys):
        info = INDUSTRIES[ikey]
        selected = st.session_state.industry_id == ikey
        check = " ✓" if selected else ""
        name_color = "#FF2442" if selected else "#1D1D1F"
        icon_bg = "linear-gradient(135deg,#FF2442,#FF6B81)" if selected else "#F5F5F7"
        icon_color = "#FFFFFF" if selected else "#86868B"
        sel_cls = "ind-sel" if selected else ""
        svg_icon = INDUSTRY_ICONS.get(ikey, "")
        svg_icon_colored = svg_icon.replace('stroke="currentColor"', f'stroke="{icon_color}"')
        with col:
            st.markdown(
                f"""
                <div class="ind-card {sel_cls}">
                    <div class="ind-icon" style="background:{icon_bg};">
                        {svg_icon_colored}
                    </div>
                    <div class="ind-name" style="color:{name_color};">
                        {info['label']}{check}
                    </div>
                    <div class="ind-desc">{info['desc']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("选择", key=f"sel_{ikey}", use_container_width=True,
                         type="primary" if selected else "secondary"):
                st.session_state.industry_id = ikey
                st.session_state.selected_mode = None   # 重置模式选择
                st.session_state.content_ready = False
                st.session_state.rewrite_done = False
                st.session_state.images_done = False
                st.session_state.rewrite_result = ""
                st.session_state.edited_images = []
                st.session_state.note_title = ""
                st.session_state.note_text = ""
                st.session_state.note_images = []
                st.session_state.store_profile = {}
                st.session_state.daily_brief = ""
                st.session_state.create_images = []
                st.session_state.dynamic_image_prompt = ""
                st.session_state.scene_images = []
                st.session_state.scene_prompt = ""
                st.session_state.feedback_submitted = False
                st.session_state["scene_tier"] = ""
                st.rerun()

if not st.session_state.industry_id:
    st.info("👆 请先选择行业，再开始处理内容")
    st.stop()

industry = INDUSTRIES[st.session_state.industry_id]


# ═══════════════════════════════════════════════════════
#  页面3：工作方式选择（竞品参考 vs 原创生成）
# ═══════════════════════════════════════════════════════
if not st.session_state.selected_mode:
    st.divider()
    st.markdown("### 第二步：选择工作方式")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(
            """
            <div style="border:1px solid #FF2442; border-radius:14px; padding:20px 16px;
                        min-height:210px; background:#FFF1F3;
                        box-shadow:0 1px 3px rgba(0,0,0,0.06);">
            <div style="width:36px; height:36px; border-radius:8px;
                        background:linear-gradient(135deg,#FF2442,#FF6B81);
                        display:inline-flex; align-items:center; justify-content:center;
                        margin:0 auto 8px; display:flex;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"/>
                </svg>
            </div>
            <div style="font-weight:800; text-align:center; font-size:1rem; margin:8px 0;
                        color:#FF2442; letter-spacing:0.02em;">
                竞品参考模式
            </div>
            <ul style="font-size:0.83rem; color:#6E6E73; padding-left:18px; margin:0 0 12px 0; line-height:1.8;">
                <li>粘贴竞品小红书笔记链接</li>
                <li>AI 拆解爆文结构</li>
                <li>自动改写成你的风格</li>
                <li>图片去水印 / 去文字</li>
            </ul>
            <div style="font-size:0.75rem; color:#86868B;">
                适合：参考同行爆文、快速出内容
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='background:#FFF1F3; border:1px solid #E5E5EA; border-radius:8px; "
            "padding:6px 10px; font-size:0.78rem; color:#FF2442; margin-top:4px;'>"
            "文案改写：免费 &nbsp;·&nbsp; 图片去水印：免费</div>",
            unsafe_allow_html=True,
        )
        if st.button("选择竞品参考模式 →", key="mode_sel_a", type="primary", use_container_width=True):
            st.session_state.selected_mode = "rewrite"
            st.rerun()

    with col_b:
        st.markdown(
            """
            <div style="border:1px solid #FF8C00; border-radius:14px; padding:20px 16px;
                        min-height:210px; background:#FFF8F0;
                        box-shadow:0 1px 3px rgba(0,0,0,0.06);">
            <div style="width:36px; height:36px; border-radius:8px;
                        background:linear-gradient(135deg,#FF8C00,#FFAB40);
                        display:inline-flex; align-items:center; justify-content:center;
                        margin:0 auto 8px; display:flex;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 3l1.912 5.813a2 2 0 001.275 1.275L21 12l-5.813 1.912a2 2 0 00-1.275 1.275L12 21l-1.912-5.813a2 2 0 00-1.275-1.275L3 12l5.813-1.912a2 2 0 001.275-1.275L12 3z"/>
                </svg>
            </div>
            <div style="font-weight:800; text-align:center; font-size:1rem; margin:8px 0;
                        color:#FF8C00; letter-spacing:0.02em;">
                原创生成模式
            </div>
            <ul style="font-size:0.83rem; color:#6E6E73; padding-left:18px; margin:0 0 12px 0; line-height:1.8;">
                <li>填写你的店铺 / 业务信息</li>
                <li>AI 根据今日主题创作文案</li>
                <li>美化真实照片（免费）</li>
                <li>AI 生成配图（免费版 / Pro精品版）</li>
            </ul>
            <div style="font-size:0.75rem; color:#86868B;">
                适合：发原创内容、建立品牌形象
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='background:#FFF8F0; border:1px solid #E5E5EA; border-radius:8px; "
            "padding:6px 10px; font-size:0.78rem; color:#FF8C00; margin-top:4px;'>"
            "文案创作：免费 &nbsp;·&nbsp; 免费AI配图 &nbsp;·&nbsp; Pro精品配图（50次/账号）</div>",
            unsafe_allow_html=True,
        )
        if st.button("选择原创生成模式 →", key="mode_sel_b", use_container_width=True):
            st.session_state.selected_mode = "create"
            st.rerun()

    st.stop()


# 已选择模式后的状态栏
mode = st.session_state.selected_mode
mode_label = "竞品参考模式" if mode == "rewrite" else "原创生成模式"
_mode_icon_color = "#FF2442" if mode == "rewrite" else "#FF8C00"

col_status, col_switch = st.columns([4, 1])
_city_label = st.session_state.city or "通用"
with col_status:
    st.markdown(
        f"<div style='background:#FFF1F3; border:1px solid #FFD6DB; border-radius:10px; "
        f"padding:10px 14px; font-size:0.88rem; color:#6E6E73;'>"
        f"<strong style='color:#FF2442;'>✓</strong>&ensp;"
        f"<strong style='color:#1D1D1F;'>{industry['label']}</strong>"
        f"&ensp;·&ensp;<span style='color:{_mode_icon_color};'>{mode_label}</span>"
        f"&ensp;·&ensp;<span style='color:#86868B;'>{_city_label}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
with col_switch:
    if st.button("切换模式", use_container_width=True):
        st.session_state.selected_mode = None
        st.session_state.content_ready = False
        st.session_state.rewrite_done = False
        st.session_state.images_done = False
        st.session_state.rewrite_result = ""
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


# ═══════════════════════════════════════════════════════
#  Step 1：输入内容（根据模式分流）
# ═══════════════════════════════════════════════════════

# ─── Mode A：粘贴竞品链接（支持批量）───
if mode == "rewrite":
    st.markdown('<span class="step-num">1</span> **粘贴竞品小红书笔记链接**', unsafe_allow_html=True)
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
            type=["jpg", "jpeg", "png", "webp"],
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
                        except Exception:
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
                type=["jpg", "jpeg", "png", "webp"],
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
                            except Exception:
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
                type=["jpg", "jpeg", "png", "webp"],
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
    st.markdown('<span class="step-num">1</span> **填写店铺信息 + 今日主题**', unsafe_allow_html=True)
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
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="create_img_upload",
    )
    if uploaded_imgs:
        imgs = []
        for f in uploaded_imgs:
            try:
                imgs.append(Image.open(f).convert("RGB"))
            except Exception:
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


# ═══════════════════════════════════════════════════════
#  Step 2：AI 文案处理
# ═══════════════════════════════════════════════════════
if st.session_state.content_ready:
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
        f'<span class="step-num">2</span> **{label_2}**',
        unsafe_allow_html=True,
    )
    st.caption("🆓 免费功能 · 由 DeepSeek 驱动")

    if st.button(btn_label, type="primary", key="btn_rewrite"):
        if mode == "rewrite" and not _is_batch_mode and not st.session_state.note_title and not st.session_state.note_text:
            st.error("标题和正文都为空，请先补充内容")
        elif mode == "create" and not st.session_state.daily_brief.strip():
            st.error("请填写今日主题")
        else:
            with st.status("AI 正在创作…", expanded=True) as _gen_status:
                try:
                    if mode == "rewrite" and _is_batch_mode:
                        # --- 批量改写 ---
                        for bi, br in enumerate(_batch):
                            _gen_status.update(label=f"正在改写第 {bi+1}/{len(_batch)} 条…")
                            result = rewrite_with_deepseek(
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
                                   detail=json.dumps({"batch_count": len(_batch)}))
                        # 兼容：第一条同步到旧变量
                        st.session_state.rewrite_result = _batch[0]["rewrite"]
                    elif mode == "rewrite":
                        _gen_status.update(label="DeepSeek 正在改写文案…")
                        result = rewrite_with_deepseek(
                            st.session_state.note_title,
                            st.session_state.note_text,
                            industry,
                            st.session_state.city,
                        )
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
                                   st.session_state.industry_id, mode)
                    else:
                        _gen_status.update(label="DeepSeek 正在创作文案…")
                        result = generate_original_content(
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
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**原文**")
                st.info(f"**{st.session_state.note_title}**\n\n{st.session_state.note_text}")
            with c2:
                st.markdown("**改写后** （右上角可复制）")
                st.code(st.session_state.rewrite_result, language=None)
        else:
            st.markdown("**生成结果** （右上角可复制）")
            st.code(st.session_state.rewrite_result, language=None)


# ═══════════════════════════════════════════════════════
#  Step 3：图片处理
#  Mode A：去水印（Gemini 编辑，免费）
#  Mode B：方案A 美化原图（Gemini，免费）+ 方案B AI配图（免费版 / Pro精品版）
# ═══════════════════════════════════════════════════════
_has_any_images = st.session_state.note_images or any(br.get("images") for br in st.session_state.batch_results)
if st.session_state.rewrite_done and (_has_any_images or mode == "create"):
    st.divider()
    st.markdown('<span class="step-num">3</span> **图片处理**', unsafe_allow_html=True)

    _batch = st.session_state.batch_results
    _is_batch_mode = mode == "rewrite" and len(_batch) > 1

    # ─── Mode A：竞品参考 → 去水印/去文字（免费）───
    if mode == "rewrite":
        st.caption("🆓 免费功能 · 去除竞品水印和文字，图片内容保持不变")
        img_prompt_r = industry["image_prompt"]

        with st.expander("查看图片处理提示词", expanded=False):
            st.code(img_prompt_r, language=None)

        # 计算总图片数
        if _is_batch_mode:
            _total_imgs = sum(len(br.get("images", [])) for br in _batch)
            _btn_img_label = f"🎨 一键处理全部图片（{_total_imgs} 张）"
        else:
            _total_imgs = len(st.session_state.note_images)
            _btn_img_label = "🎨 一键重绘图片"

        if _total_imgs > 0 and st.button(_btn_img_label, type="primary", key="btn_img"):
            if _is_batch_mode:
                # --- 批量图片处理 ---
                prog2 = st.progress(0, text="准备处理…")
                _done_count = 0
                _all_errors = []
                for bi, br in enumerate(_batch):
                    imgs = br.get("images", [])
                    if not imgs:
                        br["edited_images"] = []
                        continue
                    edited = []
                    for i, img in enumerate(imgs):
                        _done_count += 1
                        prog2.progress(_done_count / _total_imgs,
                                       text=f"笔记 {bi+1} · 第 {i+1}/{len(imgs)} 张（共 {_done_count}/{_total_imgs}）")
                        result_img, err_msg = edit_image_with_gemini(img, img_prompt_r)
                        edited.append(result_img)
                        if err_msg:
                            _all_errors.append(f"笔记{bi+1}-图片{i+1}：{err_msg}")
                    br["edited_images"] = edited
                prog2.progress(1.0, text="全部处理完成！")
                # 兼容旧变量
                if _batch:
                    st.session_state.edited_images = _batch[0].get("edited_images", [])
                st.session_state.images_done = True
                _ok = sum(1 for br in _batch for x in br.get("edited_images", []) if x)
                log_event(st.session_state.invite_code, "edit_image",
                           st.session_state.industry_id, mode,
                           detail=json.dumps({"count": _total_imgs, "ok": _ok, "type": "watermark_batch"}))
                if _ok == _total_imgs:
                    st.success(f"全部 {_total_imgs} 张处理成功！")
                elif _ok:
                    st.warning(f"{_ok}/{_total_imgs} 张成功")
                else:
                    st.error("图片处理全部失败，可跳过直接用原图下载")
                if _all_errors:
                    with st.expander("查看错误详情"):
                        for e in _all_errors:
                            st.caption(e)
                st.rerun()
            else:
                # --- 单条图片处理（原逻辑）---
                n = len(st.session_state.note_images)
                prog2 = st.progress(0, text="准备处理…")
                edited, errors = [], []
                for i, img in enumerate(st.session_state.note_images):
                    prog2.progress(i / n, text=f"正在处理第 {i+1}/{n} 张…")
                    result_img, err_msg = edit_image_with_gemini(img, img_prompt_r)
                    edited.append(result_img)
                    if err_msg:
                        errors.append(f"图片 {i+1}：{err_msg}")
                prog2.progress(1.0, text="处理完成！")
                st.session_state.edited_images = edited
                if _batch:
                    _batch[0]["edited_images"] = edited
                st.session_state.images_done = True
                log_event(st.session_state.invite_code, "edit_image",
                           st.session_state.industry_id, mode,
                           detail=json.dumps({"count": n, "type": "watermark"}))
                ok = sum(1 for x in edited if x)
                if ok == n:
                    st.success(f"全部 {n} 张处理成功！")
                elif ok:
                    st.warning(f"{ok}/{n} 张成功，{n-ok} 张失败")
                else:
                    st.error("图片处理全部失败，可跳过直接用原图下载")
                if errors:
                    with st.expander("查看错误详情"):
                        for e in errors:
                            st.caption(e)
                st.rerun()

        if st.session_state.images_done:
            if _is_batch_mode:
                # 批量模式：tabs 展示
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
                                if ed:
                                    st.image(ed, caption=f"重绘后 {i+1}", use_container_width=True)
                                else:
                                    st.warning(f"图片 {i+1} 处理失败")
            else:
                for i, (orig, ed) in enumerate(
                    zip(st.session_state.note_images, st.session_state.edited_images)
                ):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.image(orig, caption=f"原图 {i+1}", use_container_width=True)
                    with c2:
                        if ed:
                            st.image(ed, caption=f"重绘后 {i+1}", use_container_width=True)
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
                                new_img, _ = edit_image_with_gemini(img, img_prompt_r)
                                if new_img:
                                    st.session_state.edited_images[i] = new_img
                        prog3.progress(1.0, text="重试完成")
                        st.rerun()

    # ─── Mode B：原创模式 → 方案A 美化 + 方案B AI配图（免费/Pro）───
    else:
        st.caption("两种方案可单独使用，也可都做——最终选最好看的发布")

        # ── 方案A：美化原图（仅当用户已上传图片时显示）──
        if st.session_state.note_images:
            st.markdown("**📸 方案A：美化原图** — 🆓 免费 · AI 根据文案氛围调整光线 / 色调 / 质感")
            img_prompt_a = (
                st.session_state.dynamic_image_prompt
                if st.session_state.dynamic_image_prompt
                else industry["image_prompt"]
            )
            with st.expander("查看专属美化指令", expanded=False):
                if st.session_state.dynamic_image_prompt:
                    st.info(st.session_state.dynamic_image_prompt)
                    st.caption("DeepSeek 根据你的文案情绪自动生成的 Gemini 图片处理指令")
                else:
                    st.code(img_prompt_a, language=None)

            if st.button("🎨 一键美化原图", type="primary", key="btn_img"):
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

        # ── 方案B：AI 生成配图（免费版 + Pro精品版）──
        st.markdown("**🖼️ 方案B：AI 生成场景配图** — 无需上传照片，AI 根据文案内容创作")

        # 多用户额度提示
        st.info(
            "**🆓 免费版**（Gemini Nano）：1:1 方图，500次/天由**所有测试用户共享**\n\n"
            "**⭐ Pro精品版**（Imagen 4 Fast）：9:16 竖图，与小红书完美适配，画质更佳\n\n"
            "⚠️ **多人同时使用提示**：免费额度为共享资源，高峰时段（晚上7-10点）可能暂时不可用。"
            "建议：错开高峰期使用，或选择 Pro精品版获取专属额度。"
        )

        _code_now = st.session_state.invite_code
        _pro_used_now = get_pro_used(_code_now)
        _pro_left_now = PRO_GEN_LIMIT - _pro_used_now
        _has_quota = _pro_left_now > 0

        col_free, col_pro = st.columns(2)

        with col_free:
            st.markdown("**🆓 免费版** · 1:1方图 · 共享额度")
            btn_free = st.button(
                "🖼️ 生成免费AI配图（2张）",
                key="btn_gen_free",
                use_container_width=True,
            )
            if st.session_state.scene_images and st.session_state.get("scene_tier") == "free":
                btn_regen_free = st.button("🔄 换一批（免费版）", key="btn_regen_free", use_container_width=True)
            else:
                btn_regen_free = False

        with col_pro:
            st.markdown(f"**⭐ Pro精品版** · 9:16竖图 · 剩余 {_pro_left_now}/{PRO_GEN_LIMIT} 次")
            if _has_quota:
                btn_pro = st.button(
                    f"⭐ 生成Pro精品配图（2张）· 消耗1次",
                    key="btn_gen_pro",
                    type="primary",
                    use_container_width=True,
                )
            else:
                st.button(
                    "⭐ Pro 额度已用完",
                    key="btn_gen_pro_disabled",
                    disabled=True,
                    use_container_width=True,
                )
                st.caption("联系 David 获取新额度")
                btn_pro = False

        # 免费版生图
        if btn_free or btn_regen_free:
            with st.status("正在生成免费AI配图…", expanded=True) as _free_status:
                _free_status.update(label="Gemini 正在绘制图片…（约10-20秒）")
                imgs, s_prompt, s_err = generate_scene_nano_banana(
                    st.session_state.rewrite_result, industry
                )
                if imgs:
                    _free_status.update(label="生成完成！", state="complete", expanded=False)
                else:
                    _free_status.update(label="生成失败", state="error")
            if imgs:
                st.session_state.scene_images = imgs
                st.session_state.scene_prompt = s_prompt
                st.session_state["scene_tier"] = "free"
                log_event(st.session_state.invite_code, "generate_scene_free",
                           st.session_state.industry_id, mode)
                st.success(f"生成成功！共 {len(imgs)} 张 · 1:1 方图")
            else:
                log_event(st.session_state.invite_code, "generate_scene_free",
                           st.session_state.industry_id, mode, detail=s_err, success=False)
                st.error(f"生成失败：{s_err}")
                if s_err and "共享" in s_err:
                    st.warning("💡 免费额度繁忙，建议换个时间段再试，或使用 Pro精品版")
            st.rerun()

        # Pro 版生图（先扣配额，失败退回）
        if btn_pro and _has_quota:
            if not try_use_pro_quota(_code_now):
                st.error("Pro 配额已用完")
            else:
                with st.status("正在生成Pro精品配图…", expanded=True) as _pro_status:
                    _pro_status.update(label="Imagen 4 Fast 正在绘制…（约15-30秒）")
                    imgs, s_prompt, s_err = generate_scene_with_imagen4(
                        st.session_state.rewrite_result, industry
                    )
                    if imgs:
                        _pro_status.update(label="生成完成！", state="complete", expanded=False)
                    else:
                        _pro_status.update(label="生成失败", state="error")
                if imgs:
                    st.session_state.scene_images = imgs
                    st.session_state.scene_prompt = s_prompt
                    st.session_state["scene_tier"] = "pro"
                    log_event(st.session_state.invite_code, "generate_scene_pro",
                               st.session_state.industry_id, mode)
                    new_left = _pro_left_now - 1
                    st.success(f"生成成功！共 {len(imgs)} 张 · 9:16 竖图 · Pro 剩余 {new_left}/{PRO_GEN_LIMIT} 次")
                else:
                    refund_pro_quota(_code_now)
                    log_event(st.session_state.invite_code, "generate_scene_pro",
                               st.session_state.industry_id, mode, detail=s_err, success=False)
                    st.error(f"生成失败：{s_err}")
                st.rerun()

        if st.session_state.scene_images:
            tier_label = "Pro精品" if st.session_state.get("scene_tier") == "pro" else "免费版"
            _nc = img_cols(len(st.session_state.scene_images))
            _columns = st.columns(_nc)
            for i, img in enumerate(st.session_state.scene_images):
                with _columns[i % _nc]:
                    st.image(img, caption=f"AI配图 {i+1}（{tier_label}）", use_container_width=True)

            with st.expander("查看场景描述提示词", expanded=False):
                st.info(st.session_state.scene_prompt)
                st.caption("DeepSeek 根据文案内容生成，发送给 AI 模型执行")


# ═══════════════════════════════════════════════════════
#  Step 4：打包下载
# ═══════════════════════════════════════════════════════
if st.session_state.rewrite_done:
    st.divider()
    st.markdown('<span class="step-num">4</span> **打包下载**', unsafe_allow_html=True)

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
            tier_label = "Pro精品" if st.session_state.get("scene_tier") == "pro" else "免费版"
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
    st.markdown('<span class="step-num">5</span> **一键准备发布**', unsafe_allow_html=True)

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
        """渲染单条笔记的发布准备区：标题复制 + 正文复制"""
        pub_title, pub_body = _split_title_body(full_text)
        st.markdown("**📌 标题** （点右上角一键复制）")
        st.code(pub_title, language=None)
        st.markdown("**📝 正文** （点右上角一键复制）")
        st.code(pub_body, language=None)

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

    st.link_button(
        "🔗 打开小红书创作中心（网页版）",
        url="https://creator.xiaohongshu.com/publish/publish",
        use_container_width=True,
    )
    st.info(
        "**发布步骤：**\n"
        "1. 点上方按钮打开小红书创作中心\n"
        "2. 复制标题 → 粘贴到标题栏\n"
        "3. 复制正文 → 粘贴到正文区\n"
        "4. 从上方下载的 ZIP 中拖入图片\n"
        "5. 检查后点击「发布」",
        icon="💡",
    )


# ═══════════════════════════════════════════════════════
#  反馈区
# ═══════════════════════════════════════════════════════
if st.session_state.rewrite_done and not st.session_state.feedback_submitted:
    st.divider()
    st.markdown("### 💬 使用反馈")
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
                conn.close()
            except Exception:
                pass
            log_event(st.session_state.invite_code, "feedback",
                       st.session_state.get("industry_id", ""), st.session_state.get("selected_mode", ""))
            st.session_state.feedback_submitted = True
            st.rerun()

elif st.session_state.feedback_submitted:
    st.divider()
    st.success("感谢反馈！David 会认真查看每一条，下一版见 👋")

# ═══════════════════════════════════════════════════════
#  管理后台（仅 ADMIN 邀请码可见）
# ═══════════════════════════════════════════════════════
if st.session_state.invite_code in ADMIN_CODES:
    st.divider()
    st.markdown("## 📊 数据分析面板")
    st.caption("此区域仅管理员可见")

    try:
        conn = get_db()
        _today = datetime.now().strftime("%Y-%m-%d")
        _7days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        # ══════════════ 核心指标卡片 ══════════════
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

        c1, c2, c3 = st.columns(3)
        c1.metric("总用户", total_users)
        c2.metric("总生成", total_gens)
        c3.metric("今日生成", today_gens)

        c4, c5, c6 = st.columns(3)
        c4.metric("近7日生成", week_gens)
        c5.metric("提取成功率", extract_rate)
        c6.metric("反馈条数", total_feedbacks)

        # ══════════════ 每日生成趋势（近30天） ══════════════
        st.markdown("### 📈 每日生成趋势")
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

        # ══════════════ 行业使用排行 ══════════════
        st.markdown("### 🏆 行业热度排行")
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

        # ══════════════ 模式 & 图片档位分布 ══════════════
        col_mode, col_tier = st.columns(2)

        with col_mode:
            st.markdown("### 🔄 模式分布")
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
            st.markdown("### 🖼️ 图片档位")
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

        # ══════════════ 每小时活跃分布 ══════════════
        st.markdown("### ⏰ 每小时活跃分布")
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

        # ══════════════ 用户活跃排行 ══════════════
        st.markdown("### 👤 用户活跃排行")
        user_rows = conn.execute(
            "SELECT invite_code, COUNT(*) as gen_count, "
            "MAX(created_at) as last_active, "
            "COUNT(DISTINCT industry_id) as industry_count "
            "FROM generation_history GROUP BY invite_code "
            "ORDER BY gen_count DESC LIMIT 20"
        ).fetchall()
        if user_rows:
            df_users = pd.DataFrame([
                {
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

        # ══════════════ Pro 配额使用 ══════════════
        st.markdown("### 💎 Pro 配额使用")
        quota_rows = conn.execute(
            "SELECT invite_code, pro_gen_used, updated_at "
            "FROM quota_usage ORDER BY pro_gen_used DESC"
        ).fetchall()
        if quota_rows:
            df_quota = pd.DataFrame([
                {
                    "邀请码": q["invite_code"],
                    "已使用": q["pro_gen_used"],
                    "上限": PRO_GEN_LIMIT,
                    "剩余": max(PRO_GEN_LIMIT - q["pro_gen_used"], 0),
                    "最后使用": q["updated_at"][:16] if q["updated_at"] else "—",
                }
                for q in quota_rows
            ])
            st.dataframe(df_quota, use_container_width=True, hide_index=True)
        else:
            st.caption("暂无数据")

        # ══════════════ 最近反馈 ══════════════
        st.markdown("### 💬 最近反馈")
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

        # ══════════════ 事件日志浏览 ══════════════
        with st.expander("🔍 事件日志（最近50条）"):
            event_rows = conn.execute(
                "SELECT * FROM event_log ORDER BY created_at DESC LIMIT 50"
            ).fetchall()
            if event_rows:
                df_events = pd.DataFrame([
                    {
                        "事件": r["event_type"],
                        "邀请码": r["invite_code"],
                        "行业": r["industry_id"] or "—",
                        "模式": r["mode"] or "—",
                        "成功": "✅" if r["success"] else "❌",
                        "详情": (r["detail"] or "")[:60],
                        "时间": r["created_at"][:16] if r["created_at"] else "—",
                    }
                    for r in event_rows
                ])
                st.dataframe(df_events, use_container_width=True, hide_index=True)
            else:
                st.caption("暂无事件")

        conn.close()
    except Exception as e:
        st.error(f"数据库读取失败：{e}")

# ─── 页脚 ───
st.divider()
st.caption("📱 小红书内容 Agent · Demo v5.0 · 12大行业全双模式 · 免费+Pro双档AI配图")
