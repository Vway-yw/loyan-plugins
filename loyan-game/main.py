import json
import logging
import os
import random
import time
import asyncio
from datetime import datetime, timezone

from graci import LoyanImage

logger = logging.getLogger("Loyan.游戏")

# 串行化游戏状态读写，避免并发覆盖数据
_game_lock = asyncio.Lock()

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYER_FILE = os.path.join(DATA_DIR, "players.json")
STREAK_FILE = os.path.join(DATA_DIR, "streaks.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
TRASH_FILE = os.path.join(DATA_DIR, "trash.json")
TRASH_EXPIRE = 24 * 3600


def _load_players():
    if not os.path.exists(PLAYER_FILE):
        return {}
    try:
        with open(PLAYER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        logger.error("players.json 读取失败，返回空数据")
        return {}


def _save_players(data):
    tmp = PLAYER_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, PLAYER_FILE)
    except OSError as e:
        logger.error(f"players.json 写入失败: {e}")


def _load_streaks():
    if not os.path.exists(STREAK_FILE):
        return {}
    try:
        with open(STREAK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_streaks(data):
    tmp = STREAK_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, STREAK_FILE)
    except OSError as e:
        logger.error(f"streaks.json 写入失败: {e}")


def _load_trash():
    if not os.path.exists(TRASH_FILE):
        return {}
    try:
        with open(TRASH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_trash(data):
    tmp = TRASH_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, TRASH_FILE)
    except OSError as e:
        logger.error(f"trash.json 写入失败: {e}")


def _clean_trash():
    trash = _load_trash()
    now = time.time()
    expired = []
    for uid, t in list(trash.items()):
        ts = t.get("trash_time") if isinstance(t, dict) else None
        if ts is None or now - ts > TRASH_EXPIRE:
            expired.append(uid)
    for uid in expired:
        del trash[uid]
    if expired:
        _save_trash(trash)


def _get_player(players, uid):
    if uid not in players:
        now = time.time()
        players[uid] = {
            "name": "",
            "gold": 100,
            "exp": 0,
            "level": 1,
            "energy": 20,
            "max_energy": 20,
            "last_energy_recover": 0,
            "name_changes": 0,
            "banned": False,
            "inventory": {},
            "double_gold_next": False,
            "lucky_next": False,
            "quests": {},
            "quest_date": "",
            "total_fish": 0,
            "total_mine": 0,
            "total_hunt": 0,
            "total_dig": 0,
            "total_boss": 0,
            "total_work": 0,
            "total_gamble_win": 0,
            "total_earned": 0,
            "total_energy_used": 0,
            "fish_caught": {},
            "ores_mined": {},
            "hunts_killed": {},
            "achievements": [],
            "skills": {},
            "alive": True,
            "created_at": now,
            "last_active": now,
        }
    return players[uid]


def _calc_level(exp):
    level = 1
    need = 100
    while exp >= need:
        level += 1
        need = level * 100
    return level, need


def _level_exp(level):
    return sum((i * 100) for i in range(1, level))


def _add_exp(player, amount):
    old_level = player["level"]
    player["exp"] += amount
    new_level, need = _calc_level(player["exp"])
    leveled_up = new_level > player["level"]
    player["level"] = new_level
    if new_level >= 200 and old_level < new_level:
        player["gold"] += 1000  # 200级后每升一级返回1000金币
    player["max_energy"] = 20 + (new_level - 1) * 2
    if player["energy"] > player["max_energy"]:
        player["energy"] = player["max_energy"]
    return leveled_up, need


def _add_gold(player, amount):
    player["gold"] += amount


def _try_use_energy(player, cost):
    if player["energy"] >= cost:
        player["energy"] -= cost
        return True
    return False


# ── 钓鱼 ──
FISH_TABLE = [
    {"name": "🐟 鲫鱼", "weight": 40, "min_gold": 5, "max_gold": 15, "min_exp": 5, "max_exp": 10},
    {"name": "🐟 鲤鱼", "weight": 30, "min_gold": 8, "max_gold": 20, "min_exp": 8, "max_exp": 15},
    {"name": "🐟 草鱼", "weight": 15, "min_gold": 12, "max_gold": 30, "min_exp": 10, "max_exp": 20},
    {"name": "🐠 金鱼", "weight": 8, "min_gold": 20, "max_gold": 50, "min_exp": 15, "max_exp": 30},
    {"name": "🐠 彩虹鱼", "weight": 4, "min_gold": 30, "max_gold": 80, "min_exp": 20, "max_exp": 40},
    {"name": "🐡 河豚", "weight": 2, "min_gold": 50, "max_gold": 120, "min_exp": 30, "max_exp": 60},
    {"name": "🦈 小鲨鱼", "weight": 0.8, "min_gold": 80, "max_gold": 200, "min_exp": 40, "max_exp": 80},
    {"name": "🐉 龙鱼", "weight": 0.2, "min_gold": 150, "max_gold": 500, "min_exp": 60, "max_exp": 150},
]


def _roll_fish():
    total = sum(f["weight"] for f in FISH_TABLE)
    r = random.random() * total
    cumulative = 0
    for f in FISH_TABLE:
        cumulative += f["weight"]
        if r <= cumulative:
            return f
    return FISH_TABLE[-1]


FISH_EVENTS = [
    {"msg": "鱼漂沉了下去！你用力一提，", "weight": 60},
    {"msg": "水面泛起涟漪，你迅速收线，", "weight": 25},
    {"msg": "鱼线猛地绷紧！经过一番搏斗，", "weight": 10},
    {"msg": "一道金光闪过！你钓到了", "weight": 4},
    {"msg": "水下传来巨大的拉力！你拼尽全力拉上来", "weight": 1},
]


def _roll_fish_event():
    total = sum(e["weight"] for e in FISH_EVENTS)
    r = random.random() * total
    cumulative = 0
    for e in FISH_EVENTS:
        cumulative += e["weight"]
        if r <= cumulative:
            return e["msg"]
    return FISH_EVENTS[0]["msg"]


# ── 挖矿 ──
ORE_TABLE = [
    {"name": "🪨 石头", "weight": 35, "min_gold": 3, "max_gold": 8, "min_exp": 3, "max_exp": 6},
    {"name": "🪨 铁矿石", "weight": 25, "min_gold": 6, "max_gold": 15, "min_exp": 5, "max_exp": 10},
    {"name": "💎 铜矿石", "weight": 18, "min_gold": 10, "max_gold": 25, "min_exp": 8, "max_exp": 15},
    {"name": "💎 银矿石", "weight": 12, "min_gold": 15, "max_gold": 40, "min_exp": 12, "max_exp": 25},
    {"name": "💎 金矿石", "weight": 6, "min_gold": 25, "max_gold": 60, "min_exp": 18, "max_exp": 35},
    {"name": "💎 钻石", "weight": 3, "min_gold": 50, "max_gold": 150, "min_exp": 25, "max_exp": 60},
    {"name": "🔮 远古宝石", "weight": 1, "min_gold": 100, "max_gold": 400, "min_exp": 40, "max_exp": 120},
]


def _roll_ore():
    total = sum(o["weight"] for o in ORE_TABLE)
    r = random.random() * total
    cumulative = 0
    for o in ORE_TABLE:
        cumulative += o["weight"]
        if r <= cumulative:
            return o
    return ORE_TABLE[-1]


MINE_EVENTS = [
    {"msg": "你挥动镐头敲击岩壁，掉落了", "weight": 50},
    {"msg": "岩壁发出清脆的响声，你挖掘到", "weight": 30},
    {"msg": "矿镐敲到一块硬物，仔细一看是", "weight": 15},
    {"msg": "岩缝中闪烁着光芒！你得到了", "weight": 4},
    {"msg": "轰隆一声！岩壁坍塌后露出", "weight": 1},
]


def _roll_mine_event():
    total = sum(e["weight"] for e in MINE_EVENTS)
    r = random.random() * total
    cumulative = 0
    for e in MINE_EVENTS:
        cumulative += e["weight"]
        if r <= cumulative:
            return e["msg"]
    return MINE_EVENTS[0]["msg"]


# ── 打猎 ──
HUNT_TABLE = [
    {"name": "🐇 兔子", "weight": 30, "min_gold": 10, "max_gold": 25, "min_exp": 10, "max_exp": 20},
    {"name": "🦊 狐狸", "weight": 22, "min_gold": 15, "max_gold": 35, "min_exp": 15, "max_exp": 28},
    {"name": "🐗 野猪", "weight": 18, "min_gold": 20, "max_gold": 50, "min_exp": 20, "max_exp": 38},
    {"name": "🐺 狼", "weight": 14, "min_gold": 25, "max_gold": 60, "min_exp": 25, "max_exp": 45},
    {"name": "🦌 鹿", "weight": 10, "min_gold": 30, "max_gold": 80, "min_exp": 30, "max_exp": 55},
    {"name": "🐻 熊", "weight": 4, "min_gold": 50, "max_gold": 150, "min_exp": 40, "max_exp": 80},
    {"name": "🐅 老虎", "weight": 1.5, "min_gold": 80, "max_gold": 250, "min_exp": 50, "max_exp": 120},
    {"name": "🐉 幼龙", "weight": 0.5, "min_gold": 150, "max_gold": 600, "min_exp": 80, "max_exp": 200},
]


def _roll_prey():
    total = sum(h["weight"] for h in HUNT_TABLE)
    r = random.random() * total
    cumulative = 0
    for h in HUNT_TABLE:
        cumulative += h["weight"]
        if r <= cumulative:
            return h
    return HUNT_TABLE[-1]


HUNT_EVENTS = [
    {"msg": "你发现了猎物，一箭命中！获得了", "weight": 45},
    {"msg": "你设下陷阱，成功捕获了", "weight": 28},
    {"msg": "你与猎物展开激烈搏斗，最终战胜了", "weight": 18},
    {"msg": "你追踪了数公里，终于猎到了", "weight": 7},
    {"msg": "传说中的生物出现了！你成功猎杀了", "weight": 2},
]


def _roll_hunt_event():
    total = sum(e["weight"] for e in HUNT_EVENTS)
    r = random.random() * total
    cumulative = 0
    for e in HUNT_EVENTS:
        cumulative += e["weight"]
        if r <= cumulative:
            return e["msg"]
    return HUNT_EVENTS[0]["msg"]


# ── 打工 ──
WORK_QUOTES = [
    "你在餐厅洗了一上午盘子",
    "你帮人搬了一天砖",
    "你在工地搬钢筋",
    "你给人当了一天跑腿",
    "你在奶茶店帮忙",
    "你去发传单",
    "你帮邻居遛狗",
    "你在超市当收银员",
    "你帮人代课",
    "你在码头卸货",
]


def _work_gold(player):
    base = 20 + player["level"] * 5
    bonus = random.randint(-5, 10)
    return max(5, base + bonus)


# ── 签到 ──
def _checkin(uid, players, streaks):
    now = datetime.now(timezone.utc).timestamp()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    player = _get_player(players, uid)

    if uid not in streaks:
        streaks[uid] = {"last_date": "", "count": 0}

    streak = streaks[uid]

    if streak["last_date"] == today:
        return None, None, None, "already", False

    yesterday = datetime.now(timezone.utc).timestamp() - 86400
    yesterday_str = datetime.fromtimestamp(yesterday, tz=timezone.utc).strftime("%Y-%m-%d")

    if streak["last_date"] == yesterday_str:
        streak["count"] += 1
    else:
        streak["count"] = 1

    streak["last_date"] = today

    base_gold = 30 + streak["count"] * 5
    base_exp = 20 + streak["count"] * 3

    if streak["count"] >= 7:
        bonus_gold = 50
        bonus_exp = 30
    elif streak["count"] >= 3:
        bonus_gold = 20
        bonus_exp = 15
    else:
        bonus_gold = 0
        bonus_exp = 0

    gold = base_gold + bonus_gold
    exp = base_exp + bonus_exp

    _add_gold(player, gold)
    leveled_up, need = _add_exp(player, exp)

    player["energy"] = min(player["max_energy"], player["energy"] + 10)

    return gold, exp, streak["count"], "ok", leveled_up


# ── 排行榜 ──
def _get_leaderboard(players, top=10):
    def _sort_key(item):
        data = item[1]
        return (data.get("level", 0), data.get("exp", 0))
    sorted_players = sorted(players.items(), key=_sort_key, reverse=True)
    result = []
    for uid, data in sorted_players[:top]:
        safe_uid = uid[:4] + "****" + uid[-4:] if len(uid) > 8 else uid
        result.append({
            "uid": safe_uid,
            "name": data.get("name", ""),
            "gold": data.get("gold", 0),
            "level": data.get("level", 1),
            "exp": data.get("exp", 0),
        })
    return result


# ── 商店物品 ──
SHOP_ITEMS = {
    "小体力药水": {"price": 30, "desc": "恢复 20 体力"},
    "大体力药水": {"price": 60, "desc": "恢复 50 体力"},
    "经验书": {"price": 40, "desc": "增加 30 经验"},
    "护身符": {"price": 100, "desc": "下一次活动金币翻倍"},
    "幸运星": {"price": 80, "desc": "下一次赌博胜率提高"},
    "复活药水": {"price": 100000, "desc": "复活角色"},
}
SHOP_KEYS = list(SHOP_ITEMS.keys())


def _use_item(player, item_name):
    inv = player.setdefault("inventory", {})
    if item_name not in inv or inv[item_name] <= 0:
        return False, None
    if item_name == "小体力药水":
        player["energy"] = min(player["max_energy"], player["energy"] + 20)
        inv[item_name] -= 1
        return True, f"💚 使用小体力药水，恢复了 20 体力！当前 {player['energy']}/{player['max_energy']}"
    elif item_name == "大体力药水":
        player["energy"] = min(player["max_energy"], player["energy"] + 50)
        inv[item_name] -= 1
        return True, f"💚 使用大体力药水，恢复了 50 体力！当前 {player['energy']}/{player['max_energy']}"
    elif item_name == "经验书":
        leveled_up, need = _add_exp(player, 30)
        inv[item_name] -= 1
        msg = f"📖 使用经验书，获得 30 经验"
        if leveled_up:
            msg += f"\n🎉 升级了！当前等级 Lv.{player['level']}（下次升级需 {need} 经验）"
        return True, msg
    elif item_name == "护身符":
        player["double_gold_next"] = True
        inv[item_name] -= 1
        return True, "🍀 护身符已激活！下一次活动金币翻倍"
    elif item_name == "幸运星":
        player["lucky_next"] = True
        inv[item_name] -= 1
        return True, "⭐ 幸运星已激活！下一次赌博胜率提高"
    elif item_name == "复活药水":
        if player.get("alive", True):
            return True, "💊 你还活着，不用使用复活药水"
        player["alive"] = True
        player["energy"] = min(player["max_energy"], player["energy"] + 30)
        inv[item_name] -= 1
        return True, "💊 使用复活药水，你复活了！恢复 30 体力"
    return False, None


# ── 挖宝 ──
TREASURE_TABLE = [
    {"name": "💩 一坨泥巴", "weight": 25, "min_gold": 0, "max_gold": 2, "min_exp": 1, "max_exp": 3},
    {"name": "🪙 一枚古币", "weight": 20, "min_gold": 5, "max_gold": 20, "min_exp": 3, "max_exp": 8},
    {"name": "🗝️ 生锈的钥匙", "weight": 18, "min_gold": 8, "max_gold": 25, "min_exp": 5, "max_exp": 12},
    {"name": "💎 宝石碎片", "weight": 15, "min_gold": 15, "max_gold": 40, "min_exp": 8, "max_exp": 18},
    {"name": "👑 黄金王冠", "weight": 10, "min_gold": 30, "max_gold": 80, "min_exp": 15, "max_exp": 30},
    {"name": "🔮 魔法宝石", "weight": 7, "min_gold": 50, "max_gold": 150, "min_exp": 20, "max_exp": 45},
    {"name": "⚜️ 远古神器", "weight": 4, "min_gold": 80, "max_gold": 300, "min_exp": 30, "max_exp": 80},
    {"name": "🐉 龙之宝藏", "weight": 1, "min_gold": 200, "max_gold": 800, "min_exp": 50, "max_exp": 200},
]

TREASURE_EVENTS = [
    "你在一棵老树下挖到了", "你在河边沙地里发现了", "你在废弃矿洞深处找到了",
    "你跟着藏宝图挖出了", "你无意间踢开一块石头，下面藏着",
]


def _roll_treasure():
    total = sum(t["weight"] for t in TREASURE_TABLE)
    r = random.random() * total
    cumulative = 0
    for t in TREASURE_TABLE:
        cumulative += t["weight"]
        if r <= cumulative:
            return t
    return TREASURE_TABLE[-1]


# ── 转盘 ──
SPIN_MULTIPLIERS = [0, 0, 0, 0.5, 0.5, 1, 1, 1.5, 1.5, 2, 2, 3, 5, 10]
SPIN_NAMES = {
    0: "💀 空！血本无归",
    0.5: "😅 拿回一半",
    1: "😐 保本",
    1.5: "👍 小赚",
    2: "🎉 翻倍！",
    3: "🔥 三倍！",
    5: "💥 五倍！！",
    10: "👑 十倍大奖！！！",
}


# ── BOSS ──
BOSSES = [
    {"id": "baihu",  "name": "白虎", "hp": 800,  "gold": 120, "exp": 80},
    {"id": "zhuque", "name": "朱雀", "hp": 1000, "gold": 150, "exp": 100},
    {"id": "qinglong", "name": "青龙", "hp": 1200, "gold": 180, "exp": 120},
    {"id": "xuanwu", "name": "玄武", "hp": 1500, "gold": 200, "exp": 140},
    {"id": "qilin",  "name": "麒麟", "hp": 2000, "gold": 300, "exp": 200},
]
BOSS_COOLDOWN = 4 * 3600
BOSS_ENERGY_COST = 70


def _boss_init():
    cfg = _load_config()
    changed = False
    for b in BOSSES:
        key = f"boss_hp_{b['id']}"
        if key not in cfg:
            cfg[key] = b["hp"]
            changed = True
        if f"boss_killed_at_{b['id']}" not in cfg:
            cfg[f"boss_killed_at_{b['id']}"] = 0
            changed = True
    if changed:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)


