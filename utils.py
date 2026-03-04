"""
小红书通用内容 Agent — 工具模块
数据库 · 认证 · Pro配额 · ZIP打包 · 辅助函数
"""

import io
import re
import json
import random
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st
from PIL import Image

from config import DB_PATH, PRO_GEN_LIMIT, ADMIN_CODES, USER_AGENTS


# ═══════════════════════════════════════════════════════
#  SQLite 数据库
# ═══════════════════════════════════════════════════════

def _get_db() -> sqlite3.Connection:
    """获取数据库连接（带自动建表）"""
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _init_tables(conn)
    return conn


def _init_tables(conn: sqlite3.Connection):
    """建表（如果不存在）"""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS quota_usage (
            invite_code  TEXT PRIMARY KEY,
            pro_gen_used INTEGER DEFAULT 0,
            updated_at   TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS generation_history (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            invite_code  TEXT NOT NULL,
            industry_id  TEXT NOT NULL,
            mode         TEXT NOT NULL,
            input_title  TEXT DEFAULT '',
            input_text   TEXT DEFAULT '',
            input_profile TEXT DEFAULT '',
            output_text  TEXT DEFAULT '',
            image_count  INTEGER DEFAULT 0,
            image_tier   TEXT DEFAULT '',
            city         TEXT DEFAULT '',
            created_at   TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS feedback (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            invite_code  TEXT NOT NULL,
            rating       TEXT NOT NULL,
            feedback_text TEXT DEFAULT '',
            industry_id  TEXT DEFAULT '',
            mode         TEXT DEFAULT '',
            created_at   TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS event_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            invite_code  TEXT NOT NULL,
            event_type   TEXT NOT NULL,
            industry_id  TEXT DEFAULT '',
            mode         TEXT DEFAULT '',
            detail       TEXT DEFAULT '',
            success      INTEGER DEFAULT 1,
            created_at   TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_event_log_type ON event_log(event_type);
        CREATE INDEX IF NOT EXISTS idx_event_log_code ON event_log(invite_code);
        CREATE INDEX IF NOT EXISTS idx_history_code ON generation_history(invite_code);
    """)
    # 一次性迁移旧 /tmp/ 数据（如果存在）
    old_dir = Path(tempfile.gettempdir()) / "xhs_agent_v5_usage"
    if old_dir.exists():
        for f in old_dir.glob("*.json"):
            try:
                code = f.stem.upper()
                old_val = json.loads(f.read_text()).get("pro_gen", 0)
                if old_val > 0:
                    conn.execute(
                        "INSERT OR IGNORE INTO quota_usage (invite_code, pro_gen_used) VALUES (?, ?)",
                        (code, old_val),
                    )
            except Exception:
                pass
        conn.commit()


@st.cache_resource
def init_db():
    """应用启动时初始化一次数据库"""
    conn = _get_db()
    conn.close()


def log_event(invite_code: str, event_type: str, industry_id: str = "",
              mode: str = "", detail: str = "", success: bool = True):
    """记录一条事件日志（埋点）"""
    conn = None
    try:
        conn = _get_db()
        conn.execute(
            "INSERT INTO event_log (invite_code, event_type, industry_id, mode, detail, success) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (invite_code, event_type, industry_id, mode, detail, 1 if success else 0),
        )
        conn.commit()
    except sqlite3.Error:
        pass
    finally:
        if conn:
            conn.close()


def save_generation(invite_code: str, industry_id: str, mode: str,
                    input_title: str, input_text: str, input_profile: str,
                    output_text: str, image_count: int = 0, image_tier: str = "",
                    city: str = ""):
    """保存一次生成记录"""
    conn = None
    try:
        conn = _get_db()
        conn.execute(
            "INSERT INTO generation_history "
            "(invite_code, industry_id, mode, input_title, input_text, input_profile, "
            " output_text, image_count, image_tier, city) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (invite_code, industry_id, mode, input_title, input_text, input_profile,
             output_text, image_count, image_tier, city),
        )
        conn.commit()
    except sqlite3.Error:
        pass
    finally:
        if conn:
            conn.close()


def get_history(invite_code: str, limit: int = 20) -> list:
    """获取某用户最近的生成记录"""
    conn = None
    try:
        conn = _get_db()
        rows = conn.execute(
            "SELECT * FROM generation_history WHERE invite_code = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (invite_code, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error:
        return []
    finally:
        if conn:
            conn.close()


def get_db():
    """公开版 _get_db，供管理后台直接查询"""
    return _get_db()


# ═══════════════════════════════════════════════════════
#  辅助函数
# ═══════════════════════════════════════════════════════

def friendly_api_error(e: Exception) -> str:
    """将 API 异常转为用户友好的中文提示"""
    err = str(e).lower()
    if "quota" in err or "429" in err or "rate" in err:
        return "API 调用次数已达上限，请等几分钟再试"
    if "timeout" in err or "timed out" in err:
        return "网络超时，请检查网络后重试"
    if "401" in err or "unauthorized" in err or "invalid" in err:
        return "API 密钥无效或过期，请联系管理员"
    if "404" in err or "not found" in err:
        return "AI 模型暂不可用，请稍后再试"
    if "500" in err or "502" in err or "503" in err:
        return "AI 服务暂时繁忙，请稍后重试"
    if "content" in err and "filter" in err:
        return "内容触发安全过滤，请调整输入后重试"
    return f"生成失败，请稍后再试（错误代码：{str(e)[:80]}）"


def img_cols(count: int) -> int:
    """根据图片数量返回合适的列数（兼顾小屏设备）"""
    if count <= 2:
        return count
    return min(count, 3)


# ═══════════════════════════════════════════════════════
#  Pro 配额追踪
# ═══════════════════════════════════════════════════════

def get_pro_used(code: str) -> int:
    conn = None
    try:
        conn = _get_db()
        row = conn.execute(
            "SELECT pro_gen_used FROM quota_usage WHERE invite_code = ?",
            (code.upper(),),
        ).fetchone()
        return row["pro_gen_used"] if row else 0
    except sqlite3.Error:
        return 0
    finally:
        if conn:
            conn.close()


def has_pro_quota(code: str) -> bool:
    return get_pro_used(code) < PRO_GEN_LIMIT


def try_use_pro_quota(code: str) -> bool:
    """原子地检查+扣除1次 Pro 配额，成功返回 True"""
    conn = None
    try:
        conn = _get_db()
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT pro_gen_used FROM quota_usage WHERE invite_code = ?",
            (code.upper(),)
        ).fetchone()
        used = row["pro_gen_used"] if row else 0
        if used >= PRO_GEN_LIMIT:
            conn.rollback()
            return False
        conn.execute(
            "INSERT INTO quota_usage (invite_code, pro_gen_used, updated_at) "
            "VALUES (?, 1, datetime('now')) "
            "ON CONFLICT(invite_code) DO UPDATE SET "
            "pro_gen_used = pro_gen_used + 1, updated_at = datetime('now')",
            (code.upper(),)
        )
        conn.commit()
        return True
    except sqlite3.Error:
        if conn:
            try:
                conn.rollback()
            except sqlite3.Error:
                pass
        return False
    finally:
        if conn:
            conn.close()


def refund_pro_quota(code: str):
    """生成失败时退回1次 Pro 配额"""
    conn = None
    try:
        conn = _get_db()
        conn.execute(
            "UPDATE quota_usage SET pro_gen_used = MAX(pro_gen_used - 1, 0) "
            "WHERE invite_code = ?", (code.upper(),)
        )
        conn.commit()
    except sqlite3.Error:
        pass
    finally:
        if conn:
            conn.close()


# ═══════════════════════════════════════════════════════
#  认证 & API Key
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


def get_api_key(name: str) -> str:
    try:
        return st.secrets.get(name, "")
    except Exception:
        return ""


def make_session():
    """创建伪装浏览器指纹的 requests.Session"""
    s = requests.Session()
    s.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    })
    return s


# ═══════════════════════════════════════════════════════
#  ZIP 打包
# ═══════════════════════════════════════════════════════

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


def make_batch_zip(batch_results: list, use_edited: bool = True) -> io.BytesIO:
    """批量打包：每条笔记一个子目录"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, br in enumerate(batch_results):
            # 子目录名：序号 + 标题前10字
            safe_title = re.sub(r'[\\/:*?"<>|]', '_', (br.get("title") or "无标题")[:10])
            folder = f"{idx+1}_{safe_title}"
            # 文案
            text = br.get("rewrite") or br.get("text") or ""
            title = br.get("title") or ""
            zf.writestr(f"{folder}/文案.txt", f"{title}\n\n{text}".encode("utf-8"))
            # 图片
            imgs = (br.get("edited_images") if use_edited else br.get("images")) or br.get("images") or []
            for i, img in enumerate(imgs):
                if img is None:
                    # 编辑失败的用原图替代
                    orig_imgs = br.get("images", [])
                    img = orig_imgs[i] if i < len(orig_imgs) else None
                if img is not None:
                    ib = io.BytesIO()
                    img.save(ib, format="JPEG", quality=95)
                    zf.writestr(f"{folder}/图片_{i+1}.jpg", ib.getvalue())
    buf.seek(0)
    return buf
