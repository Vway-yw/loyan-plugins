"""随机头像 — 生成随机卡通头像（SVG）

命令：
  /头像 <种子>     — 生成头像（种子可自定义）
"""

import asyncio
import os
import secrets
import urllib.parse
import urllib.request
from typing import Optional

from graci import on_command, plugin_handler, PluginContext, get_logger, LoyanImage

logger = get_logger("随机头像")

# ── 常量定义 ──
API_URL = "https://api.dicebear.com/9.x/adventurer/svg?seed={seed}&backgroundColor=b6e3f4"
TIMEOUT = 20
UA = "Mozilla/5.0 (compatible; LoyanBot/1.0)"


def _get_avatar(seed: str) -> Optional[bytes]:
    """生成头像"""
    url = API_URL.format(seed=urllib.parse.quote(seed))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


@on_command("/头像", "/随机头像", "/avatar")
@plugin_handler
async def handle_avatar(ctx: PluginContext):
    """随机头像"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    seed = parts[1].strip() if len(parts) > 1 else secrets.token_hex(4)

    await ctx.reply("🎨 正在生成头像...")
    try:
        svg = await asyncio.to_thread(_get_avatar, seed)
        if not svg:
            await ctx.reply("😢 生成失败，请稍后再试")
            return
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(temp_dir, exist_ok=True)
        path = os.path.join(temp_dir, f"avatar_{secrets.token_hex(4)}.svg")
        with open(path, "wb") as f:
            f.write(svg)
        await ctx.send(LoyanImage(file_path=path))
    except Exception as e:
        logger.error(f"头像生成失败: {e}")
        await ctx.reply("😢 生成失败，请稍后再试")
