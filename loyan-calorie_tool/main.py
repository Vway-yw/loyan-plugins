"""卡路里计算 — 食物卡路里估算

命令：
  /卡路里 <食物> <份量g>     — 估算卡路里
"""

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("卡路里")

# ── 常量定义 ──
# 每100g 卡路里（kcal）
FOOD_CAL = {
    "米饭": 116, "面条": 110, "馒头": 223, "面包": 265, "鸡蛋": 144,
    "鸡肉": 167, "猪肉": 395, "牛肉": 250, "鱼": 105, "虾": 93,
    "苹果": 52, "香蕉": 89, "橙子": 47, "西瓜": 30, "葡萄": 43,
    "牛奶": 54, "酸奶": 72, "可乐": 43, "咖啡": 2, "豆浆": 31,
    "土豆": 76, "红薯": 99, "玉米": 106, "白菜": 17, "西兰花": 34,
    "黄瓜": 15, "番茄": 18, "豆腐": 81, "花生": 567, "巧克力": 546,
    "薯片": 536, "饼干": 435, "蛋糕": 347, "冰淇淋": 207, "啤酒": 43,
}


@on_command("/卡路里", "/热量", "/calories")
@plugin_handler
async def handle_cal(ctx: PluginContext):
    """卡路里估算"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split()

    if len(parts) < 2:
        foods = " ".join(FOOD_CAL.keys())
        await ctx.reply(f"🔥 卡路里估算\n━━━━━━━━━━━━\n💡 /卡路里 <食物> <克数>\n📖 例：/卡路里 米饭 200\n\n🍱 支持: {foods}")
        return

    food = parts[1]
    grams = 100
    if len(parts) > 2 and parts[2].isdigit():
        grams = int(parts[2])

    cal_per_100 = FOOD_CAL.get(food)
    if not cal_per_100:
        await ctx.reply(f"❌ 未收录「{food}」\n💡 支持: {' '.join(FOOD_CAL.keys())}")
        return

    total = cal_per_100 * grams / 100
    # 运动换算
    walk_min = total / 4  # 步行约 4kcal/min
    run_min = total / 10  # 跑步约 10kcal/min
    await ctx.reply(
        f"🔥 {food} 卡路里估算\n"
        f"━━━━━━━━━━━━\n"
        f"🍽️ {grams}g {food} ≈ {total:.0f} kcal\n"
        f"📊 每100g: {cal_per_100} kcal\n"
        f"━━━━━━━━━━━━\n"
        f"🚶 需步行约 {walk_min:.0f} 分钟\n"
        f"🏃 需跑步约 {run_min:.0f} 分钟"
    )
