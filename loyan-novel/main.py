"""小说插件 — 搜索小说 + 章节阅读 + 翻页（Playwright 渲染笔趣阁）"""
import asyncio
import re
import time
import urllib.parse
from typing import Dict, List, Optional

from loyan.core.decorators import on_command, plugin_handler, PluginContext
from graci import get_logger
from loyan.plugins.core.reading import get_reading, set_reading

logger = get_logger("小说")

BASE = "https://www.bqgui.cc"
PAGE_SIZE = 500
CACHE_TTL = 600  # 章节正文缓存 10 分钟

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# 搜索缓存: query -> (time, books)
_search_cache: Dict[str, tuple] = {}
# 章节正文缓存: url -> (time, text)
_content_cache: Dict[str, tuple] = {}

_browser = None
_browser_lock = asyncio.Lock()


async def _get_browser():
    """懒加载 Playwright 浏览器实例"""
    global _browser
    if _browser is None or not _browser.is_connected():
        from playwright.async_api import async_playwright
        pw = await async_playwright().start()
        _browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
    return _browser


async def _fetch_page(url: str) -> str:
    """用 Playwright 渲染页面（绕过 Cloudflare/JS 验证）"""
    browser = await _get_browser()
    async with _browser_lock:
        ctx = await browser.new_context(user_agent=UA, viewport={"width": 1280, "height": 800})
        try:
            page = await ctx.new_page()
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            return await page.content()
        finally:
            await ctx.close()


async def _search_books(keyword: str) -> List[Dict]:
    """搜索书籍"""
    now = time.time()
    cached = _search_cache.get(keyword)
    if cached and now - cached[0] < CACHE_TTL:
        return cached[1]
    html = await _fetch_page(f"{BASE}/s?q={urllib.parse.quote(keyword)}")
    books = []
    bad = ("淫", "肉文", "欲宗", "h文", "色情")
    for m in re.finditer(r'href="(/book/\d+/)"[^>]*>([^<]{2,40})', html):
        href, title = m.group(1), m.group(2).strip()
        if any(b["url"] == href for b in books):
            continue
        if any(x in title for x in bad):
            continue  # 过滤擦边书籍
        books.append({"title": title, "url": href})
        if len(books) >= 10:
            break
    if books:
        _search_cache[keyword] = (now, books)
    return books


async def _get_chapters(book_url: str) -> List[Dict]:
    """获取书籍章节列表"""
    html = await _fetch_page(f"{BASE}{book_url}")
    chapters = []
    skip_words = ("角色传记", "上架感言", "访谈", "人物出场", "完结感言", "作家的话")
    for m in re.finditer(r'href="(/book/\d+/\d+\.html)"[^>]*>([^<]{2,50})', html):
        href, title = m.group(1), m.group(2).strip()
        if any(c["url"] == href for c in chapters):
            continue
        if any(w in title for w in skip_words):
            continue  # 跳过非正文章节
        chapters.append({"title": title, "url": href})
        if len(chapters) >= 500:
            break
    return chapters


async def _get_chapter_text(url: str) -> Optional[str]:
    """获取章节正文（带缓存）"""
    now = time.time()
    cached = _content_cache.get(url)
    if cached and now - cached[0] < CACHE_TTL:
        return cached[1]
    html = await _fetch_page(f"{BASE}{url}")
    m = re.search(r'id="chaptercontent"[^>]*>(.*?)</div>', html, re.S)
    if not m:
        for pat in [r'class="content"[^>]*>(.*?)</div>', r'id="content"[^>]*>(.*?)</div>']:
            mm = re.search(pat, html, re.S)
            if mm:
                m = mm
                break
    if not m:
        return None
    text = re.sub(r"<[^>]+>", "", m.group(1))
    text = re.sub(r"\u3000", " ", text)
    lines = []
    for ln in text.split("\n"):
        ln = ln.strip()
        if not ln:
            continue
        # 过滤广告行：含 * 分隔的小说站广告 或 常见广告词
        if re.search(r"[*＃#]|更多.{0,4}精彩|在线阅读|最新章节|请收藏|手机站|下载地址", ln):
            if len(ln) < 40:
                continue
        lines.append(ln)
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if text:
        _content_cache[url] = (now, text)
    return text or None


def _pick_index(ctx, maxn: int) -> Optional[int]:
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    if len(parts) > 1 and parts[1].strip().isdigit():
        idx = int(parts[1].strip())
        if 1 <= idx <= maxn:
            return idx
    return None


