"""成语接龙 — 与机器人成语接龙游戏

命令：
  /成语             — 开始成语接龙
  /成语 提示        — 获取当前接龙提示
  /成语 结束        — 结束游戏
  直接回复成语       — 接龙（首字需与上句末字相同）

规则：
  - 四字成语，下一句首字 = 上一句末字
  - 重复成语 / 非成语 / 接不上 判负
"""

import json
import os
import random
import re
import time
from typing import Dict, List, Optional

from loyan.core.decorators import on_command, plugin_handler, PluginContext
from loyan.core.decorators.registration import on_fallback
from graci import get_logger
from loyan.plugins.core.reading import get_reading, set_reading

logger = get_logger("成语接龙")

# ── 常量定义 ──
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
IDIOM_FILE = os.path.join(PLUGIN_DIR, "idiom4.json")
TIMEOUT = 120       # 每回合超时秒数
MAX_ROUNDS = 20     # 最大回合数
HINT_COST = 3       # 提示需要接上的次数（简单计分用）

# ── 模块级状态 ──
_idiom_index: Optional[Dict[str, List[str]]] = None
_all_idioms: Optional[List[str]] = None


def _load_idioms() -> Dict[str, List[str]]:
    """加载成语库（首字索引），懒加载并缓存"""
    global _idiom_index, _all_idioms
    if _idiom_index is not None:
        return _idiom_index
    try:
        with open(IDIOM_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        _idiom_index = data.get("index", {})
        _all_idioms = [w for lst in _idiom_index.values() for w in lst]
    except Exception as e:
        logger.error(f"成语库加载失败: {e}")
        _idiom_index = {}
        _all_idioms = []
    return _idiom_index


def _is_idiom(word: str) -> bool:
    """判断是否为成语库中的四字成语"""
    idx = _load_idioms()
    return word in idx.get(word[:1], [])


def _find_response(last_char: str, used: set) -> Optional[str]:
    """找出以 last_char 开头且未用过的成语"""
    idx = _load_idioms()
    candidates = [w for w in idx.get(last_char, []) if w not in used]
    if not candidates:
        return None
    # 优先选能接下去的（双字回环策略：尽量让对方接不上 -> 随机即可）
    return random.choice(candidates)


def _format_used(used: List[str]) -> str:
    """格式化已用成语列表"""
    if not used:
        return ""
    lines = ["  ".join(used[i:i + 4]) for i in range(0, len(used), 4)]
    return "\n".join(lines)


def _start_game(ctx: PluginContext):
    """开始新游戏：机器人先出题"""
    uid = str(getattr(ctx, "sender_id", "") or "")
    idx = _load_idioms()
    if not idx:
        return "😢 成语库未就绪，请稍后再试"
    first = random.choice(random.choice(list(idx.values())))
    game = {
        "mode": "idiom",
        "used": [first],
        "last_char": first[-1],
        "round": 1,
        "start_time": time.time(),
    }
    set_reading(uid, game)
    return (
        f"🎮 成语接龙开始！\n"
        f"📖 {first}\n"
        f"━━━━━━━━━━━━\n"
        f"请接「{first[-1]}」字开头的成语\n"
        f"💡 /成语 提示 或 /成语 结束"
    )


@on_command("/成语", "/成语接龙")
@plugin_handler
async def handle_idiom(ctx: PluginContext):
    """成语接龙主命令：开始 / 提示 / 结束"""
    uid = str(getattr(ctx, "sender_id", "") or "")
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    action = parts[1].strip() if len(parts) > 1 else ""

    if action == "结束":
        game = get_reading(uid)
        if not game or game.get("mode") != "idiom":
            await ctx.reply("当前没有进行中的成语接龙")
            return
        set_reading(uid, None)
        await ctx.reply(f"🏁 游戏结束！本轮共接 {len(game['used']) - 1} 个成语\n{_format_used(game['used'])}")
        return

    if action == "提示":
        game = get_reading(uid)
        if not game or game.get("mode") != "idiom":
            await ctx.reply("请先 /成语 开始游戏")
            return
        idx = _load_idioms()
        candidates = [w for w in idx.get(game["last_char"], []) if w not in game["used"]]
        if candidates:
            hint = random.choice(candidates)
            masked = hint[0] + "".join("▢" if i != 1 else hint[1] for i in range(1, 4))
            await ctx.reply(f"💡 提示：{masked}\n（首字「{game['last_char']}」）")
        else:
            await ctx.reply("😅 我也想不到更多了，试试 /成语 结束")
        return

    # 开始游戏
    msg = _start_game(ctx)
    await ctx.reply(msg)


async def _handle_answer(ctx: PluginContext):
    """处理用户回复的成语（接龙）"""
    uid = str(getattr(ctx, "sender_id", "") or "")
    game = get_reading(uid)
    if not game or game.get("mode") != "idiom":
        return False

    word = (ctx.raw_text or "").strip()
    # 只处理纯四字回复（排除命令）
    if not re.fullmatch(r"[\u4e00-\u9fa5]{4}", word):
        return False

    # 超时检查
    if time.time() - game.get("turn_time", game["start_time"]) > TIMEOUT:
        await ctx.reply(f"⏰ 超时未接！游戏结束，共接 {len(game['used']) - 1} 个成语")
        set_reading(uid, None)
        return True

    # 校验：首字匹配
    if word[0] != game["last_char"]:
        await ctx.reply(f"❌ 必须以「{game['last_char']}」字开头！")
        return True

    # 校验：成语库
    if not _is_idiom(word):
        await ctx.reply(f"❌ 「{word}」不是四字成语，再想想？")
        return True

    # 校验：重复
    if word in game["used"]:
        await ctx.reply(f"⚠️ 「{word}」已经用过了，换一个！")
        return True

    # 接龙成功
    game["used"].append(word)
    game["round"] += 1
    game["last_char"] = word[-1]

    if game["round"] > MAX_ROUNDS:
        set_reading(uid, None)
        await ctx.reply(f"🎉 你连对了 {MAX_ROUNDS} 轮！太强了，本轮获胜！\n{_format_used(game['used'])}")
        return True

    # 机器人接龙
    response = _find_response(word[-1], set(game["used"]))
    if not response:
        set_reading(uid, None)
        await ctx.reply(
            f"🏆 恭喜！你赢了！\n"
            f"「{word[-1]}」字开头的成语已被用尽\n"
            f"共接 {len(game['used']) - 1} 个成语\n{_format_used(game['used'])}"
        )
        return True

    game["used"].append(response)
    game["last_char"] = response[-1]
    game["turn_time"] = time.time()
    set_reading(uid, game)

    await ctx.reply(
        f"✅ 接得好！\n"
        f"🤖 {response}\n"
        f"━━━━━━━━━━━━\n"
        f"请接「{response[-1]}」字开头\n"
        f"⏱️ 限时 {TIMEOUT} 秒 · 第 {game['round']} 轮"
    )
    return True


@on_fallback()
async def handle_answer_fallback(self_bot, bot, message, user_id, chat_type, permission, log_func):
    """兜底：拦截未匹配消息作为成语接龙"""
    async def _reply(text):
        await bot(str(user_id), text, chat_type=chat_type)
    ctx = PluginContext(
        sender_id=str(user_id),
        target_id=str(user_id),
        chat_type=chat_type,
        raw_text=(message.get("text", "") if isinstance(message, dict) else str(message or "")),
        text=(message.get("text", "") if isinstance(message, dict) else str(message or "")),
        nickname="",
        images=[],
        ats=[],
        is_at_bot=False,
        command="",
        plugin_name="成语接龙",
        raw_data=message if isinstance(message, dict) else {},
        runtime=None,
    )
    ctx.reply = _reply
    ctx.send = _reply
    return await _handle_answer(ctx)
