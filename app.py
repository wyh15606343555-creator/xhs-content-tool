"""
小红书通用内容 Agent — Demo v5.0
邀请码测试版 | 10大行业全部支持双模式 | 免费+Pro双档AI配图
"""

import streamlit as st
import requests
import json
import re
import io
import time
import random
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
from PIL import Image

st.set_page_config(
    page_title="小红书内容Agent",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ═══════════════════════════════════════════════
   DARK THEME — Gleamy Editorial Style
   Background: #0A0A0A · Text: #FFF · Accent: #FF6B00
═══════════════════════════════════════════════ */

/* ── Global ── */
html, body,
[data-testid="stApp"],
.stApp {
    background-color: #0A0A0A !important;
    color: #E0E0E0 !important;
}
.main .block-container {
    background-color: #0A0A0A !important;
    padding-top: 1.5rem;
}

/* ── Top header / toolbar ── */
[data-testid="stHeader"],
[data-testid="stToolbar"] {
    background-color: #0A0A0A !important;
    border-bottom: 1px solid #1E1E1E !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background-color: #111111 !important;
    border-right: 1px solid #1E1E1E !important;
}
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    color: #B0B0B0 !important;
}
section[data-testid="stSidebar"] strong {
    color: #FFFFFF !important;
}
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #555555 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: #222222 !important;
}

/* ── Headings ── */
h1, h2, h3, h4, h5 {
    color: #FFFFFF !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
}
h1 { font-size: 2.2rem !important; }
h3 { font-size: 1.1rem !important; }

/* ── Divider ── */
hr {
    border: none !important;
    border-top: 1px solid #1E1E1E !important;
    margin: 1rem 0 !important;
}

