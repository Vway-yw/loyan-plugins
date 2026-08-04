"""GitHub Trending — 查看 GitHub 热门仓库

命令：
  /trending           — 今日热门仓库
  /trending 周        — 本周热门
  /trending 月        — 本月热门
  /trending <语言>    — 按语言筛选（如 /trending python）
"""

import asyncio
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from graci import on_command, plugin_handler, PluginContext
from graci import get_logger

logger = get_logger("GitHub热门")

# ── 常量定义 ──
API_URL = "https://api.github.com/search/repositories?q=created:>{since}&sort=stars&order=desc&per_page={limit}"
TIMEOUT = 15
CACHE_TTL = 3600
UA = "Mozilla/5.0 (compatible; LoyanBot/1.0)"

# ── 模块级状态 ──
_cache: Dict[str, tuple] = {}


def _since_days(period: str) -> int:
    """时间段转天数：日=1 周=7 月=30"""
    p = period.lower()
    if "周" in p or "week" in p:
        return 7
    if "月" in p or "month" in p:
        return 30
    return 1


def _fetch(since: int, limit: int = 10) -> Optional[Dict]:
    """请求 GitHub 搜索 API"""
    date = (datetime.utcnow() - timedelta(days=since)).strftime("%Y-%m-%d")
    url = API_URL.format(since=date, limit=limit)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _format_repo(r: Dict) -> str:
    """格式化单个仓库"""
    desc = r.get("description") or "（无描述）"
    desc = desc[:60] + "…" if len(desc) > 60 else desc
    return (
        f"★ {r['stargazers_count']} | {r['full_name']}\n"
        f"   📌 {desc}\n"
        f"   🔗 {r['html_url']}"
    )


@on_command("/trending", "/github热门", "/github热榜")
@plugin_handler
async def handle_trending(ctx: PluginContext):
    """查看 GitHub 热门仓库"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    arg = parts[1].strip() if len(parts) > 1 else ""

    # 解析参数：时间段 或 语言
    since = 1
    lang = ""
    if arg:
        if arg in ("日", "天", "今天"):
            since = 1
        elif arg in ("周", "本周", "week"):
            since = 7
        elif arg in ("月", "本月", "month"):
            since = 30
        else:
            lang = arg

    await ctx.reply("🔥 正在获取 GitHub 热门...")
    cache_key = f"{since}:{lang}"
    now = time.time()
    cached = _cache.get(cache_key)
    if cached and now - cached[0] < CACHE_TTL:
        data = cached[1]
    else:
        data = await asyncio.to_thread(_fetch, since)
        if data:
            _cache[cache_key] = (now, data)

    if not data or not data.get("items"):
        logger.error("trending 获取失败")
        await ctx.reply("😢 获取失败，请稍后再试")
        return

    items = data["items"]
    if lang:
        items = [r for r in items if lang.lower() in (r.get("language") or "").lower()]
    if not items:
        await ctx.reply(f"😢 没有找到 {lang} 语言的热门仓库")
        return

    period = "日" if since == 1 else ("周" if since == 7 else "月")
    lines = [f"🔥 GitHub 热门仓库 · 本{period}", "━━━━━━━━━━━━"]
    for i, r in enumerate(items[:10], 1):
        lines.append(f"{i}. {_format_repo(r)}")
    lines.append("━━━━━━━━━━━━\n💡 /trending 周 /trending 月 /trending python")
    await ctx.reply("\n".join(lines))
