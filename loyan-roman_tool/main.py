"""罗马数字 — 阿拉伯数字与罗马数字互转

命令：
  /罗马 1999        — 转罗马数字
  /罗马 MCMXCIX     — 罗马转阿拉伯
"""

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("罗马数字")

# ── 常量定义 ──
ROMAN_NUM = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'),
             (90, 'XC'), (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'),
             (5, 'V'), (4, 'IV'), (1, 'I')]


def _to_roman(n: int) -> str:
    """阿拉伯转罗马"""
    result = ""
    for val, sym in ROMAN_NUM:
        while n >= val:
            result += sym
            n -= val
    return result


def _from_roman(s: str) -> int:
    """罗马转阿拉伯"""
    rom_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total = 0
    prev = 0
    for c in reversed(s.upper()):
        val = rom_map[c]
        if val < prev:
            total -= val
        else:
            total += val
        prev = val
    return total


@on_command("/罗马", "/罗马数字", "/roman")
@plugin_handler
async def handle_roman(ctx: PluginContext):
    """罗马数字转换"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    arg = parts[1].strip() if len(parts) > 1 else ""

    if not arg:
        await ctx.reply("🏛️ 用法：\n/罗马 1999 → MCMXCIX\n/罗马 MCMXCIX → 1999")
        return

    if arg.isdigit():
        n = int(arg)
        if not (0 < n < 4000):
            await ctx.reply("❌ 范围 1-3999")
            return
        await ctx.reply(f"🏛️ {n} = **{_to_roman(n)}**")
    elif all(c.upper() in "IVXLCDM" for c in arg):
        try:
            result = _from_roman(arg)
            await ctx.reply(f"🏛️ {arg.upper()} = **{result}**")
        except KeyError:
            await ctx.reply("❌ 非法罗马数字")
    else:
        await ctx.reply("❌ 请输入数字或罗马数字")