/* ── Paragraphs / captions ── */
p, .stMarkdown p { color: #C0C0C0 !important; }
.stCaption, [data-testid="stCaptionContainer"],
.stCaption > p, [data-testid="stCaptionContainer"] > p {
    color: #555555 !important;
}

/* ── Step Number Badge ── */
.step-num {
    display: inline-block;
    background: #FF6B00;
    color: #000000 !important;
    border-radius: 50%;
    width: 26px; height: 26px;
    text-align: center; line-height: 26px;
    font-size: 0.85rem; font-weight: 900;
    margin-right: 8px;
    vertical-align: middle;
}

/* ── Buttons ── */
.stButton > button {
    background-color: #1A1A1A !important;
    color: #B0B0B0 !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 8px !important;
    transition: border-color 0.15s, color 0.15s;
}
.stButton > button:hover {
    border-color: #FF6B00 !important;
    color: #FF6B00 !important;
    background-color: #1A1A1A !important;
}
.stButton > button[kind="primary"] {
    background-color: #FF6B00 !important;
    color: #000000 !important;
    border: none !important;
    font-weight: 700 !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #FF8C33 !important;
    color: #000000 !important;
}
.stButton > button:disabled {
    background-color: #1A1A1A !important;
    color: #333333 !important;
    border-color: #1A1A1A !important;
}

/* ── Download Button ── */
[data-testid="stDownloadButton"] > button {
    background-color: #1A1A1A !important;
    color: #B0B0B0 !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 8px !important;
}
[data-testid="stDownloadButton"] > button:hover {
    border-color: #FF6B00 !important;
    color: #FF6B00 !important;
}

/* ── Text Inputs / Text Areas ── */
.stTextInput input,
.stTextArea textarea {
    background-color: #141414 !important;
    color: #FFFFFF !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 8px !important;
    caret-color: #FF6B00;
}
.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: #FF6B00 !important;
    box-shadow: 0 0 0 2px rgba(255,107,0,0.12) !important;
    outline: none !important;
}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #444444 !important;
}
.stTextInput label,
.stTextArea label {
    color: #888888 !important;
    font-size: 0.85rem !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div[data-baseweb="select"] > div {
    background-color: #141414 !important;
    color: #FFFFFF !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 8px !important;
}
.stSelectbox label { color: #888888 !important; }
.stSelectbox svg { fill: #555555 !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    border: 1px solid #222222 !important;
    border-radius: 10px !important;
    overflow: hidden;
    background-color: #111111 !important;
}
[data-testid="stExpander"] summary {
    background-color: #141414 !important;
    color: #CCCCCC !important;
    padding: 10px 14px !important;
}
[data-testid="stExpander"] summary:hover {
    color: #FF6B00 !important;
}
[data-testid="stExpander"] svg { fill: #555555 !important; }
.streamlit-expanderContent {
    background-color: #111111 !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    border-width: 0 0 0 3px !important;
    border-style: solid !important;
    background-color: #141414 !important;
    color: #CCCCCC !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] div,
[data-testid="stAlert"] span {
    color: inherit !important;
}
/* success */
[data-testid="stAlert"][data-baseweb="notification"] {
    background-color: #141414 !important;
}

/* ── Progress Bar ── */
[data-testid="stProgressBar"] > div {
    background-color: #1E1E1E !important;
    border-radius: 4px !important;
}
[data-testid="stProgressBar"] > div > div {
    background-color: #FF6B00 !important;
    border-radius: 4px !important;
}

/* ── Code / Pre ── */
.stCode, [data-testid="stCode"],
code, pre {
    background-color: #141414 !important;
    color: #888888 !important;
    border: 1px solid #222222 !important;
    border-radius: 6px !important;
}

/* ── File Uploader ── */
[data-testid="stFileUploader"],
[data-testid="stFileUploaderDropzone"] {
    background-color: #141414 !important;
    border: 1px dashed #2A2A2A !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploader"] label {
    color: #888888 !important;
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
    color: #888888;
}
[data-testid="stFileUploaderDropzoneInstructions"] small {
    font-size: 0 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] small::after {
    content: "支持 JPG / JPEG / PNG / WEBP，单文件最大 20MB";
    font-size: 0.75rem;
    color: #555555;
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
.gate-title {
    font-size: 2.8rem;
    font-weight: 900;
    margin-bottom: 0.5rem;
    color: #FFFFFF;
    letter-spacing: -0.04em;
    line-height: 1.1;
}
.gate-accent {
    color: #FF6B00;
}
.gate-sub {
    color: #444444;
    font-size: 0.85rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 0.5rem;
}

/* ── Spinner ── */
[data-testid="stSpinner"] > div {
    border-top-color: #FF6B00 !important;
}

/* ── Image captions ── */
[data-testid="stImage"] p { color: #555555 !important; font-size: 0.75rem !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0A0A0A; }
::-webkit-scrollbar-thumb { background: #2A2A2A; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #3A3A3A; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
#  Pro 配额追踪（基于临时目录，同一 Streamlit 实例内跨 session 持久）
# ═══════════════════════════════════════════════════════
_USAGE_DIR = Path(tempfile.gettempdir()) / "xhs_agent_v5_usage"
_PRO_GEN_LIMIT = 50


def _get_pro_used(code: str) -> int:
    try:
        _USAGE_DIR.mkdir(exist_ok=True)
        f = _USAGE_DIR / f"{code.upper()}.json"
        return json.loads(f.read_text()).get("pro_gen", 0) if f.exists() else 0
    except Exception:
        return 0


def _inc_pro_used(code: str) -> int:
    try:
        _USAGE_DIR.mkdir(exist_ok=True)
        f = _USAGE_DIR / f"{code.upper()}.json"
        new_val = _get_pro_used(code) + 1
        f.write_text(json.dumps({"pro_gen": new_val}))
        return new_val
    except Exception:
        return 0


def _has_pro_quota(code: str) -> bool:
    return _get_pro_used(code) < _PRO_GEN_LIMIT


# ═══════════════════════════════════════════════════════
#  行业模板库（10 个行业，每个均支持竞品参考 + 原创生成双模式）
# ═══════════════════════════════════════════════════════
INDUSTRIES = {

    "fitness": {
        "label": "💪 健身私教",
        "desc": "上门私教 / 减脂增肌 / 产后恢复",

        # ── 竞品参考模式 (Mode A) ──
        "system_prompt": (
            "你是专业的健身私教小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留原文核心卖点（效果数据、课程亮点、真实反馈）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：专业权威+亲切真实，口语化，适当使用 emoji\n"
            "4. 融入城市本地元素（地标、商圈、区域名）\n"
            "5. 保留并优化话题标签（#xxx）\n"
            "6. 强调「效果」「专业」「上门服务」「变化」等高转化词\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        # ── 原创生成模式 (Mode B) ──
        "profile_fields": [
            {"key": "studio_name",  "label": "工作室/品牌名", "placeholder": "如：FitPro私教中心"},
            {"key": "service_type", "label": "主营项目",      "placeholder": "如：上门私教 / 减脂增肌 / 产后恢复"},
            {"key": "coach_cred",   "label": "教练资质",      "placeholder": "如：ACE认证 / 5年经验 / 体育院校毕业"},
            {"key": "price_range",  "label": "课程价格",      "placeholder": "如：单次300元 / 10次课2800元"},
        ],
        "brief_placeholder": "如：学员小李3个月减脂18斤，腰围小了两圈，今天拍了对比照，想做成功案例展示",
        "create_system_prompt": (
            "你是专业的健身私教小红书文案创作专家。\n\n"
            "根据教练/工作室信息和今日主题，创作一篇原创小红书笔记。\n\n"
            "创作要求：\n"
            "1. 风格：专业权威+真实亲切，口语化，适当使用 emoji\n"
            "2. 结构：效果钩子标题 + 痛点共鸣 + 课程/教练介绍 + 成功案例/数据 + 预约引导\n"
            "3. 多用「效果翻倍」「专属方案」「上门服务」「真实蜕变」等高转化词\n"
            "4. 可加入学员真实反馈或前后数据对比\n"
            "5. 结尾加话题标签（5-8个）\n"
            "6. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，突出效果）\n"
            "【正文】原创正文"
        ),

        # ── 图片处理提示词 ──
        "image_prompt": (
            "Remove ALL text, titles, captions, watermarks, logos, and any overlaid "
            "text or graphics from this fitness/workout image completely. "
            "Reconstruct the areas behind removed text naturally. "
            "Do NOT change any people, faces, poses, clothing, gym equipment, or background. "
            "The output should look like a clean, professional fitness photo."
        ),
    },

    "beauty": {
        "label": "💄 美容美发",
        "desc": "护肤 / 美甲 / 发型设计 / 美容院",

        "system_prompt": (
            "你是专业的美容美发小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心卖点（效果对比、技术亮点、价格、使用感受）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：精致时尚、有种草感，口语化，适当使用 emoji\n"
            "4. 强调「变美」「蜕变」「显白」「专业技术」等高转化词\n"
            "5. 可加入使用前后对比的描述\n"
            "6. 融入城市消费和审美特点\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        "profile_fields": [
            {"key": "store_name",     "label": "店铺/工作室名", "placeholder": "如：颜研美容工作室"},
            {"key": "main_service",   "label": "主营项目",      "placeholder": "如：皮肤管理 / 美甲 / 睫毛 / 发型设计"},
            {"key": "tech_highlight", "label": "技术亮点",      "placeholder": "如：韩国进口仪器 / 10年技师 / 进口材料"},
            {"key": "price_range",    "label": "价格区间",      "placeholder": "如：皮肤管理基础护理188元起"},
        ],
        "brief_placeholder": "如：最近做了一个学员的皮肤管理，毛孔明显收缩，素颜都亮了很多，想展示效果吸引新客",
        "create_system_prompt": (
            "你是专业的美容美发小红书文案创作专家。\n\n"
            "根据店铺信息和今日主题，创作一篇原创小红书笔记。\n\n"
            "创作要求：\n"
            "1. 风格：精致时尚、有种草感，口语化，多用 emoji\n"
            "2. 结构：变美钩子标题 + 皮肤/发型痛点 + 项目/技术介绍 + 效果描述 + 预约引导\n"
            "3. 多用「蜕变」「显白」「焕然一新」「专业护理」等种草词\n"
            "4. 可加入 before/after 效果对比描述\n"
            "5. 结尾加话题标签（5-8个）\n"
            "6. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，体现变美感）\n"
            "【正文】原创正文"
        ),

        "image_prompt": (
            "Remove ALL text, watermarks, logos, price information, and overlaid graphics "
            "from this beauty/hair/cosmetic image completely. "
            "Reconstruct the areas naturally. "
            "Keep the hairstyle, makeup, beauty results, and the person exactly the same. "
            "The result should look glamorous and professional."
        ),
    },

    "education": {
        "label": "📚 教育培训",
        "desc": "技能培训 / 考证备考 / 儿童教育",

        "system_prompt": (
            "你是专业的教育培训小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心卖点（课程内容、学员成果、师资力量、价格）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：专业可信、激励感强，适当使用 emoji\n"
            "4. 强调「学会」「提升」「改变」「拿证」「成功上岸」等激励词\n"
            "5. 可加入学员真实反馈或成绩数据\n"
            "6. 结尾引导报名/咨询\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        "profile_fields": [
            {"key": "institution",  "label": "机构名称",    "placeholder": "如：启航职业培训中心"},
            {"key": "main_course",  "label": "主营课程",    "placeholder": "如：健身教练证 / 营养师证 / 育婴师证"},
            {"key": "pass_rate",    "label": "通过率/成果", "placeholder": "如：一次性通过率95% / 已培训2000+学员"},
            {"key": "price_range",  "label": "课程价格",    "placeholder": "如：周末班3980元 / 全程班5800元"},
        ],
        "brief_placeholder": "如：本月又有8名学员拿到了NSCA健身教练认证，想做成功案例展示，吸引更多学员报名",
        "create_system_prompt": (
            "你是专业的教育培训小红书文案创作专家。\n\n"
            "根据机构信息和今日主题，创作一篇原创小红书笔记。\n\n"
            "创作要求：\n"
            "1. 风格：专业可信、激励感强，适当使用 emoji\n"
            "2. 结构：成功钩子标题 + 学员痛点共鸣 + 课程/机构介绍 + 学员成果/数据 + 报名引导\n"
            "3. 多用「学会」「提升」「改变」「拿证」「成功上岸」等激励词\n"
            "4. 加入具体学员成功案例和数据\n"
            "5. 结尾加话题标签（5-8个）\n"
            "6. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，体现成功感）\n"
            "【正文】原创正文"
        ),

        "image_prompt": (
            "Remove ALL text, watermarks, logos, and overlaid graphics "
            "from this education/training image completely. "
            "Reconstruct the areas naturally. "
            "Keep the students, teachers, learning materials, and classroom setting exactly the same. "
            "The result should look professional and inspiring."
        ),
    },

    "food": {
        "label": "🍜 餐饮美食",
        "desc": "餐厅 / 咖啡馆 / 烘焙甜品 / 探店",

        "system_prompt": (
            "你是专业的餐饮探店小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心卖点（招牌菜、环境特色、价格、地址区域）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：有食欲感、温馨治愈，口语化，适当使用 emoji\n"
            "4. 融入当地商圈、地标元素，增加本地属性\n"
            "5. 多用「宝藏小店」「必点」「隐藏菜单」「氛围感」「性价比」等高流量词\n"
            "6. 结尾保留并优化话题标签（5-8个）\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        "profile_fields": [
            {"key": "store_name",  "label": "店名",       "placeholder": "如：猫窝咖啡"},
            {"key": "store_style", "label": "风格/特色",  "placeholder": "如：日系复古 / 宠物友好 / 手冲精品"},
            {"key": "price_range", "label": "人均消费",   "placeholder": "如：人均35元"},
            {"key": "location",    "label": "所在商圈",   "placeholder": "如：三里屯附近 / 朝阳望京"},
        ],
        "brief_placeholder": "如：新上了西西里柠檬拿铁，搭草莓奶油可颂，周末限定，想做一篇种草文",
        "create_system_prompt": (
            "你是专业的餐饮探店小红书文案创作专家。\n\n"
            "根据商家提供的店铺信息和今日主题，创作一篇原创小红书笔记。\n\n"
            "创作要求：\n"
            "1. 风格：有食欲感、温馨治愈，口语化，适当使用 emoji\n"
            "2. 结构：钩子标题 + 场景带入 + 产品描述 + 推荐理由 + 价格/地址引导\n"
            "3. 多用「宝藏小店」「必点」「隐藏菜单」「氛围感」等高流量词\n"
            "4. 结尾加推荐话题标签（5-8个）\n"
            "5. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，吸引眼球）\n"
            "【正文】原创正文"
        ),

        "image_prompt": (
            "Enhance this food/restaurant photo for social media: "
            "improve brightness, contrast, and color saturation to make the food look more appetizing. "
            "Sharpen details. Remove any distracting elements at the edges if present. "
            "Do NOT change the food, drinks, or restaurant setting. "
            "Make it look like a professional food photography shot."
        ),
    },

    "medical_beauty": {
        "label": "💉 医疗美容",
        "desc": "皮肤管理 / 医美项目 / 美容诊所",

        "system_prompt": (
            "你是专业的医疗美容小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心信息（项目名称、效果体验、价格、机构资质）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：专业可信 + 真实亲切，避免过度营销\n"
            "4. 合规：不夸大效果、不承诺疗效、不用医疗绝对化用语\n"
            "5. 强调「专业」「安全」「正规资质」「个性化方案」等信任词\n"
            "6. 融入城市本地元素，增加本地属性\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        "profile_fields": [
            {"key": "store_name",    "label": "机构名称", "placeholder": "如：纯粹医美·光感肌肤管理"},
            {"key": "main_service",  "label": "主营项目", "placeholder": "如：水光针 / 热玛吉 / 皮肤管理"},
            {"key": "price_range",   "label": "项目价格", "placeholder": "如：水光针单次980起"},
            {"key": "highlights",    "label": "核心优势", "placeholder": "如：正规医疗资质 / 院长亲诊 / 韩国进口材料"},
        ],
        "brief_placeholder": "如：最近做了一批水光针客户，效果很好，皮肤喝饱水那种感觉，想发真实反馈种草",
        "create_system_prompt": (
            "你是专业的医疗美容小红书文案创作专家。\n\n"
            "根据机构信息和今日主题，创作一篇原创小红书笔记。\n\n"
            "创作要求：\n"
            "1. 风格：专业可信 + 真实亲切，避免过度营销语气\n"
            "2. 合规：不夸大效果、不承诺疗效、不用医疗绝对化用语\n"
            "3. 内容：项目介绍 + 体验感受 + 效果描述（用形容词）+ 预约引导\n"
            "4. 强调「专业」「安全」「正规资质」「个性化方案」等信任词\n"
            "5. 结尾加话题标签（5-8个）\n"
            "6. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，体现效果感）\n"
            "【正文】原创正文"
        ),

        "image_prompt": (
            "Enhance this medical beauty/skincare clinic photo for social media: "
            "improve lighting to create a clean, professional, clinical yet welcoming atmosphere. "
            "Remove any text overlays, watermarks, or branding from the image. "
            "The result should look trustworthy, professional, and aspirational."
        ),
    },

    "fashion": {
        "label": "🛍️ 服装销售",
        "desc": "实体门店 / 网店直播 / 穿搭种草 / 新品上架",

        "system_prompt": (
            "你是专业的服装穿搭小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心卖点（款式特点、面料质感、适合场合、价格、搭配建议）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：时尚有种草力，口语化，多用穿搭场景，适当使用 emoji\n"
            "4. 多用「显瘦」「显白」「气质」「百搭」「穿搭公式」等种草词\n"
            "5. 融入本地消费场景（商场 / 街边店 / 市集），增加本地属性\n"
            "6. 结尾保留并优化话题标签（5-8个）\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        "profile_fields": [
            {"key": "store_name",    "label": "店铺名称",   "placeholder": "如：衣柜研究所 / 小熊女装"},
            {"key": "main_category", "label": "主营品类",   "placeholder": "如：休闲女装 / 男装 / 童装 / 男女皆有"},
            {"key": "style_tag",     "label": "风格标签",   "placeholder": "如：百搭休闲 / 韩系甜美 / 职场通勤 / 运动户外"},
            {"key": "price_range",   "label": "价格区间",   "placeholder": "如：单品59-199元 / 全场百元以内"},
        ],
        "brief_placeholder": "如：刚到一批春款碎花连衣裙，版型显瘦，颜色好看，价格才89元，想做种草吸引进店",
        "create_system_prompt": (
            "你是专业的服装穿搭小红书文案创作专家，擅长为本地实体服装店创作种草内容。\n\n"
            "根据店铺信息和今日主题，创作一篇原创小红书穿搭种草笔记。\n\n"
            "创作要求：\n"
            "1. 风格：接地气、有种草力，口语化，真实感强，适当使用 emoji\n"
            "2. 结构：视觉钩子标题 + 穿搭场景代入 + 款式亮点（颜色/版型/面料）+ 搭配建议 + 到店/购买引导\n"
            "3. 多用「显瘦」「显白」「气质」「百搭」「性价比」「新款」等高转化词\n"
            "4. 可以描述不同穿搭场景（逛街/上班/约会/周末休闲）\n"
            "5. 结尾引导到店试穿或私信询价，加话题标签（5-8个）\n"
            "6. 字数：正文300-500字，语言贴近本地消费者\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，突出款式或价格亮点）\n"
            "【正文】原创正文"
        ),

        "image_prompt": (
            "Enhance this clothing/fashion product photo for social media: "
            "improve lighting and colors to make the clothing look more appealing and true-to-color. "
            "Clean up the background if possible. Sharpen fabric texture details. "
            "Remove any text overlays, price tags, or watermarks. "
            "Make the colors look vivid and the fabric look high quality. "
            "The result should look like a clean product photo suitable for a clothing store post."
        ),
    },

    "drinks": {
        "label": "🍺 精酿&酒吧",
        "desc": "精酿啤酒 / 鸡尾酒 / 清吧 / 居酒屋",

        "system_prompt": (
            "你是专业的酒吧/精酿饮品小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心卖点（招牌酒款、环境氛围、价格、特色活动）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：有氛围感、微醺感，口语化，适当使用 emoji\n"
            "4. 多用「氛围感」「微醺」「宝藏小店」「下班后的第一杯」等情绪词\n"
            "5. 融入城市夜生活场景，增加本地属性\n"
            "6. 结尾保留并优化话题标签（5-8个）\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        "profile_fields": [
            {"key": "store_name",  "label": "店名",       "placeholder": "如：雾霾蓝精酿小馆"},
            {"key": "store_style", "label": "风格/类型",  "placeholder": "如：工业风精酿 / 日式居酒屋 / 复古清吧"},
            {"key": "price_range", "label": "人均消费",   "placeholder": "如：人均120-200元"},
            {"key": "highlights",  "label": "特色/招牌",  "placeholder": "如：自酿IPA / 现调特调 / 不插电live"},
        ],
        "brief_placeholder": "如：新出春日限定鸡尾酒「樱花泡泡」，粉色渐变，微甜微酸，女生超爱，想做种草",
        "create_system_prompt": (
            "你是专业的酒吧/精酿小红书文案创作专家。\n\n"
            "根据店铺信息和今日主题，创作一篇原创小红书种草笔记。\n\n"
            "创作要求：\n"
            "1. 风格：有氛围感、微醺感，口语化，适当使用 emoji\n"
            "2. 结构：情绪钩子标题 + 场景代入 + 产品描述（颜色/口感/视觉）+ 氛围 + 到店引导\n"
            "3. 多用「氛围感」「微醺」「宝藏小店」「隐藏款」「下班后的第一杯」等情绪词\n"
            "4. 可以描述喝酒的场景和心情\n"
            "5. 结尾加话题标签（5-8个）\n"
            "6. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，有情绪感）\n"
            "【正文】原创正文"
        ),

        "image_prompt": (
            "Enhance this bar/cocktail/craft beer photo for social media: "
            "improve lighting to create a warm, atmospheric, moody feel. "
            "Make the drinks look more vibrant and appealing - enhance colors and clarity. "
            "Remove any text overlays or watermarks. "
            "The result should evoke a relaxed, enjoyable bar atmosphere."
        ),
    },

    "photography": {
        "label": "📸 摄影工作室",
        "desc": "写真 / 婚纱 / 儿童 / 商业摄影",

        "system_prompt": (
            "你是专业的摄影工作室小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心卖点（摄影风格、出片效果、套餐价格、拍摄体验）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：有质感、有故事感，口语化，适当使用 emoji\n"
            "4. 多用「光影」「质感」「记录美好」「专属」「出片率高」等种草词\n"
            "5. 融入城市文艺场景，增加本地属性\n"
            "6. 结尾保留并优化话题标签（5-8个）\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        "profile_fields": [
            {"key": "store_name",   "label": "工作室名称", "placeholder": "如：光影印记摄影工作室"},
            {"key": "main_service", "label": "主营类型",   "placeholder": "如：个人写真 / 情侣写真 / 儿童摄影"},
            {"key": "photo_style",  "label": "拍摄风格",   "placeholder": "如：日系胶片 / 韩系清新 / 复古港风"},
            {"key": "price_range",  "label": "套餐价格",   "placeholder": "如：单人写真套餐599起"},
        ],
        "brief_placeholder": "如：最近出了一组日系胶片风格的闺蜜写真，在复古咖啡馆拍的，特别好看，想吸引新客预约",
        "create_system_prompt": (
            "你是专业的摄影工作室小红书文案创作专家。\n\n"
            "根据工作室信息和今日主题，创作一篇原创小红书种草笔记。\n\n"
            "创作要求：\n"
            "1. 风格：有质感、有故事感，口语化，适当使用 emoji\n"
            "2. 结构：视觉吸引标题 + 拍摄场景故事 + 风格/技术描述 + 出片效果 + 预约引导\n"
            "3. 多用「光影」「质感」「记录美好」「专属」「出片率高」等种草词\n"
            "4. 可以描述拍摄体验和拿到照片时的感受\n"
            "5. 结尾加话题标签（5-8个）\n"
            "6. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，体现画面感）\n"
            "【正文】原创正文"
        ),

        "image_prompt": (
            "Enhance this portrait/photography studio photo for social media: "
            "improve overall tone, contrast, and warmth to match the intended artistic style. "
            "Enhance skin tones naturally. "
            "Remove any watermarks, studio logos, or text overlays completely. "
            "The result should look like a professionally edited portrait photo."
        ),
    },

    "hotel": {
        "label": "🏨 民宿&酒店",
        "desc": "精品民宿 / 特色酒店 / 亲子酒店 / 度假村",

        # ── 竞品参考模式 (Mode A) ──
        "system_prompt": (
            "你是专业的民宿/酒店小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心卖点（地理位置、环境氛围、特色房型、配套设施、价格）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：有情调、有故事感，口语化，适当使用 emoji\n"
            "4. 多用「氛围感」「治愈系」「宝藏住所」「出片率高」「私藏地」等种草词\n"
            "5. 融入城市/地区旅游场景，增加在地属性\n"
            "6. 结尾保留并优化话题标签（5-8个）\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        # ── 原创生成模式 (Mode B) ──
        "profile_fields": [
            {"key": "hotel_name",   "label": "民宿/酒店名称", "placeholder": "如：山间云舍民宿"},
            {"key": "hotel_type",   "label": "类型/风格",     "placeholder": "如：山景民宿 / 海景精品酒店 / 亲子主题"},
            {"key": "price_range",  "label": "每晚价格",      "placeholder": "如：大床房每晚388元起"},
            {"key": "location",     "label": "地理位置",      "placeholder": "如：峨眉山脚下 / 大理古城附近"},
        ],
        "brief_placeholder": "如：周末入住了一对来度蜜月的客人，他们特别喜欢山景房，拍了很多照片，想展示环境吸引更多预定",
        "create_system_prompt": (
            "你是专业的民宿/酒店小红书文案创作专家。\n\n"
            "根据民宿/酒店信息和今日主题，创作一篇原创小红书种草笔记。\n\n"
            "创作要求：\n"
            "1. 风格：有情调、有故事感，口语化，适当使用 emoji\n"
            "2. 结构：场景钩子标题 + 初到感受/打卡亮点 + 房间/设施描述 + 周边配套 + 预订引导\n"
            "3. 多用「氛围感」「治愈」「宝藏住所」「出片率高」「打卡地」等高流量种草词\n"
            "4. 可描述入住体验、早餐、景色、周边游玩等细节\n"
            "5. 结尾加话题标签（5-8个）\n"
            "6. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，体现氛围感或地标感）\n"
            "【正文】原创正文"
        ),

        # ── 图片处理提示词 ──
        "image_prompt": (
            "Enhance this hotel/B&B/accommodation photo for social media: "
            "improve lighting, warmth, and atmosphere to make the space look inviting and cozy. "
            "Enhance natural light, make colors richer, and improve clarity of architectural details. "
            "Remove any text overlays, watermarks, price tags, or logos completely. "
            "The result should look like a professional interior or landscape photography shot "
            "that makes viewers want to book a stay."
        ),
    },

    "jewelry": {
        "label": "💍 珠宝黄金",
        "desc": "黄金 / 翡翠 / 钻石 / 银饰 / 珠宝定制",

        # ── 竞品参考模式 (Mode A) ──
        "system_prompt": (
            "你是专业的珠宝黄金小红书文案改写专家。\n\n"
            "改写规则：\n"
            "1. 保留核心卖点（材质工艺、设计亮点、价格/克价、品牌/店铺信息）\n"
            "2. 完全更换表达方式，改写率 > 70%\n"
            "3. 风格：精致优雅有品位感，口语化，适当使用 emoji\n"
            "4. 多用「质感」「有重量感」「送礼首选」「传家款」「保值」「每日佩戴」等种草词\n"
            "5. 融入节日/送礼/纪念日等消费场景\n"
            "6. 结尾保留并优化话题标签（5-8个）\n\n"
            "请严格按以下格式输出：\n"
            "【标题】改写后的标题\n"
            "【正文】改写后的正文"
        ),

        # ── 原创生成模式 (Mode B) ──
        "profile_fields": [
            {"key": "store_name",    "label": "品牌/店铺名", "placeholder": "如：福满堂黄金珠宝"},
            {"key": "main_product",  "label": "主营品类",    "placeholder": "如：黄金饰品 / 翡翠玉石 / 钻石定制"},
            {"key": "price_range",   "label": "价格/克价",   "placeholder": "如：黄金今日克价640元 / 钻石戒指5000元起"},
            {"key": "highlights",    "label": "品牌/工艺亮点", "placeholder": "如：国家认证 / 手工镶嵌 / 支持以旧换新"},
        ],
        "brief_placeholder": "如：新到了一批足金999蝴蝶结项链，轻奢感很强，今天主推，适合送女朋友，想做种草笔记",
        "create_system_prompt": (
            "你是专业的珠宝黄金小红书文案创作专家。\n\n"
            "根据店铺信息和今日主题，创作一篇原创小红书种草笔记。\n\n"
            "创作要求：\n"
            "1. 风格：精致有品位感，口语化，适当使用 emoji\n"
            "2. 结构：视觉吸引标题 + 材质/工艺介绍 + 佩戴效果/上身感 + 送礼/纪念日场景 + 购买引导\n"
            "3. 多用「质感」「有重量感」「保值」「送礼首选」「轻奢风」等高转化词\n"
            "4. 可结合节日、纪念日、自我犒赏等消费动机\n"
            "5. 结尾加话题标签（5-8个）\n"
            "6. 字数：正文300-500字\n\n"
            "请严格按以下格式输出：\n"
            "【标题】原创标题（含emoji，体现品质感或礼赠感）\n"
            "【正文】原创正文"
        ),

        # ── 图片处理提示词 ──
        "image_prompt": (
            "Enhance this jewelry/gold/gemstone product photo for social media: "
            "improve lighting to make the metal shine brilliantly and gemstones sparkle vividly. "
            "Enhance color saturation of gold tones, gem colors, and metallic luster. "
            "Clean up the background for a professional, studio-quality look. "
            "Remove any text overlays, price tags, watermarks, or logos completely. "
            "The result should look like a high-end jewelry catalog photo that conveys luxury and quality."
        ),
    },
}


# ═══════════════════════════════════════════════════════
#  Session State 初始化
# ═══════════════════════════════════════════════════════
_DEFAULTS = dict(
    authed=False,
    invite_code="",
    industry_id=None,
    selected_mode=None,    # "rewrite" 或 "create"，由用户选择
    city="",
    # Mode A：竞品参考
    note_title="",
    note_text="",
    note_images=[],
    rewrite_result="",
    edited_images=[],
    content_ready=False,
    rewrite_done=False,
    images_done=False,
    extract_log="",
    # Mode B：原创生成
    store_profile={},
    daily_brief="",
    create_images=[],
    dynamic_image_prompt="",
    scene_images=[],
    scene_prompt="",
    feedback_submitted=False,
)
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ═══════════════════════════════════════════════════════
#  工具函数
# ═══════════════════════════════════════════════════════

def check_invite_code(code: str) -> bool:
    try:
        raw = st.secrets.get("INVITE_CODES", "")
        valid = [c.strip().upper() for c in raw.split(",") if c.strip()]
        if not valid:
            return True
        return code.strip().upper() in valid
    except Exception:
        return True


def _get_api_key(name: str) -> str:
    try:
        return st.secrets.get(name, "")
    except Exception:
        return ""


_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.6167.178 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
    "MicroMessenger/8.0.47(0x18002f30) NetType/WIFI Language/zh_CN",
]


def _make_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    })
    return s


def _extract_url(raw: str) -> str:
    m = re.search(r'https?://[^\s，,、!！\]】]+', raw)
    return m.group(0).rstrip('.,;:!?。，；：！？') if m else raw.strip()


def _extract_share_title(raw: str) -> str:
    m = re.search(r'https?://', raw)
    if not m:
        return ""
    before = raw[:m.start()].strip()
    before = re.sub(r'^\d+\s*', '', before).rstrip('.,。，…、 ')
    return before if len(before) >= 4 else ""


_GARBAGE_TITLES = {"小红书", "小红书 - 你的生活指南", "发现 - 小红书", ""}


def _is_useful_title(t: str) -> bool:
    return bool(t) and t.strip() not in _GARBAGE_TITLES and len(t.strip()) > 3


def try_extract_xhs(raw_input: str, progress_callback=None):
    """多策略提取小红书内容，返回 (title, text, image_urls, logs)"""
    logs = []
    url = _extract_url(raw_input)
    share_title = _extract_share_title(raw_input)
    if share_title:
        logs.append(f"从分享文本识别标题片段：「{share_title[:40]}」")
    if not url.startswith("http"):
        logs.append("未找到有效链接")
        return share_title, "", [], logs

    logs.append(f"提取到链接：{url}")
    session = _make_session()
    title, text, images, note_id = "", "", [], ""

    for attempt in range(2):
        try:
            if attempt > 0:
                session = _make_session()
                time.sleep(0.5)
                logs.append(f"重试第 {attempt + 1} 次（更换浏览器指纹）")
            if progress_callback:
                progress_callback(0.1 + attempt * 0.1, f"策略1：模拟手机浏览器访问（第{attempt+1}次）…")

            resp = session.get(url, timeout=15, allow_redirects=True)
            final_url = resp.url
            logs.append(f"最终URL：{final_url}（状态码 {resp.status_code}）")
            if resp.status_code != 200:
                continue

            html = resp.text
            nid = re.search(r'/(?:explore|discovery/item)/([a-f0-9]{24})', final_url)
            if nid:
                note_id = nid.group(1)
                logs.append(f"笔记ID：{note_id}")

            for pat in [
                r'<meta[^>]+property="og:title"[^>]+content="([^"]*)"',
                r'<meta[^>]+content="([^"]*)"[^>]+property="og:title"',
            ]:
                t = re.search(pat, html)
                if t:
                    title = t.group(1)
                    break
            for pat in [
                r'<meta[^>]+property="og:description"[^>]+content="([^"]*)"',
                r'<meta[^>]+name="description"[^>]+content="([^"]*)"',
                r'<meta[^>]+content="([^"]*)"[^>]+property="og:description"',
            ]:
                d = re.search(pat, html)
                if d and len(d.group(1)) > len(text):
                    text = d.group(1)
            for pat in [
                r'<meta[^>]+property="og:image"[^>]+content="([^"]*)"',
                r'<meta[^>]+content="([^"]*)"[^>]+property="og:image"',
            ]:
                for m in re.finditer(pat, html):
                    if m.group(1) and m.group(1) not in images:
                        images.append(m.group(1))

            if (_is_useful_title(title) and text) or len(text) > 10 or images:
                logs.append(f"og:tags 提取成功（标题{len(title)}字，正文{len(text)}字，{len(images)}张图）")
                break

            state = re.search(
                r'window\.__INITIAL_STATE__\s*=\s*(\{.+?\})\s*</script>',
                html, re.DOTALL,
            )
            if state:
                raw_json = re.sub(r":\s*undefined", ": null", state.group(1))
                try:
                    data = json.loads(raw_json)
                    _note = None
                    nd = data.get("noteData", {})
                    nd_inner = nd.get("data", {}).get("noteData", {})
                    if nd_inner and nd_inner.get("title"):
                        _note = nd_inner
                    if not _note:
                        preload = nd.get("normalNotePreloadData", {})
                        if preload and preload.get("title"):
                            _note = preload
                    if not _note:
                        note_map = data.get("note", {}).get("noteDetailMap", {})
                        if note_map:
                            _note = list(note_map.values())[0].get("note", {})
                    if _note and (_note.get("title") or _note.get("desc")):
                        title = _note.get("title", "") or title
                        text = _note.get("desc", "") or text
                        for img in (_note.get("imageList", []) or _note.get("imagesList", [])):
                            u = img.get("url") or img.get("urlDefault") or img.get("urlSizeLarge") or ""
                            if u and u not in images:
                                images.append(u)
                        logs.append(f"INITIAL_STATE 提取成功（标题{len(title)}字，正文{len(text)}字，{len(images)}张图）")
                        break
                except json.JSONDecodeError:
                    logs.append("INITIAL_STATE JSON解析失败")

            title_tag = re.search(r'<title[^>]*>([^<]+)</title>', html)
            if title_tag and not _is_useful_title(title):
                raw_t = re.sub(r'\s*[-–—|]\s*小红书.*$', '', title_tag.group(1).strip())
                if _is_useful_title(raw_t):
                    title = raw_t
                    logs.append(f"从 <title> 提取：「{title[:30]}」")

        except requests.exceptions.Timeout:
            logs.append(f"第{attempt+1}次请求超时")
        except Exception as e:
            logs.append(f"第{attempt+1}次异常：{type(e).__name__}")

    if not title and not text and note_id:
        if progress_callback:
            progress_callback(0.5, "策略2：尝试备用接口…")
        try:
            s2 = _make_session()
            s2.headers["Referer"] = "https://www.xiaohongshu.com/"
            r2 = s2.get(f"https://www.xiaohongshu.com/explore/{note_id}", timeout=15, allow_redirects=True)
            if r2.status_code == 200:
                for pat in [
                    r'<meta[^>]+property="og:title"[^>]+content="([^"]*)"',
                    r'<meta[^>]+(?:property="og:description"|name="description")[^>]+content="([^"]*)"',
                ]:
                    m2 = re.search(pat, r2.text)
                    if m2:
                        if "title" in pat:
                            title = m2.group(1)
                        else:
                            text = m2.group(1)
                if title or text:
                    logs.append("备用接口提取成功")
        except Exception:
            logs.append("备用接口未成功")

    if share_title and (not _is_useful_title(title) or len(share_title) > len(title) * 2):
        logs.append(f"使用分享文本标题（替代「{title}」）")
        title = share_title

    logs.append(
        f"最终结果：标题{len(title)}字，正文{len(text)}字，{len(images)}张图"
        if (title or text) else "所有策略均未成功"
    )
    return title, text, images, logs


def download_image_url(url: str):
    try:
        s = _make_session()
        s.headers["Referer"] = "https://www.xiaohongshu.com/"
        r = s.get(url, timeout=15)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception:
        return None


def rewrite_with_deepseek(title: str, text: str, industry: dict, city: str) -> str:
    """Mode A：调用 DeepSeek 改写竞品文案"""
    from openai import OpenAI
    api_key = _get_api_key("DEEPSEEK_API_KEY")
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    system = industry["system_prompt"] + f"\n\n目标城市：{city}"
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"原标题：{title}\n\n原正文：{text}"},
        ],
        temperature=0.8,
        max_tokens=2000,
    )
    return resp.choices[0].message.content


def generate_original_content(store_profile: dict, brief: str, industry: dict, city: str) -> str:
    """Mode B：根据店铺信息生成原创文案"""
    from openai import OpenAI
    api_key = _get_api_key("DEEPSEEK_API_KEY")
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    lines = []
    for field in industry.get("profile_fields", []):
        val = store_profile.get(field["key"], "").strip()
        if val:
            lines.append(f"{field['label']}：{val}")
    store_info = "\n".join(lines) if lines else "（未填写店铺信息）"

    system = industry["create_system_prompt"] + f"\n\n目标城市：{city}"
    user_content = f"店铺信息：\n{store_info}\n\n今日发帖主题：{brief}"

    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        temperature=0.85,
        max_tokens=2000,
    )
    return resp.choices[0].message.content


def generate_dynamic_image_prompt(copy_text: str, industry: dict) -> str:
    """Mode B：根据已生成的文案，动态生成 Gemini 图片处理提示词"""
    from openai import OpenAI
    api_key = _get_api_key("DEEPSEEK_API_KEY")
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    system = (
        "You are an expert at writing Gemini image editing prompts for social media content.\n"
        "Given a Chinese XiaoHongShu (RedNote) post, write a concise English image enhancement prompt.\n\n"
        "Rules:\n"
        "1. Extract 2-3 visual mood keywords from the post (e.g. warm, cozy, vibrant, elegant, fresh, moody, bright).\n"
        "2. Adjust lighting, color tone, and atmosphere to MATCH the post's emotional style.\n"
        "3. Do NOT change the main subject, composition, or add new elements.\n"
        "4. Always include: 'Remove any text overlays or watermarks.'\n"
        "5. Keep the result realistic and natural — not AI-generated looking.\n"
        "6. Output: 3-5 English sentences only. No Chinese, no explanations.\n\n"
        f"Industry: {industry['label']}"
    )
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"Post content:\n{copy_text[:600]}"},
        ],
        temperature=0.4,
        max_tokens=200,
    )
    return resp.choices[0].message.content.strip()


