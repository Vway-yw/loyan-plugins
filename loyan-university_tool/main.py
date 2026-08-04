"""大学查询 — 查询中国大学信息

命令：
  /大学             — 随机大学
  /大学 清华        — 搜索大学
"""

import asyncio
import json
import random
import urllib.parse
import urllib.request
from typing import Optional

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("大学查询")

# ── 常量定义 ──
API_URL = "http://universities.hipolabs.com/search?country=China&name={name}"
TIMEOUT = 15

# ── 模块级状态 ──
_all_universities: Optional[list] = None


def _fetch(name: str = "") -> list:
    """查询大学"""
    url = API_URL.format(name=urllib.parse.quote(name))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


@on_command("/大学", "/大学查询", "/university")
@plugin_handler
async def handle_university(ctx: PluginContext):
    """大学查询"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    name = parts[1].strip() if len(parts) > 1 else ""

    try:
        if name:
            data = await asyncio.to_thread(_fetch, name)
            if not data:
                await ctx.reply(f"😢 未找到大学「{name}」")
                return
            lines = [f"🎓 「{name}」相关大学", "━━━━━━━━━━━━"]
            for u in data[:8]:
                lines.append(f"🏫 {u.get('name', '')}")
                if u.get("web_pages"):
                    lines.append(f"   🔗 {u['web_pages'][0]}")
            await ctx.reply("\n".join(lines))
        else:
            global _all_universities
            if _all_universities is None:
                _all_universities = await asyncio.to_thread(_fetch)
            u = random.choice(_all_universities)
            await ctx.reply(
                f"🎓 随机大学\n"
                f"━━━━━━━━━━━━\n"
                f"🏫 {u.get('name', '')}\n"
                f"🌍 国家: {u.get('country', '')}\n"
                f"📍 地区: {u.get('alpha_two_code', '')}\n"
                f"🔗 {u.get('web_pages', [''])[0]}\n"
                f"💡 /大学 清华 搜索指定大学"
            )
    except Exception as e:
        logger.error(f"大学查询失败: {e}")
        await ctx.reply("😢 查询失败，请稍后再试")
