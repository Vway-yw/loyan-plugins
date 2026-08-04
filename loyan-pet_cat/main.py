"""随机猫咪 — 获取随机猫咪图片

命令：
  /猫咪     — 随机猫咪图片
  /猫图     — 同 /猫咪
"""

import asyncio
import json
import os
import secrets
import urllib.request
from typing import Optional

from graci import on_command, plugin_handler, PluginContext, get_logger, LoyanImage

logger = get_logger("随机猫咪")

# ── 常量定义 ──
API_URL = "https://api.thecatapi.com/v1/images/search"
TIMEOUT = 20
UA = "Mozilla/5.0 (compatible; LoyanBot/1.0)"


def _get_image_url() -> Optional[str]:
    """获取随机猫咪图片 URL"""
    req = urllib.request.Request(API_URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data:
        return data[0].get("url")
    return None


def _download(url: str) -> bytes:
    """下载图片"""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


@on_command("/猫咪", "/猫图", "/随机猫咪")
@plugin_handler
async def handle_cat(ctx: PluginContext):
    """获取随机猫咪图片"""
    await ctx.reply("🐱 正在寻找猫咪...")
    try:
        url = await asyncio.to_thread(_get_image_url)
        if not url:
            await ctx.reply("😢 获取失败，请稍后再试")
            return
        img = await asyncio.to_thread(_download, url)
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(temp_dir, exist_ok=True)
        path = os.path.join(temp_dir, f"cat_{secrets.token_hex(4)}.jpg")
        with open(path, "wb") as f:
            f.write(img)
        await ctx.send(LoyanImage(file_path=path))
    except Exception as e:
        logger.error(f"猫咪图片获取失败: {e}")
        await ctx.reply("😢 获取失败，请稍后再试")