async def _show_reading(ctx: PluginContext, url: str, title: str, idx: int, page: int):
    """显示章节正文某一页"""
    uid = str(getattr(ctx, "sender_id", "") or "")
    text = await _get_chapter_text(url)
    if not text:
        await ctx.reply(f"📖 {title}\n⚠️ 本章获取失败，请试试其他章节")
        return
    total = max(1, (len(text) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(max(page, 1), total)
    set_reading(uid, {"mode": "novel", "url": url, "idx": idx, "page": page, "total": total, "title": title})
    start = (page - 1) * PAGE_SIZE
    lines = [f"📖 {title}", "━━━━━━━━━━━━"]
    lines.append(text[start:start + PAGE_SIZE])
    lines.append("━━━━━━━━━━━━")
    lines.append(f"📄 {page}/{total} 页")
    lines.append("💡 /下一页 /上一页 /尾页 /第N页")
    await ctx.reply("\n".join(lines))


@on_command("/小说", "/搜书", "/搜索小说")
@plugin_handler
async def handle_novel(ctx: PluginContext):
    """搜索小说：/小说 <书名>；/小说 序号 选书；/小说 序号 章节 阅读"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 2)
    if len(parts) < 2:
        await ctx.reply("📖 用法：\n/小说 <书名> 搜索\n/小说 序号 选择书籍\n/小说 序号 章节 阅读\n例：/小说 斗破苍穹")
        return
    keyword = parts[1].strip()
    uid = str(getattr(ctx, "sender_id", "") or "")

    # 阅读已有选择：/小说 序号 章节
    if len(parts) > 2 and parts[2].strip().isdigit():
        c = get_reading(uid)
        if c and c.get("mode") == "novel_books":
            books = c["books"]
            bi = int(keyword)
            if not (1 <= bi <= len(books)):
                await ctx.reply(f"序号超出范围（1-{len(books)}）")
                return
            ch_idx = int(parts[2].strip())
            chapters = c.get("chapters")
            if not chapters:
                await ctx.reply("📚 正在加载章节列表...")
                chapters = await _get_chapters(books[bi - 1]["url"])
                if not chapters:
                    await ctx.reply("❌ 章节获取失败")
                    return
                c["chapters"] = chapters
                set_reading(uid, c)
            if not (1 <= ch_idx <= len(chapters)):
                await ctx.reply(f"章节超出范围（1-{len(chapters)}）")
                return
            await _show_reading(ctx, chapters[ch_idx - 1]["url"], chapters[ch_idx - 1]["title"], ch_idx, 1)
            return

    # 序号选书
    if keyword.isdigit():
        c = get_reading(uid)
        if not c or c.get("mode") != "novel_books":
            await ctx.reply("请先 /小说 <书名> 搜索")
            return
        books = c["books"]
        bi = int(keyword)
        if not (1 <= bi <= len(books)):
            await ctx.reply(f"序号超出范围（1-{len(books)}）")
            return
        book = books[bi - 1]
        await ctx.reply(f"📚 {book['title']} 加载章节中...")
        chapters = await _get_chapters(book["url"])
        if not chapters:
            await ctx.reply("❌ 章节获取失败")
            return
        c["chapters"] = chapters
        set_reading(uid, c)
        lines = [f"📚 {book['title']} · 共{len(chapters)}章", "━━━━━━━━━━━━"]
        for i, ch in enumerate(chapters[:15], 1):
            lines.append(f"{i}. {ch['title'][:30]}")
        lines.append("━━━━━━━━━━━━")
        lines.append("💡 /小说 序号 章节 阅读，如：/小说 1 1")
        await ctx.reply("\n".join(lines))
        return

    # 搜索
    await ctx.reply(f"🔍 正在搜索「{keyword}」...")
    books = await _search_books(keyword)
    if not books:
        await ctx.reply("😢 未找到相关小说，换个关键词试试")
        return
    set_reading(uid, {"mode": "novel_books", "books": books})
    lines = [f"🔍 「{keyword}」搜索结果", "━━━━━━━━━━━━"]
    for i, b in enumerate(books, 1):
        lines.append(f"{i}. {b['title'][:30]}")
    lines.append("━━━━━━━━━━━━")
    lines.append("💡 /小说 序号 选择书籍，如：/小说 1")
    await ctx.reply("\n".join(lines))


@on_command("/章节")
@plugin_handler
async def handle_chapter(ctx: PluginContext):
    """直接阅读某章节：/章节 12"""
    uid = str(getattr(ctx, "sender_id", "") or "")
    c = get_reading(uid)
    if not c or c.get("mode") != "novel_books" or not c.get("chapters"):
        await ctx.reply("请先 /小说 <书名> 搜索并选择书籍")
        return
    idx = _pick_index(ctx, len(c["chapters"]))
    if not idx:
        await ctx.reply(f"用法：/章节 序号（1-{len(c['chapters'])}）")
        return
    ch = c["chapters"][idx - 1]
    await _show_reading(ctx, ch["url"], ch["title"], idx, 1)
