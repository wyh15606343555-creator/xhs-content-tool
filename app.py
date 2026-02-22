"""
小红书内容智能处理工具 - Demo v2.0
一键粘贴 → 自动提取 → DeepSeek改写 → Gemini图片重绘 → 打包下载
"""

import streamlit as st
import requests
import json
import re
import io
import zipfile
import time
import random
from datetime import datetime
from PIL import Image

# ═══════════════════════════════════════════════════════
#  页面配置
# ═══════════════════════════════════════════════════════
st.set_page_config(
    page_title="小红书内容工具 - Demo",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""<style>
.block-container { padding-top: 1.5rem; }
div.stButton > button[kind="primary"] {
    background-color: #ff2442;
    border: none;
}
div.stButton > button[kind="primary"]:hover {
    background-color: #e6203c;
    border: none;
}
.step-num {
    display: inline-block;
    background: #ff2442;
    color: white;
    width: 28px; height: 28px;
    border-radius: 50%;
    text-align: center;
    line-height: 28px;
    font-weight: bold;
    font-size: 14px;
    margin-right: 6px;
}
.status-ok { color: #10b981; font-weight: bold; }
.status-partial { color: #f59e0b; font-weight: bold; }
.status-fail { color: #ef4444; font-weight: bold; }
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
#  Session State
# ═══════════════════════════════════════════════════════
_DEFAULTS = dict(
    note_title="",
    note_text="",
    note_images=[],          # list[PIL.Image]
    rewrite_result="",
    edited_images=[],        # list[PIL.Image | None]
    content_ready=False,
    rewrite_done=False,
    images_done=False,
    extract_log="",          # 提取过程日志
)
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ═══════════════════════════════════════════════════════
#  工具函数
# ═══════════════════════════════════════════════════════

def _resolve_key(user_input: str, name: str) -> str:
    """优先级：用户侧边栏输入 > Streamlit Secrets（本地secrets.toml 或 Cloud Secrets）"""
    if user_input and user_input.strip():
        return user_input.strip()
    try:
        val = st.secrets.get(name, "")
        if val:
            return val
    except Exception:
        pass
    return ""


# ── 多组UA轮换 ──
_USER_AGENTS = [
    # iPhone Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.4 Mobile/15E148 Safari/604.1",
    # Android Chrome
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.6167.178 Mobile Safari/537.36",
    # 微信内置浏览器
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
    "MicroMessenger/8.0.47(0x18002f30) NetType/WIFI Language/zh_CN",
    # iPad Safari
    "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.4 Mobile/15E148 Safari/604.1",
]


def _make_session():
    """创建一个带完整浏览器指纹的 requests Session"""
    s = requests.Session()
    ua = random.choice(_USER_AGENTS)
    s.headers.update({
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    })
    return s


def _extract_url(raw: str) -> str:
    """从小红书分享文本中提取URL"""
    m = re.search(r'https?://[^\s，,、!！\]】]+', raw)
    return m.group(0).rstrip('.,;:!?。，；：！？') if m else raw.strip()


def _extract_share_title(raw: str) -> str:
    """从分享文本中提取标题（URL前面的文字部分）"""
    m = re.search(r'https?://', raw)
    if not m:
        return ""
    before = raw[:m.start()].strip()
    # 清理常见前缀/后缀噪音
    before = re.sub(r'^\d+\s*', '', before)  # 去掉开头数字
    before = before.rstrip('.,。，…、 ')
    # 如果太短可能只是噪音
    if len(before) < 4:
        return ""
    return before


# 无用的标题（只是小红书站名，不是笔记内容）
_GARBAGE_TITLES = {"小红书", "小红书 - 你的生活指南", "发现 - 小红书", ""}


def _is_useful_title(t: str) -> bool:
    """判断标题是否有实际内容（而不是网站名称）"""
    return bool(t) and t.strip() not in _GARBAGE_TITLES and len(t.strip()) > 3


# ── 图片重绘预设模式 ──
_IMAGE_PROMPT_PRESETS = {
    "去除文字水印（推荐）": (
        "Remove ALL text, titles, captions, watermarks, logos, and any overlaid "
        "text or graphics from this image completely. "
        "Reconstruct the areas behind the removed text naturally using the "
        "surrounding visual context. "
        "Do NOT change any people, faces, objects, poses, clothing, or the background. "
        "The output should look like the original clean photo without any text overlays."
    ),
    "去文字 + 暖色调微调": (
        "Edit this image with these specific changes: "
        "1) Remove ALL text, watermarks, logos, and overlaid graphics completely. "
        "2) Adjust the overall color temperature to be slightly warmer and brighter. "
        "3) Add a subtle professional lighting enhancement. "
        "Keep all people, faces, objects, poses, and the scene exactly the same."
    ),
    "转为手绘插画风格": (
        "Transform this photograph into a clean, modern digital illustration: "
        "- Remove all text, watermarks, and overlaid graphics. "
        "- Convert the realistic photo into a stylized hand-drawn illustration. "
        "- Use bright, warm, inviting color palette. "
        "- Maintain the same composition, people's poses, and activities. "
        "- Style: professional fitness and wellness brand illustration."
    ),
    "更换人物外观（全身重绘）": (
        "Replace the main person in this image with a completely different person: "
        "- Generate a new person with different facial features, hairstyle, and body build. "
        "- The new person should wear similar style athletic clothing but in different colors. "
        "- Maintain the same general pose and activity. "
        "- Remove all text, watermarks, and overlaid graphics. "
        "- Keep the background and setting unchanged. "
        "- The result must look like a natural, professional fitness photograph."
    ),
    "自定义提示词": "",
}


def try_extract_xhs(raw_input: str, progress_callback=None):
    """
    增强版提取：多策略尝试。
    返回 (title, text, image_urls, log_messages)
    """
    logs = []
    url = _extract_url(raw_input)
    share_title = _extract_share_title(raw_input)

    if share_title:
        logs.append(f"从分享文本识别到标题片段：「{share_title[:40]}」")

    if not url.startswith("http"):
        logs.append("未找到有效链接")
        return share_title, "", [], logs

    logs.append(f"提取到链接：{url}")

    # ── 策略1：带完整浏览器指纹的Session请求 ──
    if progress_callback:
        progress_callback(0.1, "策略1：模拟手机浏览器访问…")

    session = _make_session()
    title, text, images = "", "", []

    for attempt in range(2):
        try:
            if attempt > 0:
                session = _make_session()  # 换一个UA重试
                time.sleep(0.5)
                logs.append(f"重试第{attempt + 1}次（更换浏览器指纹）")

            resp = session.get(url, timeout=15, allow_redirects=True)
            final_url = resp.url
            logs.append(f"最终URL：{final_url}（状态码 {resp.status_code}）")

            if resp.status_code != 200:
                continue

            html = resp.text

            # 提取 note_id 备用
            note_id = ""
            nid = re.search(r'/(?:explore|discovery/item)/([a-f0-9]{24})', final_url)
            if nid:
                note_id = nid.group(1)
                logs.append(f"笔记ID：{note_id}")

            # ── 方法A：og tags ──
            t = re.search(
                r'<meta[^>]+property="og:title"[^>]+content="([^"]*)"', html
            )
            if not t:
                t = re.search(
                    r'<meta[^>]+content="([^"]*)"[^>]+property="og:title"', html
                )
            if t:
                title = t.group(1)

            for pattern in [
                r'<meta[^>]+property="og:description"[^>]+content="([^"]*)"',
                r'<meta[^>]+name="description"[^>]+content="([^"]*)"',
                r'<meta[^>]+content="([^"]*)"[^>]+property="og:description"',
            ]:
                d = re.search(pattern, html)
                if d and len(d.group(1)) > len(text):
                    text = d.group(1)

            for m in re.finditer(
                r'<meta[^>]+property="og:image"[^>]+content="([^"]*)"', html
            ):
                img_url = m.group(1)
                if img_url and img_url not in images:
                    images.append(img_url)
            # 也尝试反向属性顺序
            for m in re.finditer(
                r'<meta[^>]+content="([^"]*)"[^>]+property="og:image"', html
            ):
                img_url = m.group(1)
                if img_url and img_url not in images:
                    images.append(img_url)

            if (_is_useful_title(title) and text) or (text and len(text) > 10) or (images and len(images) > 0):
                logs.append(f"og:tags 提取成功 ✓（标题{len(title)}字，正文{len(text)}字，{len(images)}张图）")
                break
            elif title or text:
                logs.append(f"og:tags 有部分数据（标题{len(title)}字，正文{len(text)}字，{len(images)}张图），继续尝试…")

            # ── 方法B：__INITIAL_STATE__ ──
            state = re.search(
                r'window\.__INITIAL_STATE__\s*=\s*(\{.+?\})\s*</script>',
                html, re.DOTALL,
            )
            if state:
                raw_json = re.sub(r":\s*undefined", ": null", state.group(1))
                try:
                    data = json.loads(raw_json)
                    _note = None

                    # 路径1（新版）: noteData.data.noteData
                    nd = data.get("noteData", {})
                    nd_inner = nd.get("data", {}).get("noteData", {})
                    if nd_inner and nd_inner.get("title"):
                        _note = nd_inner

                    # 路径1b: normalNotePreloadData（备用）
                    if not _note:
                        preload = nd.get("normalNotePreloadData", {})
                        if preload and preload.get("title"):
                            _note = preload

                    # 路径2（旧版）: note.noteDetailMap
                    if not _note:
                        note_map = data.get("note", {}).get("noteDetailMap", {})
                        if note_map:
                            _note = list(note_map.values())[0].get("note", {})

                    if _note and (_note.get("title") or _note.get("desc")):
                        title = _note.get("title", "") or title
                        text = _note.get("desc", "") or text
                        # 提取图片（兼容多种字段名）
                        img_list = _note.get("imageList", []) or _note.get("imagesList", [])
                        for img in img_list:
                            u = (img.get("url", "")
                                 or img.get("urlDefault", "")
                                 or img.get("urlSizeLarge", ""))
                            if u and u not in images:
                                images.append(u)
                        logs.append(
                            f"INITIAL_STATE 提取成功 ✓"
                            f"（标题{len(title)}字，正文{len(text)}字，{len(images)}张图）"
                        )
                        break
                    else:
                        logs.append(f"INITIAL_STATE 存在但未找到笔记数据（keys: {list(data.keys())}）")
                except json.JSONDecodeError:
                    logs.append("INITIAL_STATE JSON解析失败")

            # ── 方法C：从HTML正文提取更多线索 ──
            title_tag = re.search(r'<title[^>]*>([^<]+)</title>', html)
            if title_tag and not _is_useful_title(title):
                raw_title = title_tag.group(1).strip()
                # 去掉 " - 小红书" 后缀
                raw_title = re.sub(r'\s*[-–—|]\s*小红书.*$', '', raw_title)
                if _is_useful_title(raw_title):
                    title = raw_title
                    logs.append(f"从 <title> 标签提取标题：「{title[:30]}」")
                else:
                    logs.append(f"<title> 标签内容无用：「{raw_title}」，跳过")

        except requests.exceptions.Timeout:
            logs.append(f"第{attempt + 1}次请求超时")
        except Exception as e:
            logs.append(f"第{attempt + 1}次请求异常：{type(e).__name__}")

    # ── 策略2：如果笔记ID可用，尝试XHS web API ──
    if not title and not text and note_id:
        if progress_callback:
            progress_callback(0.5, "策略2：尝试API接口…")
        try:
            api_url = f"https://www.xiaohongshu.com/explore/{note_id}"
            session2 = _make_session()
            session2.headers["Referer"] = "https://www.xiaohongshu.com/"
            resp2 = session2.get(api_url, timeout=15, allow_redirects=True)
            if resp2.status_code == 200:
                html2 = resp2.text
                t2 = re.search(
                    r'<meta[^>]+property="og:title"[^>]+content="([^"]*)"', html2
                )
                if t2:
                    title = t2.group(1)
                d2 = re.search(
                    r'<meta[^>]+(?:property="og:description"|name="description")[^>]+content="([^"]*)"',
                    html2,
                )
                if d2:
                    text = d2.group(1)
                for m2 in re.finditer(
                    r'<meta[^>]+property="og:image"[^>]+content="([^"]*)"', html2
                ):
                    if m2.group(1) not in images:
                        images.append(m2.group(1))
                if title or text:
                    logs.append(f"API策略提取成功 ✓")
        except Exception:
            logs.append("API策略未成功")

    # ── 最终兜底：优先使用分享文本中更完整的标题 ──
    if share_title and (not _is_useful_title(title) or len(share_title) > len(title) * 2):
        logs.append(f"使用分享文本中的完整标题（优于网页标题「{title}」）")
        title = share_title

    if title or text:
        logs.append(f"最终结果：标题{len(title)}字，正文{len(text)}字，{len(images)}张图片")
    else:
        logs.append("所有策略均未成功提取到内容")

    return title, text, images, logs


def download_image_url(url: str):
    """下载图片返回 PIL Image"""
    try:
        session = _make_session()
        session.headers["Referer"] = "https://www.xiaohongshu.com/"
        r = session.get(url, timeout=15)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception:
        return None


def rewrite_with_deepseek(api_key: str, title: str, text: str, track: str, city: str) -> str:
    """调用 DeepSeek 改写文案"""
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    system = f"""你是专业的小红书文案改写专家。

改写规则：
1. 保留原文核心卖点和信息结构
2. 完全更换表达方式，改写率 > 70%
3. 赛道风格：{track}
4. 保持小红书写作风格（口语化、有感染力、适当使用 emoji）
5. 保留并优化话题标签（#xxx#）
6. 融入{city}本地元素（地标、商圈、区域名）
7. 标题要有吸引力，适合小红书搜索

请严格按以下格式输出：
【标题】改写后的标题
【正文】改写后的正文"""

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


def edit_image_with_gemini(api_key: str, image: Image.Image, prompt: str):
    """调用 Google Gemini API 编辑图片"""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    # 缩小图片以减少传输量和处理时间
    img_copy = image.copy()
    img_copy.thumbnail((1024, 1024))

    buf = io.BytesIO()
    img_copy.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    # 按优先级尝试多个模型（新 → 旧）
    models = [
        "gemini-2.5-flash-preview-04-17",          # Gemini 2.5 Flash（最新preview）
        "gemini-2.5-flash-image",                   # Gemini 2.5 Flash Image
        "gemini-2.0-flash-exp-image-generation",    # 旧版fallback
    ]

    last_error = None
    for model_name in models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
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
                        and hasattr(part.inline_data, "mime_type")
                        and part.inline_data.mime_type
                        and part.inline_data.mime_type.startswith("image/")
                    ):
                        st.toast(f"使用模型: {model_name}", icon="✅")
                        return Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
            # 有响应但无图片
            last_error = f"{model_name}: 返回了响应但无图片数据"
        except Exception as e:
            err_msg = str(e)
            if "leaked" in err_msg.lower():
                last_error = f"{model_name}: API Key已泄露，请更换"
            elif "404" in err_msg:
                last_error = f"{model_name}: 模型不可用"
            else:
                last_error = f"{model_name}: {err_msg[:100]}"
            continue

    # 所有模型都失败
    if last_error:
        st.toast(f"图片重绘失败: {last_error}", icon="❌")
    return None


def make_zip(title: str, text: str, images: list) -> io.BytesIO:
    """打包文案 + 图片为 ZIP"""
    buf = io.BytesIO()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"文案_{ts}.txt", f"{title}\n\n{text}".encode("utf-8"))
        for i, img in enumerate(images):
            ib = io.BytesIO()
            img.save(ib, format="JPEG", quality=95)
            zf.writestr(f"图片_{i + 1}.jpg", ib.getvalue())
    buf.seek(0)
    return buf


# ═══════════════════════════════════════════════════════
#  侧边栏
# ═══════════════════════════════════════════════════════
with st.sidebar:
    st.title("⚙️ 设置")

    # 检测 Secrets 中是否已有配置
    def _has_secret(name):
        try:
            return bool(st.secrets.get(name, ""))
        except Exception:
            return False

    _has_ds = _has_secret("DEEPSEEK_API_KEY")
    _has_gg = _has_secret("GOOGLE_API_KEY")

    _ds_input = st.text_input(
        "DeepSeek API Key",
        value="",
        type="password",
        placeholder="已从Secrets读取 ✓" if _has_ds else "请输入DeepSeek API Key",
        help="在 Streamlit Secrets 中配置 DEEPSEEK_API_KEY，或直接粘贴到此处",
    )
    deepseek_key = _resolve_key(_ds_input, "DEEPSEEK_API_KEY")

    _gg_input = st.text_input(
        "Google Gemini API Key",
        value="",
        type="password",
        placeholder="已从Secrets读取 ✓" if _has_gg else "请输入Google API Key",
        help="在 Google AI Studio 生成 → 粘贴到此处，或在 Streamlit Secrets 中配置 GOOGLE_API_KEY",
    )
    google_key = _resolve_key(_gg_input, "GOOGLE_API_KEY")

    st.divider()

    track = st.selectbox("🏃 赛道", ["上门私教", "产后恢复", "青少年体育（长高）"])
    city = st.text_input("📍 城市", value="北京")

    st.divider()

    prompt_mode = st.selectbox(
        "🎨 图片重绘模式",
        list(_IMAGE_PROMPT_PRESETS.keys()),
        index=0,
    )

    if prompt_mode == "自定义提示词":
        image_prompt = st.text_area(
            "自定义提示词",
            value="",
            height=100,
            placeholder="描述你想要的图片编辑效果…",
        )
    else:
        image_prompt = _IMAGE_PROMPT_PRESETS[prompt_mode]
        with st.expander("查看提示词内容"):
            st.caption(image_prompt)

    st.divider()
    st.caption("Demo v2.0 | 技术支持：David")


# ═══════════════════════════════════════════════════════
#  主页面
# ═══════════════════════════════════════════════════════

st.title("📱 小红书内容智能处理工具")
st.caption("粘贴分享文本 → 自动提取 → 改写文案 → 图片重绘 → 打包下载")
st.divider()

# ─────────────────────────────────────────
#  第一步：粘贴内容（一个框搞定）
# ─────────────────────────────────────────
st.markdown(
    '<span class="step-num">1</span> <b>粘贴小红书笔记</b>',
    unsafe_allow_html=True,
)

st.markdown(
    "**操作方法：** 在小红书App中打开笔记 → 点击「分享」→「复制链接」→ 粘贴到下方输入框",
)

paste_input = st.text_area(
    "粘贴分享内容",
    height=80,
    placeholder='直接粘贴，例如：北京火爆的上门体育到家🔥 http://xhslink.com/xxx 复制后打开【小红书】查看笔记!',
    key="paste_box",
    label_visibility="collapsed",
)

col_extract, col_upload = st.columns([1, 2])
with col_extract:
    btn_extract = st.button("🚀 一键提取", type="primary", key="btn_extract", use_container_width=True)
with col_upload:
    extra_imgs = st.file_uploader(
        "补充上传图片（可选，可多选）",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key="extra_imgs",
    )

# ── 提取逻辑 ──
if btn_extract:
    if not paste_input.strip():
        st.warning("请先粘贴小红书分享内容")
    else:
        progress = st.progress(0, text="开始提取…")

        def _progress(pct, msg):
            progress.progress(pct, text=msg)

        title, text, img_urls, logs = try_extract_xhs(paste_input.strip(), _progress)

        progress.progress(0.7, text="下载图片中…")

        # 下载图片
        downloaded_imgs = []
        for i, u in enumerate(img_urls or []):
            progress.progress(
                0.7 + 0.25 * (i / max(len(img_urls), 1)),
                text=f"下载第 {i + 1}/{len(img_urls)} 张图片…",
            )
            im = download_image_url(u)
            if im:
                downloaded_imgs.append(im)

        # 加上用户额外上传的图片
        if extra_imgs:
            for f in extra_imgs:
                try:
                    downloaded_imgs.append(Image.open(f).convert("RGB"))
                except Exception:
                    pass

        progress.progress(1.0, text="提取完成！")

        # 保存提取日志
        st.session_state.extract_log = "\n".join(logs)

        # 判断结果
        has_title = bool(title)
        has_text = bool(text)
        has_imgs = len(downloaded_imgs) > 0

        if has_title or has_text:
            st.session_state.note_title = title or ""
            st.session_state.note_text = text or ""
            st.session_state.note_images = downloaded_imgs
            st.session_state.content_ready = True
            st.session_state.rewrite_done = False
            st.session_state.images_done = False
            st.session_state.rewrite_result = ""
            st.session_state.edited_images = []

            # 显示结果摘要
            parts = []
            if has_title:
                parts.append("标题 ✓")
            if has_text:
                parts.append(f"正文 ✓（{len(text)}字）")
            if has_imgs:
                parts.append(f"{len(downloaded_imgs)}张图片 ✓")
            elif img_urls:
                parts.append(f"图片下载失败（{len(img_urls)}张）")

            st.success(f"提取成功！ {' | '.join(parts)}")

            if not has_text and has_title:
                st.info(
                    "💡 正文未提取到（小红书云端反爬限制），但标题已获取。\n\n"
                    "**操作方法：** 在小红书App中打开该笔记 → 长按正文 → 全选 → 复制 → "
                    "粘贴到下方「正文」框中 → 点击「更新内容」→ 继续改写"
                )
            if not has_imgs and has_title:
                st.info(
                    "💡 图片未提取到，可在下方「补充/替换图片」处手动上传原图。\n\n"
                    "**操作方法：** 在小红书App中长按图片 → 保存到手机 → 传到电脑 → 上传"
                )

            st.rerun()
        else:
            st.error("提取失败")
            st.info(
                "💡 **解决方法：** 在小红书App中打开笔记，"
                "长按选中正文文字 → 复制 → 粘贴到下方「补充正文」框中"
            )

# ── 提取日志（折叠显示） ──
if st.session_state.extract_log:
    with st.expander("查看提取过程详情", expanded=False):
        st.code(st.session_state.extract_log, language=None)

# ─────────────────────────────────────────
#  内容预览 & 补充编辑
# ─────────────────────────────────────────
if st.session_state.content_ready:
    with st.expander("📋 已提取的内容（可编辑补充）", expanded=True):
        edit_title = st.text_input(
            "标题",
            value=st.session_state.note_title,
            key="edit_title",
        )
        edit_text = st.text_area(
            "正文",
            value=st.session_state.note_text,
            height=150,
            key="edit_text",
            placeholder="如果正文未提取到，从小红书App中复制正文粘贴到这里…",
        )

        # 补充上传图片
        add_imgs = st.file_uploader(
            "补充/替换图片（可选，可多选）",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            key="add_imgs",
        )

        if st.button("💾 更新内容", key="btn_update"):
            st.session_state.note_title = edit_title.strip()
            st.session_state.note_text = edit_text.strip()
            if add_imgs:
                new_imgs = []
                for f in add_imgs:
                    try:
                        new_imgs.append(Image.open(f).convert("RGB"))
                    except Exception:
                        pass
                if new_imgs:
                    st.session_state.note_images = new_imgs
            st.session_state.rewrite_done = False
            st.session_state.images_done = False
            st.success("内容已更新！")
            st.rerun()

        # 显示已有图片
        if st.session_state.note_images:
            cols = st.columns(min(len(st.session_state.note_images), 4))
            for i, img in enumerate(st.session_state.note_images):
                with cols[i % 4]:
                    st.image(img, caption=f"原图 {i + 1}", use_container_width=True)

    # ─────────────────────────────────────────
    #  第二步：AI 文案改写
    # ─────────────────────────────────────────
    st.divider()
    st.markdown(
        '<span class="step-num">2</span> <b>AI 文案改写（DeepSeek）</b>',
        unsafe_allow_html=True,
    )

    col_btn, col_tag = st.columns([1, 3])
    with col_btn:
        do_rewrite = st.button("🚀 一键改写", type="primary", key="btn_rewrite")
    with col_tag:
        st.caption(f"赛道：{track}　|　城市：{city}")

    if do_rewrite:
        if not st.session_state.note_title and not st.session_state.note_text:
            st.error("标题和正文都为空，请先补充内容")
        elif not deepseek_key:
            st.error("请在左侧栏填入 DeepSeek API Key")
        else:
            with st.spinner("DeepSeek 正在改写文案… ⏳"):
                try:
                    result = rewrite_with_deepseek(
                        deepseek_key,
                        st.session_state.note_title,
                        st.session_state.note_text,
                        track,
                        city,
                    )
                    st.session_state.rewrite_result = result
                    st.session_state.rewrite_done = True
                    st.rerun()
                except Exception as e:
                    st.error(f"改写失败：{e}")

    if st.session_state.rewrite_done:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📄 原文**")
            st.info(
                f"**{st.session_state.note_title}**\n\n"
                f"{st.session_state.note_text}"
            )
        with col2:
            st.markdown("**✨ 改写后**")
            st.success(st.session_state.rewrite_result)

    # ─────────────────────────────────────────
    #  第三步：图片重绘
    # ─────────────────────────────────────────
    if st.session_state.rewrite_done and st.session_state.note_images:
        st.divider()
        st.markdown(
            '<span class="step-num">3</span> <b>图片智能重绘（Google Gemini）</b>',
            unsafe_allow_html=True,
        )

        with st.expander("当前重绘提示词", expanded=False):
            st.code(image_prompt, language=None)

        if st.button("🎨 一键重绘图片", type="primary", key="btn_img"):
            if not google_key:
                st.error("请在左侧栏填入 Google Gemini API Key")
            else:
                n = len(st.session_state.note_images)
                progress = st.progress(0, text="准备重绘…")
                edited = []

                for i, img in enumerate(st.session_state.note_images):
                    progress.progress(
                        i / n,
                        text=f"正在重绘第 {i + 1}/{n} 张…",
                    )
                    result = edit_image_with_gemini(google_key, img, image_prompt)
                    edited.append(result)

                progress.progress(1.0, text="✅ 重绘完成！")
                st.session_state.edited_images = edited
                st.session_state.images_done = True
                st.rerun()

        if st.session_state.images_done:
            for i, (orig, edited) in enumerate(
                zip(st.session_state.note_images, st.session_state.edited_images)
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.image(orig, caption=f"原图 {i + 1}", use_container_width=True)
                with col2:
                    if edited:
                        st.image(edited, caption=f"重绘后 {i + 1}", use_container_width=True)
                    else:
                        st.warning(f"图片 {i + 1} 重绘失败，可尝试调整提示词重试")

    # ─────────────────────────────────────────
    #  第四步：打包下载
    # ─────────────────────────────────────────
    if st.session_state.rewrite_done:
        st.divider()
        st.markdown(
            '<span class="step-num">4</span> <b>打包下载</b>',
            unsafe_allow_html=True,
        )

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.download_button(
                "📝 下载改写文案",
                data=st.session_state.rewrite_result.encode("utf-8"),
                file_name=f"改写文案_{ts}.txt",
                mime="text/plain",
            )

        with col2:
            if st.session_state.images_done:
                good_imgs = [
                    img
                    for img in st.session_state.edited_images
                    if img is not None
                ]
                if good_imgs:
                    zip_data = make_zip(
                        st.session_state.rewrite_result[:60],
                        st.session_state.rewrite_result,
                        good_imgs,
                    )
                    st.download_button(
                        "📦 下载全部（ZIP）",
                        data=zip_data,
                        file_name=f"小红书内容_{ts}.zip",
                        mime="application/zip",
                    )

        with col3:
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
                )

# ─────────────────────────────────────────
#  页脚
# ─────────────────────────────────────────
st.divider()
st.caption(
    "💡 使用流程：小红书App → 分享 → 复制链接 → 粘贴到上方 → 一键提取"
)
