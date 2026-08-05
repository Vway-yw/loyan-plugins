"""猜数字 — 与机器人玩猜数字游戏

命令：
  /猜数字             — 开始游戏（1-100）
  /猜数字 50          — 猜一个数字
  /猜数字 重开        — 重新开始
  /猜数字 放弃        — 结束并公布答案
"""

import random
import time

from graci import on_command, plugin_handler, PluginContext, get_logger
from graci import get_reading, set_reading

logger = get_logger("猜数字")

# ── 常量定义 ──
RANGE_MAX = 100
TIMEOUT = 300


@on_command("/猜数字", "/猜数", "/guess")
@plugin_handler
async def handle_guess(ctx: PluginContext):
    """猜数字游戏"""
    uid = str(getattr(ctx, "sender_id", "") or "")
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    arg = parts[1].strip() if len(parts) > 1 else ""

    game = get_reading(uid)

    # 重开新游戏
    if arg == "重开":
        target = random.randint(1, RANGE_MAX)
        set_reading(uid, {"mode": "guess", "target": target, "tries": 0, "start": time.time()})
        await ctx.reply(
            f"🎮 猜数字游戏重新开始！\n"
            f"━━━━━━━━━━━━\n"
            f"🔢 范围 1-{RANGE_MAX}\n"
            f"💡 /猜数字 <数字> 猜数\n"
            f"⏱️ 限时 {TIMEOUT // 60} 分钟"
        )
        return

    # 无参数：显示当前状态（不重置游戏）
    if not arg:
        if game and game.get("mode") == "guess":
            remaining = max(0, int(TIMEOUT - (time.time() - game.get("start", 0))))
            mins, secs = divmod(remaining, 60)
            await ctx.reply(
                f"🎮 游戏进行中\n"
                f"━━━━━━━━━━━━\n"
                f"🔢 已猜 {game['tries']} 次\n"
                f"⏱️ 剩余 {mins}:{secs:02d}\n"
                f"💡 /猜数字 <数字> 继续猜"
            )
        else:
            await ctx.reply(
                f"🎮 猜数字游戏\n"
                f"━━━━━━━━━━━━\n"
                f"💡 /猜数字 开始游戏（1-100）\n"
                f"📖 /猜数字 <数字> 猜数"
            )
        return

    if arg == "放弃":
        if game and game.get("mode") == "guess":
            set_reading(uid, None)
            await ctx.reply(f"🏳️ 放弃！答案是 **{game['target']}**")
        else:
            await ctx.reply("当前没有进行中的游戏")
        return

    if not game or game.get("mode") != "guess":
        await ctx.reply("请先 /猜数字 开始游戏")
        return

    # 超时检查
    if time.time() - game.get("start", 0) > TIMEOUT:
        set_reading(uid, None)
        await ctx.reply(f"⏰ 超时！答案是 **{game['target']}**，/猜数字 重新开始")
        return

    if not arg.isdigit():
        await ctx.reply("❌ 请输入数字（1-100）")
        return

    guess = int(arg)
    if not (1 <= guess <= RANGE_MAX):
        await ctx.reply(f"❌ 范围 1-{RANGE_MAX}")
        return

    game["tries"] += 1
    target = game["target"]

    if guess < target:
        set_reading(uid, game)
        await ctx.reply(f"📈 太小了！（第 {game['tries']} 次）")
    elif guess > target:
        set_reading(uid, game)
        await ctx.reply(f"📉 太大了！（第 {game['tries']} 次）")
    else:
        set_reading(uid, None)
        await ctx.reply(
            f"🎉 恭喜猜中！\n"
            f"━━━━━━━━━━━━\n"
            f"🔢 答案: {target}\n"
            f"🎯 用了 {game['tries']} 次\n"
            f"💡 /猜数字 再来一局"
        )
