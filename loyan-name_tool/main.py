"""随机姓名 — 生成随机中文姓名

命令：
  /名字       — 随机中文姓名
  /名字 女     — 女性姓名
  /名字 男     — 男性姓名
"""

import random

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("随机姓名")

# ── 常量定义 ──
SURNAMES = list("赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹")
MALE_NAMES = list("伟刚勇毅俊峰强军平保东文辉力明永健世广志义兴良海山仁波宁贵福生龙元全国胜学祥才发武新利清飞彬富顺信子杰涛昌成康星光天达安岩中茂进林有坚和彪博诚先敬震振壮会思群豪心邦承乐绍功松善厚庆磊民友裕河哲江超浩亮政谦亨奇固之轮翰朗伯宏言若鸣朋斌梁栋维启克伦翔旭鹏泽晨辰士以建家致树炎德行时泰盛雄琛钧冠策腾楠榕风航弘")
FEMALE_NAMES = list("秀娟英华慧巧美娜静淑惠珠翠雅芝玉萍红娥玲芬芳燕彩春菊兰凤洁梅琳素云莲真环雪荣爱妹霞香月莺媛艳瑞凡佳嘉琼勤珍贞莉桂娣叶璧璐娅琦晶妍茜秋珊莎锦黛青倩婷姣婉娴瑾颖露瑶怡婵雁蓓纨仪荷丹蓉眉君琴蕊薇菁梦岚苑婕馨瑗琰韵融园艺咏卿聪澜纯毓悦昭冰爽琬茗羽希欣飘育滢馥筠柔竹霭凝晓欢霄枫芸菲寒伊亚宜可姬舒影荔枝思丽")

def _gen_name(gender: str = "") -> str:
    """生成随机姓名"""
    surname = random.choice(SURNAMES)
    pool = FEMALE_NAMES if gender == "女" else (MALE_NAMES if gender == "男" else random.choice([MALE_NAMES, FEMALE_NAMES]))
    name = "".join(random.sample(pool, 2))
    return surname + name


@on_command("/名字", "/随机名字", "/随机姓名")
@plugin_handler
async def handle_name(ctx: PluginContext):
    """随机姓名"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    gender = parts[1].strip() if len(parts) > 1 else ""

    if gender not in ("", "男", "女"):
        await ctx.reply("❌ 用法：/名字 [男|女]")
        return

    name = _gen_name(gender)
    label = "女性" if gender == "女" else ("男性" if gender == "男" else "随机")
    await ctx.reply(f"👤 随机{label}姓名\n━━━━━━━━━━━━\n📛 {name}\n\n💡 /名字 男 /名字 女")
