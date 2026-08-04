"""备忘录 — 简单的文本备忘（本地存储）

命令：
  /备忘                    — 查看所有备忘
  /备忘 添加 <内容>        — 添加备忘
  /备忘 删除 <编号>        — 删除备忘
  /备忘 清空               — 清空全部
"""

import json
import os
from datetime import datetime

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("备忘录")

# ── 常量定义 ──
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memo.json")
MAX_ITEMS = 50


def _load() -> list:
    """加载备忘"""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save(data: list):
    """保存备忘"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@on_command("/备忘", "/memo", "/记一下")
@plugin_handler
async def handle_memo(ctx: PluginContext):
    """备忘录管理"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 2)
    data = _load()

    # 无参数：查看全部
    if len(parts) < 2:
        if not data:
            await ctx.reply("📝 暂无备忘\n💡 /备忘 添加 <内容>\n例：/备忘 添加 记得买牛奶")
            return
        lines = ["📝 备忘列表", "━━━━━━━━━━━━"]
        for i, item in enumerate(data, 1):
            lines.append(f"{i}. {item['text'][:40]}")
            lines.append(f"   📌 {item['time']}")
        lines.append("━━━━━━━━━━━━\n💡 /备忘 删除 <编号>")
        await ctx.reply("\n".join(lines))
        return

    action = parts[1].strip()
    if action == "添加":
        text = parts[2].strip() if len(parts) > 2 else ""
        if not text:
            await ctx.reply("❌ 用法：/备忘 添加 <内容>")
            return
        if len(data) >= MAX_ITEMS:
            await ctx.reply(f"❌ 最多 {MAX_ITEMS} 条备忘")
            return
        data.append({"text": text, "time": datetime.now().strftime("%m-%d %H:%M")})
        _save(data)
        await ctx.reply(f"✅ 已添加备忘（共 {len(data)} 条）")
    elif action == "删除":
        idx = parts[2].strip() if len(parts) > 2 else ""
        if not idx.isdigit():
            await ctx.reply("❌ 用法：/备忘 删除 <编号>")
            return
        i = int(idx) - 1
        if 0 <= i < len(data):
            removed = data.pop(i)
            _save(data)
            await ctx.reply(f"✅ 已删除: {removed['text'][:30]}")
        else:
            await ctx.reply(f"❌ 编号超出范围（1-{len(data)}）")
    elif action == "清空":
        _save([])
        await ctx.reply("✅ 已清空全部备忘")
    else:
        await ctx.reply("❌ 用法：/备忘 查看|添加|删除|清空")
