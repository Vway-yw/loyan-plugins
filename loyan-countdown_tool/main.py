"""倒数日 — 记录重要日期并倒计时（本地存储）

命令：
  /倒数日                    — 查看所有记录
  /倒数日 添加 名称 2026-10-01 — 添加记录
  /倒数日 删除 名称           — 删除记录
"""

import json
import os
from datetime import datetime

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("倒数日")

# ── 常量定义 ──
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "countdown.json")
MAX_ITEMS = 20


def _load() -> dict:
    """加载记录"""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict):
    """保存记录"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _parse_date(s: str):
    """解析日期"""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


@on_command("/倒数日", "/纪念日", "/countdowns")
@plugin_handler
async def handle_countdown(ctx: PluginContext):
    """倒数日管理"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 3)
    data = _load()

    # 无参数：查看全部
    if len(parts) < 2:
        if not data:
            await ctx.reply("📅 暂无记录\n💡 /倒数日 添加 <名称> <日期>\n例：/倒数日 添加 生日 2026-10-01")
            return
        lines = ["📅 倒数日列表", "━━━━━━━━━━━━"]
        now = datetime.now()
        for name, date_str in sorted(data.items(), key=lambda x: x[1]):
            target = _parse_date(date_str)
            if not target:
                continue
            delta = (target - now).days
            if delta >= 0:
                lines.append(f"🎯 {name}: 还有 {delta} 天（{date_str}）")
            else:
                lines.append(f"✅ {name}: 已过 {abs(delta)} 天（{date_str}）")
        lines.append("━━━━━━━━━━━━\n💡 /倒数日 添加 <名称> <日期>")
        await ctx.reply("\n".join(lines))
        return

    action = parts[1].strip()
    if action == "添加":
        if len(parts) < 4:
            await ctx.reply("❌ 用法：/倒数日 添加 <名称> <日期>\n例：/倒数日 添加 生日 2026-10-01")
            return
        name = parts[2].strip()
        date_str = parts[3].strip()
        if not _parse_date(date_str):
            await ctx.reply("❌ 日期格式错误（如 2026-10-01）")
            return
        if len(data) >= MAX_ITEMS:
            await ctx.reply(f"❌ 最多记录 {MAX_ITEMS} 条")
            return
        data[name] = date_str
        _save(data)
        await ctx.reply(f"✅ 已添加: {name} → {date_str}")
    elif action == "删除":
        if len(parts) < 3:
            await ctx.reply("❌ 用法：/倒数日 删除 <名称>")
            return
        name = parts[2].strip()
        if name in data:
            del data[name]
            _save(data)
            await ctx.reply(f"✅ 已删除: {name}")
        else:
            await ctx.reply(f"❌ 未找到: {name}")
    else:
        await ctx.reply("❌ 用法：/倒数日 查看|添加|删除")
