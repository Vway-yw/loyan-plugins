"""柠柚API整合 — 调用柠柚API平台功能接口

命令：
  /设置key <key>       — 设置 API Key（仅主人）
  /恶搞语音 <文本>     — 文字转趣味恶搞语音
  /踢球 <QQ号>         — 踢球恶搞动图
  /答案之书 <问题>     — 答案之书
  /黑丝 <关键词>       — 随机黑丝图片
  /语音 <文本>         — 同 /恶搞语音
"""

import asyncio
import json
import os
import secrets
import urllib.parse
import urllib.request
from typing import Dict, Optional

from graci import on_command, plugin_handler, PluginContext, get_logger
from graci import require_master, config_manager, LoyanImage

logger = get_logger("柠柚API")

# ── 常量定义 ──
API_BASE = "https://api.nycnm.cn/api/v2"
TIMEOUT = 20
UA = "Mozilla/5.0 (compatible; LoyanBot/1.0)"

# ── 模块级状态 ──
_config_cache: Optional[dict] = None


def _load_config() -> dict:
    """读取插件配置（带缓存）"""
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    _config_cache = config_manager.get_plugin("柠柚API") or {}
    return _config_cache


def _save_config(cfg: dict):
    """保存插件配置"""
    global _config_cache
    _config_cache = cfg
    config_manager.update_plugin("柠柚API", cfg)


def _get_api_key() -> str:
    """获取 API Key"""
    cfg = _load_config()
    return cfg.get("api_key", "") or ""


def _build_url(path: str, params: dict) -> str:
    """构造带 apikey 的请求 URL"""
    params = dict(params)
    params["apikey"] = _get_api_key()
    return API_BASE + path + "?" + urllib.parse.urlencode(params)


def _request_json(url: str) -> Optional[Dict]:
    """GET 请求返回 JSON"""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://api.nycnm.cn/"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _request_bytes(url: str) -> Optional[bytes]:
    """GET 请求返回二进制"""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://api.nycnm.cn/"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


@on_command("/设置key", "/设置密钥", "/setkey")
@require_master
@plugin_handler
async def handle_setkey(ctx: PluginContext):
    """设置 API Key（仅主人可用）"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    key = parts[1].strip() if len(parts) > 1 else ""

    if not key:
        await ctx.reply("🔑 用法：/设置key <你的API Key>\n例：/设置key sk-xxxx")
        return

    cfg = _load_config()
    cfg["api_key"] = key
    _save_config(cfg)
    await ctx.reply("✅ API Key 已设置（仅主人可见，已安全保存）")


@on_command("/恶搞语音", "/语音", "/tts")
@plugin_handler
async def handle_tts(ctx: PluginContext):
    """文字转趣味恶搞语音"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    text = parts[1].strip() if len(parts) > 1 else ""

    if not text:
        await ctx.reply("🎙️ 用法：/恶搞语音 <文本>\n例：/恶搞语音 柠柚牛逼")
        return
    if len(text) > 200:
        await ctx.reply("❌ 文本过长（最多 200 字）")
        return

    if not _get_api_key():
        await ctx.reply("⚠️ 尚未设置 API Key，请联系管理员设置\n💡 主人可用 /设置key <key> 配置")
        return

    await ctx.reply("🎙️ 正在生成语音...")
    try:
        url = _build_url("/kktts", {"type": "mp3", "uid": 1, "text": text})
        result = await asyncio.to_thread(_request_json, url)
        if not result or result.get("code") != 200:
            await ctx.reply(f"❌ 接口错误: {(result or {}).get('msg', '调用失败')}")
            return
        data = result.get("data", {})
        audio_url = data.get("url", "")
        if not audio_url:
            await ctx.reply("❌ 未获取到语音地址")
            return
        await ctx.reply(f"🎙️ 语音生成成功！\n📝 {data.get('text', text)}\n🔗 {audio_url}")
    except Exception as e:
        logger.error(f"语音生成失败: {e}")
        await ctx.reply("❌ 生成失败，请稍后再试")


