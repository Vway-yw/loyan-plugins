"""系统指令查询 — Linux/Windows 常用实用指令

命令：
  /指令            — 查看指令帮助
  /指令 linux      — 推送 Linux 常用指令
  /指令 windows    — 推送 Windows 常用指令
  /指令 <关键词>   — 定向查询（如：/指令 网络 /指令 文件）

自动识别：用户回复中包含系统关键词时自动匹配对应系统。
"""

import re
from typing import List, Optional, Tuple

from graci import on_command, plugin_handler, PluginContext
from graci import get_logger
from graci import get_reading, set_reading

logger = get_logger("系统指令")

# ── 常量定义 ──
PAGE_SIZE = 30  # 每页指令条数

# ── 指令库 ──
LINUX_CMDS: List[Tuple[str, str, str]] = [
    # (命令, 说明, 分类)
    ("uname -a", "查看系统内核版本信息", "系统信息"),
    ("cat /etc/os-release", "查看发行版信息", "系统信息"),
    ("uptime", "查看系统运行时间与负载", "系统信息"),
    ("free -h", "查看内存使用情况", "系统信息"),
    ("df -h", "查看磁盘分区使用情况", "系统信息"),
    ("du -sh *", "查看当前目录各文件大小", "系统信息"),
    ("top", "实时查看进程与资源占用", "系统信息"),
    ("htop", "交互式进程监控（更友好）", "系统信息"),
    ("ls -lah", "列出当前目录文件详情", "文件操作"),
    ("cd <目录>", "切换目录", "文件操作"),
    ("cp -r <源> <目标>", "复制文件/目录", "文件操作"),
    ("mv <源> <目标>", "移动/重命名", "文件操作"),
    ("rm -rf <路径>", "删除文件/目录（谨慎）", "文件操作"),
    ("mkdir -p <目录>", "递归创建目录", "文件操作"),
    ("find <路径> -name '*.log'", "按名称查找文件", "文件操作"),
    ("grep -r '关键词' <路径>", "递归搜索文件内容", "文件操作"),
    ("cat <文件>", "查看文件内容", "文件操作"),
    ("tail -f <日志文件>", "实时跟踪日志输出", "文件操作"),
    ("chmod +x <文件>", "给文件添加执行权限", "权限"),
    ("chown <用户>:<组> <文件>", "修改文件所有者", "权限"),
    ("sudo <命令>", "以管理员权限执行", "权限"),
    ("ip addr", "查看网络接口 IP", "网络"),
    ("ss -tlnp", "查看监听端口及进程", "网络"),
    ("netstat -tulnp", "查看端口占用", "网络"),
    ("curl <URL>", "发送 HTTP 请求", "网络"),
    ("wget <URL>", "下载文件", "网络"),
    ("ping <主机>", "测试网络连通性", "网络"),
    ("ssh <用户>@<主机>", "远程连接服务器", "网络"),
    ("scp <本地> <用户>@<主机>:<路径>", "远程拷贝文件", "网络"),
    ("ps aux", "查看所有进程", "进程"),
    ("kill -9 <PID>", "强制结束进程", "进程"),
    ("systemctl start <服务>", "启动系统服务", "服务"),
    ("systemctl status <服务>", "查看服务状态", "服务"),
    ("systemctl enable <服务>", "设置开机自启", "服务"),
    ("systemctl stop <服务>", "停止服务", "服务"),
    ("apt update && apt upgrade", "更新软件包（Debian/Ubuntu）", "包管理"),
    ("apt install <包名>", "安装软件包", "包管理"),
    ("yum install <包名>", "安装软件包（CentOS/RHEL）", "包管理"),
    ("pip install <包名>", "安装 Python 包", "包管理"),
    ("lsblk", "查看磁盘与分区", "磁盘"),
    ("fdisk -l", "查看磁盘分区表", "磁盘"),
    ("history", "查看命令历史", "其他"),
    ("alias ll='ls -l'", "设置命令别名", "其他"),
]

WINDOWS_CMDS: List[Tuple[str, str, str]] = [
    ("systeminfo", "查看完整系统信息", "系统信息"),
    ("ver", "查看 Windows 版本", "系统信息"),
    ("msinfo32", "打开系统信息窗口", "系统信息"),
    ("dxdiag", "查看 DirectX 诊断信息", "系统信息"),
    ("wmic cpu get name", "查看 CPU 型号", "系统信息"),
    ("taskmgr", "打开任务管理器", "系统信息"),
    ("dir /a", "列出当前目录全部文件", "文件操作"),
    ("cd <目录>", "切换目录", "文件操作"),
    ("copy <源> <目标>", "复制文件", "文件操作"),
    ("move <源> <目标>", "移动文件", "文件操作"),
    ("del <文件>", "删除文件", "文件操作"),
    ("ren <旧名> <新名>", "重命名文件", "文件操作"),
    ("type <文件>", "查看文本文件内容", "文件操作"),
    ("tree /f", "树状显示目录结构", "文件操作"),
    ("mkdir <目录>", "创建目录", "文件操作"),
    ("rd /s <目录>", "删除目录（含子目录）", "文件操作"),
    ("ipconfig /all", "查看完整网络配置", "网络"),
    ("ipconfig /flushdns", "刷新 DNS 缓存", "网络"),
    ("ping <主机>", "测试网络连通性", "网络"),
    ("tracert <主机>", "路由追踪", "网络"),
    ("netstat -ano", "查看端口占用及 PID", "网络"),
    ("nslookup <域名>", "DNS 解析查询", "网络"),
    ("tasklist", "查看运行中的进程列表", "进程"),
    ("taskkill /F /PID <PID>", "强制结束进程", "进程"),
    ("net user", "查看本地用户列表", "系统管理"),
    ("net localgroup administrators", "查看管理员组成员", "系统管理"),
    ("chkdsk <盘符>:", "磁盘检查修复", "磁盘"),
    ("cleanmgr", "打开磁盘清理", "磁盘"),
    ("sfc /scannow", "系统文件完整性检查修复", "系统修复"),
    ("dism /online /cleanup-image /restorehealth", "修复系统映像", "系统修复"),
    ("powercfg /batteryreport", "生成电池续航报告（笔记本）", "电源"),
    ("shutdown /s /t 0", "立即关机", "电源"),
    ("shutdown /r /t 0", "立即重启", "电源"),
    ("where <程序名>", "查找程序路径", "其他"),
    ("echo %PATH%", "查看环境变量 PATH", "其他"),
]

