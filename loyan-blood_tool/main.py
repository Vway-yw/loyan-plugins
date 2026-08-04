"""血型配对 — 血型性格与配对

命令：
  /血型       — 血型知识
  /血型 A     — 指定血型
"""

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("血型性格")

# ── 常量定义 ──
BLOOD_INFO = {
    "A": ("认真细致，有条理，责任感强", "搭配 O 型最合拍，AB 型需多包容"),
    "B": ("自由奔放，创造力强，直觉敏锐", "与 AB 型最默契，A 型需互相理解"),
    "AB": ("理性冷静，双面性格，适应力强", "与 B 型最搭，O 型互补性强"),
    "O": ("乐观开朗，领导力强，行动派", "与 A 型绝配，同型需避免固执"),
}


@on_command("/血型", "/血型配对", "/blood")
@plugin_handler
async def handle_blood(ctx: PluginContext):
    """血型性格"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    bt = parts[1].strip().upper() if len(parts) > 1 else ""

    if not bt:
        await ctx.reply(
            "🩸 血型性格\n"
            f"━━━━━━━━━━━━\n"
            f"💡 /血型 A /血型 B /血型 AB /血型 O"
        )
        return

    if bt not in BLOOD_INFO:
        await ctx.reply("❌ 仅支持 A/B/AB/O 四种血型")
        return

    desc, match = BLOOD_INFO[bt]
    await ctx.reply(
        f"🩸 {bt} 型血性格\n"
        f"━━━━━━━━━━━━\n"
        f"📌 性格: {desc}\n"
        f"💞 配对: {match}"
    )