@on_command("/踢球", "/踢球动图", "/kickball")
@plugin_handler
async def handle_kickball(ctx: PluginContext):
    """踢球恶搞动图"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    qq = parts[1].strip() if len(parts) > 1 else ""

    if not qq:
        await ctx.reply("⚽ 用法：/踢球 <QQ号>\n例：/踢球 505169296")
        return
    if not qq.isdigit():
        await ctx.reply("❌ 请输入 QQ 号")
        return

    if not _get_api_key():
        await ctx.reply("⚠️ 尚未设置 API Key，请联系管理员设置\n💡 主人可用 /设置key <key> 配置")
        return

    await ctx.reply("⚽ 正在生成踢球动图...")
    try:
        url = _build_url("/kick_ball", {"qq": qq})
        gif = await asyncio.to_thread(_request_bytes, url)
        if not gif or not gif.startswith(b"GIF"):
            await ctx.reply("❌ 生成失败，接口未返回图片")
            return
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(temp_dir, exist_ok=True)
        path = os.path.join(temp_dir, f"kick_{secrets.token_hex(4)}.gif")
        with open(path, "wb") as f:
            f.write(gif)
        await ctx.send(LoyanImage(file_path=path))
    except Exception as e:
        logger.error(f"踢球动图失败: {e}")
        await ctx.reply("❌ 生成失败，请稍后再试")


@on_command("/答案之书", "/答案", "/answerbook")
@plugin_handler
async def handle_answer(ctx: PluginContext):
    """答案之书：问一个问题得到答案"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    question = parts[1].strip() if len(parts) > 1 else ""

    if not question:
        await ctx.reply("📖 用法：/答案之书 <问题>\n例：/答案之书 我今天会成功吗?")
        return
    if len(question) > 100:
        await ctx.reply("❌ 问题过长（最多 100 字）")
        return

    if not _get_api_key():
        await ctx.reply("⚠️ 尚未设置 API Key，请联系管理员设置\n💡 主人可用 /设置key <key> 配置")
        return

    await ctx.reply("📖 正在翻阅答案之书...")
    try:
        url = _build_url("/answer", {"format": "json", "question": question})
        result = await asyncio.to_thread(_request_json, url)
        if not result or result.get("code") != 200:
            await ctx.reply(f"❌ 接口错误: {(result or {}).get('message', '调用失败')}")
            return
        data = result.get("data", {})
        answer = data.get("answer", "")
        desc = data.get("description", "")
        if not answer:
            await ctx.reply("❌ 未获取到答案")
            return
        await ctx.reply(
            f"📖 答案之书\n"
            f"━━━━━━━━━━━━\n"
            f"❓ {data.get('question', question)}\n"
            f"📌 答案: {answer}\n"
            f"💬 解读: {desc or '顺其自然'}"
        )
    except Exception as e:
        logger.error(f"答案之书失败: {e}")
        await ctx.reply("❌ 查询失败，请稍后再试")


@on_command("/黑丝", "/黑丝图片", "/heisi")
@plugin_handler
async def handle_heisi(ctx: PluginContext):
    """随机黑丝图片"""
    await ctx.reply("🖼️ 正在获取图片...")
    try:
        params = {}
        if _get_api_key():
            params["apikey"] = _get_api_key()
        url = API_BASE + "/heisi1" + ("?" + urllib.parse.urlencode(params) if params else "")
        img = await asyncio.to_thread(_request_bytes, url)
        if not img or not (img.startswith(b"\xff\xd8") or img.startswith(b"GIF") or img.startswith(b"\x89PNG")):
            await ctx.reply("❌ 获取失败，接口未返回图片")
            return
        ext = ".jpg" if img.startswith(b"\xff\xd8") else ".gif" if img.startswith(b"GIF") else ".png"
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(temp_dir, exist_ok=True)
        path = os.path.join(temp_dir, f"heisi_{secrets.token_hex(4)}{ext}")
        with open(path, "wb") as f:
            f.write(img)
        await ctx.send(LoyanImage(file_path=path))
    except Exception as e:
        logger.error(f"黑丝图片失败: {e}")
        await ctx.reply("❌ 获取失败，请稍后再试")

