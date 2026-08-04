"""随机密码 — 生成随机安全密码

命令：
  /密码             — 生成 16 位随机密码
  /密码 12          — 生成 12 位密码
  /密码 16 强       — 16 位高强度密码（含符号）
"""

import random
import secrets
import string

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("随机密码")

# ── 常量定义 ──
DEFAULT_LEN = 16
MAX_LEN = 64


def _gen_password(length: int, strong: bool = False) -> str:
    """生成随机密码"""
    chars = string.ascii_letters + string.digits
    if strong:
        chars += string.punctuation
    return "".join(secrets.choice(chars) for _ in range(length))


@on_command("/密码", "/随机密码", "/生成密码")
@plugin_handler
async def handle_password(ctx: PluginContext):
    """生成随机密码"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 2)

    length = DEFAULT_LEN
    strong = False
    if len(parts) > 1 and parts[1].strip().isdigit():
        length = int(parts[1].strip())
    if len(parts) > 2 and parts[2].strip() in ("强", "strong", "s"):
        strong = True

    if not (6 <= length <= MAX_LEN):
        await ctx.reply(f"❌ 密码长度需在 6-{MAX_LEN} 之间")
        return

    pwd = _gen_password(length, strong)
    strength = "🔒 高强度（含符号）" if strong else "🔐 标准强度"
    await ctx.reply(
        f"{strength} 随机密码\n"
        f"━━━━━━━━━━━━\n"
        f"🔑 {pwd}\n"
        f"━━━━━━━━━━━━\n"
        f"📏 长度: {length} 位\n"
        f"💡 /密码 20 强 生成更强密码"
    )