def _get_boss_state(boss_id):
    cfg = _load_config()
    hp = cfg.get(f"boss_hp_{boss_id}", 0)
    base_hp = next((b["hp"] for b in BOSSES if b["id"] == boss_id), 500)
    killed_at = cfg.get(f"boss_killed_at_{boss_id}", 0)
    return hp, base_hp, killed_at


def _save_boss_hp(boss_id, hp):
    cfg = _load_config()
    cfg[f"boss_hp_{boss_id}"] = hp
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def _set_boss_killed(boss_id):
    cfg = _load_config()
    cfg[f"boss_hp_{boss_id}"] = 0
    cfg[f"boss_killed_at_{boss_id}"] = time.time()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def _load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 每日任务 ──
DAILY_QUESTS_POOL = [
    {"id": "fish3", "desc": "🎣 钓鱼 3 次", "need": {"钓鱼": 3}, "gold": 50, "exp": 30},
    {"id": "mine3", "desc": "⛏️ 挖矿 3 次", "need": {"挖矿": 3}, "gold": 50, "exp": 30},
    {"id": "hunt2", "desc": "🏹 打猎 2 次", "need": {"打猎": 2}, "gold": 60, "exp": 35},
    {"id": "work2", "desc": "💼 打工 2 次", "need": {"打工": 2}, "gold": 40, "exp": 20},
    {"id": "gamble_win2", "desc": "🎲 赌大小赢 2 次", "need": {"赌赢": 2}, "gold": 80, "exp": 40},
    {"id": "dig3", "desc": "🪓 挖宝 3 次", "need": {"挖宝": 3}, "gold": 60, "exp": 35},
    {"id": "boss2", "desc": "👊 打 BOSS 2 次", "need": {"打BOSS": 2}, "gold": 70, "exp": 40},
]


