# LoyanBot 插件合集

Vway-yw 开发的 LoyanBot 插件集合，共 19 个插件，统一托管在本仓库。

## 插件列表

| # | 插件 | 目录 | 说明 |
|---|---|---|---|
| 1 | 象棋启动器 | `loyan-chess-start/` | 检测象棋服务器是否正常运行 |
| 2 | 系统指令 | `loyan-cmds/` | Linux/Windows 实用指令，自动识别系统 |
| 3 | Loyan配置 | `loyan-config/` | 获取 LoyanBot 安装与 Web 可视化配置过程 |
| 4 | 汇率转换 | `loyan-currency/` | 实时汇率查询与货币转换（免key） |
| 5 | 游戏插件 | `loyan-game/` | 钓鱼/挖矿/打猎等小游戏，金币、经验、等级、排行榜 |
| 6 | 一言 | `loyan-hitokoto/` | 一言/诗词/动漫/名言/英文句子 |
| 7 | 和平精英热点 | `loyan-hpjy/` | 和平精英热点/爆料/攻略，序号+翻页看全文 |
| 8 | 成语接龙 | `loyan-idiom/` | 与机器人成语接龙游戏 |
| 9 | IP查询 | `loyan-ipinfo/` | 查询 IP 归属地与网络信息 |
| 10 | MasterControl | `loyan-master-control/` | 主人控制面板 - 群聊管理、跨群发消息 |
| 11 | NASA每日一图 | `loyan-nasa/` | NASA 每日天文图片与说明 |
| 12 | 小说阅读 | `loyan-novel/` | 小说搜索与阅读，序号+翻页看全文 |
| 13 | 表情包生成 | `loyan-sticker/` | 互动表情包生成，支持自定义文字和模板 |
| 14 | SysInfo_plugin | `loyan-sysinfo/` | 系统状态查询：运行信息、资源占用 |
| 15 | 逃跑吧少年 | `loyan-tpbsn/` | 热点/爆料/攻略/通用兑换码，序号+翻页看全文 |
| 16 | 翻译 | `loyan-translate/` | 中英互译及多语言翻译（免费） |
| 17 | GitHub热门 | `loyan-trending/` | GitHub 热门仓库（日/周/月/按语言） |
| 18 | 天气预报 | `loyan-weather/` | 城市天气实况与未来预报（免key） |
| 19 | 王者荣耀热点 | `loyan-wzry/` | 王者荣耀热点/爆料/攻略，序号+翻页看全文 |

## 游戏热点/阅读插件使用

三个游戏热点插件（王者/和平/逃跑）和小说阅读共用一套交互：

```
/王者热点          → 标题列表（带序号）
/王者热点 1        → 第 1 条正文第 1 页（每页 500 字）
/下一页 /上一页    → 翻页
/尾页              → 跳最后一页
/第3页             → 跳到指定页
```

翻页命令全局共用，当前在读哪篇就翻哪篇。

## 安装

在 LoyanBot 插件商店中添加本仓库：

```
https://github.com/Vway-yw/loyan-plugins
```

商店采集后即可搜索安装各插件。

## 框架

LoyanBot 框架: https://github.com/MiniYv-IT2/LoyanBot

## 文档

框架完整文档: https://github.com/MiniYv-IT2/LoyanBot/tree/main/docs
