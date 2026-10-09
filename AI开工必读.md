# 给下一个 AI / 下一个窗口的入口清单

> 这是**操作说明**。项目当前状态（完成 / 未完成 / 别重做 / 待办）在 **`交接说明.md`**。
> 更细的历史与教训在 **`WastelandSoul/开发说明.md`**（按批次记录，最全）。

## 开工顺序（照做就行）

1. `pwd` 确认在 `E:\开发`；读 **`交接说明.md`**（状态快照）+ **`WastelandSoul/开发说明.md` 最后两批**（最新改动与教训）。
2. `git log --oneline -5` + `git status --short` 看清本地状态。
   **不要 `git push` / `git fetch`** —— 玩家自己上传推送（本机到 GitHub 常瞬时失败）。
3. 改代码前先读文件（默认 `fs-observation-policy` 要求）；大改动优先**新增文件**，少动共享大文件。
4. 中间步骤只跑：构建 + 2~3 个关键检查器。
5. **装机前**跑完整流水线：`cmd /c "powershell -NoProfile -ExecutionPolicy Bypass -File ""E:\开发\tools\ws_pipeline.ps1"" -WaitForGame 300"`
6. 完成后：更新 `开发说明.md`（新批次）+ `交接说明.md`（刷新状态与待办）→ **本地 `git commit`**（不 push）。

## 绝对的禁忌（踩过血案）

- ⛔ 不许 `git push` / `git fetch` / `git clean` / force push。
- ⛔ 不许修改安装在 `Mods` 目录里的第三方模组文件（**读源码、调 API 是允许的**）。
- ⛔ 不许做**白色激光/光柱**或"不表示任何机制"的糊屏特效（玩家明令；`check_no_white_fx` 盯着）。
- ⛔ 不许把高清插画**缩放**成小尺寸像素贴图（会糊成"贴纸"，护甲那次的教训）。
- ⛔ 不许在加载期钩子里创建 GPU/音频资源（会 `ThreadStateException` 禁用整个模组）。
- ⛔ 不许写 `Main.tile[x, y] = ...`（只读；`Tile` 是结构体，改了也静默无效）。

## 常用入口

| 要做的事 | 命令 / 文件 |
| --- | --- |
| 构建 | 见 `交接说明.md`「常用命令」（必须 cd 到 tModLoader 目录） |
| 完整流水线（含装机） | `tools/ws_pipeline.ps1` |
| ChatGPT 出图 | `tools/chatgpt_art.py --prompt "..." --out art-inbox/raw/x.png`（已登录） |
| 护甲穿身图像素画 | `tools/gen_armor_pixel_equip.py`（自带 6 倍预览，**先看图再装机**） |
| 3D 角色 / 装备件 | `tools/gen_3d_blocky_characters.py`、`import_survival_kit.py`、`convert_blocky_gltf.py` |
| 汉化 | `tools/sync_cn_translation.py` → `tools/check_cn_parity.py` |
| 贴图抠底清理 | `tools/key_magenta_sprites.py`、`tools/clean_sprite_cutouts.py` |

## 汇报风格

**短**：结论 + 哈希 + 待办。不要一步步汇报；攒到有结论一次说清。玩家说过"省着点花 token"。
