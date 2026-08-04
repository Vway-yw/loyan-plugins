"""Loyan配置 — 获取 LoyanBot 安装与 Web 可视化配置过程

命令：
  /loyan get /loyan安装 /loyan配置 — 查看安装配置教程"""

from graci import on_command, plugin_handler, PluginContext


@on_command("/loyan get", "/loyan安装", "/loyan配置")
@plugin_handler
async def handle_loyan_get(ctx: PluginContext):
    """返回 LoyanBot 安装与 Web 可视化配置过程"""
    await ctx.reply(
        "🅻 LoyanBot 安装与配置过程\n\n"
        "1️⃣ 安装：\n"
        "   git clone https://github.com/MiniYv-IT2/LoyanBot\n"
        "   cd loyan\n"
        "   python -m venv .venv && source .venv/bin/activate\n"
        "   pip install -r requirements.txt\n"
        "   pip install . --force-reinstall --no-deps\n\n"
        "2️⃣ 启动：\n"
        "   loyan run\n"
        "   启动后会自动拉起 Web 管理面板\n\n"
        "3️⃣ Web 可视化配置（新）：\n"
        "   🌐 浏览器打开面板地址（默认 http://127.0.0.1:5090）\n"
        "   🔑 默认账号 Admin / 密码 @Loyan\n"
        "   ⚙️ 在面板中可完成全部配置：\n"
        "      • 适配器管理（QQ/微信/Telegram 接入）\n"
        "      • AI 提供商配置（模型/密钥/实例）\n"
        "      • 插件商店（安装/管理/更新插件）\n"
        "      • 机器人设置与监控\n"
        "      • 无需手动编辑 config.json\n\n"
        "📖 完整文档：https://github.com/MiniYv-IT2/LoyanBot/tree/main/docs"
    )