def _roll_daily_quests(count=3):
    return random.sample(DAILY_QUESTS_POOL, min(count, len(DAILY_QUESTS_POOL)))


def _update_quest_progress(player, activity, amount=1):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # 先清理过期任务，避免累加后又被清空
    if player.get("quest_date") != today:
        player["quests"] = {}
    quests = player.get("quests", {})
    for q in quests.values():
        for k in q["need"]:
            if k == activity:
                q["progress"][k] = q["progress"].get(k, 0) + amount


def _check_quest_rewards(player):
    """Return rewards from completed quests and remove them."""
    quests = player.get("quests", {})
    total_gold = 0
    total_exp = 0
    completed_ids = []
    for qid, q in quests.items():
        done = all(q["progress"].get(k, 0) >= v for k, v in q["need"].items())
        if done:
            total_gold += q["gold"]
            total_exp += q["exp"]
            completed_ids.append(qid)
    for qid in completed_ids:
        del quests[qid]
    return total_gold, total_exp, len(completed_ids)


# ── 反噬 & 死亡 ──
def _roll_backlash(player, activity_name):
    """10% backlash, 0.07% death. Returns (message, died)."""
    if not player.get("alive", True):
        return "", False
    if random.random() < 0.0007:
        player["alive"] = False
        return f"\n💀 你死了！{activity_name}时遭遇致命意外……使用复活药水或重开", True
    if random.random() < 0.10:
        r = random.random()
        if r < 0.4:
            loss = max(1, int(player["gold"] * random.uniform(0.03, 0.10)))
            player["gold"] = max(0, player["gold"] - loss)
            return f"\n💢 {activity_name}时出了意外，损失 {loss} 金币", False
        elif r < 0.7:
            loss = random.randint(3, 8)
            player["energy"] = max(0, player["energy"] - loss)
            return f"\n💢 {activity_name}时扭伤了脚，损失 {loss} 体力", False
        else:
            inv = player.get("inventory", {})
            items = [k for k, v in inv.items() if v > 0]
            if items:
                lost = random.choice(items)
                inv[lost] -= 1
                return f"\n💢 {activity_name}时弄丢了 {lost}", False
    return "", False


# ── 成就系统 ──
ACHIEVEMENTS = [
    {"id": "fish10", "name": "🎣 钓鱼新手", "cond": {"total_fish": 10}, "gold": 50, "exp": 30},
    {"id": "fish100", "name": "🎣 钓鱼大师", "cond": {"total_fish": 100}, "gold": 300, "exp": 200},
    {"id": "fish500", "name": "🎣 钓鱼宗师", "cond": {"total_fish": 500}, "gold": 1000, "exp": 800},
    {"id": "mine10", "name": "⛏️ 矿工新手", "cond": {"total_mine": 10}, "gold": 50, "exp": 30},
    {"id": "mine100", "name": "⛏️ 矿工大师", "cond": {"total_mine": 100}, "gold": 300, "exp": 200},
    {"id": "hunt10", "name": "🏹 猎人新手", "cond": {"total_hunt": 10}, "gold": 50, "exp": 30},
    {"id": "hunt100", "name": "🏹 猎人大师", "cond": {"total_hunt": 100}, "gold": 300, "exp": 200},
    {"id": "dig30", "name": "🪓 探险家", "cond": {"total_dig": 30}, "gold": 200, "exp": 150},
    {"id": "boss10", "name": "👊 BOSS 猎人", "cond": {"total_boss": 10}, "gold": 500, "exp": 300},
    {"id": "boss50", "name": "👊 BOSS 屠夫", "cond": {"total_boss": 50}, "gold": 2000, "exp": 1500},
    {"id": "rich", "name": "💰 万元户", "cond": {"total_earned": 10000}, "gold": 500, "exp": 200},
    {"id": "gamble50", "name": "🎲 赌神", "cond": {"total_gamble_win": 50}, "gold": 800, "exp": 400},
    {"id": "lv50", "name": "🏆 等级达人", "cond": {"level": 50}, "gold": 5000, "exp": 3000},
    {"id": "collector", "name": "🐟 鱼类收藏家", "cond": {"unique_fish": 8}, "gold": 1000, "exp": 500},
    {"id": "mineralist", "name": "💎 矿物收藏家", "cond": {"unique_ores": 7}, "gold": 1000, "exp": 500},
    {"id": "hunter_collector", "name": "🦌 猎物收藏家", "cond": {"unique_hunts": 8}, "gold": 1000, "exp": 500},
]


def _check_achievements(player):
    unlocked = set(player.get("achievements", []))
    new_rewards = []
    for ach in ACHIEVEMENTS:
        if ach["id"] in unlocked:
            continue
        met = True
        for key, val in ach["cond"].items():
            if key == "unique_fish":
                if len(player.get("fish_caught", {})) < val:
                    met = False
            elif key == "unique_ores":
                if len(player.get("ores_mined", {})) < val:
                    met = False
            elif key == "unique_hunts":
                if len(player.get("hunts_killed", {})) < val:
                    met = False
            elif player.get(key, 0) < val:
                met = False
        if met:
            unlocked.add(ach["id"])
            _add_gold(player, ach["gold"])
            _add_exp(player, ach["exp"])
            new_rewards.append(ach)
    player["achievements"] = list(unlocked)
    return new_rewards


