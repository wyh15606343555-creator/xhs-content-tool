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


# ═══════════════════════════════════════════════════════
#  Claude 文案生成（企业版专属）
# ═══════════════════════════════════════════════════════

def rewrite_with_claude(title: str, text: str, industry: dict, city: str) -> str:
    """企业版 Mode A：调用 Claude 改写竞品文案"""
    import anthropic
    api_key = get_api_key("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("未配置 ANTHROPIC_API_KEY，请联系管理员")
    client = anthropic.Anthropic(api_key=api_key)
    system = industry["system_prompt"] + f"\n\n目标城市：{city}"
    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=system,
        messages=[
            {"role": "user", "content": f"原标题：{title}\n\n原正文：{text}"},
        ],
        temperature=0.8,
    )
    return resp.content[0].text


def generate_original_with_claude(store_profile: dict, brief: str, industry: dict, city: str) -> str:
    """企业版 Mode B：调用 Claude 根据店铺信息生成原创文案"""
    import anthropic
    api_key = get_api_key("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("未配置 ANTHROPIC_API_KEY，请联系管理员")
    client = anthropic.Anthropic(api_key=api_key)

    lines = []
    for field in industry.get("profile_fields", []):
        val = store_profile.get(field["key"], "").strip()
        if val:
            lines.append(f"{field['label']}：{val}")
    store_info = "\n".join(lines) if lines else "（未填写店铺信息）"

    system = industry["create_system_prompt"] + f"\n\n目标城市：{city}"
    user_content = f"店铺信息：\n{store_info}\n\n今日发帖主题：{brief}"

    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=system,
        messages=[
            {"role": "user", "content": user_content},
        ],
        temperature=0.85,
    )
    return resp.content[0].text


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
        "3. CRITICAL: Do NOT change, alter, or replace the main product/subject in the photo. "
        "Keep the exact same product shape, color, design, logo, packaging, and all visual details. "
        "Only enhance the surrounding lighting, background atmosphere, and color grading.\n"
        "4. Do NOT change composition, perspective, or add/remove any objects.\n"
        "5. Always include: 'Remove any text overlays or watermarks.'\n"
        "6. Keep the result realistic and natural — not AI-generated looking.\n"
        "7. Output: 3-5 English sentences only. No Chinese, no explanations.\n\n"
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
    """体验版/达人版：Imagen 4 Fast 文生图（9:16竖图）
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
                {"role": "system", "content": _build_scene_system_prompt(industry, is_pro=True)},
                {"role": "user", "content": f"Post content:\n{copy_text[:500]}"},
            ],
            temperature=0.6,
            max_tokens=180,
        )
        scene_prompt = ds_resp.choices[0].message.content.strip()
    except Exception as e:
        return [], "", friendly_api_error(e)

    # Step 2: Imagen 4 Fast 文生图（一次请求2张，9:16竖图）
    gai_key = get_api_key("GOOGLE_API_KEY")
    if not gai_key:
        return [], scene_prompt, "未配置 Google API Key"

    g_client = genai.Client(api_key=gai_key)
    images = []
    last_err = ""
    try:
        response = g_client.models.generate_images(
            model="imagen-4.0-fast-generate-001",
            prompt=scene_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=2,
                aspect_ratio="9:16",
                person_generation="allow_adult",
            ),
        )
        for gen_img in response.generated_images:
            images.append(Image.open(io.BytesIO(gen_img.image.image_bytes)).convert("RGB"))
    except Exception as e:
        err = str(e)
        if "quota" in err.lower() or "429" in err:
            last_err = "配图额度已用完，请稍后再试或升级会员"
        elif "not found" in err.lower() or "404" in err:
            last_err = "图片引擎暂不可用，请确认 API Key 已开通图片生成权限"
        else:
            last_err = f"生成失败：{err[:150]}"

    if images:
        return images, scene_prompt, ""
    return [], scene_prompt, last_err or "图片引擎未返回图片数据"


def generate_scene_with_imagen4(copy_text: str, industry: dict) -> tuple:
    """商家版：Imagen 4 Ultra 文生图（9:16竖图，最高画质，消耗Pro配额）
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

    # Step 2: Imagen 4 Ultra 文生图（一次请求2张，9:16竖图）
    gai_key = get_api_key("GOOGLE_API_KEY")
    if not gai_key:
        return [], scene_prompt, "未配置 Google API Key"

    g_client = genai.Client(api_key=gai_key)
    images = []
    last_err = ""
    try:
        response = g_client.models.generate_images(
            model="imagen-4.0-ultra-generate-001",
            prompt=scene_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=2,
                aspect_ratio="9:16",
                person_generation="allow_adult",
            ),
        )
        for gen_img in response.generated_images:
            images.append(Image.open(io.BytesIO(gen_img.image.image_bytes)).convert("RGB"))
    except Exception as e:
        err = str(e)
        if "quota" in err.lower() or "429" in err:
            last_err = "API 配额不足，请稍后重试"
        elif "not found" in err.lower() or "404" in err:
            last_err = "高级图片引擎暂不可用，请确认 API Key 已开通图片生成权限"
        else:
            last_err = f"生成失败：{err[:150]}"

    if images:
        return images, scene_prompt, ""
    return [], scene_prompt, last_err or "高级图片引擎未返回图片数据"


