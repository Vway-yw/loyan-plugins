"""游戏插件 — 帮助图片绘制"""

import io
import os
import sys

_venv_sp = None
try:
    import site
    _venv_sp = site.getsitepackages()[0]
except Exception:
    for p in sys.path:
        if "site-packages" in p:
            _venv_sp = p
            break
if _venv_sp and _venv_sp not in sys.path:
    sys.path.insert(0, _venv_sp)

from PIL import Image, ImageDraw, ImageFont

from loyan.plugins.core.zhfont import get_zh_font

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_font(size):
    return get_zh_font(size)


async def draw_game_help() -> bytes:
    commands = [
        ("🎣 钓鱼", "抛竿钓鱼，捕获各类鱼获"),
        ("⛏️ 挖矿", "挥舞镐头，挖掘稀有矿石"),
        ("🏹 打猎", "进入森林，狩猎各种猎物"),
        ("💼 打工", "做兼职赚取金币"),
        ("📅 签到", "每日签到获取奖励 + 体力"),
        ("🎲 赌大小 <大/小> <金额>", "猜骰子大小搏一搏"),
        ("🪓 挖宝", "消耗体力挖掘宝藏"),
        ("🎡 转盘 <金额>", "转盘赌运气，0~10倍"),
        ("👊 打BOSS <名称>", "挑战世界BOSS（白虎/朱雀/青龙/玄武/麒麟）"),
        ("📋 任务", "查看每日任务进度"),
        ("🏅 成就", "查看成就列表及解锁进度"),
        ("📚 技能", "查看/升级技能等级"),
        ("🎣 大赛 / 参赛", "查看/报名钓鱼大赛"),
        ("🛒 商店 / 购买", "查看商店/购买物品"),
        ("🎒 背包 / 使用", "查看背包/使用物品"),
        ("🔋 恢复", "恢复体力（每1小时可用）"),
        ("👤 我的信息", "查看你的游戏数据"),
        ("🏆 排行榜", "查看等级排行榜"),
        ("⬆️ 升级", "花费金币购买经验升级"),
        ("✏️ 改名 <名字>", "修改你的游戏昵称"),
        ("🔄 重开", "角色死亡后重置游戏数据（保留名字）"),
        ("🗑️ 注销", "删除所有游戏数据"),
        ("↩️ 撤销", "恢复24小时内注销或重开的数据"),
    ]

    card_w = 420
    card_h = 40 + len(commands) * 52 + 40
    img = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # background
    draw.rounded_rectangle(
        [(0, 0), (card_w - 1, card_h - 1)],
        radius=16, fill=(255, 255, 255, 230),
        outline=(200, 180, 220, 180), width=2,
    )

    title_font = _load_font(22)
    cmd_font = _load_font(16)
    desc_font = _load_font(14)

    # title
    draw.text((24, 20), "🎮 游戏指令大全", fill=(80, 60, 120), font=title_font)

    y = 58
    for cmd, desc in commands:
        # gradient bar
        draw.rounded_rectangle(
            [(16, y - 2), (card_w - 16, y + 40)],
            radius=8, fill=(245, 240, 255, 200),
        )
        draw.text((28, y), cmd, fill=(60, 40, 100), font=cmd_font)
        draw.text((28, y + 22), desc, fill=(140, 130, 160), font=desc_font)
        y += 52

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
