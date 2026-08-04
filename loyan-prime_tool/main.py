"""质数工具 — 质数判断/分解/区间质数

命令：
  /质数 17          — 判断是否质数
  /质数 分解 100    — 质因数分解
  /质数 区间 1 50   — 列出区间质数
"""

import math

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("质数工具")


def _is_prime(n: int) -> bool:
    """判断质数"""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def _factorize(n: int) -> list:
    """质因数分解"""
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        factors.append(n)
    return factors


@on_command("/质数", "/素数", "/prime")
@plugin_handler
async def handle_prime(ctx: PluginContext):
    """质数工具"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split()

    if len(parts) < 2:
        await ctx.reply(
            "🔢 质数工具\n"
            "━━━━━━━━━━━━\n"
            "💡 /质数 <数字> 判断\n"
            "💡 /质数 分解 <数字> 质因数分解\n"
            "💡 /质数 区间 <起> <止> 区间质数\n"
            "📖 例：/质数 17"
        )
        return

    action = parts[1].strip()
    if action == "分解" and len(parts) >= 3:
        try:
            n = int(parts[2])
        except ValueError:
            await ctx.reply("❌ 请输入数字")
            return
        factors = _factorize(n)
        expr = " × ".join(str(f) for f in factors)
        await ctx.reply(f"🔢 {n} 的质因数分解\n━━━━━━━━━━━━\n{n} = {expr}")
        return

    if action == "区间" and len(parts) >= 4:
        try:
            lo, hi = int(parts[2]), int(parts[3])
        except ValueError:
            await ctx.reply("❌ 请输入数字")
            return
        primes = [str(n) for n in range(max(2, lo), hi + 1) if _is_prime(n)]
        if not primes:
            await ctx.reply(f"🔢 {lo}-{hi} 之间没有质数")
            return
        await ctx.reply(f"🔢 {lo}-{hi} 之间的质数（{len(primes)} 个）\n━━━━━━━━━━━━\n{' '.join(primes[:50])}")
        return

    try:
        n = int(action)
    except ValueError:
        await ctx.reply("❌ 用法：/质数 <数字>")
        return

    if _is_prime(n):
        await ctx.reply(f"✅ {n} 是质数！")
    else:
        factors = _factorize(n)
        await ctx.reply(f"❌ {n} 不是质数\n📌 因数分解: {' × '.join(str(f) for f in factors)}")
