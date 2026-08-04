"""今日宜忌 — 生成今日宜忌（本地算法，节假日数据）

命令：
  /宜忌     — 今日宜忌
"""

import random
from datetime import datetime

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("今日宜忌")

# ── 常量定义 ──
DO_LIST = [
    "出行", "求财", "会友", "动土", "开市", "纳财", "安床", "交易",
    "签约", "学习", "锻炼", "冥想", "写作", "旅行", "表白", "面试",
]
DONT_LIST = [
    "争执", "冲动消费", "熬夜", "借钱", "轻易承诺", "鲁莽驾驶",
    "暴饮暴食", "久坐", "刷屏", "拖延", "赌博", "冒险投资",
]


@on_command("/宜忌", "/今日宜忌", "/黄历")
@plugin_handler
async def handle_yiji(ctx: PluginContext):
    """今日宜忌"""
    now = datetime.now()
    seed = int(now.strftime("%Y%m%d"))
    rng = random.Random(seed)  # 同一天结果固定
    dos = rng.sample(DO_LIST, 3)
    donts = rng.sample(DONT_LIST, 3)
    weekday = "一二三四五六日"[now.weekday()]
    await ctx.reply(
        f"📅 {now.strftime('%Y-%m-%d')} 星期{weekday}\n"
        f"━━━━━━━━━━━━\n"
        f"✅ 宜: {' '.join(dos)}\n"
        f"❌ 忌: {' '.join(donts)}\n"
        f"━━━━━━━━━━━━\n"
        f"🔮 今日运势: {'🍀' * (rng.randint(3, 5))}"
    )
