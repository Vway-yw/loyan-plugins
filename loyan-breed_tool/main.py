"""狗狗品种 — 查询狗狗品种列表/随机品种图片

命令：
  /犬种             — 随机狗狗品种
  /犬种 猎犬        — 指定品种的狗狗
"""

import asyncio
import json
import os
import secrets
import urllib.request
from typing import Optional

from graci import on_command, plugin_handler, PluginContext, get_logger, LoyanImage

logger = get_logger("犬种")

# ── 常量定义 ──
BREEDS_URL = "https://dog.ceo/api/breeds/list/all"
IMAGE_URL = "https://dog.ceo/api/breed/{breed}/images/random"
TIMEOUT = 20
UA = "Mozilla/5.0 (compatible; LoyanBot/1.0)"

# ── 模块级状态 ──
_breeds: Optional[list] = None


def _get_breeds() -> list:
    """获取全部犬种"""
    global _breeds
    if _breeds:
        return _breeds
    req = urllib.request.Request(BREEDS_URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    breeds = []
    for main, subs in data.get("message", {}).items():
        if subs:
            for s in subs:
                breeds.append(f"{main}-{s}")
        else:
            breeds.append(main)
    _breeds = breeds
    return breeds


def _get_image(breed: str) -> Optional[str]:
    """获取指定品种图片"""
    url = IMAGE_URL.format(breed=breed)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("message") if data.get("status") == "success" else None


def _download(url: str) -> bytes:
    """下载图片"""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


@on_command("/犬种", "/狗狗品种", "/breeds")
@plugin_handler
async def handle_breeds(ctx: PluginContext):
    """狗狗品种查询"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    breed = parts[1].strip() if len(parts) > 1 else ""

    try:
        breeds = await asyncio.to_thread(_get_breeds)

        # 无参数：随机品种
        if not breed:
            import random
            chosen = random.choice(breeds)
            await ctx.reply(f"🐶 随机品种: **{chosen}**\n📷 正在获取图片...")
            url = await asyncio.to_thread(_get_image, chosen)
            if url:
                img = await asyncio.to_thread(_download, url)
                temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
                os.makedirs(temp_dir, exist_ok=True)
                path = os.path.join(temp_dir, f"breed_{secrets.token_hex(4)}.jpg")
                with open(path, "wb") as f:
                    f.write(img)
                await ctx.send(LoyanImage(file_path=path))
            return

        # 指定品种
        matches = [b for b in breeds if breed.lower() in b]
        if not matches:
            await ctx.reply(f"😢 未找到品种「{breed}」\n💡 /犬种 查看随机品种")
            return
        chosen = matches[0]
        await ctx.reply(f"🐶 品种: **{chosen}**\n📷 正在获取图片...")
        url = await asyncio.to_thread(_get_image, chosen)
        if url:
            img = await asyncio.to_thread(_download, url)
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
            os.makedirs(temp_dir, exist_ok=True)
            path = os.path.join(temp_dir, f"breed_{secrets.token_hex(4)}.jpg")
            with open(path, "wb") as f:
                f.write(img)
            await ctx.send(LoyanImage(file_path=path))
    except Exception as e:
        logger.error(f"犬种查询失败: {e}")
        await ctx.reply("😢 查询失败，请稍后再试")