# ── 技能系统 ──
SKILLS = ["钓鱼技能", "挖矿技能", "打猎技能", "战斗技能"]


def _skill_bonus(skill_lv):
    return skill_lv * 2  # extra gold/exp per level


def _skill_up_cost(skill_lv):
    return (skill_lv + 1) * 50


# ── 钓鱼大赛 ──
TOURNAMENT_DURATION = 300  # 5 minutes
TOURNAMENT_COST = 20  # energy to join


def _get_tournament():
    cfg = _load_config()
    t = cfg.get("tournament", {})
    if not t or t.get("end_time", 0) < time.time():
        return None, 0
    return t, cfg.get("tournament_pot", 0)


def _start_tournament():
    cfg = _load_config()
    cfg["tournament"] = {
        "start_time": time.time(),
        "end_time": time.time() + TOURNAMENT_DURATION,
        "scores": {},
    }
    cfg["tournament_pot"] = 0
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def _end_tournament(players):
    cfg = _load_config()
    t = cfg.get("tournament", {})
    # 清除所有参赛者的参赛标记，避免下一届无法参加
    for p in players.values():
        if p.get("in_tournament"):
            p["in_tournament"] = False
    if not t:
        cfg.pop("tournament", None)
        cfg["tournament_pot"] = 0
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return
    scores = t.get("scores", {})
    if not scores:
        cfg.pop("tournament", None)
        cfg["tournament_pot"] = 0
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return
    winner_uid = max(scores, key=scores.get)
    pot = cfg.get("tournament_pot", 0)
    if winner_uid in players:
        players[winner_uid]["gold"] += pot
    cfg.pop("tournament", None)
    cfg["tournament_pot"] = 0
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


async def _make_image_seg(path):
    return LoyanImage(file_path=path)


async def handle_game(ctx):
    async with _game_lock:
        return await _handle_game_locked(ctx)


