"""汇率转换 — 实时汇率查询与货币转换（免 key）

命令：
  /汇率             — 常见货币汇率
  /汇率 USD          — 美元兑人民币
  /汇率 USD 100      — 100 美元 = ? 人民币
  /汇率 USD EUR      — 美元兑欧元
  /汇率 USD 100 EUR  — 100 美元 = ? 欧元
"""

import asyncio
import json
import time
import urllib.request
from typing import Dict, Optional

from graci import on_command, plugin_handler, PluginContext
from graci import get_logger

logger = get_logger("汇率转换")

# ── 常量定义 ──
API_URL = "https://open.er-api.com/v6/latest/USD"
TIMEOUT = 15
CACHE_TTL = 3600  # 汇率 1 小时缓存

# 常见货币
CURRENCY_ZH = {
    "CNY": "人民币", "USD": "美元", "EUR": "欧元", "JPY": "日元",
    "GBP": "英镑", "HKD": "港币", "TWD": "台币", "KRW": "韩元",
    "AUD": "澳元", "CAD": "加元", "SGD": "新加坡元", "THB": "泰铢",
    "RUB": "卢布", "INR": "卢比", "MYR": "马币", "VND": "越南盾",
    "CHF": "瑞士法郎", "NZD": "新西兰元", "PHP": "比索", "IDR": "印尼盾",
}
BASE_CURRENCIES = ["CNY", "USD", "EUR", "JPY", "GBP", "HKD", "KRW"]

# ── 模块级状态 ──
_cache: Optional[tuple] = None


def _fetch_rates() -> Optional[Dict]:
    """请求汇率数据（以 USD 为基准）"""
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


async def _get_rates() -> Optional[Dict]:
    """获取汇率（带缓存）"""
    global _cache
    now = time.time()
    if _cache and now - _cache[0] < CACHE_TTL:
        return _cache[1]
    data = await asyncio.to_thread(_fetch_rates)
    if data and data.get("result") == "success":
        _cache = (now, data)
        return data
    return None


def _convert(rates: Dict, amount: float, from_c: str, to_c: str) -> Optional[float]:
    """通过 USD 基准换算：from -> USD -> to"""
    if from_c not in rates or to_c not in rates:
        return None
    usd_amount = amount / rates[from_c]
    return usd_amount * rates[to_c]


def _fmt_amount(v: float) -> str:
    """格式化金额"""
    if v >= 10000:
        return f"{v:,.2f}"
    return f"{v:,.4f}".rstrip("0").rstrip(".")


@on_command("/汇率", "/汇率查询", "/currency")
@plugin_handler
async def handle_currency(ctx: PluginContext):
    """汇率查询与货币转换"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split()

    await ctx.reply("💱 正在获取实时汇率...")
    data = await _get_rates()
    if data is None:
        logger.error("汇率获取失败")
    if not data:
        await ctx.reply("❌ 汇率获取失败，请稍后再试")
        return
    rates = data["rates"]

    # 无参数：常见货币列表
    if not parts:
        usd = rates["USD"]
        lines = ["💱 常见货币兑人民币（USD 基准）", "━━━━━━━━━━━━"]
        for c in BASE_CURRENCIES:
            if c == "USD":
                continue
            v = _convert(rates, 1, c, "CNY")
            if v:
                zh = CURRENCY_ZH.get(c, c)
                lines.append(f"1 {c} = {_fmt_amount(v)} CNY · {zh}")
        lines.append("━━━━━━━━━━━━\n💡 /汇率 USD 100 或 /汇率 USD EUR")
        await ctx.reply("\n".join(lines))
        return

    # 解析参数
    from_c = parts[0].upper()
    amount = 1.0
    to_c = "CNY"
    if len(parts) >= 2:
        if parts[1].replace(".", "").isdigit():
            amount = float(parts[1])
        else:
            to_c = parts[1].upper()
    if len(parts) >= 3 and parts[2].replace(".", "").isdigit():
        amount = float(parts[2])
    elif len(parts) >= 3:
        to_c = parts[2].upper()

    if from_c == to_c:
        await ctx.reply(f"💱 {amount} {from_c} = {amount} {to_c}")
        return

    result = _convert(rates, amount, from_c, to_c)
    if result is None:
        await ctx.reply(f"❌ 暂不支持货币：{from_c} / {to_c}\n支持：{' '.join(rates.keys())[:80]}…")
        return

    from_zh = CURRENCY_ZH.get(from_c, from_c)
    to_zh = CURRENCY_ZH.get(to_c, to_c)
    await ctx.reply(
        f"💱 {_fmt_amount(amount)} {from_c}（{from_zh}）\n"
        f"━━━━━━━━━━━━\n"
        f"= {_fmt_amount(result)} {to_c}（{to_zh}）\n"
        f"━━━━━━━━━━━━\n"
        f"📌 汇率 1 {from_c} = {_fmt_amount(result / amount)} {to_c}"
    )
