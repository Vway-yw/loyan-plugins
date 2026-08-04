"""番茄钟 — 番茄工作法计时

命令：
  /番茄开始     — 开始 25 分钟番茄钟
  /番茄          — 查看剩余
  /番茄结束     — 结束
"""

import time

from graci import on_command, plugin_handler, PluginContext, get_logger
from graci import get_reading, set_reading

logger = get_logger("番茄钟")

# ── 常量定义 ──
WORK_MIN = 25
BREAK_MIN = 5


@on_command("/番茄开始", "/番茄钟", "/pomodoro")
@plugin_handler
async def handle_pomo_start(ctx: PluginContext):
    """开始番茄钟"""
    uid = str(getattr(ctx, "sender_id", "") or "")
    set_reading(uid, {"mode": "pomodoro", "start": time.time(), "work": WORK_MIN * 60})
    await ctx.reply(
        f"🍅 番茄钟开始！专注 {WORK_MIN} 分钟\n"
        f"━━━━━━━━━━━━\n"
        f"💡 /番茄 查看剩余 · /番茄结束 结束\n"
        f"📌 结束后休息 {BREAK_MIN} 分钟"
    )


@on_command("/番茄", "/番茄剩余", "/pomo_status")
@plugin_handler
async def handle_pomo(ctx: PluginContext):
    """查看番茄钟"""
    uid = str(getattr(ctx, "sender_id", "") or "")
    game = get_reading(uid)
    if not game or game.get("mode") != "pomodoro":
        await ctx.reply("请先 /番茄开始")
        return
    remaining = game["work"] - (time.time() - game["start"])
    if remaining <= 0:
        set_reading(uid, None)
        await ctx.reply("🎉 番茄钟完成！休息一下吧 🍅\n💡 /番茄开始 再来一轮")
        return
    mins, secs = divmod(int(remaining), 60)
    await ctx.reply(f"🍅 专注剩余 {mins:02d}:{secs:02d}\n📌 保持专注！")


@on_command("/番茄结束", "/番茄停止", "/pomo_end")
@plugin_handler
async def handle_pomo_end(ctx: PluginContext):
    """结束番茄钟"""
    uid = str(getattr(ctx, "sender_id", "") or "")
    game = get_reading(uid)
    if not game or game.get("mode") != "pomodoro":
        await ctx.reply("请先 /番茄开始")
        return
    set_reading(uid, None)
    await ctx.reply("🍅 番茄钟已结束")
