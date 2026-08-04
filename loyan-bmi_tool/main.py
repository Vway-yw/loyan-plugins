"""BMI 计算 — 身体质量指数

命令：
  /bmi <体重kg> <身高cm>     — 计算 BMI
"""

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("BMI计算")

# ── 常量定义 ──
RANGES = [
    (0, 18.5, "偏瘦", "📉 建议适当增加营养摄入"),
    (18.5, 24, "正常", "✅ 保持健康的生活方式"),
    (24, 28, "偏胖", "📈 建议加强运动控制饮食"),
    (28, 99, "肥胖", "⚠️ 建议咨询专业健康管理"),
]


@on_command("/bmi", "/身体质量", "/体质指数")
@plugin_handler
async def handle_bmi(ctx: PluginContext):
    """BMI 计算"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split()

    if len(parts) < 3:
        await ctx.reply("📊 用法：/bmi <体重kg> <身高cm>\n例：/bmi 65 175")
        return

    try:
        weight = float(parts[1])
        height_cm = float(parts[2])
    except ValueError:
        await ctx.reply("❌ 请输入数字")
        return

    if weight <= 0 or height_cm <= 0:
        await ctx.reply("❌ 请输入有效数值")
        return

    height_m = height_cm / 100
    bmi = weight / (height_m ** 2)
    for lo, hi, label, advice in RANGES:
        if lo <= bmi < hi:
            status, tip = label, advice
            break
    else:
        status, tip = "异常", "数据有误"

    await ctx.reply(
        f"📊 BMI 计算\n"
        f"━━━━━━━━━━━━\n"
        f"⚖️ 体重: {weight}kg · 📏 身高: {height_cm}cm\n"
        f"📈 BMI: {bmi:.1f}\n"
        f"📌 状态: {status}\n"
        f"💡 {tip}"
    )
