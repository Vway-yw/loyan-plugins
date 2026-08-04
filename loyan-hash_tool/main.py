"""MD5/哈希 — 计算文本哈希值

命令：
  /md5 <文本>      — MD5 哈希
  /sha1 <文本>     — SHA1 哈希
  /sha256 <文本>   — SHA256 哈希
"""

import hashlib

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("哈希工具")

# ── 常量定义 ──
MAX_LEN = 2000


def _hash_text(text: str, algo: str) -> str:
    """计算文本哈希"""
    h = hashlib.new(algo)
    h.update(text.encode("utf-8"))
    return h.hexdigest()


@on_command("/md5", "/sha1", "/sha256", "/哈希")
@plugin_handler
async def handle_hash(ctx: PluginContext):
    """计算文本哈希"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    text = parts[1].strip() if len(parts) > 1 else ""

    if not text:
        await ctx.reply("🔐 用法：\n/md5 <文本>\n/sha1 <文本>\n/sha256 <文本>\n例：/md5 hello")
        return
    if len(text) > MAX_LEN:
        await ctx.reply(f"❌ 文本过长（最多 {MAX_LEN} 字符）")
        return

    algo = ctx.command.lstrip("/").lower()
    if algo == "哈希":
        algo = "md5"
    if algo not in ("md5", "sha1", "sha256"):
        await ctx.reply("❌ 仅支持 md5/sha1/sha256")
        return

    result = _hash_text(text, algo)
    await ctx.reply(
        f"🔐 {algo.upper()} 哈希\n"
        f"━━━━━━━━━━━━\n"
        f"📝 输入: {text[:50]}{'…' if len(text) > 50 else ''}\n"
        f"🔑 结果: {result}"
    )
