"""主人控制面板 — 群聊管理、跨群发消息"""

import logging
import time
from datetime import datetime

from graci import on_command, plugin_handler, PluginContext
from graci import LoyanText, LoyanImage

_logger = logging.getLogger("Loyan.MasterControl")


def _is_master(ctx: PluginContext) -> bool:
    """检查发送者是否为主人"""
    try:
        from loyan.core.runtime import RuntimeContext
        runtime = RuntimeContext.get()
        if runtime and hasattr(runtime, "master_id"):
            return str(ctx.sender_id) == str(runtime.master_id)
    except Exception:
        pass
    try:
        import json, os
        from loyan.core.tools.paths import get_instances_dir
        instances_dir = get_instances_dir()
        for inst_name in os.listdir(instances_dir):
            cfg_path = os.path.join(instances_dir, inst_name, "config.json")
            if not os.path.exists(cfg_path):
                continue
            try:
                with open(cfg_path, encoding="utf-8") as f:
                    cfg = json.load(f)
                if cfg.get("default") or not hasattr(ctx, "runtime") or not ctx.runtime:
                    if str(ctx.sender_id) == str(cfg.get("master_id", "")):
                        return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def _format_time(ts: float) -> str:
    """格式化时间戳"""
    if not ts:
        return "未知"
    try:
        return datetime.fromtimestamp(ts).strftime("%m-%d %H:%M")
    except Exception:
        return "未知"


@on_command("/群列表", "/发群", "/set群名")
@plugin_handler
async def handle_master(ctx: PluginContext):
    cmd = ctx.command

    if cmd == "/群列表":
        if not _is_master(ctx):
            await ctx.reply("仅主人可用")
            return

        from loyan.plugins.core.group_registry import get_all_groups
        groups = get_all_groups()
        if not groups:
            await ctx.reply("暂无群聊记录\n群里有人发消息后会自动记录")
            return

        lines = [f"已记录 {len(groups)} 个群聊:\n"]
        for i, g in enumerate(groups, 1):
            gid = g.get("group_id", "")
            name = g.get("group_name", "")
            msg_count = g.get("message_count", 0)
            last = _format_time(g.get("last_active", 0))
            lines.append(f"{i}. {name}")
            lines.append(f"   ID: {gid}")
            lines.append(f"   消息数: {msg_count} | 最近活跃: {last}")
            members = g.get("known_members", [])
            if members:
                lines.append(f"   已知成员: {len(members)} 人")
            lines.append("")

        await ctx.reply("\n".join(lines))
        return

    if cmd == "/发群":
        if not _is_master(ctx):
            await ctx.reply("仅主人可用")
            return

        parts = ctx.raw_text.split(None, 2)
        if len(parts) < 3:
            await ctx.reply(
                "用法: /发群 <群ID> <消息>\n"
                "  或: /发群 <群ID> reply:<消息ID> <消息>\n"
                "  或: /发群 <群ID> qq:<QQ号> <消息>\n"
                "例: /发群 E9D46CED2B4449B30073997FD7B878A4 你好\n"
                "例: /发群 E9D46CED2B4449B30073997FD7B878A4 reply:xxx 你好\n"
                "例: /发群 E9D46CED2B4449B30073997FD7B878A4 qq:192004908 你好"
            )
            return

        group_id = parts[1]
        message = parts[2]

        from graci import loyan_send_msg
        from graci import LoyanText, LoyanReply

        # 解析 reply:<msg_id> 或 qq:<QQ号>
        reply_msg_id = ""
        if message.lower().startswith("reply:"):
            after = message[6:].strip()
            sp = after.split(None, 1)
            if len(sp) < 2:
                await ctx.reply("格式: reply:<消息ID> <消息内容>")
                return
            reply_msg_id = sp[0]
            message = sp[1]
        elif message.lower().startswith("qq:"):
            after = message[3:].strip()
            sp = after.split(None, 1)
            if len(sp) < 2:
                await ctx.reply("格式: qq:<QQ号> <消息内容>")
                return
            target_qq = sp[0]
            message = sp[1]
            from loyan.plugins.core.group_registry import get_group
            group_info = get_group(group_id)
            if group_info:
                member_msg = group_info.get("member_last_msg", {})
                reply_msg_id = member_msg.get(target_qq, "")
            if not reply_msg_id:
                await ctx.reply(f"未找到 {target_qq} 在群内的最近消息，请让该用户先发条消息")
                return

        if reply_msg_id:
            await loyan_send_msg(
                group_id,
                LoyanReply(message_id=reply_msg_id),
                LoyanText(text=message),
                chat_type="group",
            )
            await ctx.reply(f"已回复到群 {group_id[:8]}...")
            return

        # 清除缓存的 msg_id，避免把私聊 msg_id 带到群聊发送
        try:
            from loyan.core.loyan_adapter.pool import adapter_pool
            adapter = adapter_pool.get_default()
            if adapter and hasattr(adapter, '_last_msg_id'):
                adapter._last_msg_id = ""
                adapter._last_msg_id_time = 0.0
        except Exception:
            pass

        success = await loyan_send_msg(
            group_id, LoyanText(text=message), chat_type="group"
        )
        if success:
            await ctx.reply(f"已发送到群 {group_id[:8]}...")
        else:
            from loyan.plugins.core.group_registry import get_group
            group_info = get_group(group_id)
            last_msg_id = group_info.get("last_msg_id", "") if group_info else ""
            if last_msg_id:
                await loyan_send_msg(
                    group_id,
                    LoyanReply(message_id=last_msg_id),
                    LoyanText(text=message),
                    chat_type="group",
                )
                await ctx.reply(f"已通过回复发送到群 {group_id[:8]}...")
            else:
                await ctx.reply(f"发送失败: 群内无最近消息可回复，请先让群里有人发条消息")
        return

    if cmd == "/set群名":
        if not _is_master(ctx):
            await ctx.reply("仅主人可用")
            return

        parts = ctx.raw_text.split(None, 2)
        if len(parts) < 3:
            await ctx.reply("用法: /set群名 <群ID> <备注名>")
            return

        group_id = parts[1]
        name = parts[2]

        from loyan.plugins.core.group_registry import set_group_name, get_group
        existing = get_group(group_id)
        if not existing:
            await ctx.reply(f"未找到群 {group_id[:8]}... 先让群里发条消息让它被记录")
            return

        set_group_name(group_id, name)
        await ctx.reply(f"已将群 {group_id[:8]}... 备注为: {name}")
        return
