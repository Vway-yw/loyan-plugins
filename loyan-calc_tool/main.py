"""计算器 — 数学表达式计算

命令：
  /计算 <表达式>    — 计算表达式（如 /计算 (1+2)*3）
  /calc <表达式>    — 同 /计算
"""

import math
import re

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("计算器")

# ── 常量定义 ──
MAX_LEN = 100
# 允许的字符
ALLOWED = set("0123456789+-*/().,% sqrt^ ")


def _safe_eval(expr: str):
    """安全计算表达式"""
    expr = expr.replace("^", "**").replace("sqrt", "math.sqrt")
    if not all(c in ALLOWED for c in expr):
        raise ValueError("包含非法字符")
    return eval(expr, {"__builtins__": {}}, {"math": math})


@on_command("/计算", "/calc", "/算一下")
@plugin_handler
async def handle_calc(ctx: PluginContext):
    """计算表达式"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    expr = parts[1].strip() if len(parts) > 1 else ""

    if not expr:
        await ctx.reply("🧮 用法：/计算 <表达式>\n例：/计算 (1+2)*3\n例：/计算 sqrt(16)+2^3")
        return
    if len(expr) > MAX_LEN:
        await ctx.reply(f"❌ 表达式过长（最多 {MAX_LEN} 字符）")
        return

    try:
        result = _safe_eval(expr)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        result_str = f"{result:,.10f}".rstrip("0").rstrip(".") if isinstance(result, float) else f"{result:,}"
        await ctx.reply(
            f"🧮 计算器\n"
            f"━━━━━━━━━━━━\n"
            f"📝 {expr}\n"
            f"= **{result_str}**"
        )
    except ZeroDivisionError:
        await ctx.reply("❌ 除数为零！")
    except Exception as e:
        logger.error(f"计算失败: {e}")
        await ctx.reply("❌ 表达式无法计算，请检查格式")
