# WastelandSoul

WastelandSoul 是一个面向 tModLoader 的 Terraria 模组，聚焦废土主题、剧情推进、Boss 战、城镇 NPC 和多阶段玩法体验。

## 项目简介

- 主题：废土科幻 / 机械废墟 / 残骸传奇
- 核心内容：
  - 智械人城镇 NPC
  - 清道夫 Boss 与阶段战斗
  - 物品、材料、污染系统、剧情进度
  - 中英双语本地化

## 目录结构

- `WastelandSoul/`：主模组代码与内容
- `WastelandSoulCN/`：中文语言包（由 `tools/sync_cn_translation.py` 生成）
- `tools/`：辅助脚本与校验工具
- `交接说明.md` / `WastelandSoul/开发说明.md`：当前状态与批次记录

## 仓库范围（2026-10-09 起）

本仓库**只放能开源的东西**：源码、我们自绘/自合成的资源、脚本、文档。

**不入库**（`.gitignore` 已挡）：编译产物（`*.tmod`、`obj/`、`bin/`、`.tml-*`）、
第三方模组的二进制与反汇编、临时与备份目录（`.tmp-*`、`.backup/`）、AI 出图原始件
（`art-inbox/`）、游戏日志、交付包（`测评包/`、`*.zip`）。

## 运行方式

1. 安装 tModLoader
2. 把该仓库克隆到本地
3. 将 `WastelandSoul` 作为模组源目录放到 tModLoader 的 ModSources 中
4. 使用 tModLoader 内置“生成模组”或命令行方式编译

示例：

```bat
cd /d E:\steam\steamapps\common\tModLoader
dotnet tModLoader.dll -build E:\开发\WastelandSoul
```

## 代码说明

本项目目前重点在以下内容：

- `WastelandSoul/Common/Systems/`：系统逻辑、剧情状态和全局玩法
- `WastelandSoul/Content/NPCs/`：NPC 与 Boss
- `WastelandSoul/Content/Items/`：物品与材料
- `WastelandSoul/Localization/`：本地化文本

## 许可证与第三方内容

本项目的**原创部分**采用 MIT License，详情见 [LICENSE](LICENSE)。

⚠️ **MIT 不覆盖**：Terraria（Re-Logic）原版素材的演绎件、以及任何第三方模组的
代码/二进制/反汇编内容。逐项清单见 **[NOTICE.md](NOTICE.md)** —— 再分发前请先读它。

## 贡献

欢迎提交 issue 和 PR。若你想参与开发，建议先阅读 `WastelandSoul/开发说明.md`。

## 状态

当前本仓库适合用于开源协作、模组开发、内容迭代和共享交流。
