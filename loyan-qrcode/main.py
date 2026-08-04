"""二维码生成 — 文本/链接转二维码图片

命令：
  /二维码 <内容>      — 生成二维码图片
  /qr <内容>          — 同 /二维码
"""

import asyncio
import os
import secrets
import urllib.parse
import urllib.request
from typing import Optional

from graci import on_command, plugin_handler, PluginContext, get_logger, LoyanImage

logger = get_logger("二维码")

# ── 常量定义 ──
API_URL = "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={data}"
TIMEOUT = 20
MAX_LEN = 500
UA = "Mozilla/5.0 (compatible; LoyanBot/1.0)"


def _make_qr(data: str) -> Optional[bytes]:
    """生成二维码图片"""
    url = API_URL.format(data=urllib.parse.quote(data[:MAX_LEN]))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


@on_command("/二维码", "/qr", "/生成二维码")
@plugin_handler
async def handle_qrcode(ctx: PluginContext):
    """生成二维码"""
    rest = (ctx.raw_text or "").strip()
    data = rest.split(None, 1)[1].strip() if len(rest.split(None, 1)) > 1 else ""

    if not data:
        await ctx.reply("📱 用法：/二维码 <内容>\n例：/二维码 https://example.com")
        return

    if len(data) > MAX_LEN:
        await ctx.reply(f"❌ 内容过长（最多 {MAX_LEN} 字符）")
        return

    await ctx.reply("📱 正在生成二维码...")
    try:
        img = await asyncio.to_thread(_make_qr, data)
        if not img:
            await ctx.reply("😢 生成失败，请稍后再试")
            return
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(temp_dir, exist_ok=True)
        path = os.path.join(temp_dir, f"qr_{secrets.token_hex(4)}.png")
        with open(path, "wb") as f:
            f.write(img)
        await ctx.send(LoyanImage(file_path=path))
    except Exception as e:
        logger.error(f"二维码生成失败: {e}")
        await ctx.reply("😢 生成失败，请稍后再试")