def _build_scene_system_prompt(industry: dict, is_pro: bool) -> str:
    style = "cinematic lighting, ultra realistic, portrait 9:16" if is_pro else "ultra realistic, lifestyle photography"
    return (
        "You are an expert at writing image generation prompts for social media.\n"
        "Given a Chinese XiaoHongShu post, write a detailed English prompt for image generation.\n\n"
        "Requirements:\n"
        "1. Describe a specific scene, setting, lighting, and atmosphere matching the post's emotion\n"
        "2. Include the generic product/food/environment type (do NOT mention brand names)\n"
        f"3. Style: {style}\n"
        "4. Match emotional keywords from the post (warm, cozy, vibrant, elegant, fresh, etc.)\n"
        "5. Output: one detailed English prompt only (3-4 sentences), no explanations, no Chinese\n\n"
        f"Industry: {industry['label']}"
    )


def generate_scene_nano_banana(copy_text: str, industry: dict) -> tuple:
    """免费档：Gemini 2.5 Flash Image 文生图（1:1方图，500次/天共享额度）
    返回 (images: list[PIL.Image], scene_prompt: str, error_msg: str)
    """
    from openai import OpenAI
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return [], "", "请先安装 google-genai 库"

    # Step 1: DeepSeek 生成英文场景描述
    try:
        ds_client = OpenAI(api_key=_get_api_key("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
        ds_resp = ds_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": _build_scene_system_prompt(industry, is_pro=False)},
                {"role": "user", "content": f"Post content:\n{copy_text[:500]}"},
            ],
            temperature=0.6,
            max_tokens=150,
        )
        scene_prompt = ds_resp.choices[0].message.content.strip()
    except Exception as e:
        return [], "", f"场景描述生成失败：{e}"

    # Step 2: Gemini 2.5 Flash Image 文生图（调用2次得到2张图）
    gai_key = _get_api_key("GOOGLE_API_KEY")
    if not gai_key:
        return [], scene_prompt, "未配置 Google API Key"

    g_client = genai.Client(api_key=gai_key)
    images = []
    last_err = ""
    for _ in range(2):
        try:
            response = g_client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[scene_prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if (
                        hasattr(part, "inline_data")
                        and part.inline_data
                        and getattr(part.inline_data, "mime_type", "").startswith("image/")
                    ):
                        images.append(Image.open(io.BytesIO(part.inline_data.data)).convert("RGB"))
                        break
        except Exception as e:
            err = str(e)
            if "quota" in err.lower() or "429" in err:
                last_err = "免费配图额度已用完（每日500次共享限制），请稍后再试或升级Pro"
                break
            last_err = f"生成失败：{err[:120]}"

    if images:
        return images, scene_prompt, ""
    return [], scene_prompt, last_err or "Gemini 未返回图片数据"


def generate_scene_with_imagen4(copy_text: str, industry: dict) -> tuple:
    """Pro档：Imagen 4 Fast 文生图（9:16竖图，高质量，消耗Pro配额）
    返回 (images: list[PIL.Image], scene_prompt: str, error_msg: str)
    """
    from openai import OpenAI
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return [], "", "请先安装 google-genai 库"

    # Step 1: DeepSeek 生成英文场景描述（Pro风格提示词）
    try:
        ds_client = OpenAI(api_key=_get_api_key("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
        ds_resp = ds_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": _build_scene_system_prompt(industry, is_pro=True)},
                {"role": "user", "content": f"Post content:\n{copy_text[:500]}"},
            ],
            temperature=0.6,
            max_tokens=180,
        )
        scene_prompt = ds_resp.choices[0].message.content.strip()
    except Exception as e:
        return [], "", f"场景描述生成失败：{e}"

    # Step 2: Imagen 4 Fast 文生图（9:16竖图）
    gai_key = _get_api_key("GOOGLE_API_KEY")
    if not gai_key:
        return [], scene_prompt, "未配置 Google API Key"

    g_client = genai.Client(api_key=gai_key)
    try:
        response = g_client.models.generate_images(
            model="imagen-4.0-fast-generate-001",
            prompt=scene_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=2,
                aspect_ratio="9:16",
            ),
        )
        images = []
        for gi in (response.generated_images or []):
            if gi.image and gi.image.image_bytes:
                images.append(Image.open(io.BytesIO(gi.image.image_bytes)).convert("RGB"))
        if images:
            return images, scene_prompt, ""
        return [], scene_prompt, "Imagen 4 未返回图片数据"
    except Exception as e:
        err = str(e)
        if "quota" in err.lower():
            return [], scene_prompt, "API 配额不足，请稍后重试"
        if "not found" in err.lower() or "404" in err:
            return [], scene_prompt, "Imagen 4 Fast 模型暂不可用（需确认 Google AI 账号已开通此功能）"
        return [], scene_prompt, f"生成失败：{err[:150]}"


