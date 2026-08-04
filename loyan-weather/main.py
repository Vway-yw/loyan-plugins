"""天气预报 — 查询天气实况与未来预报（免 key，wttr.in 数据源）

命令：
  /天气 <城市>     — 查询城市天气（如：/天气 北京）
  /天气            — 默认查询北京天气
  /天气 <城市> 3   — 查询未来 3 天预报
"""

import asyncio
import json
import re
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

from graci import on_command, plugin_handler, PluginContext
from graci import get_logger

logger = get_logger("天气预报")

# ── 常量定义 ──
API_URL = "https://wttr.in/{city}?format=j1"
TIMEOUT = 15
CACHE_TTL = 1800  # 缓存 30 分钟
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# 城市中英文映射（常用城市）
CITY_MAP = {
    "北京": "Beijing", "上海": "Shanghai", "广州": "Guangzhou", "深圳": "Shenzhen",
    "天津": "Tianjin", "重庆": "Chongqing", "成都": "Chengdu", "杭州": "Hangzhou",
    "武汉": "Wuhan", "西安": "Xian", "南京": "Nanjing", "苏州": "Suzhou",
    "郑州": "Zhengzhou", "长沙": "Changsha", "沈阳": "Shenyang", "青岛": "Qingdao",
    "大连": "Dalian", "厦门": "Xiamen", "福州": "Fuzhou", "济南": "Jinan",
    "哈尔滨": "Harbin", "长春": "Changchun", "昆明": "Kunming", "贵阳": "Guiyang",
    "南宁": "Nanning", "海口": "Haikou", "三亚": "Sanya", "兰州": "Lanzhou",
    "乌鲁木齐": "Urumqi", "拉萨": "Lhasa", "石家庄": "Shijiazhuang", "太原": "Taiyuan",
    "合肥": "Hefei", "南昌": "Nanchang", "无锡": "Wuxi", "宁波": "Ningbo",
}

# 天气描述英译中
WEATHER_ZH = {
    "sunny": "☀️ 晴", "clear": "☀️ 晴", "partly cloudy": "⛅ 多云",
    "cloudy": "☁️ 阴", "overcast": "☁️ 阴", "fog": "🌫️ 雾",
    "mist": "🌫️ 薄雾", "rain": "🌧️ 雨", "light rain": "🌦️ 小雨",
    "moderate rain": "🌧️ 中雨", "heavy rain": "⛈️ 大雨", "drizzle": "🌦️ 毛毛雨",
    "patchy rain nearby": "🌦️ 局部小雨", "thunder": "⛈️ 雷阵雨",
    "snow": "❄️ 雪", "light snow": "🌨️ 小雪", "heavy snow": "❄️ 大雪",
    "sleet": "🌨️ 雨夹雪", "hail": "🧊 冰雹", "wind": "💨 大风",
    "thundery outbreaks in nearby": "⛈️ 附近雷暴",
}


def _city_en(city: str) -> str:
    """中文城市名转英文（供 wttr.in 查询）"""
    city = city.strip()
    if city in CITY_MAP:
        return CITY_MAP[city]
    return city


def _weather_zh(desc: str) -> str:
    """英文天气描述转中文"""
    key = desc.lower()
    if key in WEATHER_ZH:
        return WEATHER_ZH[key]
    for k, v in WEATHER_ZH.items():
        if k in key:
            return v
    return desc


def _fetch(city_en: str) -> Optional[Dict]:
    """请求天气数据"""
    url = API_URL.format(city=urllib.parse.quote(city_en))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _format_now(data: Dict, city: str) -> str:
    """格式化当前天气"""
    try:
        cur = data["current_condition"][0]
        area = data["nearest_area"][0]
        area_name = area["areaName"][0]["value"]
        temp = cur["temp_C"]
        feels = cur["FeelsLikeC"]
        desc = cur["weatherDesc"][0]["value"]
        humidity = cur["humidity"]
        wind = cur["windspeedKmph"]
        wind_dir = cur["winddir16Point"]
        precip = cur["precipMM"]
        pressure = cur["pressure"]
        lines = [
            f"🌤️ {city} 天气（{area_name}）",
            "━━━━━━━━━━━━",
            f"🌡️ 气温：{temp}°C（体感 {feels}°C）",
            f"☁️ 天气：{_weather_zh(desc)}",
            f"💧 湿度：{humidity}%",
            f"🌬️ 风：{wind_dir} {wind}km/h",
            f"🌧️ 降水：{precip}mm",
            f"📊 气压：{pressure}hPa",
        ]
        return "\n".join(lines)
    except (KeyError, IndexError, TypeError):
        return "❌ 天气数据解析失败"


def _format_forecast(data: Dict, city: str, days: int) -> str:
    """格式化未来预报"""
    try:
        weather_list = data.get("weather", [])[:days]
        lines = [f"📅 {city} 未来 {len(weather_list)} 天预报", "━━━━━━━━━━━━"]
        for day in weather_list:
            date = day["date"]
            maxt = day["maxtempC"]
            mint = day["mintempC"]
            hourly = day["hourly"]
            # 取白天时段（9点-15点）描述
            desc = hourly[4]["weatherDesc"][0]["value"] if len(hourly) > 4 else hourly[0]["weatherDesc"][0]["value"]
            precip = day.get("totalSnow_cm", "0")
            lines.append(f"📆 {date}")
            lines.append(f"   🌡️ {mint}~{maxt}°C · {_weather_zh(desc)}")
        lines.append("━━━━━━━━━━━━\n📌 数据来源 wttr.in · 30分钟缓存")
        return "\n".join(lines)
    except (KeyError, IndexError, TypeError):
        return "❌ 预报数据解析失败"


@on_command("/天气", "/天气预报", "/weather")
@plugin_handler
async def handle_weather(ctx: PluginContext):
    """查询天气：/天气 <城市> [天数]"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 2)
    city = parts[1].strip() if len(parts) > 1 else "北京"
    days = 0
    if len(parts) > 2 and parts[2].strip().isdigit():
        days = min(max(int(parts[2].strip()), 1), 5)

    city_en = _city_en(city)
    await ctx.reply(f"🌤️ 正在查询 {city} 天气...")
    try:
        data = await asyncio.to_thread(_fetch, city_en)
        if not data:
            await ctx.reply("❌ 查询失败，请检查城市名或稍后再试")
            return
        if days:
            await ctx.reply(_format_forecast(data, city, days))
        else:
            await ctx.reply(_format_now(data, city))
    except Exception as e:
        logger.error(f"天气查询失败: {e}")
        await ctx.reply("❌ 查询失败，请稍后再试")
