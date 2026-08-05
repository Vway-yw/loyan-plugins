"""成语接龙 — 与机器人成语接龙游戏（HTML 卡片渲染）

命令：
  /成语             — 开始成语接龙
  /成语 提示        — 获取当前接龙提示
  /成语 结束        — 结束游戏
  直接回复成语       — 接龙（首字需与上句末字相同）

规则：
  - 四字成语，下一句首字 = 上一句末字
  - 重复成语 / 非成语 / 接不上 判负
"""

import asyncio
import json
import os
import random
import re
import secrets
import time
from typing import Dict, List, Optional

from graci import on_command, plugin_handler, PluginContext, LoyanImage
from graci import on_fallback
from graci import get_logger
from graci import get_reading, set_reading

logger = get_logger("成语接龙")

# ── 常量定义 ──
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
IDIOM_FILE = os.path.join(PLUGIN_DIR, "idiom4.json")
TIMEOUT = 120       # 每回合超时秒数
MAX_ROUNDS = 20     # 最大回合数
RENDER_WIDTH = 520  # 渲染图片宽度

# ── 模块级状态 ──
_idiom_index: Optional[Dict[str, List[str]]] = None
_all_idioms: Optional[List[str]] = None
_browser = None
_browser_lock = asyncio.Lock()


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
    return random.choice(candidates)


def _format_used(used: List[str]) -> str:
    """格式化已用成语列表"""
    if not used:
        return ""
    lines = ["  ".join(used[i:i + 4]) for i in range(0, len(used), 4)]
    return "\n".join(lines)


# ── HTML 渲染 ──

async def _get_browser():
    """懒加载 Playwright 浏览器"""
    global _browser
    if _browser is None or not _browser.is_connected():
        from playwright.async_api import async_playwright
        pw = await async_playwright().start()
        _browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
    return _browser


