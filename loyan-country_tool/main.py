"""国家信息 — 查询世界各国信息

命令：
  /国家 <名字>     — 查询国家
  /国家 随机       — 随机国家
"""

import asyncio
import json
import random
import urllib.parse
import urllib.request
from typing import Optional

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("国家信息")

# ── 常量定义 ──
API_URL = "https://restcountries.com/v3.1/name/{name}"
ALL_URL = "https://restcountries.com/v3.1/all"
TIMEOUT = 15

# ── 模块级状态 ──
_all_countries: Optional[list] = None


def _fetch(name: str) -> list:
    """查询国家"""
    url = API_URL.format(name=urllib.parse.quote(name))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fetch_all() -> list:
    """获取全部国家"""
    req = urllib.request.Request(ALL_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fmt_country(c: dict) -> str:
    """格式化国家信息"""
    name = c.get("name", {}).get("common", "")
    official = c.get("name", {}).get("official", "")
    capital = ", ".join(c.get("capital", []) or ["未知"])
    region = c.get("region", "")
    subregion = c.get("subregion", "")
    pop = c.get("population", 0)
    area = c.get("area", 0)
    currency = ""
    for code, cur in (c.get("currencies") or {}).items():
        currency = f"{cur.get('name', code)} ({code})"
        break
    lang = ", ".join(list((c.get("languages") or {}).values())[:3])
    flag = c.get("flag", "")
    return (
        f"{flag} {name}\n"
        f"━━━━━━━━━━━━\n"
        f"📌 官方名: {official}\n"
        f"🏙️ 首都: {capital}\n"
        f"🌍 地区: {region} / {subregion}\n"
        f"👥 人口: {pop:,}\n"
        f"🗺️ 面积: {area:,} km²\n"
        f"💰 货币: {currency}\n"
        f"🗣️ 语言: {lang}"
    )


@on_command("/国家", "/国家查询", "/country")
@plugin_handler
async def handle_country(ctx: PluginContext):
    """国家信息"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    name = parts[1].strip() if len(parts) > 1 else ""

    try:
        if name == "随机":
            global _all_countries
            if _all_countries is None:
                _all_countries = await asyncio.to_thread(_fetch_all)
            c = random.choice(_all_countries)
            await ctx.reply(_fmt_country(c))
        elif name:
            data = await asyncio.to_thread(_fetch, name)
            if not data:
                await ctx.reply(f"😢 未找到国家「{name}」")
                return
            await ctx.reply(_fmt_country(data[0]))
        else:
            await ctx.reply("🌍 用法：\n/国家 <名字> 查询\n/国家 随机 随机国家\n例：/国家 中国")
    except Exception as e:
        logger.error(f"国家查询失败: {e}")
        await ctx.reply("😢 查询失败，请稍后再试")
