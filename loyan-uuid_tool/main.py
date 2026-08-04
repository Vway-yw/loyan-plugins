"""UUID 生成 — 生成 UUID

命令：
  /uuid       — 生成 UUID v4
  /uuid 5     — 生成 5 个
"""

import uuid

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("UUID生成")

# ── 常量定义 ──
MAX_N = 10


@on_command("/uuid", "/uuid生成", "/uuid4")
@plugin_handler
async def handle_uuid(ctx: PluginContext):
    """生成 UUID"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    n = 1
    if len(parts) > 1 and parts[1].strip().isdigit():
        n = min(max(int(parts[1].strip()), 1), MAX_N)

    uuids = [str(uuid.uuid4()) for _ in range(n)]
    lines = [f"🔑 UUID v4（{n} 个）", "━━━━━━━━━━━━"]
    lines.extend(uuids)
    lines.append("━━━━━━━━━━━━\n💡 /uuid 5 生成多个")
    await ctx.reply("\n".join(lines))
