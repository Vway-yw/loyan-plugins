from loyan.core.decorators import on_command, plugin_handler, PluginContext


@on_command("/loyan get", "/loyan安装", "/loyan配置")
@plugin_handler
async def handle_gracy_get(ctx: PluginContext):
    """返回 LoyanBot 安装与配置过程"""
    await ctx.reply(
        "🅻 LoyanBot 安装与配置过程\n\n"
        "1️⃣ 环境要求：Python 3.11+，内存 256MB+，磁盘 200MB+\n\n"
        "2️⃣ 安装：\n"
        "   git clone https://github.com/MiniYv-IT2/LoyanBot\n"
        "   cd loyan\n"
        "   python -m venv .venv && source .venv/bin/activate\n"
        "   pip install -r requirements.txt\n"
        "   pip install . --force-reinstall --no-deps\n\n"
        "3️⃣ 配置：\n"
        "   cp config.template.json config.json\n"
        "   编辑 config.json 填写机器人配置\n\n"
        "4️⃣ 配置 NapCat（QQ 协议端）：\n"
        "   下载 https://github.com/NapNeko/NapCat\n"
        "   启动后添加 WebSocket 客户端 wsServer → 127.0.0.1:3001\n"
        "   在 res/instances/ 创建实例配置（type=ws_forward，填 host/port/robot_id/master_id）\n\n"
        "5️⃣ 启动：\n"
        "   gracy run\n"
        "   gracy run --debug （调试）\n"
        "   gracy status / gracy stop\n\n"
        "📖 完整文档：https://github.com/MiniYv-IT2/LoyanBot/tree/main/docs\n"
        "💬 官方商店：插件商店可直接安装插件"
    )
