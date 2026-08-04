"""密码强度 — 检测密码强度

命令：
  /强度 <密码>     — 检测密码强度
"""

import re

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("密码强度")


def _strength(pwd: str) -> tuple:
    """评估密码强度"""
    score = 0
    checks = []
    if len(pwd) >= 8:
        score += 1
        checks.append("✅ 长度 ≥8")
    else:
        checks.append("❌ 长度 <8")
    if re.search(r"[a-z]", pwd):
        score += 1
        checks.append("✅ 含小写字母")
    else:
        checks.append("❌ 无小写字母")
    if re.search(r"[A-Z]", pwd):
        score += 1
        checks.append("✅ 含大写字母")
    else:
        checks.append("❌ 无大写字母")
    if re.search(r"\d", pwd):
        score += 1
        checks.append("✅ 含数字")
    else:
        checks.append("❌ 无数字")
    if re.search(r"[^a-zA-Z0-9]", pwd):
        score += 1
        checks.append("✅ 含特殊字符")
    else:
        checks.append("❌ 无特殊字符")

    if score <= 2:
        level, icon = "弱", "🔴"
    elif score == 3:
        level, icon = "中", "🟡"
    elif score == 4:
        level, icon = "较强", "🟢"
    else:
        level, icon = "强", "🟢"
    return level, icon, checks


@on_command("/强度", "/密码强度", "/strength")
@plugin_handler
async def handle_strength(ctx: PluginContext):
    """密码强度检测"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    pwd = parts[1].strip() if len(parts) > 1 else ""

    if not pwd:
        await ctx.reply("🔐 用法：/强度 <密码>\n例：/强度 Abc123!@#")
        return
    if len(pwd) > 64:
        await ctx.reply("❌ 密码过长")
        return

    level, icon, checks = _strength(pwd)
    masked = pwd[:2] + "****" + pwd[-2:] if len(pwd) > 4 else "****"
    await ctx.reply(
        f"{icon} 密码强度: {level}\n"
        f"━━━━━━━━━━━━\n"
        f"🔑 {masked}\n"
        f"{chr(10).join(checks)}"
    )
