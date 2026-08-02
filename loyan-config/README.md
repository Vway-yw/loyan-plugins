# Loyan配置

获取 LoyanBot 安装与 Web 可视化配置过程

## 安装

在 LoyanBot 插件商店中搜索「Loyan配置」即可安装。

## 命令列表

| 命令 | 说明 | 使用环境 | 权限 |
|---|---|---|---|
| `/loyan get` | 获取 LoyanBot 安装与配置过程 | 群聊/私聊 | 所有人 |
| `/loyan安装` | 查看 LoyanBot 安装配置教程 | 群聊/私聊 | 所有人 |
| `/loyan配置` | 查看 LoyanBot 配置教程 | 群聊/私聊 | 所有人 |

## 配置说明

LoyanBot 已全面支持 **Web 可视化配置**，无需手动编辑 config.json：

1. 启动 `gracy run` 后自动拉起管理面板
2. 浏览器打开面板地址（默认 http://127.0.0.1:5090）
3. 默认账号 `Admin` / 密码 `@Loyan`
4. 面板内可配置：
   - 适配器管理（QQ/微信/Telegram 接入）
   - AI 提供商（模型、密钥、实例管理）
   - 插件商店（安装/管理/更新）
   - 机器人设置与监控

## 仓库

GitHub: https://github.com/Vway-yw/loyan-config

## 文档

完整框架文档: https://github.com/MiniYv-IT2/LoyanBot/tree/main/docs
