"""Fibonacci — 斐波那契数列/黄金分割

命令：
  /斐波那契 10     — 前 10 项
"""

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("斐波那契")

# ── 常量定义 ──
MAX_N = 40


def _fib(n: int) -> list:
    """斐波那契前 n 项"""
    seq = [0, 1]
    for _ in range(2, n):
        seq.append(seq[-1] + seq[-2])
    return seq[:n]


@on_command("/斐波那契", "/fib", "/黄金分割")
@plugin_handler
async def handle_fib(ctx: PluginContext):
    """斐波那契数列"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    n = 10
    if len(parts) > 1 and parts[1].strip().isdigit():
        n = int(parts[1].strip())
    if not (1 <= n <= MAX_N):
        await ctx.reply(f"❌ 请输入 1-{MAX_N} 之间的数字")
        return

    seq = _fib(n)
    ratio = seq[-1] / seq[-2] if len(seq) >= 2 and seq[-2] else 0
    await ctx.reply(
        f"🔢 斐波那契数列（前 {n} 项）\n"
        f"━━━━━━━━━━━━\n"
        f"{' '.join(str(x) for x in seq)}\n"
        f"━━━━━━━━━━━━\n"
        f"📐 相邻比: {ratio:.6f}（趋近黄金分割 1.618）"
    )