def stealth_anti_hash(image: Image.Image) -> Image.Image:
    """隐形防查重：肉眼看不出变化，但改变图片数字指纹。
    不翻转、不变色、不改变商品外观。零 API 成本，100% 成功率。
    """
    import random
    import numpy as np
    from PIL import ImageFilter

    img = image.copy()
    w, h = img.size

    # 1. 去除所有 EXIF 元数据（新建干净图片）
    clean = Image.new("RGB", (w, h))
    clean.paste(img)
    img = clean

    # 2. 轻微裁边 2-3%（肉眼几乎看不出，但尺寸和像素都变了）
    crop_px = max(2, int(min(w, h) * random.uniform(0.02, 0.03)))
    img = img.crop((crop_px, crop_px, w - crop_px, h - crop_px))

    # 3. 微缩放（改变分辨率，±2% 以内）
    new_w = int(img.width * random.uniform(0.98, 1.02))
    new_h = int(img.height * random.uniform(0.98, 1.02))
    img = img.resize((new_w, new_h), Image.LANCZOS)

    # 4. 隐形噪点（±2 像素值，肉眼完全不可见）
    arr = np.array(img, dtype=np.int16)
    noise = np.random.randint(-2, 3, arr.shape, dtype=np.int16)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)

    # 5. 极轻微模糊（radius=0.3，几乎不可见但改变像素指纹）
    img = img.filter(ImageFilter.GaussianBlur(radius=0.3))

    # 6. 背景模糊（只模糊背景，突出主体）
    try:
        from rembg import remove as rembg_remove
        # 获取前景蒙版（RGBA，A通道=前景mask）
        fg_rgba = rembg_remove(img)
        mask = fg_rgba.split()[-1]  # Alpha 通道作为前景蒙版
        # 背景微模糊（10%≈radius 1.5，轻微虚化不影响观感）
        bg_blur = img.filter(ImageFilter.GaussianBlur(radius=1.5))
        # 合成：前景清晰 + 背景模糊
        img = Image.composite(img, bg_blur, mask)
    except Exception:
        pass  # rembg 不可用时跳过背景模糊

    return img


def remove_watermark_and_protect(image: Image.Image) -> tuple:
    """去水印 + 隐形防查重（两步组合）。
    第1步：Gemini AI 去除小红书水印
    第2步：隐形防查重（不翻转、不变色）
    返回 (处理后的图片 PIL.Image | None, error_msg: str)
    """
    # 专门针对小红书水印的提示词
    watermark_prompt = (
        "Remove the semi-transparent white Chinese text watermark '小红书' "
        "(which means 'Xiaohongshu') from the center of this image. "
        "The watermark is white/light colored text overlaid on the image. "
        "Carefully reconstruct the area behind the watermark to match the surrounding content. "
        "IMPORTANT: Do NOT flip, mirror, or rotate the image. "
        "Do NOT change any colors of clothing, products, or objects. "
        "Do NOT add any new elements. "
        "Keep everything else exactly the same — only remove the watermark text. "
        "The result should look like the original photo without any text overlay."
    )

    # 第1步：Gemini 去水印
    cleaned, err = edit_image_with_gemini(image, watermark_prompt)

    if cleaned:
        # 第2步：隐形防查重
        result = stealth_anti_hash(cleaned)
        return result, ""
    else:
        # Gemini 失败时，仍然做隐形防查重（至少改变指纹）
        fallback = stealth_anti_hash(image)
        return fallback, f"去水印未成功（{err}），已完成隐形防查重"


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
            last_error = "图片引擎：返回响应但无图片数据"
        except Exception as e:
            err = str(e)
            if "404" in err:
                last_error = "图片引擎：模型暂不可用"
            elif "quota" in err.lower():
                last_error = "图片引擎配额已用尽，请稍后重试"
            else:
                last_error = f"图片引擎：{err[:120]}"

    return None, last_error