async def _handle_game_locked(ctx):
    raw = ctx.raw_text.strip()
    parts = raw.split(maxsplit=1)
    cmd = parts[0].lstrip("/")

    players = _load_players()
    streaks = _load_streaks()
    uid = ctx.sender_id

    player = _get_player(players, uid)

    # auto recover energy
    now = time.time()
    if player["last_energy_recover"] > 0:
        elapsed = now - player["last_energy_recover"]
        recover = int(elapsed / 60)
        if recover > 0:
            player["energy"] = min(player["max_energy"], player["energy"] + recover)
            player["last_energy_recover"] = now
    player["last_energy_recover"] = now
    player["last_active"] = now

    # ── 封禁检查 ──
    if player.get("banned"):
        await ctx.reply("🚫 你的账号已被封禁，无法使用游戏功能")
        return

    # ── 死亡检查 ──
    if not player.get("alive", True):
        if cmd in ("复活药水", "使用", "注销", "撤销"):
            pass
        elif cmd == "重开":
            _clean_trash()
            trash = _load_trash()
            trash[uid] = player.copy()
            trash[uid]["trash_time"] = time.time()
            trash[uid]["trash_type"] = "reset"
            _save_trash(trash)
            now = time.time()
            keep_name = player.get("name", "")
            keep_changes = player.get("name_changes", 0)
            players[uid] = {
                "name": keep_name,
                "gold": 100,
                "exp": 0,
                "level": 1,
                "energy": 20,
                "max_energy": 20,
                "last_energy_recover": 0,
                "name_changes": keep_changes,
                "banned": False,
                "inventory": {},
                "double_gold_next": False,
                "lucky_next": False,
                "quests": {},
                "quest_date": "",
                "achievements": [],
                "skills": {},
                "alive": True,
                "total_fish": 0,
                "total_mine": 0,
                "total_hunt": 0,
                "total_dig": 0,
                "total_boss": 0,
                "total_work": 0,
                "total_gamble_win": 0,
                "total_earned": 0,
                "total_energy_used": 0,
                "fish_caught": {},
                "ores_mined": {},
                "hunts_killed": {},
                "created_at": now,
                "last_active": now,
            }
            _save_players(players)
            await ctx.reply("🔄 你已重开，所有数据已重置！获得 100 金币重新开始")
            return
        await ctx.reply("💀 你已经死了！使用复活药水或输入「重开」重新开始")
        return

    # ── 注销 ──
    if cmd == "注销":
        _clean_trash()
        trash = _load_trash()
        trash[uid] = players.get(uid, {})
        trash[uid]["trash_time"] = time.time()
        trash[uid]["trash_type"] = "delete"
        _save_trash(trash)
        players.pop(uid, None)
        _save_players(players)
        await ctx.reply(f"🗑️ 数据已备份，24小时内可发送「撤销」恢复")
        return

    # ── 撤销 ──
    if cmd == "撤销":
        _clean_trash()
        trash = _load_trash()
        if uid not in trash:
            await ctx.reply("⚠️ 没有找到可恢复的备份数据（超过24小时已自动清除）")
            return
        backup = trash.pop(uid)
        _save_trash(trash)
        backup.pop("trash_time", None)
        backup.pop("trash_type", None)
        players[uid] = backup
        _save_players(players)
        await ctx.reply("✅ 数据已恢复！")
        return

    # ── 强制改名 ──
    if not player.get("name") and cmd not in ("改名", "注销", "撤销", "游戏", "游戏帮助", "我的信息", "商店", "背包", "使用", "用户列表", "金币", "体力", "设置", "封禁", "解封", "开启大赛", "list"):
        await ctx.reply("⚠️ 请先设置昵称！输入「改名 <名字>」开始游戏\n例：改名 钓鱼王")
        return

    # ── 管理员命令 ──
    from graci import get_current_master_id
    is_master = str(uid) == str(get_current_master_id())

    if cmd == "游戏" and is_master:
        args = raw.split(maxsplit=3)
        if len(args) < 2:
            await ctx.reply("管理员命令：\n游戏 金币 <数量>\n游戏 体力 <数量>\n游戏 用户列表\n游戏 设置 <用户ID> 金币 <数量>\n游戏 设置 <用户ID> 体力 <数量>\n游戏 封禁 <用户ID>\n游戏 解封 <用户ID>")
            return
        sub = args[1]
        if sub == "用户列表":
            lines = [f"共 {len(players)} 个用户："]
            for pid, pdata in players.items():
                nm = pdata.get("name", "") or "(未设置)"
                ban = "🚫" if pdata.get("banned") else ""
                lines.append(f"{pid[:8]}... {nm} {ban}")
            await ctx.reply("\n".join(lines))
            return
        if sub == "金币" and len(args) >= 3:
            try:
                amt = int(args[2])
                player["gold"] = amt
                _save_players(players)
                await ctx.reply(f"✅ 已将你的金币设为 {amt}")
            except ValueError:
                await ctx.reply("⚠️ 数量必须为数字")
            return
        if sub == "体力" and len(args) >= 3:
            try:
                amt = int(args[2])
                player["energy"] = amt
                _save_players(players)
                await ctx.reply(f"✅ 已将你的体力设为 {amt}")
            except ValueError:
                await ctx.reply("⚠️ 数量必须为数字")
            return
        if sub == "设置" and len(args) >= 5:
            target = args[2]
            field = args[3]
            try:
                val = int(args[4])
            except ValueError:
                await ctx.reply("⚠️ 数量必须为数字")
                return
            if target not in players:
                await ctx.reply("⚠️ 该用户不存在")
                return
            if field == "金币":
                players[target]["gold"] = val
                _save_players(players)
                await ctx.reply(f"✅ 已设置 {target[:8]}... 的金币为 {val}")
            elif field == "体力":
                players[target]["energy"] = val
                _save_players(players)
                await ctx.reply(f"✅ 已设置 {target[:8]}... 的体力为 {val}")
            else:
                await ctx.reply("⚠️ 支持字段：金币 / 体力")
            return
        if sub == "封禁" and len(args) >= 3:
            target = args[2]
            if target not in players:
                await ctx.reply("⚠️ 该用户不存在")
                return
            players[target]["banned"] = True
            _save_players(players)
            await ctx.reply(f"✅ 已封禁 {target[:8]}...")
            return
        if sub == "解封" and len(args) >= 3:
            target = args[2]
            if target not in players:
                await ctx.reply("⚠️ 该用户不存在")
                return
            players[target]["banned"] = False
            _save_players(players)
            await ctx.reply(f"✅ 已解封 {target[:8]}...")
            return
        if sub == "开启大赛":
            _start_tournament()
            await ctx.reply("🎣 钓鱼大赛已开启！持续5分钟，用「参赛」报名！")
            return
        await ctx.reply("未知管理员命令。用 游戏 查看帮助")
        return

    # ── list game (master only) ──
    if cmd == "list":
        from graci import get_current_master_id
        if str(uid) != str(get_current_master_id()):
            await ctx.reply("⚠️ 仅管理员可用")
            return
        if len(parts) >= 2 and parts[1].strip() == "game":
            lines = [f"📋 玩家列表（共 {len(players)} 人）"]
            for pid, pdata in players.items():
                nm = pdata.get("name", "") or "(未设置)"
                ban = " 🚫" if pdata.get("banned") else ""
                lines.append(f"{pid} | {nm}{ban}")
            await ctx.reply("\n".join(lines))
            return

    # ── 商店 ──
    if cmd == "商店":
        lines = ["🛒 **游戏商店**\n"]
        for k, v in SHOP_ITEMS.items():
            lines.append(f"{k} — {v['price']} 金币（{v['desc']}）")
        lines.append("\n💡 用「购买 <物品名>」购买")
        await ctx.reply("\n".join(lines))
        _save_players(players)
        return

    # ── 购买 ──
    if cmd == "购买":
        if len(parts) < 2:
            await ctx.reply("⚠️ 用法：购买 <物品名>\n可用：小体力药水、大体力药水、经验书、护身符、幸运星")
            return
        item_name = parts[1].strip()
        if item_name not in SHOP_ITEMS:
            await ctx.reply(f"⚠️ 没有「{item_name}」，可用：{'、'.join(SHOP_KEYS)}")
            return
        price = SHOP_ITEMS[item_name]["price"]
        if player["gold"] < price:
            await ctx.reply(f"⚠️ 金币不足！{item_name} 需 {price} 金币（你只有 {player['gold']}）")
            return
        player["gold"] -= price
        inv = player.setdefault("inventory", {})
        inv[item_name] = inv.get(item_name, 0) + 1
        _save_players(players)
        await ctx.reply(f"✅ 购买了 {item_name}！花费 {price} 金币，剩余 {player['gold']} 金币")
        return

    # ── 背包 ──
    if cmd == "背包":
        inv = player.get("inventory", {})
        has_items = {k: v for k, v in inv.items() if v > 0}
        if not has_items:
            await ctx.reply("🎒 背包空空如也，去商店买点东西吧！")
            return
        lines = ["🎒 **我的背包**\n"]
        for k, v in has_items.items():
            lines.append(f"{k} ×{v}")
        lines.append("\n💡 用「使用 <物品名>」使用物品")
        await ctx.reply("\n".join(lines))
        return

    # ── 使用 ──
    if cmd == "使用":
        if len(parts) < 2:
            await ctx.reply("⚠️ 用法：使用 <物品名>")
            return
        item_name = parts[1].strip()
        ok, msg = _use_item(player, item_name)
        if not ok:
            await ctx.reply(f"⚠️ 你没有{item_name}，或无法使用")
            return
        _save_players(players)
        await ctx.reply(msg)
        return

    # ── 每日任务 ──
    if cmd == "任务":
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if player.get("quest_date") != today:
            quests = _roll_daily_quests(3)
            player["quests"] = {q["id"]: {"desc": q["desc"], "need": q["need"], "gold": q["gold"], "exp": q["exp"], "progress": {k: 0 for k in q["need"]}} for q in quests}
            player["quest_date"] = today
        qdata = player.get("quests", {})
        if not qdata:
            await ctx.reply("📋 今日暂无任务，试试重新登录")
            return
        lines = ["📋 **每日任务**\n"]
        finished = True
        for qid, q in qdata.items():
            progress_parts = []
            for k, v in q["need"].items():
                current = q["progress"].get(k, 0)
                progress_parts.append(f"{current}/{v}")
            done = all(q["progress"].get(k, 0) >= v for k, v in q["need"].items())
            status = "✅" if done else "⏳"
            if not done:
                finished = False
            lines.append(f"{status} {q['desc']}（{'/'.join(progress_parts)}）💰+{q['gold']} ✨+{q['exp']}")
        if finished:
            lines.append("\n🎉 今日任务全部完成！")
        await ctx.reply("\n".join(lines))
        _save_players(players)
        return

    # ── 挖宝 ──
    if cmd == "挖宝":
        if not _try_use_energy(player, 6):
            await ctx.reply(f"⚠️ 体力不足（当前 {player['energy']}/{player['max_energy']}），可用 恢复 补充")
            _save_players(players)
            return
        treasure = _roll_treasure()
        event = random.choice(TREASURE_EVENTS)
        gold = random.randint(treasure["min_gold"], treasure["max_gold"])
        exp_amt = random.randint(treasure["min_exp"], treasure["max_exp"])
        if player.pop("double_gold_next", False):
            gold *= 2
        bl_msg, died = _roll_backlash(player, "挖宝")
        if died:
            _save_players(players)
            await ctx.reply(f"🪓 {event} {treasure['name']}！{bl_msg}")
            return
        _add_gold(player, gold)
        leveled_up, need = _add_exp(player, exp_amt)
        player["total_dig"] = player.get("total_dig", 0) + 1
        player["total_energy_used"] = player.get("total_energy_used", 0) + 6
        _update_quest_progress(player, "挖宝")
        qg, qe, qc = _check_quest_rewards(player)
        if qg or qe:
            _add_gold(player, qg)
            _add_exp(player, qe)
        msg = f"🪓 {event} {treasure['name']}！\n💰 +{gold} 金币  ✨ +{exp_amt} 经验{bl_msg}"
        if qg or qe:
            msg += f"\n📋 任务完成 +{qg}💰 +{qe}✨"
        if leveled_up:
            msg += f"\n🎉 升级了！当前等级 Lv.{player['level']}（下次升级需 {need} 经验）"
        _save_players(players)
        await ctx.reply(msg)
        return

    # ── 转盘 ──
    if cmd == "转盘":
        if len(parts) < 2:
            await ctx.reply("⚠️ 用法：转盘 <金额>\n例：转盘 100\n🎡 随机获得 0~10 倍奖励")
            return
        try:
            bet = int(parts[1])
        except ValueError:
            await ctx.reply("⚠️ 金额必须为数字")
            return
        if bet <= 0:
            await ctx.reply("⚠️ 金额必须大于0")
            return
        if player["gold"] < bet:
            await ctx.reply(f"⚠️ 金币不足！你只有 {player['gold']} 金币")
            return
        player["gold"] -= bet
        bl_msg, died = _roll_backlash(player, "转盘")
        if died:
            _save_players(players)
            await ctx.reply(f"🎡 转盘还没转就{bl_msg}")
            return
        mul = random.choice(SPIN_MULTIPLIERS)
        winnings = int(bet * mul)
        player["gold"] += winnings
        exp_amt = random.randint(1, 10)
        leveled_up, need = _add_exp(player, exp_amt)
        result_name = SPIN_NAMES.get(mul, f"{mul}倍")
        msg = f"🎡 **转盘结果**\n赌注：{bet} 金币\n结果：{result_name}\n获得：{winnings} 金币{bl_msg}"
        if leveled_up:
            msg += f"\n🎉 升级了！当前等级 Lv.{player['level']}"
        _save_players(players)
        await ctx.reply(msg)
        return

    # ── 打BOSS ──
    if cmd in ("打BOSS", "boss", "打boss"):
        _boss_init()
        parts = raw.split(maxsplit=1)
        target = parts[1].strip() if len(parts) > 1 else ""

        if not target:
            lines_list = ["🐉 **世界BOSS列表**\n"]
            for b in BOSSES:
                hp, base_hp, killed_at = _get_boss_state(b["id"])
                remaining = killed_at + BOSS_COOLDOWN - time.time() if killed_at > 0 else 0
                if hp <= 0 and remaining > 0:
                    h = int(remaining // 3600)
                    m = int((remaining % 3600) // 60)
                    status = f"⏳ 冷却中 ({h}h{m}min)"
                elif hp <= 0:
                    status = "✅ 可挑战"
                else:
                    status = f"💢 HP {hp:.0f}/{base_hp}"
                lines_list.append(f"{b['name']}：{status}")
            lines_list.append("\n⚔️ 攻击消耗 70 体力")
            lines_list.append("📝 使用「打BOSS <名称>」挑战指定BOSS")
            await ctx.reply("\n".join(lines_list))
            _save_players(players)
            return

        boss = None
        for b in BOSSES:
            if target in (b["name"], b["id"]):
                boss = b
                break
        if not boss:
            names = "、".join(b["name"] for b in BOSSES)
            await ctx.reply(f"⚠️ 未知BOSS！可选：{names}")
            _save_players(players)
            return

        hp, base_hp, killed_at = _get_boss_state(boss["id"])
        remaining = killed_at + BOSS_COOLDOWN - time.time() if killed_at > 0 else 0

        if hp <= 0 and remaining > 0:
            h = int(remaining // 3600)
            m = int((remaining % 3600) // 60)
            await ctx.reply(f"⏳ {boss['name']}已被击败，需等待 {h}h{m}min 后刷新")
            _save_players(players)
            return

        if hp <= 0:
            hp = base_hp
            _save_boss_hp(boss["id"], hp)

        if not _try_use_energy(player, BOSS_ENERGY_COST):
            await ctx.reply(f"⚠️ 体力不足！打 BOSS 需要 70 体力（当前 {player['energy']}/{player['max_energy']}）")
            _save_players(players)
            return

        skills = player.setdefault("skills", {})
        combat_skill = skills.get("战斗技能", 0)
        dmg_bonus = combat_skill * 2
        damage = random.randint(10, 30) + player["level"] * 2 + dmg_bonus
        hp -= damage

        death_msg = ""
        if random.random() < 0.0007:
            player["alive"] = False
            _save_players(players)
            await ctx.reply(f"👊 **{boss['name']} 战**\n💢 BOSS 击中要害，你倒下了……使用复活药水或重开")
            return

        backlash_msg = ""
        if hp > 0 and random.random() < 0.3:
            if random.random() < 0.5:
                loss = max(1, int(player["gold"] * random.uniform(0.05, 0.15)))
                player["gold"] = max(0, player["gold"] - loss)
                backlash_msg = f"\n💢 BOSS 反噬！掉了 {loss} 金币"
            else:
                loss = random.randint(5, 10)
                player["energy"] = max(0, player["energy"] - loss)
                backlash_msg = f"\n💢 BOSS 反噬！损失 {loss} 体力"

        is_killed = False
        if hp <= 0:
            hp = 0
            _set_boss_killed(boss["id"])
            gold_reward = boss["gold"] * 3
            exp_reward = boss["exp"] * 3
            bonus_msg = f"\n💥 **{boss['name']} 被击杀了！4小时后刷新**"
            is_killed = True
        else:
            gold_reward = boss["gold"] + random.randint(-10, 20)
            exp_reward = boss["exp"] + random.randint(-5, 15)
            bonus_msg = ""

        if player.pop("double_gold_next", False):
            gold_reward *= 2
        _add_gold(player, gold_reward)
        leveled_up, need = _add_exp(player, exp_reward)
        player["total_boss"] = player.get("total_boss", 0) + 1
        player["total_energy_used"] = player.get("total_energy_used", 0) + BOSS_ENERGY_COST
        player["total_earned"] = player.get("total_earned", 0) + gold_reward
        _update_quest_progress(player, "打BOSS")
        qg, qe, qc = _check_quest_rewards(player)
        if qg or qe:
            _add_gold(player, qg)
            _add_exp(player, qe)
        new_achs = _check_achievements(player)
        if not is_killed:
            _save_boss_hp(boss["id"], hp)
        _save_players(players)
        msg = f"👊 **{boss['name']} 战**\n⚔️ 造成 {damage} 点伤害！\n🐉 {boss['name']} HP：{max(0, hp):.0f}/{base_hp}\n💰 +{gold_reward} 金币  ✨ +{exp_reward} 经验{backlash_msg}{bonus_msg}"
        if qg or qe:
            msg += f"\n📋 任务完成 +{qg}💰 +{qe}✨"
        for ach in new_achs:
            msg += f"\n🏅 解锁成就：{ach['name']} 💰+{ach['gold']} ✨+{ach['exp']}"
        if leveled_up:
            msg += f"\n🎉 升级了！当前等级 Lv.{player['level']}"
        await ctx.reply(msg)
        return


    # ── 成就 ──
    if cmd == "成就":
        unlocked = set(player.get("achievements", []))
        lines = ["🏅 **成就列表**\n"]
        count = 0
        for ach in ACHIEVEMENTS:
            done = ach["id"] in unlocked
            status = "✅" if done else "🔒"
            if not done:
                met = True
                for key, val in ach["cond"].items():
                    if key == "unique_fish":
                        if len(player.get("fish_caught", {})) < val:
                            met = False
                    elif key == "unique_ores":
                        if len(player.get("ores_mined", {})) < val:
                            met = False
                    elif key == "unique_hunts":
                        if len(player.get("hunts_killed", {})) < val:
                            met = False
                    elif player.get(key, 0) < val:
                        met = False
                status = "✅" if done else ("⭐" if met else "🔒")
            if done or met:
                count += 1
                lines.append(f"{status} {ach['name']} 💰+{ach['gold']} ✨+{ach['exp']}")
        if count == 0:
            lines.append("暂无成就，多玩游戏解锁！")
        lines.append(f"\n📊 已解锁：{sum(1 for a in ACHIEVEMENTS if a['id'] in unlocked)}/{len(ACHIEVEMENTS)}")
        await ctx.reply("\n".join(lines))
        _save_players(players)
        return

    # ── 技能 ──
    if cmd == "技能":
        if len(parts) >= 2 and parts[1].strip() in SKILLS:
            skill = parts[1].strip()
            skills = player.setdefault("skills", {})
            cur_lv = skills.get(skill, 0)
            if cur_lv >= 10:
                await ctx.reply(f"⭐ {skill} 已满级（Lv.10）")
                return
            cost = _skill_up_cost(cur_lv)
            if player["gold"] < cost:
                await ctx.reply(f"⚠️ 金币不足！{skill} Lv.{cur_lv}→Lv.{cur_lv+1} 需 {cost} 金币")
                return
            player["gold"] -= cost
            skills[skill] = cur_lv + 1
            _save_players(players)
            await ctx.reply(f"✅ {skill} 升级！Lv.{cur_lv} → Lv.{cur_lv+1}\n效果：加成 +{_skill_bonus(cur_lv+1)} 金币/经验")
            return
        skills = player.setdefault("skills", {})
        lines = ["📚 **我的技能**\n"]
        for s in SKILLS:
            lv = skills.get(s, 0)
            bonus = _skill_bonus(lv)
            if lv < 10:
                cost = _skill_up_cost(lv)
                lines.append(f"{s} Lv.{lv}/10（+{bonus}）升级费：{cost}💰")
            else:
                lines.append(f"{s} Lv.MAX（+{bonus}）")
        lines.append("\n💡 技能 <技能名> 升级（如：技能 钓鱼技能）")
        await ctx.reply("\n".join(lines))
        _save_players(players)
        return

    # ── 钓鱼大赛 ──
    if cmd == "大赛":
        t, pot = _get_tournament()
        if t is None:
            remaining = TOURNAMENT_DURATION - (time.time() - t.get("start_time", 0)) if t else 0
            await ctx.reply("🎣 当前没有钓鱼大赛！管理员可用「游戏 开启大赛」启动\n⏱️ 大赛持续5分钟，参赛费20体力，冠军赢取全部奖池！")
            return
        end = t["end_time"]
        remaining = int(end - time.time())
        if remaining <= 0:
            _end_tournament(players)
            _save_players(players)
            await ctx.reply("🎣 钓鱼大赛已结束！")
            return
        scores = t.get("scores", {})
        my_score = scores.get(uid, 0)
        lines = [
            f"🎣 **钓鱼大赛进行中！**",
            f"⏱️ 剩余时间：{remaining//60}分{remaining%60}秒",
            f"💰 奖池：{pot} 金币",
            f"🐟 你的成绩：{my_score} 条",
        ]
        if scores:
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
            lines.append("\n🏆 **当前排名**")
            for i, (pid, sc) in enumerate(sorted_scores, 1):
                nm = players.get(pid, {}).get("name", "") or pid[:8]
                lines.append(f"{i}. {nm} — {sc}条")
        await ctx.reply("\n".join(lines))
        return

    if cmd == "参赛":
        t, pot = _get_tournament()
        if t is None:
            await ctx.reply("🎣 当前没有钓鱼大赛！")
            return
        end = t["end_time"]
        if time.time() > end:
            _end_tournament(players)
            _save_players(players)
            await ctx.reply("🎣 钓鱼大赛已结束！")
            return
        if player.get("in_tournament"):
            await ctx.reply("🎣 你已经参赛了！快去钓鱼赚取积分吧")
            return
        if not _try_use_energy(player, TOURNAMENT_COST):
            await ctx.reply(f"⚠️ 体力不足！参赛需要 {TOURNAMENT_COST} 体力")
            return
        player["in_tournament"] = True
        cfg = _load_config()
        cfg.setdefault("tournament_pot", 0)
        entry_fee = 50
        if player["gold"] < entry_fee:
            player["energy"] = min(player["max_energy"], player["energy"] + TOURNAMENT_COST)
            await ctx.reply(f"⚠️ 金币不足！参赛费 {entry_fee} 金币")
            return
        player["gold"] -= entry_fee
        cfg["tournament_pot"] += entry_fee
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        _save_players(players)
        await ctx.reply(f"🎣 已报名钓鱼大赛！消耗 {TOURNAMENT_COST} 体力 + {entry_fee} 金币\n快去钓鱼赚积分吧！🐟")
        return

    if cmd == "钓鱼":
        if not _try_use_energy(player, 5):
            await ctx.reply(f"⚠️ 体力不足（当前 {player['energy']}/{player['max_energy']}），可用 恢复 补充")
            _save_players(players)
            return
        fish = _roll_fish()
        event = _roll_fish_event()
        gold = random.randint(fish["min_gold"], fish["max_gold"])
        exp_amt = random.randint(fish["min_exp"], fish["max_exp"])
        skills = player.setdefault("skills", {})
        fish_skill = skills.get("钓鱼技能", 0)
        bonus = _skill_bonus(fish_skill)
        gold += bonus
        exp_amt += bonus
        if player.pop("double_gold_next", False):
            gold *= 2
        bl_msg, died = _roll_backlash(player, "钓鱼")
        if died:
            _save_players(players)
            await ctx.reply(f"🎣 {event} {fish['name']}！{bl_msg}")
            return
        _add_gold(player, gold)
        leveled_up, need = _add_exp(player, exp_amt)
        player["total_fish"] += 1
        player["total_energy_used"] = player.get("total_energy_used", 0) + 5
        player["total_earned"] = player.get("total_earned", 0) + gold
        fname = fish["name"]
        player.setdefault("fish_caught", {})
        player["fish_caught"][fname] = player["fish_caught"].get(fname, 0) + 1
        t, _ = _get_tournament()
        if t and player.get("in_tournament") and time.time() < t.get("end_time", 0):
            scores = t.setdefault("scores", {})
            scores[uid] = scores.get(uid, 0) + 1
            cfg = _load_config()
            cfg["tournament"] = t
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        _update_quest_progress(player, "钓鱼")
        qg, qe, qc = _check_quest_rewards(player)
        if qg or qe:
            _add_gold(player, qg)
            _add_exp(player, qe)
        new_achs = _check_achievements(player)
        _save_players(players)
        msg = f"🎣 {event} {fname}！\n💰 +{gold} 金币  ✨ +{exp_amt} 经验{bl_msg}"
        if qg or qe:
            msg += f"\n📋 任务完成 +{qg}💰 +{qe}✨"
        for ach in new_achs:
            msg += f"\n🏅 解锁成就：{ach['name']} 💰+{ach['gold']} ✨+{ach['exp']}"
        if leveled_up:
            msg += f"\n🎉 升级了！当前等级 Lv.{player['level']}（下次升级需 {need} 经验）"
        await ctx.reply(msg)

    elif cmd == "挖矿":
        if not _try_use_energy(player, 5):
            await ctx.reply(f"⚠️ 体力不足（当前 {player['energy']}/{player['max_energy']}），可用 恢复 补充")
            _save_players(players)
            return
        ore = _roll_ore()
        event = _roll_mine_event()
        gold = random.randint(ore["min_gold"], ore["max_gold"])
        exp_amt = random.randint(ore["min_exp"], ore["max_exp"])
        skills = player.setdefault("skills", {})
        mine_skill = skills.get("挖矿技能", 0)
        bonus = _skill_bonus(mine_skill)
        gold += bonus
        exp_amt += bonus
        if player.pop("double_gold_next", False):
            gold *= 2
        bl_msg, died = _roll_backlash(player, "挖矿")
        if died:
            _save_players(players)
            await ctx.reply(f"⛏️ {event} {ore['name']}！{bl_msg}")
            return
        _add_gold(player, gold)
        leveled_up, need = _add_exp(player, exp_amt)
        player["total_mine"] += 1
        player["total_energy_used"] = player.get("total_energy_used", 0) + 5
        player["total_earned"] = player.get("total_earned", 0) + gold
        oname = ore["name"]
        player.setdefault("ores_mined", {})
        player["ores_mined"][oname] = player["ores_mined"].get(oname, 0) + 1
        _update_quest_progress(player, "挖矿")
        qg, qe, qc = _check_quest_rewards(player)
        if qg or qe:
            _add_gold(player, qg)
            _add_exp(player, qe)
        new_achs = _check_achievements(player)
        _save_players(players)
        msg = f"⛏️ {event} {oname}！\n💰 +{gold} 金币  ✨ +{exp_amt} 经验{bl_msg}"
        if qg or qe:
            msg += f"\n📋 任务完成 +{qg}💰 +{qe}✨"
        for ach in new_achs:
            msg += f"\n🏅 解锁成就：{ach['name']} 💰+{ach['gold']} ✨+{ach['exp']}"
        if leveled_up:
            msg += f"\n🎉 升级了！当前等级 Lv.{player['level']}（下次升级需 {need} 经验）"
        await ctx.reply(msg)

    elif cmd == "打猎":
        if not _try_use_energy(player, 8):
            await ctx.reply(f"⚠️ 体力不足（当前 {player['energy']}/{player['max_energy']}），可用 恢复 补充")
            _save_players(players)
            return
        prey = _roll_prey()
        event = _roll_hunt_event()
        gold = random.randint(prey["min_gold"], prey["max_gold"])
        exp_amt = random.randint(prey["min_exp"], prey["max_exp"])
        skills = player.setdefault("skills", {})
        hunt_skill = skills.get("打猎技能", 0)
        bonus = _skill_bonus(hunt_skill)
        gold += bonus
        exp_amt += bonus
        if player.pop("double_gold_next", False):
            gold *= 2
        bl_msg, died = _roll_backlash(player, "打猎")
        if died:
            _save_players(players)
            await ctx.reply(f"🏹 {event} {prey['name']}！{bl_msg}")
            return
        _add_gold(player, gold)
        leveled_up, need = _add_exp(player, exp_amt)
        player["total_hunt"] += 1
        player["total_energy_used"] = player.get("total_energy_used", 0) + 8
        player["total_earned"] = player.get("total_earned", 0) + gold
        hname = prey["name"]
        player.setdefault("hunts_killed", {})
        player["hunts_killed"][hname] = player["hunts_killed"].get(hname, 0) + 1
        _update_quest_progress(player, "打猎")
        qg, qe, qc = _check_quest_rewards(player)
        if qg or qe:
            _add_gold(player, qg)
            _add_exp(player, qe)
        new_achs = _check_achievements(player)
        _save_players(players)
        msg = f"🏹 {event} {hname}！\n💰 +{gold} 金币  ✨ +{exp_amt} 经验{bl_msg}"
        if qg or qe:
            msg += f"\n📋 任务完成 +{qg}💰 +{qe}✨"
        for ach in new_achs:
            msg += f"\n🏅 解锁成就：{ach['name']} 💰+{ach['gold']} ✨+{ach['exp']}"
        if leveled_up:
            msg += f"\n🎉 升级了！当前等级 Lv.{player['level']}（下次升级需 {need} 经验）"
        await ctx.reply(msg)

    elif cmd == "打工":
        if not _try_use_energy(player, 3):
            await ctx.reply(f"⚠️ 体力不足（当前 {player['energy']}/{player['max_energy']}），可用 恢复 补充")
            _save_players(players)
            return
        quote = random.choice(WORK_QUOTES)
        gold = _work_gold(player)
        if player.pop("double_gold_next", False):
            gold *= 2
        exp_amt = random.randint(3, 8)
        bl_msg, died = _roll_backlash(player, "打工")
        if died:
            _save_players(players)
            await ctx.reply(f"💼 {quote}！{bl_msg}")
            return
        _add_gold(player, gold)
        leveled_up, need = _add_exp(player, exp_amt)
        player["total_work"] = player.get("total_work", 0) + 1
        player["total_energy_used"] = player.get("total_energy_used", 0) + 3
        player["total_earned"] = player.get("total_earned", 0) + gold
        _update_quest_progress(player, "打工")
        qg, qe, qc = _check_quest_rewards(player)
        if qg or qe:
            _add_gold(player, qg)
            _add_exp(player, qe)
        _save_players(players)
        msg = f"💼 {quote}，赚了 {gold} 金币！\n💰 +{gold} 金币  ✨ +{exp_amt} 经验{bl_msg}"
        if qg or qe:
            msg += f"\n📋 任务完成 +{qg}💰 +{qe}✨"
        if leveled_up:
            msg += f"\n🎉 升级了！当前等级 Lv.{player['level']}（下次升级需 {need} 经验）"
        await ctx.reply(msg)

    elif cmd == "签到":
        gold, exp, streak_count, status, leveled_up = _checkin(uid, players, streaks)
        if status == "already":
            await ctx.reply("⚠️ 你今天已经签到了！明天再来吧")
            return
        msg = f"📅 签到成功！连续签到 {streak_count} 天"
        if streak_count >= 7:
            msg += " 🔥（7天以上额外奖励！）"
        elif streak_count >= 3:
            msg += " ✨（3天以上额外奖励！）"
        msg += f"\n💰 +{gold} 金币  ✨ +{exp} 经验\n🔋 体力 +10"
        if leveled_up:
            msg += f"\n🎉 升级了！当前等级 Lv.{player['level']}"
        _save_players(players)
        _save_streaks(streaks)
        await ctx.reply(msg)

    elif cmd == "我的信息":
        rank = sum(1 for p in players.values() if p["level"] > player["level"] or (p["level"] == player["level"] and p["exp"] > player["exp"])) + 1
        _, need = _calc_level(player["exp"])
        display_name = player.get("name") or _safe_uid(uid)
        inv_count = sum(v for v in player.get("inventory", {}).values() if v > 0)
        msg = (
            f"👤 **{display_name}** 的游戏信息\n"
            f"🏆 等级：Lv.{player['level']}（经验 {player['exp']}/{need}）\n"
            f"💰 金币：{player['gold']}\n"
            f"🔋 体力：{player['energy']}/{player['max_energy']}\n"
            f"🎣 钓鱼 {player['total_fish']}次 | ⛏️ 挖矿 {player['total_mine']}次\n"
            f"🏹 打猎 {player.get('total_hunt',0)}次 | 🪓 挖宝 {player.get('total_dig',0)}次\n"
            f"🎒 背包物品 {inv_count} 种\n"
            f"🏅 等级排名：第 {rank} 名"
        )
        await ctx.reply(msg)
        _save_players(players)

    elif cmd == "排行榜":
        lb = _get_leaderboard(players)
        if not lb:
            await ctx.reply("暂无玩家数据")
            return
        lines = ["🏆 **等级排行榜**\n"]
        for i, entry in enumerate(lb, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            name = entry.get("name") or entry["uid"]
            lines.append(f"{medal} {name}  Lv.{entry['level']}  💰{entry['gold']}")
        await ctx.reply("\n".join(lines))
        _save_players(players)

    elif cmd == "升级":
        _, need = _calc_level(player["exp"])
        if player["exp"] >= need:
            _add_exp(player, 0)
            _, need = _calc_level(player["exp"])
            await ctx.reply(f"🎉 已升级！当前等级 Lv.{player['level']}，下次升级需 {need} 经验")
            _save_players(players)
            return
        cost = need - player["exp"]
        cost_gold = cost * 2
        if player["gold"] < cost_gold:
            await ctx.reply(f"⚠️ 金币不足！升级还需 {cost} 经验，需花费 {cost_gold} 金币（你只有 {player['gold']}）")
            return
        player["gold"] -= cost_gold
        _add_exp(player, cost)
        _, need = _calc_level(player["exp"])
        await ctx.reply(f"💰 花费 {cost_gold} 金币购买了 {cost} 经验，成功升级！\n当前等级 Lv.{player['level']}，下次升级需 {need} 经验")
        _save_players(players)

    elif cmd == "改名":
        if len(parts) < 2:
            await ctx.reply("⚠️ 用法：改名 <新名字>\n例：改名 钓鱼王\n💡 首次免费，之后每次 50 金币")
            return
        new_name = parts[1].strip()
        if len(new_name) > 20:
            await ctx.reply("⚠️ 名字不能超过20个字符")
            return
        if not new_name:
            await ctx.reply("⚠️ 名字不能为空")
            return
        changes = player.get("name_changes", 0)
        if changes > 0:
            if player["gold"] < 50:
                await ctx.reply(f"⚠️ 金币不足！改名需要 50 金币（你只有 {player['gold']}）")
                return
            player["gold"] -= 50
        player["name"] = new_name
        player["name_changes"] = changes + 1
        cost_msg = "首次免费" if changes == 0 else "花费 50 金币"
        await ctx.reply(f"✅ 已改名为「{new_name}」（{cost_msg}）")
        _save_players(players)

    elif cmd == "赌大小":
        if len(parts) < 2:
            await ctx.reply("⚠️ 用法：赌大小 <大/小> <金额>\n例：赌大小 大 100\n🎲 1-3为小，4-6为大，猜对得2倍")
            return
        args = parts[1].split()
        if len(args) < 2:
            await ctx.reply("⚠️ 用法：赌大小 <大/小> <金额>\n例：赌大小 大 100")
            return
        guess = args[0]
        if guess not in ("大", "小"):
            await ctx.reply("⚠️ 请猜「大」或「小」")
            return
        try:
            bet = int(args[1])
        except ValueError:
            await ctx.reply("⚠️ 金额必须为数字")
            return
        if bet <= 0:
            await ctx.reply("⚠️ 金额必须大于0")
            return
        if player["gold"] < bet:
            await ctx.reply(f"⚠️ 金币不足！你只有 {player['gold']} 金币")
            return
        bl_msg, died = _roll_backlash(player, "赌大小")
        if died:
            _save_players(players)
            await ctx.reply(f"🎲 你还没开始赌就{bl_msg}")
            return
        dice = random.randint(1, 6)
        is_big = dice >= 4
        lucky = player.pop("lucky_next", False)
        if lucky:
            is_big = dice >= 3  # tilt odds
        is_win = (guess == "大" and is_big) or (guess == "小" and not is_big)
        if is_win:
            winnings = bet
            if player.pop("double_gold_next", False):
                winnings *= 2
            _add_gold(player, winnings)
            player["total_gamble_win"] = player.get("total_gamble_win", 0) + 1
            player["total_earned"] = player.get("total_earned", 0) + winnings
            _update_quest_progress(player, "赌赢", 1)
            msg = f"🎲 骰子：{dice}（{'大' if is_big else '小'}）\n你猜：{guess}\n🎉 猜对了！赢得 {winnings} 金币！"
        else:
            player["gold"] -= bet
            msg = f"🎲 骰子：{dice}（{'大' if is_big else '小'}）\n你猜：{guess}\n😭 猜错了，输掉 {bet} 金币"
        ex = random.randint(1, 5)
        _add_exp(player, ex)
        qg, qe, qc = _check_quest_rewards(player)
        if qg or qe:
            _add_gold(player, qg)
            _add_exp(player, qe)
        leveled_up, need = _calc_level(player["exp"])
        if leveled_up:
            msg += f"\n🎉 升级了！当前等级 Lv.{player['level']}"
        _save_players(players)
        await ctx.reply(msg + bl_msg)

    elif cmd == "恢复":
        # limit once per 60 minutes
        last = player.get("last_recover_time", 0)
        cooldown = 3600
        remaining = cooldown - (now - last)
        if remaining > 0:
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            await ctx.reply(f"⏳ 恢复技能冷却中，还需 {mins} 分 {secs} 秒")
            return
        recover = 20 + player["level"] * 2
        player["energy"] = min(player["max_energy"], player["energy"] + recover)
        player["last_recover_time"] = now
        _save_players(players)
        await ctx.reply(f"🔋 恢复了 {recover} 点体力！当前 {player['energy']}/{player['max_energy']}")

    elif cmd in ("游戏", "game", "游戏帮助"):
        from .draw import draw_game_help
        data = await draw_game_help()
        temp = os.path.join(DATA_DIR, "game_help.png")
        with open(temp, "wb") as f:
            f.write(data)
        await ctx.send(await _make_image_seg(temp))

    else:
        await ctx.reply("未知命令。用 游戏 或 游戏帮助 查看所有指令")


def _safe_uid(uid):
    if len(uid) <= 8:
        return uid
    return uid[:4] + "****" + uid[-4:]
