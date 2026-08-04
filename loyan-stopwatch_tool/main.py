"""秒表 — 计时器

命令：
  /秒表开始     — 开始计时
  /秒表          — 查看耗时
  /秒表结束     — 结束并显示总耗时
"""

import time

from graci import on_command, plugin_handler, PluginContext, get_logger
from graci import get_reading, set_reading

logger = get_logger("秒表")


@on_command("/秒表开始", "/开始计时", "/计时")
@plugin_handler
async def handle_stopwatch_start(ctx: PluginContext):
    """开始计时"""
    uid = str(getattr(ctx, "sender_id", "") or "")
    set_reading(uid, {"mode": "stopwatch", "start": time.time()})
    await ctx.reply("⏱️ 秒表已开始！\n💡 /秒表 查看耗时 · /秒表结束 结束")


@on_command("/秒表", "/计时查看", "/stopwatch")
@plugin_handler
async def handle_stopwatch(ctx: PluginContext):
    """查看秒表"""
    uid = str(getattr(ctx, "sender_id", "") or "")
    game = get_reading(uid)
    if not game or game.get("mode") != "stopwatch":
        await ctx.reply("请先 /秒表开始")
        return
    elapsed = time.time() - game["start"]
    mins, secs = divmod(int(elapsed), 60)
    hours, mins = divmod(mins, 60)
    await ctx.reply(f"⏱️ 已计时 {hours:02d}:{mins:02d}:{secs:02d}")


@on_command("/秒表结束", "/停止计时", "/stopwatch_end")
@plugin_handler
async def handle_stopwatch_end(ctx: PluginContext):
    """结束秒表"""
    uid = str(getattr(ctx, "sender_id", "") or "")
    game = get_reading(uid)
    if not game or game.get("mode") != "stopwatch":
        await ctx.reply("请先 /秒表开始")
        return
    elapsed = time.time() - game["start"]
    set_reading(uid, None)
    mins, secs = divmod(int(elapsed), 60)
    hours, mins = divmod(mins, 60)
    await ctx.reply(f"⏱️ 计时结束！总耗时 {hours:02d}:{mins:02d}:{secs:02d}")
