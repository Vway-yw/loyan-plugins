"""IP 查询 — 查询 IP 归属地与网络信息

命令：
  /ip          — 查询本机公网 IP 信息
  /ip 8.8.8.8  — 查询指定 IP
  /ipinfo      — 同 /ip
"""

import asyncio
import re
import time
import urllib.request
from typing import Dict, Optional

from graci import on_command, plugin_handler, PluginContext
from graci import get_logger

logger = get_logger("IP查询")

# ── 常量定义 ──
MYIP_URL = "https://myip.ipip.net/"
IPAPI_URL = "http://ip-api.com/json/{ip}?lang=zh-CN"
TIMEOUT = 15
CACHE_TTL = 600

# ── 模块级状态 ──
_cache: Dict[str, tuple] = {}


def _get_my_ip() -> Optional[str]:
    """获取本机公网 IP"""
    req = urllib.request.Request(MYIP_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    m = re.search(r"(\d+\.\d+\.\d+\.\d+)", text)
    return m.group(1) if m else None


def _query_ip(ip: str) -> Optional[Dict]:
    """查询 IP 详细信息"""
    url = IPAPI_URL.format(ip=ip)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return __import__("json").loads(resp.read().decode("utf-8", errors="replace"))


@on_command("/ip", "/ipinfo", "/查询IP")
@plugin_handler
async def handle_ip(ctx: PluginContext):
    """IP 归属地查询"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    ip = parts[1].strip() if len(parts) > 1 else ""

    await ctx.reply("🌐 正在查询 IP 信息...")
    try:
        if not ip:
            ip = await asyncio.to_thread(_get_my_ip)
            if not ip:
                await ctx.reply("❌ 无法获取本机 IP")
                return

        # 校验 IP 格式
        if not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", ip):
            await ctx.reply("❌ IP 格式不正确（如 8.8.8.8）")
            return

        now = time.time()
        cached = _cache.get(ip)
        if cached and now - cached[0] < CACHE_TTL:
            data = cached[1]
        else:
            data = await asyncio.to_thread(_query_ip, ip)
            if data and data.get("ip"):
                _cache[ip] = (now, data)

        if not data or data.get("error"):
            await ctx.reply("❌ 查询失败，请稍后再试")
            return

        lines = [f"🌐 IP: {data.get('query', ip)}", "━━━━━━━━━━━━"]
        fields = [
            ("📍 国家/地区", data.get("country")),
            ("🏙️ 城市", data.get("city")),
            ("🧭 经纬度", f"{data.get('lat')}, {data.get('lon')}" if data.get("lat") else None),
            ("🏢 运营商", data.get("isp")),
            ("🕒 时区", data.get("timezone")),
        ]
        for label, val in fields:
            if val:
                lines.append(f"{label}: {val}")
        if data.get("regionName"):
            lines.append(f"🗺️ 省份: {data['regionName']}")
        await ctx.reply("\n".join(lines))
    except Exception as e:
        logger.error(f"IP 查询失败: {e}")
        await ctx.reply("❌ 查询失败，请稍后再试")
