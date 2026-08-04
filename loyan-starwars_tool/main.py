"""星战百科 — 查询星球大战角色/星球/飞船

命令：
  /星战 角色 1     — 查询角色
  /星战 星球 1     — 查询星球
  /星战 飞船 1     — 查询飞船
"""

import asyncio
import json
import urllib.request
from typing import Optional

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("星战百科")

# ── 常量定义 ──
API_URL = "https://swapi.py4e.com/api/{cat}/{id}/"
TIMEOUT = 15


def _fetch(cat: str, id: int) -> Optional[dict]:
    """查询星战数据"""
    url = API_URL.format(cat=cat, id=id)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


@on_command("/星战", "/starwars", "/星球大战")
@plugin_handler
async def handle_sw(ctx: PluginContext):
    """星战百科"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 2)
    if len(parts) < 3:
        await ctx.reply("🚀 用法：\n/星战 角色 1\n/星战 星球 1\n/星战 飞船 1")
        return

    cat_map = {"角色": "people", "人物": "people", "星球": "planets", "飞船": "starships"}
    cat = cat_map.get(parts[1].strip())
    if not cat or not parts[2].strip().isdigit():
        await ctx.reply("❌ 用法：/星战 角色|星球|飞船 <编号>")
        return

    try:
        data = await asyncio.to_thread(_fetch, cat, int(parts[2].strip()))
        if not data:
            await ctx.reply("😢 查询失败")
            return
        if cat == "people":
            await ctx.reply(
                f"👤 {data.get('name', '')}\n"
                f"━━━━━━━━━━━━\n"
                f"📏 身高: {data.get('height', '')}cm\n"
                f"⚖️ 体重: {data.get('mass', '')}kg\n"
                f"👀 眼睛: {data.get('eye_color', '')}\n"
                f"💇 发色: {data.get('hair_color', '')}\n"
                f"🧬 性别: {data.get('gender', '')}\n"
                f"🌍 出生地: {data.get('homeworld', '')}"
            )
        elif cat == "planets":
            await ctx.reply(
                f"🪐 {data.get('name', '')}\n"
                f"━━━━━━━━━━━━\n"
                f"🌡️ 气候: {data.get('climate', '')}\n"
                f"🏜️ 地形: {data.get('terrain', '')}\n"
                f"👥 人口: {data.get('population', '')}\n"
                f"📏 直径: {data.get('diameter', '')}km\n"
                f"⏱️ 自转周期: {data.get('rotation_period', '')}h"
            )
        else:
            await ctx.reply(
                f"🚀 {data.get('name', '')}\n"
                f"━━━━━━━━━━━━\n"
                f"📏 长度: {data.get('length', '')}m\n"
                f"👥 载员: {data.get('crew', '')}\n"
                f"🚢 级: {data.get('starship_class', '')}\n"
                f"⚡ 速度: {data.get('max_atmosphering_speed', '')}"
            )
    except Exception as e:
        logger.error(f"星战查询失败: {e}")
        await ctx.reply("😢 查询失败，编号可能不存在")
