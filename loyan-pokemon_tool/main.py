"""宝可梦图鉴 — 查询宝可梦信息

命令：
  /宝可梦 <名字>     — 查询宝可梦
  /宝可梦 随机       — 随机宝可梦
"""

import asyncio
import json
import urllib.request
from typing import Optional

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("宝可梦图鉴")

# ── 常量定义 ──
API_URL = "https://pokeapi.co/api/v2/pokemon/{name}"
TIMEOUT = 15


def _fetch(name: str) -> Optional[dict]:
    """查询宝可梦"""
    url = API_URL.format(name=name.lower().strip())
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


@on_command("/宝可梦", "/pokemon", "/神奇宝贝")
@plugin_handler
async def handle_pokemon(ctx: PluginContext):
    """查询宝可梦"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    name = parts[1].strip() if len(parts) > 1 else ""

    if not name:
        await ctx.reply("⚡ 用法：/宝可梦 <名字>\n例：/宝可梦 pikachu /宝可梦 随机")
        return

    if name == "随机":
        import random
        name = random.choice(["pikachu", "charizard", "bulbasaur", "squirtle", "mewtwo",
                              "gengar", "snorlax", "eevee", "jigglypuff", "machamp"])

    try:
        data = await asyncio.to_thread(_fetch, name)
        if not data:
            await ctx.reply(f"😢 未找到宝可梦「{name}」")
            return
        types = ", ".join(t["type"]["name"] for t in data.get("types", []))
        stats = {s["stat"]["name"]: s["base_stat"] for s in data.get("stats", [])}
        abilities = ", ".join(a["ability"]["name"] for a in data.get("abilities", [])[:3])
        await ctx.reply(
            f"⚡ {data['name'].capitalize()}\n"
            f"━━━━━━━━━━━━\n"
            f"🔖 编号: #{data.get('id', '')}\n"
            f"🔮 属性: {types}\n"
            f"📏 身高: {data.get('height', 0) / 10}m · 体重: {data.get('weight', 0) / 10}kg\n"
            f"💪 能力: {abilities}\n"
            f"📊 HP: {stats.get('hp', 0)} · 攻击: {stats.get('attack', 0)} · 防御: {stats.get('defense', 0)}\n"
            f"⚡ 速度: {stats.get('speed', 0)}"
        )
    except Exception as e:
        logger.error(f"宝可梦查询失败: {e}")
        await ctx.reply(f"😢 未找到宝可梦「{name}」")
