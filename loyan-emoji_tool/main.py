"""表情符号 — 表情符号搜索/随机

命令：
  /表情符号       — 随机表情
  /表情符号 笑    — 搜索含关键词的表情
"""

import random

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("表情符号")

# ── 常量定义 ──
EMOJI_DB = {
    "笑": "😀😁😂🤣😊😄😃😆😉😜🤪😝",
    "哭": "😢😭😿😥😔😞😟😠",
    "爱": "❤️🧡💛💚💙💜🖤🤍💕💞💓💗💖💘",
    "动物": "🐶🐱🐭🐹🐰🦊🐻🐼🐨🐯🦁🐮🐷🐸🐵🐔🐧🐦🦆🦅🦉🐴🦄🐝🐢🐙🦑🦐🦀🐬🐳🐋🦈",
    "食物": "🍎🍐🍊🍋🍌🍉🍇🍓🫐🍈🍒🍑🥭🍍🥥🥝🍅🍆🥑🥦🥬🥒🌽🥕🧄🧅🥔🍠🥐🥯🍞🥖🥨🧀🥚🍳🧈🥞🧇🥓🥩🍗🍖🌭🍔🍟🍕🥪🥙🧆🌮🌯🥗🥘🍝🍜🍲🍛🍣🍱🥟🍤🍙🍚🍘🍥🥠🍢🍡🍧🍨🍦🥧🧁🍰🎂🍮🍭🍬🍫🍿🍩🍪🌰🥜",
    "天气": "☀️🌤️⛅🌥️☁️🌦️🌧️⛈️🌩️🌨️❄️☃️🌬️💨💧💦🌊🌫️🌪️🌈☂️",
    "运动": "⚽🏀🏈⚾🎾🏐🏉🎱🏓🏸🥅🏒🏑🥍🏏🥌🎿🛷🥅⛸️🎣🥊🥋🎽🛹🛼⛷️🏂",
    "科技": "💻🖥️⌨️🖱️🖨️📱📲☎️📞📟📠📡📺📻🎙️🎚️🎛️🧭⏱️⏲️",
    "心情": "😀😁😂🤣😃😄😅😆😉😊😋😎😍😘🥰😗😙😚🙂🤗🤔🤨😐😑😶🙄😏😣😥😮🤐😯😪😫😴😌😛😜😝🤤😒😓😔😕🙃🤑😲☹️🙁😖😞😟😤😢😭😦😧😨😩🤯😬😰😱🥵🥶😳🤪😵😡😠🤬😷🤒🤕🤢🤮🤧😇🥳🥺",
}


@on_command("/表情符号", "/emoji", "/表情")
@plugin_handler
async def handle_emoji(ctx: PluginContext):
    """表情符号"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    kw = parts[1].strip() if len(parts) > 1 else ""

    if not kw:
        all_emojis = "".join(EMOJI_DB.values())
        pick = "".join(random.sample(all_emojis, 10))
        await ctx.reply(f"🎨 随机表情\n━━━━━━━━━━━━\n{pick}\n\n💡 /表情符号 笑 /表情符号 动物")
        return

    for key, emojis in EMOJI_DB.items():
        if kw in key or kw in emojis:
            await ctx.reply(f"🎨 「{kw}」相关表情（{key}）\n━━━━━━━━━━━━\n{emojis}")
            return
    await ctx.reply(f"😢 未找到「{kw}」\n💡 分类: {' '.join(EMOJI_DB.keys())}")