def edit_image_with_gemini(image: Image.Image, prompt: str):
    """调用 Gemini 编辑/美化图片，返回 (PIL.Image | None, error_msg)"""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return None, "请先安装 google-genai 库"

    api_key = _get_api_key("GOOGLE_API_KEY")
    if not api_key:
        return None, "未配置 Google API Key"

    client = genai.Client(api_key=api_key)
    img_copy = image.copy()
    img_copy.thumbnail((1024, 1024))
    buf = io.BytesIO()
    img_copy.save(buf, format="PNG")

    models = [
        "gemini-2.5-flash-image",
        "gemini-2.0-flash-exp-image-generation",
    ]
    last_error = "未知错误"
    for model_name in models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png"),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if (
                        hasattr(part, "inline_data")
                        and part.inline_data
                        and getattr(part.inline_data, "mime_type", "").startswith("image/")
                    ):
                        return Image.open(io.BytesIO(part.inline_data.data)).convert("RGB"), ""
            last_error = f"{model_name}：返回响应但无图片数据"
        except Exception as e:
            err = str(e)
            if "404" in err:
                last_error = f"{model_name}：模型暂不可用"
            elif "quota" in err.lower():
                last_error = "API 配额已用尽，请稍后重试"
            else:
                last_error = f"{model_name}：{err[:120]}"

    return None, last_error


