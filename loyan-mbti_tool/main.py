"""MBTI 测试 — 简易 MBTI 性格测试（本地）

命令：
  /mbti     — 开始测试（回答 8 道题）
  /mbti <E或I> <N或S> <T或F> <J或P> — 直接计算
"""

from graci import on_command, plugin_handler, PluginContext, get_logger
from graci import get_reading, set_reading

logger = get_logger("MBTI测试")

# ── 常量定义 ──
QUESTIONS = [
    ("你更喜欢？", ["E 和朋友一起热闹", "I 独自安静思考"]),
    ("你更关注？", ["N 未来与可能性", "S 现实与细节"]),
    ("做决定时更靠？", ["T 逻辑分析", "F 感受体谅"]),
    ("你的生活方式？", ["J 计划有序", "P 灵活随性"]),
    ("聚会后你？", ["E 更精神了", "I 需要独处充电"]),
    ("学习新事物时？", ["N 先看整体框架", "S 一步步来"]),
    ("朋友倾诉时？", ["T 给建议分析", "F 倾听共情"]),
    ("面对变化？", ["J 提前规划", "P 随遇而安"]),
]
TYPES = {
    "INTJ": "建筑师", "INTP": "逻辑学家", "ENTJ": "指挥官", "ENTP": "辩论家",
    "INFJ": "提倡者", "INFP": "调停者", "ENFJ": "主人公", "ENFP": "竞选者",
    "ISTJ": "物流师", "ISFJ": "守卫者", "ESTJ": "总经理", "ESFJ": "执政官",
    "ISTP": "鉴赏家", "ISFP": "探险家", "ESTP": "企业家", "ESFP": "表演者",
}


@on_command("/mbti", "/性格测试", "/mbti测试")
@plugin_handler
async def handle_mbti(ctx: PluginContext):
    """MBTI 性格测试"""
    uid = str(getattr(ctx, "sender_id", "") or "")
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)

    # 直接计算模式：/mbti E N T J
    if len(parts) > 1:
        args = parts[1].upper().replace(" ", "")
        if len(args) == 4 and all(c in "EISNTFJP" for c in args):
            result = args
            await ctx.reply(f"🧬 你的 MBTI: **{result}** — {TYPES.get(result, '未知类型')}")
            return

    # 开始测试
    if len(parts) < 2 or parts[1].strip() == "开始":
        set_reading(uid, {"mode": "mbti", "q": 0, "answers": ""})
        q, opts = QUESTIONS[0]
        await ctx.reply(f"🧬 MBTI 测试（共 {len(QUESTIONS)} 题）\n━━━━━━━━━━━━\n📝 {q}\n1️⃣ {opts[0]}\n2️⃣ {opts[1]}\n💡 回复 1 或 2")
        return

    # 回答模式
    game = get_reading(uid)
    if not game or game.get("mode") != "mbti":
        await ctx.reply("请先 /mbti 开始测试")
        return

    choice = parts[1].strip()
    if choice not in ("1", "2"):
        await ctx.reply("❌ 请回复 1 或 2")
        return

    q_idx = game["q"]
    _, opts = QUESTIONS[q_idx]
    answer_key = opts[int(choice) - 1][0]
    game["answers"] += answer_key
    game["q"] += 1

    if game["q"] >= len(QUESTIONS):
        ans = game["answers"]
        result = (
            ("E" if ans.count("E") > ans.count("I") else "I") +
            ("N" if ans.count("N") > ans.count("S") else "S") +
            ("T" if ans.count("T") > ans.count("F") else "F") +
            ("J" if ans.count("J") > ans.count("P") else "P")
        )
        set_reading(uid, None)
        await ctx.reply(
            f"🧬 测试完成！\n"
            f"━━━━━━━━━━━━\n"
            f"🎯 你的 MBTI: **{result}**\n"
            f"🏷️ {TYPES.get(result, '未知类型')}\n"
            f"💡 /mbti 再来一次"
        )
        return

    set_reading(uid, game)
    q, opts = QUESTIONS[game["q"]]
    await ctx.reply(f"📝 第 {game['q'] + 1}/{len(QUESTIONS)} 题: {q}\n1️⃣ {opts[0]}\n2️⃣ {opts[1]}")
