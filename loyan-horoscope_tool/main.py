"""星座运势 — 星座信息与运势（本地算法）

命令：
  /星座           — 今日星座运势
  /星座 双子       — 指定星座
  /星座 <生日>    — 按生日查星座（如 1996-05-20）
"""

import random
from datetime import datetime

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("星座运势")

# ── 常量定义 ──
SIGNS = [
    ("摩羯座", (12, 22), (1, 19)), ("水瓶座", (1, 20), (2, 18)),
    ("双鱼座", (2, 19), (3, 20)), ("白羊座", (3, 21), (4, 19)),
    ("金牛座", (4, 20), (5, 20)), ("双子座", (5, 21), (6, 21)),
    ("巨蟹座", (6, 22), (7, 22)), ("狮子座", (7, 23), (8, 22)),
    ("处女座", (8, 23), (9, 22)), ("天秤座", (9, 23), (10, 23)),
    ("天蝎座", (10, 24), (11, 22)), ("射手座", (11, 23), (12, 21)),
]
RANK = ["综合", "爱情", "事业", "财运", "健康"]
LUCKY = ["红色", "蓝色", "绿色", "金色", "紫色", "白色", "黑色", "橙色"]


def _sign_by_date(month: int, day: int) -> str:
    """按日期查星座"""
    for name, (sm, sd), (em, ed) in SIGNS:
        if (month == sm and day >= sd) or (month == em and day <= ed):
            return name
    return "摩羯座"


@on_command("/星座", "/星座运势", "/horoscope")
@plugin_handler
async def handle_sign(ctx: PluginContext):
    """星座运势"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    arg = parts[1].strip() if len(parts) > 1 else ""

    # 按生日
    try:
        dt = datetime.strptime(arg, "%Y-%m-%d")
        sign = _sign_by_date(dt.month, dt.day)
    except ValueError:
        sign = None
        for name, *_ in SIGNS:
            if name in arg:
                sign = name
                break
        if not sign and not arg:
            sign = _sign_by_date(datetime.now().month, datetime.now().day)

    if not sign:
        await ctx.reply("❌ 用法：/星座 <星座名> 或 /星座 <生日>\n例：/星座 双子 /星座 1996-05-20")
        return

    rng = random.Random(int(datetime.now().strftime("%Y%m%d")) + SIGNS.index((sign, *_)))
    lines = [f"♈ {sign} 今日运势", "━━━━━━━━━━━━"]
    for r in RANK:
        stars = rng.randint(3, 5)
        lines.append(f"{r}: {'★' * stars}{'☆' * (5 - stars)}")
    lines.append(f"🍀 幸运色: {rng.choice(LUCKY)}")
    lines.append(f"🔢 幸运数字: {rng.randint(1, 99)}")
    await ctx.reply("\n".join(lines))
