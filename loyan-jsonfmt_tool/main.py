"""JSON 格式化 — JSON 格式化/压缩/校验

命令：
  /json <JSON>     — 格式化 JSON
"""

import json

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("JSON格式化")


@on_command("/json", "/json格式化", "/json校验")
@plugin_handler
async def handle_json(ctx: PluginContext):
    """JSON 格式化"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    text = parts[1].strip() if len(parts) > 1 else ""

    if not text:
        await ctx.reply("🔧 用法：/json <JSON字符串>\n例：/json {\"a\":1,\"b\":[1,2]}")
        return

    try:
        data = json.loads(text)
        formatted = json.dumps(data, ensure_ascii=False, indent=2)
        await ctx.reply(f"✅ JSON 有效\n━━━━━━━━━━━━\n{formatted[:1500]}")
    except json.JSONDecodeError as e:
        await ctx.reply(f"❌ JSON 无效：{e}\n📌 请检查引号/逗号/括号")
