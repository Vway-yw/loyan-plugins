"""翻译 — 中英互译（免费 MyMemory API）

命令：
  /翻译 <文本>            — 自动识别中英互译
  /翻译 en <文本>         — 翻译成英文
  /翻译 zh <文本>         — 翻译成中文
  /翻译 ja <文本>         — 翻译成日语
  /translate <text>       — 英译中
"""

import asyncio
import json
import re
import time
import urllib.parse
import urllib.request
from typing import Dict, Optional

from graci import on_command, plugin_handler, PluginContext
from graci import get_logger

logger = get_logger("翻译")

# ── 常量定义 ──
API_URL = "https://api.mymemory.translated.net/get?q={text}&langpair={pair}"
TIMEOUT = 15
CACHE_TTL = 600

# 语言代码映射
LANG_MAP = {
    "en": "English", "zh": "中文", "ja": "日语", "ko": "韩语",
    "fr": "法语", "de": "德语", "ru": "俄语", "es": "西班牙语",
    "it": "意大利语", "pt": "葡萄牙语", "ar": "阿拉伯语", "th": "泰语",
}
PAIR_MAP = {
    "zh": "zh-CN|en", "en": "en|zh-CN", "ja": "zh-CN|ja",
    "ko": "zh-CN|ko", "fr": "zh-CN|fr", "de": "zh-CN|de",
    "ru": "zh-CN|ru", "es": "zh-CN|es", "it": "zh-CN|it",
    "pt": "zh-CN|pt", "ar": "zh-CN|ar", "th": "zh-CN|th",
}

# ── 模块级状态 ──
_cache: Dict[str, tuple] = {}


def _has_cjk(text: str) -> bool:
    """判断是否包含中文"""
    return bool(re.search(r"[\u4e00-\u9fa5]", text))


def _fetch(text: str, pair: str) -> Optional[str]:
    """请求翻译 API"""
    url = API_URL.format(text=urllib.parse.quote(text[:300]), pair=pair)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    if data.get("responseStatus") == 200:
        translated = data["responseData"]["translatedText"]
        # 清理 MyMemory 的占位符
        return translated.replace("MYMEMORY WARNING", "").strip()
    return None


@on_command("/翻译", "/translate", "/译")
@plugin_handler
async def handle_translate(ctx: PluginContext):
    """翻译文本（中英互译 + 多语言）"""
    rest = (ctx.raw_text or "").strip()

    # 提取语言参数
    lang = ""
    text = rest
    parts = rest.split(None, 2)
    if len(parts) >= 2 and parts[0].lstrip("/") in LANG_MAP:
        lang = parts[0].lstrip("/")
        text = " ".join(parts[1:]) if len(parts) > 2 else (parts[1] if len(parts) == 2 else "")

    if not text:
        await ctx.reply(
            "🌐 翻译助手\n"
            "━━━━━━━━━━━━\n"
            "💡 /翻译 <文本> 自动中英互译\n"
            "🔧 /翻译 en <文本> 指定语言\n"
            "🌍 支持: en/zh/ja/ko/fr/de/ru/es/it/pt/ar/th\n"
            "📖 例：/翻译 hello world"
        )
        return

    # 确定翻译方向
    if not lang:
        pair = "zh-CN|en" if _has_cjk(text) else "en|zh-CN"
        lang = "en" if _has_cjk(text) else "zh"
    else:
        pair = PAIR_MAP.get(lang)
        if not pair:
            await ctx.reply(f"❌ 不支持的语言：{lang}\n支持：{' '.join(LANG_MAP.keys())}")
            return

    await ctx.reply(f"🌐 正在翻译（{LANG_MAP[lang]}）...")
    cache_key = f"{pair}:{text[:100]}"
    now = time.time()
    cached = _cache.get(cache_key)
    if cached and now - cached[0] < CACHE_TTL:
        result = cached[1]
    else:
        result = await asyncio.to_thread(_fetch, text, pair)
        if result:
            _cache[cache_key] = (now, result)

    if not result:
        await ctx.reply("❌ 翻译失败，请稍后再试")
        return

    await ctx.reply(
        f"🌐 翻译结果（{LANG_MAP[lang]}）\n"
        f"━━━━━━━━━━━━\n"
        f"📝 {result}"
    )
