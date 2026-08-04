"""随机骰子 — 掷骰子 / 抛硬币 / 随机数

命令：
  /骰子           — 掷一个 6 面骰子
  /骰子 3         — 掷 3 个骰子
  /骰子 1d20      — 掷 20 面骰子
  /硬币           — 抛硬币
  /随机 1 100     — 生成 1-100 随机数
"""

import random

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("骰子硬币")


def _roll_dice(count: int, sides: int) -> list:
    """掷骰子"""
    return [random.randint(1, sides) for _ in range(count)]


@on_command("/骰子", "/掷骰子", "/dice")
@plugin_handler
async def handle_dice(ctx: PluginContext):
    """掷骰子"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    arg = parts[1].strip() if len(parts) > 1 else ""

    count, sides = 1, 6
    if arg:
        if "d" in arg.lower():
            # NdM 格式
            m = arg.lower().split("d")
            count = int(m[0]) if m[0] and m[0].isdigit() else 1
            sides = int(m[1]) if len(m) > 1 and m[1].isdigit() else 6
        elif arg.isdigit():
            count = int(arg)
        else:
            await ctx.reply("❌ 用法：/骰子 [数量] 或 /骰子 2d20")
            return

    if not (1 <= count <= 10):
        await ctx.reply("❌ 骰子数量需在 1-10 之间")
        return
    if not (2 <= sides <= 100):
        await ctx.reply("❌ 骰子面数需在 2-100 之间")
        return

    rolls = _roll_dice(count, sides)
    total = sum(rolls)
    lines = [f"🎲 掷 {count} 个 {sides} 面骰子", "━━━━━━━━━━━━"]
    if count == 1:
        lines.append(f"🎯 结果: {rolls[0]}")
    else:
        lines.append(f"🎯 结果: {' + '.join(str(r) for r in rolls)}")
        lines.append(f"📊 总和: {total}")
    await ctx.reply("\n".join(lines))


@on_command("/硬币", "/抛硬币", "/coin")
@plugin_handler
async def handle_coin(ctx: PluginContext):
    """抛硬币"""
    result = random.choice(["正面", "反面"])
    await ctx.reply(f"🪙 抛硬币结果: **{result}**")


@on_command("/随机", "/随机数", "/rand")
@plugin_handler
async def handle_rand(ctx: PluginContext):
    """随机数"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split()
    try:
        low = int(parts[1]) if len(parts) > 1 else 1
        high = int(parts[2]) if len(parts) > 2 else 100
    except ValueError:
        await ctx.reply("❌ 用法：/随机 1 100")
        return
    if low > high:
        low, high = high, low
    result = random.randint(low, high)
    await ctx.reply(f"🎲 随机数（{low}-{high}）: **{result}**")