# 系统关键词识别
LINUX_KEYWORDS = ("linux", "ubuntu", "debian", "centos", "kali", "fedora", "arch", "wsl", "ssh", "服务器")
WINDOWS_KEYWORDS = ("windows", "win", "cmd", "dos", "电脑", "台式", "笔记本")

# 分类关键词
CATEGORY_KEYWORDS = {
    "网络": ("网络", "端口", "ip", "ping", "连接"),
    "文件": ("文件", "目录", "复制", "删除", "查找", "ls", "dir"),
    "进程": ("进程", "task", "kill", "ps"),
    "系统信息": ("系统", "信息", "版本", "内存", "cpu", "磁盘", "df"),
    "服务": ("服务", "systemctl", "启动"),
    "包管理": ("安装", "包", "apt", "yum", "pip"),
    "磁盘": ("磁盘", "分区", "chkdsk", "lsblk"),
}


def _log_error(msg: str):
    """记录错误日志"""
    logger.error(msg)


def _detect_system(text: str) -> Optional[str]:
    """根据关键词自动识别用户系统"""
    t = text.lower()
    if any(k in t for k in LINUX_KEYWORDS):
        return "linux"
    if any(k in t for k in WINDOWS_KEYWORDS):
        return "windows"
    return None


def _detect_category(text: str) -> Optional[str]:
    """根据关键词识别指令分类"""
    t = text.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(k in t for k in kws):
            return cat
    return None


def _format_cmds(cmds: List[Tuple[str, str, str]], page: int = 1) -> str:
    """格式化指令列表（分页）"""
    total = len(cmds)
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(max(page, 1), pages)
    start = (page - 1) * PAGE_SIZE
    chunk = cmds[start:start + PAGE_SIZE]
    lines = [f"📋 共 {total} 条指令 · 第 {page}/{pages} 页", "━━━━━━━━━━━━"]
    for cmd, desc, cat in chunk:
        lines.append(f"💻 {cmd}")
        lines.append(f"   📌 {desc} · {cat}")
    lines.append("━━━━━━━━━━━━")
    lines.append("💡 /下一页 /上一页 /尾页 /第N页 翻页")
    return "\n".join(lines)


@on_command("/指令", "/命令", "/linux指令", "/windows指令")
@plugin_handler
async def handle_cmds(ctx: PluginContext):
    """系统指令查询：自动识别系统或手动指定"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    query = parts[1].strip() if len(parts) > 1 else ""

    # 手动指定系统
    sys_choice = None
    if query:
        if any(k in query.lower() for k in LINUX_KEYWORDS):
            sys_choice = "linux"
        elif any(k in query.lower() for k in WINDOWS_KEYWORDS):
            sys_choice = "windows"

    # 无参数或指定系统
    if not sys_choice and not query:
        await ctx.reply(
            "🖥️ 系统指令查询\n"
            "━━━━━━━━━━━━\n"
            "💡 自动识别系统：回复含 linux/ubuntu/windows 等关键词即可\n"
            "🔧 手动指定：/指令 linux 或 /指令 windows\n"
            "🔍 定向查询：/指令 网络 /指令 文件 /指令 进程\n"
            "📄 翻页：/指令 2（看第 2 页）\n"
            "📖 例：/指令 linux 网络"
        )
        return

    # 纯数字 = 翻页
    if query.isdigit():
        uid = str(getattr(ctx, "sender_id", "") or "")
        c = get_reading(uid)
        if not c or c.get("mode") != "cmds":
            await ctx.reply("请先 /指令 linux 或 /指令 windows 再翻页")
            return
        page = int(query)
        await ctx.reply(f"{c['title']}\n{_format_cmds(c['cmds'], page)}")
        return

    if not sys_choice:
        sys_choice = _detect_system(query)
        if not sys_choice:
            await ctx.reply("❓ 无法识别系统。请指定：/指令 linux 或 /指令 windows")
            return

    cmds = LINUX_CMDS if sys_choice == "linux" else WINDOWS_CMDS
    title = "🐧 Linux 常用指令" if sys_choice == "linux" else "🪟 Windows 常用指令"

    # 分类筛选
    cat = _detect_category(query)
    if cat:
        filtered = [c for c in cmds if c[2] == cat]
        if filtered:
            await ctx.reply(f"{title} · {cat}\n{_format_cmds(filtered)}")
            return
        await ctx.reply(f"❌ 「{cat}」分类暂无指令，展示全部：\n{title}\n{_format_cmds(cmds)}")
        return

    uid = str(getattr(ctx, "sender_id", "") or "")
    set_reading(uid, {"mode": "cmds", "cmds": cmds, "title": title, "page": 1, "total": max(1, (len(cmds) + PAGE_SIZE - 1) // PAGE_SIZE)})
    await ctx.reply(f"{title}\n{_format_cmds(cmds)}")