def make_zip(title: str, text: str, images: list) -> io.BytesIO:
    buf = io.BytesIO()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"文案_{ts}.txt", f"{title}\n\n{text}".encode("utf-8"))
        for i, img in enumerate(images):
            ib = io.BytesIO()
            img.save(ib, format="JPEG", quality=95)
            zf.writestr(f"图片_{i+1}.jpg", ib.getvalue())
    buf.seek(0)
    return buf


# ═══════════════════════════════════════════════════════
#  页面1：邀请码门禁
# ═══════════════════════════════════════════════════════
if not st.session_state.authed:
    st.markdown("""
    <div class="gate-box">
        <div class="gate-title">小红书<span class="gate-accent">内容</span> Agent</div>
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
    _pro_used = _get_pro_used(_code)
    _pro_left = _PRO_GEN_LIMIT - _pro_used
    st.markdown("**⭐ Pro 精品配图额度**")
    if _pro_left > 10:
        st.success(f"剩余 **{_pro_left}** / {_PRO_GEN_LIMIT} 次")
    elif _pro_left > 0:
        st.warning(f"剩余 **{_pro_left}** / {_PRO_GEN_LIMIT} 次（快用完了）")
    else:
        st.error("Pro 额度已用完")
        st.caption("联系 David 获取新额度")

    st.caption(
        "免费配图：每日500次共享额度\n"
        "Pro配图：Imagen 4，专属9:16竖图"
    )

    st.divider()
    st.caption("Demo v5.0 · 内测版\n\n遇到问题请截图反馈给 David")

    if st.button("退出登录", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ═══════════════════════════════════════════════════════
#  页面2：行业选择（10个，2行×4列 + 1行×2列）
# ═══════════════════════════════════════════════════════
st.markdown(
    "<h1 style='margin-bottom:0; font-size:2rem; font-weight:900; "
    "letter-spacing:-0.03em;'>小红书<span style='color:#FF6B00;'>内容</span> Agent</h1>",
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
        border_color = "#FF6B00" if selected else "#222222"
        bg_color = "#1E1207" if selected else "#141414"
        check = " ✓" if selected else ""
        name_color = "#FF6B00" if selected else "#FFFFFF"
        with col:
            st.markdown(
                f"""
                <div style="border:2px solid {border_color}; border-radius:12px;
                            padding:14px 10px; text-align:center; background:{bg_color};
                            min-height:110px; transition:border-color 0.2s;">
                    <div style="font-size:1.8rem;">{info['label'].split()[0]}</div>
                    <div style="font-weight:700; margin-top:4px; font-size:0.9rem; color:{name_color};">
                        {info['label'].split(' ', 1)[1]}{check}
                    </div>
                    <div style="font-size:0.72rem; color:#555555; margin-top:3px;">{info['desc']}</div>
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
            <div style="border:2px solid #FF6B00; border-radius:14px; padding:20px 16px;
                        min-height:210px; background:#1A1207;">
            <div style="font-size:2rem; text-align:center;">📋</div>
            <div style="font-weight:800; text-align:center; font-size:1rem; margin:8px 0;
                        color:#FF6B00; letter-spacing:0.02em;">
                竞品参考模式
            </div>
            <ul style="font-size:0.83rem; color:#999999; padding-left:18px; margin:0 0 12px 0; line-height:1.8;">
                <li>粘贴竞品小红书笔记链接</li>
                <li>AI 拆解爆文结构</li>
                <li>自动改写成你的风格</li>
                <li>图片去水印 / 去文字</li>
            </ul>
            <div style="font-size:0.75rem; color:#555555;">
                💡 适合：参考同行爆文、快速出内容
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='background:#1A1207; border:1px solid #2A2A2A; border-radius:8px; "
            "padding:6px 10px; font-size:0.78rem; color:#FF8C33; margin-top:4px;'>"
            "🆓 文案改写：免费 &nbsp;·&nbsp; 🆓 图片去水印：免费</div>",
            unsafe_allow_html=True,
        )
        if st.button("选择竞品参考模式 →", key="mode_sel_a", type="primary", use_container_width=True):
            st.session_state.selected_mode = "rewrite"
            st.rerun()

    with col_b:
        st.markdown(
            """
            <div style="border:2px solid #00C896; border-radius:14px; padding:20px 16px;
                        min-height:210px; background:#071A13;">
            <div style="font-size:2rem; text-align:center;">✨</div>
            <div style="font-weight:800; text-align:center; font-size:1rem; margin:8px 0;
                        color:#00C896; letter-spacing:0.02em;">
                原创生成模式
            </div>
            <ul style="font-size:0.83rem; color:#999999; padding-left:18px; margin:0 0 12px 0; line-height:1.8;">
                <li>填写你的店铺 / 业务信息</li>
                <li>AI 根据今日主题创作文案</li>
                <li>美化真实照片（免费）</li>
                <li>AI 生成配图（免费版 / Pro精品版）</li>
            </ul>
            <div style="font-size:0.75rem; color:#555555;">
                💡 适合：发原创内容、建立品牌形象
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='background:#071A13; border:1px solid #2A2A2A; border-radius:8px; "
            "padding:6px 10px; font-size:0.78rem; color:#00C896; margin-top:4px;'>"
            "🆓 文案创作：免费 &nbsp;·&nbsp; 🆓 免费AI配图 &nbsp;·&nbsp; ⭐ Pro精品配图（50次/账号）</div>",
            unsafe_allow_html=True,
        )
        if st.button("选择原创生成模式 →", key="mode_sel_b", use_container_width=True):
            st.session_state.selected_mode = "create"
            st.rerun()

    st.stop()


# 已选择模式后的状态栏
mode = st.session_state.selected_mode
mode_label = "📋 竞品参考模式" if mode == "rewrite" else "✨ 原创生成模式"

col_status, col_switch = st.columns([4, 1])
with col_status:
    st.markdown(
        f"<div style='background:#1A1207; border:1px solid #FF6B00; border-radius:8px; "
        f"padding:10px 14px; font-size:0.88rem; color:#FF8C33;'>"
        f"<strong style='color:#FF6B00;'>✓</strong>&ensp;"
        f"<strong style='color:#FFFFFF;'>{industry['label']}</strong>"
        f"&ensp;·&ensp;{mode_label}"
        f"&ensp;·&ensp;<span style='color:#888888;'>{st.session_state.city}</span>"
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
        st.session_state.store_profile = {}
        st.session_state.daily_brief = ""
        st.session_state.scene_images = []
        st.session_state.scene_prompt = ""
        st.rerun()

st.divider()


# ═══════════════════════════════════════════════════════
#  Step 1：输入内容（根据模式分流）
# ═══════════════════════════════════════════════════════

# ─── Mode A：粘贴竞品链接 ───
if mode == "rewrite":
    st.markdown('<span class="step-num">1</span> **粘贴竞品小红书笔记链接**', unsafe_allow_html=True)
    st.caption("在小红书 App 打开竞品笔记 → 分享 → 复制链接 → 粘贴到下方")

    paste_input = st.text_area(
        "粘贴分享内容",
        height=80,
        placeholder="直接粘贴，例如：宝藏健身房推荐🔥 http://xhslink.com/xxx 复制后打开小红书查看",
        label_visibility="collapsed",
    )

    col_btn, col_up = st.columns([1, 2])
    with col_btn:
        btn_extract = st.button("🚀 一键提取", type="primary", use_container_width=True)
    with col_up:
        extra_imgs = st.file_uploader(
            "补充上传图片（可选）",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
        )

    if btn_extract:
        if not paste_input.strip():
            st.warning("请先粘贴小红书分享内容")
        else:
            prog = st.progress(0, text="开始提取…")

            def _cb(pct, msg):
                prog.progress(pct, text=msg)

            title, text, img_urls, logs = try_extract_xhs(paste_input.strip(), _cb)
            prog.progress(0.7, text="下载图片中…")

            downloaded = []
            for i, u in enumerate(img_urls or []):
                prog.progress(0.7 + 0.25 * (i / max(len(img_urls), 1)),
                              text=f"下载第 {i+1}/{len(img_urls)} 张…")
                im = download_image_url(u)
                if im:
                    downloaded.append(im)

            if extra_imgs:
                for f in extra_imgs:
                    try:
                        downloaded.append(Image.open(f).convert("RGB"))
                    except Exception:
                        pass

            prog.progress(1.0, text="提取完成！")
            st.session_state.extract_log = "\n".join(logs)

            if title or text:
                st.session_state.note_title = title or ""
                st.session_state.note_text = text or ""
                st.session_state.note_images = downloaded
                st.session_state.content_ready = True
                st.session_state.rewrite_done = False
                st.session_state.images_done = False
                st.session_state.rewrite_result = ""
                st.session_state.edited_images = []

                parts = []
                if title:
                    parts.append("标题 ✓")
                if text:
                    parts.append(f"正文 ✓（{len(text)}字）")
                if downloaded:
                    parts.append(f"{len(downloaded)}张图片 ✓")
                elif img_urls:
                    parts.append(f"图片下载失败（{len(img_urls)}张，可手动上传）")
                st.success(f"提取成功！{' | '.join(parts)}")

                if not text and title:
                    st.info(
                        "💡 **正文未提取到**（小红书反爬限制）\n\n"
                        "操作：小红书 App 打开该笔记 → 长按正文 → 全选复制 → 粘贴到下方「正文」框 → 点击「更新内容」"
                    )
                if not downloaded and title:
                    st.info("💡 **图片未提取到**，可在下方手动上传原图")
                st.rerun()
            else:
                st.error("提取失败，小红书可能已限制访问")
                st.info("💡 **手动补救**：在小红书 App 打开笔记 → 长按正文 → 复制 → 粘贴到下方「正文」框")

    if st.session_state.extract_log:
        with st.expander("查看提取详情", expanded=False):
            st.code(st.session_state.extract_log, language=None)

    if st.session_state.content_ready:
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
                st.session_state.rewrite_done = False
                st.session_state.images_done = False
                st.success("内容已更新！")
                st.rerun()

            if st.session_state.note_images:
                img_cols = st.columns(min(len(st.session_state.note_images), 4))
                for i, img in enumerate(st.session_state.note_images):
                    with img_cols[i % 4]:
                        st.image(img, caption=f"原图 {i+1}", use_container_width=True)


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
            img_cols = st.columns(min(len(imgs), 4))
            for i, img in enumerate(imgs):
                with img_cols[i % 4]:
                    st.image(img, caption=f"图片 {i+1}", use_container_width=True)

    if st.button("✅ 确认，开始生成", type="primary"):
        if not brief.strip():
            st.warning("请填写今日主题")
        else:
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

    if mode == "rewrite":
        label_2 = f"AI 文案改写（{industry['label']} · {st.session_state.city}风格）"
        btn_label = "✨ 一键改写文案"
    else:
        label_2 = f"AI 原创文案生成（{industry['label']} · {st.session_state.city}风格）"
        btn_label = "✨ 一键生成文案"

    st.markdown(
        f'<span class="step-num">2</span> **{label_2}**',
        unsafe_allow_html=True,
    )
    st.caption("🆓 免费功能 · 由 DeepSeek 驱动")

    if st.button(btn_label, type="primary", key="btn_rewrite"):
        if mode == "rewrite" and not st.session_state.note_title and not st.session_state.note_text:
            st.error("标题和正文都为空，请先补充内容")
        elif mode == "create" and not st.session_state.daily_brief.strip():
            st.error("请填写今日主题")
        else:
            with st.spinner("DeepSeek 正在生成… ⏳"):
                try:
                    if mode == "rewrite":
                        result = rewrite_with_deepseek(
                            st.session_state.note_title,
                            st.session_state.note_text,
                            industry,
                            st.session_state.city,
                        )
                    else:
                        result = generate_original_content(
                            st.session_state.store_profile,
                            st.session_state.daily_brief,
                            industry,
                            st.session_state.city,
                        )
                    st.session_state.rewrite_result = result
                    st.session_state.rewrite_done = True
                    if mode == "create":
                        try:
                            dp = generate_dynamic_image_prompt(result, industry)
                            st.session_state.dynamic_image_prompt = dp
                        except Exception:
                            st.session_state.dynamic_image_prompt = ""
                    st.rerun()
                except Exception as e:
                    st.error(f"生成失败：{e}")

    if st.session_state.rewrite_done:
        if mode == "rewrite":
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**原文**")
                st.info(f"**{st.session_state.note_title}**\n\n{st.session_state.note_text}")
            with c2:
                st.markdown("**改写后**")
                st.success(st.session_state.rewrite_result)
        else:
            st.markdown("**生成结果**")
            st.success(st.session_state.rewrite_result)


# ═══════════════════════════════════════════════════════
#  Step 3：图片处理
#  Mode A：去水印（Gemini 编辑，免费）
#  Mode B：方案A 美化原图（Gemini，免费）+ 方案B AI配图（免费版 / Pro精品版）
# ═══════════════════════════════════════════════════════
if st.session_state.rewrite_done and (st.session_state.note_images or mode == "create"):
    st.divider()
    st.markdown('<span class="step-num">3</span> **图片处理**', unsafe_allow_html=True)

    # ─── Mode A：竞品参考 → 去水印/去文字（免费）───
    if mode == "rewrite":
        st.caption("🆓 免费功能 · 去除竞品水印和文字，图片内容保持不变")
        img_prompt_r = industry["image_prompt"]

        with st.expander("查看图片处理提示词", expanded=False):
            st.code(img_prompt_r, language=None)

        if st.button("🎨 一键重绘图片", type="primary", key="btn_img"):
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
            st.session_state.images_done = True
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
        _pro_used_now = _get_pro_used(_code_now)
        _pro_left_now = _PRO_GEN_LIMIT - _pro_used_now
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
                st.button("🔄 换一批（免费版）", key="btn_regen_free", use_container_width=True)

        with col_pro:
            st.markdown(f"**⭐ Pro精品版** · 9:16竖图 · 剩余 {_pro_left_now}/{_PRO_GEN_LIMIT} 次")
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
        if btn_free or (
            st.session_state.get("_regen_free_clicked")
            and st.session_state.get("scene_tier") == "free"
        ):
            with st.spinner("Gemini 正在生成… 约 10~20 秒 ⏳"):
                imgs, s_prompt, s_err = generate_scene_nano_banana(
                    st.session_state.rewrite_result, industry
                )
            if imgs:
                st.session_state.scene_images = imgs
                st.session_state.scene_prompt = s_prompt
                st.session_state["scene_tier"] = "free"
                st.success(f"生成成功！共 {len(imgs)} 张 · 1:1 方图")
            else:
                st.error(f"生成失败：{s_err}")
                if s_err and "共享" in s_err:
                    st.warning("💡 免费额度繁忙，建议换个时间段再试，或使用 Pro精品版")
            st.rerun()

        # Pro 版生图
        if btn_pro and _has_quota:
            with st.spinner("Imagen 4 Fast 正在生成… 约 15~30 秒 ⏳"):
                imgs, s_prompt, s_err = generate_scene_with_imagen4(
                    st.session_state.rewrite_result, industry
                )
            if imgs:
                _inc_pro_used(_code_now)
                st.session_state.scene_images = imgs
                st.session_state.scene_prompt = s_prompt
                st.session_state["scene_tier"] = "pro"
                new_left = _pro_left_now - 1
                st.success(f"生成成功！共 {len(imgs)} 张 · 9:16 竖图 · Pro 剩余 {new_left}/{_PRO_GEN_LIMIT} 次")
            else:
                st.error(f"生成失败：{s_err}")
            st.rerun()

        if st.session_state.scene_images:
            tier_label = "Pro精品" if st.session_state.get("scene_tier") == "pro" else "免费版"
            img_cols = st.columns(min(len(st.session_state.scene_images), 4))
            for i, img in enumerate(st.session_state.scene_images):
                with img_cols[i % 4]:
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
    c1, c2, c3 = st.columns(3)

    with c1:
        st.download_button(
            "📝 下载文案（TXT）",
            data=st.session_state.rewrite_result.encode("utf-8"),
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

    st.caption("下载后手动发布到小红书即可")


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
            st.session_state.feedback_submitted = True
            st.rerun()

elif st.session_state.feedback_submitted:
    st.divider()
    st.success("感谢反馈！David 会认真查看每一条，下一版见 👋")

# ─── 页脚 ───
st.divider()
st.caption("📱 小红书内容 Agent · Demo v5.0 · 10大行业全双模式 · 免费+Pro双档AI配图")
