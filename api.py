"""
小红书通用内容 Agent — API 模块
小红书内容提取 · DeepSeek文案 · Gemini图片 · 所有外部网络调用
"""

import io
import re
import json
import time

import requests
import streamlit as st
from PIL import Image

from config import GARBAGE_TITLES
from utils import get_api_key, make_session, log_event, friendly_api_error


# ═══════════════════════════════════════════════════════
#  URL 解析 & 内容提取
# ═══════════════════════════════════════════════════════

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


def _is_useful_title(t: str) -> bool:
    return bool(t) and t.strip() not in GARBAGE_TITLES and len(t.strip()) > 3


def _resolve_short_url(url: str) -> str:
    """展开 xhslink.com 短链接为完整URL"""
    if "xhslink.com" not in url:
        return url
    try:
        s = make_session()
        r = s.head(url, timeout=10, allow_redirects=True)
        if r.url and "xiaohongshu.com" in r.url:
            return r.url
        r = s.get(url, timeout=10, allow_redirects=True)
        return r.url
    except Exception:
        return url


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

    # 展开短链接
    if "xhslink.com" in url:
        logs.append("检测到短链接，正在展开…")
        url = _resolve_short_url(url)
        logs.append(f"展开后：{url}")

    logs.append(f"提取到链接：{url}")
    session = make_session()
    title, text, images, note_id = "", "", [], ""

    for attempt in range(2):
        try:
            if attempt > 0:
                session = make_session()
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
            s2 = make_session()
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
    log_event(
        st.session_state.get("invite_code", ""),
        "extract_link",
        industry_id=st.session_state.get("industry_id", ""),
        mode="rewrite",
        detail=json.dumps({"title_len": len(title), "text_len": len(text), "img_count": len(images)}),
        success=bool(title or text),
    )
    return title, text, images, logs


def download_image_url(url: str):
    try:
        s = make_session()
        s.headers["Referer"] = "https://www.xiaohongshu.com/"
        r = s.get(url, timeout=15)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception:
        return None


# ═══════════════════════════════════════════════════════
#  DeepSeek 文案生成
# ═══════════════════════════════════════════════════════

def rewrite_with_deepseek(title: str, text: str, industry: dict, city: str) -> str:
    """Mode A：调用 DeepSeek 改写竞品文案"""
    from openai import OpenAI
    api_key = get_api_key("DEEPSEEK_API_KEY")
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
    api_key = get_api_key("DEEPSEEK_API_KEY")
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
    api_key = get_api_key("DEEPSEEK_API_KEY")
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


# ═══════════════════════════════════════════════════════
#  Gemini / Imagen 图片生成 & 编辑
# ═══════════════════════════════════════════════════════

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
        ds_client = OpenAI(api_key=get_api_key("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
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
        return [], "", friendly_api_error(e)

    # Step 2: Gemini 2.5 Flash Image 文生图（调用2次得到2张图）
    gai_key = get_api_key("GOOGLE_API_KEY")
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
        ds_client = OpenAI(api_key=get_api_key("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
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
        return [], "", friendly_api_error(e)

    # Step 2: Imagen 4 Fast 文生图（9:16竖图）
    gai_key = get_api_key("GOOGLE_API_KEY")
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

    api_key = get_api_key("GOOGLE_API_KEY")
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
