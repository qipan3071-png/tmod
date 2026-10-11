# Boss ChatGPT 原图（预览，未装进游戏）

2026-10-11 用本机已登录的 ChatGPT（`tools/chatgpt_art.py` + Edge 配置）出的**高清原图**，没有缩小、没有量化、没有写进 `Content/`。

觉得哪张能用，再说换进模组。要改哪一句提示词，改同目录 `prompt_*.txt` 再出一张覆盖即可。

| 文件 | 你定的外形 | 原图像素 |
| --- | --- | --- |
| `AshHeart_f0.png` | 四棱水晶，碎晶，略红光。**已点头装进模组** | 1254×1254 |
| `FireplaceGuardian_f0.png` | 四足机械骑士，长枪 + 盾，盔内黑、一只红眼。**已点头装进模组** | 1209×1300 |
| `FireplaceGuardian_ingame.png` | 装机用 256×307 的 3 倍最近邻预览 | — |
| `FireplaceGuardian_f0_twoleg.png` | 上一版双足无武器，仅对照 | 1129×1393 |
| `Archivist_canon.png` | **定稿参考**：金十字白兜帽、黑眼罩一颗红灯。出动作帧必须 `--image` 带上这张 | 1254×1254 |
| `Archivist_sheet.png` | 一张 4×2 出齐 7 个动作（第 8 格空），再抠成 `f0`–`f6` | 1536×1024 |
| `Archivist_f0.png`–`f2.png` | 待机：无红灯 / 脚左摆 / 脚右摆 | 从整表抠 |
| `Archivist_f3.png` | 前兆：一颗红灯 | 从整表抠 |
| `Archivist_f4.png`–`f6.png` | 攻击翻书 | 从整表抠 |
| `noattach/` | 没带参考图时出的旧稿，仅对照 | — |

出动作帧：一张整表 `prompt_archivist_sheet.txt` + `--image Archivist_canon.png`，再按格抠。不要一帧一帧问。3D 仍按批次 39 不作。