def _html_card(title: str, used: List[str], last_char: str, status: str, footer: str = "") -> str:
    """生成成语接龙 HTML 卡片"""
    chain_html = ""
    for i, w in enumerate(used):
        if i == 0:
            chain_html += f'<span class="idiom first">{w}</span>'
        elif i == len(used) - 1:
            chain_html += f'<span class="arrow">→</span><span class="idiom last">{w}</span>'
        else:
            chain_html += f'<span class="arrow">→</span><span class="idiom">{w}</span>'

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: "Noto Sans CJK SC", "PingFang SC", sans-serif; background: #1a1a2e; }}
  .card {{ width: {RENDER_WIDTH}px; padding: 24px; background: linear-gradient(135deg, #16213e, #1a1a2e);
          border-radius: 16px; color: #eee; }}
  .header {{ text-align: center; margin-bottom: 16px; }}
  .title {{ font-size: 26px; font-weight: bold; color: #f8c15c; letter-spacing: 2px; }}
  .subtitle {{ font-size: 12px; color: #8899aa; margin-top: 4px; }}
  .chain {{ background: rgba(255,255,255,0.06); border-radius: 12px; padding: 16px 12px; margin-bottom: 16px;
           display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 6px; }}
  .idiom {{ background: #2a3a55; border-radius: 8px; padding: 8px 10px; font-size: 20px; font-weight: bold; color: #dde6f0; }}
  .idiom.first {{ background: #f8c15c; color: #1a1a2e; }}
  .idiom.last {{ background: #4ecdc4; color: #1a1a2e; box-shadow: 0 0 12px rgba(78,205,196,0.4); }}
  .arrow {{ color: #8899aa; font-size: 14px; }}
  .status {{ text-align: center; font-size: 18px; color: #4ecdc4; margin-bottom: 12px; }}
  .prompt {{ text-align: center; font-size: 14px; color: #aabbcc; margin-bottom: 16px; }}
  .footer {{ text-align: center; font-size: 12px; color: #667788; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px; }}
</style></head><body>
  <div class="card">
    <div class="header">
      <div class="title">🎴 成语接龙</div>
      <div class="subtitle">{title}</div>
    </div>
    <div class="chain">{chain_html}</div>
    <div class="status">{status}</div>
    <div class="prompt">💡 /成语 提示 · /成语 结束</div>
    <div class="footer">{footer}</div>
  </div>
</body></html>"""


async def _render_card(html: str) -> Optional[str]:
    """渲染 HTML 卡片为图片，返回本地路径"""
    try:
        browser = await _get_browser()
        async with _browser_lock:
            page = await browser.new_page()
            try:
                await page.set_content(html, wait_until="networkidle")
                card = await page.query_selector(".card")
                if not card:
                    return None
                temp_dir = os.path.join(PLUGIN_DIR, "data")
                os.makedirs(temp_dir, exist_ok=True)
                path = os.path.join(temp_dir, f"idiom_{secrets.token_hex(4)}.png")
                await card.screenshot(path=path, type="png")
                return path
            finally:
                await page.close()
    except Exception as e:
        logger.error(f"渲染失败: {e}")
        return None


async def _reply_card(ctx: PluginContext, title: str, used: List[str], last_char: str, status: str, footer: str = ""):
    """发送 HTML 卡片（失败时回退文本）"""
    html = _html_card(title, used, last_char, status, footer)
    path = await _render_card(html)
    if path:
        try:
            await ctx.send(LoyanImage(file_path=path))
            return True
        except Exception as e:
            logger.error(f"发送图片失败: {e}")
    await ctx.reply(
        f"{status}\n"
        f"━━━━━━━━━━━━\n"
        f"{_format_used(used)}\n"
        f"💡 请接「{last_char}」字开头"
    )
    return False


def _start_game(ctx: PluginContext):
    """开始新游戏：机器人先出题"""
    uid = str(getattr(ctx, "sender_id", "") or "")
    idx = _load_idioms()
    if not idx:
        return None, "😢 成语库未就绪，请稍后再试"
    first = random.choice(random.choice(list(idx.values())))
    game = {
        "mode": "idiom",
        "used": [first],
        "last_char": first[-1],
        "round": 1,
        "start_time": time.time(),
    }
    set_reading(uid, game)
    return game, None


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
        await _reply_card(
            ctx, "游戏结束", game["used"], "",
            f"🏁 共接 {len(game['used']) - 1} 个成语",
            "期待下次再战！/成语 开始"
        )
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
    game, err = _start_game(ctx)
    if err:
        await ctx.reply(err)
        return
    await _reply_card(
        ctx, "游戏开始", game["used"], game["last_char"],
        f"请接「{game['last_char']}」字开头的成语",
        f"⏱️ 限时 {TIMEOUT} 秒 · 第 {game['round']} 轮"
    )


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
        set_reading(uid, None)
        await ctx.reply(f"⏰ 超时未接！游戏结束，共接 {len(game['used']) - 1} 个成语")
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
        await _reply_card(
            ctx, "🎉 你赢了！", game["used"], "",
            f"连对 {MAX_ROUNDS} 轮！太强了",
            "/成语 再来一局"
        )
        return True

    # 机器人接龙
    response = _find_response(word[-1], set(game["used"]))
    if not response:
        set_reading(uid, None)
        await _reply_card(
            ctx, "🏆 恭喜获胜！", game["used"], "",
            f"「{word[-1]}」字成语已被用尽 · 共接 {len(game['used']) - 1} 个",
            "/成语 再来一局"
        )
        return True

    game["used"].append(response)
    game["last_char"] = response[-1]
    game["turn_time"] = time.time()
    set_reading(uid, game)

    await _reply_card(
        ctx, "✅ 接得好！", game["used"], game["last_char"],
        f"请接「{game['last_char']}」字开头",
        f"⏱️ 限时 {TIMEOUT} 秒 · 第 {game['round']} 轮"
    )
    return True


@on_fallback()
async def handle_answer_fallback(self_bot, bot, message, user_id, chat_type, permission, log_func):
    """兜底：拦截未匹配消息作为成语接龙"""
    async def _reply(text):
        await bot(str(user_id), text, chat_type=chat_type)

    async def _send(seg, ct=None):
        await bot(str(user_id), seg, chat_type=chat_type)
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
    ctx.send = _send
    return await _handle_answer(ctx)
