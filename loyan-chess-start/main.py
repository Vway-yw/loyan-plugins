"""象棋启动器 — 检测象棋服务器是否正常运行

命令：
  /chess status — 检测象棋服务器状态"""

import asyncio
from urllib.parse import urlparse

import websockets

from graci import get_logger, on_command, plugin_handler, PluginContext

_logger = get_logger("象棋启动器")

PING_URL = "ws://api.cchess.moyegame.com:10000/"


@on_command("/chess status")
@plugin_handler
async def handle_chess_status(ctx: PluginContext):
    try:
        parsed = urlparse(PING_URL)
        async with asyncio.timeout(5):
            async with websockets.connect(PING_URL) as ws:
                await ws.close()
        await ctx.reply("服务器正常运行")
    except Exception as e:
        _logger.warning(f"象棋服务器状态异常: {e}")
        await ctx.reply("状态异常")
