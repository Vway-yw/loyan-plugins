"""解梦 — 简单梦境解析（本地库）

命令：
  /解梦 <关键词>     — 解析梦境
"""

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("解梦")

# ── 常量定义 ──
DREAM_DB = {
    "水": "水主财，梦见水象征财运流动，清澈的水预示财运亨通。",
    "鱼": "鱼谐音余，梦见鱼象征富余丰收，是财运与机遇的吉兆。",
    "蛇": "蛇象征智慧与转变，梦见蛇预示即将迎来重要变化。",
    "飞": "飞翔代表自由与突破，梦见飞翔预示事业将有新高度。",
    "掉": "梦见坠落反映焦虑与不安，提醒放松心态，稳扎稳打。",
    "牙": "牙齿象征根基，梦见掉牙提醒关注健康与关系稳固。",
    "钱": "梦见钱币象征对物质的渴望，也是财运到来的预示。",
    "考试": "梦见考试反映压力与自我审视，预示即将面临考验。",
    "鬼": "梦见鬼怪多因压力所致，寓意战胜恐惧后豁然开朗。",
    "结婚": "梦见结婚象征新的开始与结合，是喜事临门之兆。",
    "死人": "梦见逝者代表旧事物终结，预示新的阶段即将开启。",
    "追": "梦见被追反映逃避心理，提醒直面问题才能解脱。",
    "火": "火象征热情与能量，梦见火预示事业蓬勃或情绪高涨。",
    "花": "花开富贵，梦见花象征美好与收获，感情运势上升。",
    "雨": "雨润万物，梦见下雨象征洗涤与新生，忧愁将散。",
}


@on_command("/解梦", "/周公解梦", "/dream")
@plugin_handler
async def handle_dream(ctx: PluginContext):
    """解梦"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    keyword = parts[1].strip() if len(parts) > 1 else ""

    if not keyword:
        await ctx.reply("🌙 用法：/解梦 <关键词>\n例：/解梦 水 /解梦 鱼 /解梦 蛇")
        return

    for k, v in DREAM_DB.items():
        if k in keyword:
            await ctx.reply(f"🌙 解梦「{keyword}」\n━━━━━━━━━━━━\n{ v}")
            return
    await ctx.reply(f"🌙 关于「{keyword}」的梦\n━━━━━━━━━━━━\n梦境常反映内心状态，保持平和心态，好事自然来。\n💡 试试：水 鱼 蛇 飞 掉 牙 钱 火 花 雨")
