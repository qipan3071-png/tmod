# -*- coding: utf-8 -*-
"""Draw vanilla-proportioned armour equip sheets, pixel by pixel.

Output: ``Content/Items/Armor/<ItemName>_{Head,Body,Legs}.png`` =
40 wide x 1120 tall = **20 frames of 40x56**, which is exactly what vanilla's
player drawing code expects (head/body use ``bodyFrame``, legs use ``legFrame``).

Why hand-drawn pixel rows instead of a scaled illustration
----------------------------------------------------------
Scaling a 512px ChatGPT render down to 56px turns it into a "sticker": the shading
smears and the silhouette stops matching the player. So every piece here is an
explicit list of pixel rows; the ChatGPT art is only used to pick the palette.

Alignment facts this file is built on (measured, do not "fix" them)
------------------------------------------------------------------
* The player silhouette inside the 40-wide frame is centred on **x = 14.5**
  (measured row by row from the wiki's own player sprite). An earlier version
  centred pieces on x = 20, which hung every helmet off to the right.
* Vertical bands: head y11..22, torso y21..36, legs y36..51. Pieces overlap by
  1-2 px so no bare skin shows between them.
* Legs get a real per-frame swing (walking rows shift one leg up/down), which is
  what makes them read as walked-in armour rather than a static board.
"""
import argparse
import os
import sys

from PIL import Image

MAIN = r"E:\开发\WastelandSoul"
ARMOR_DIR = os.path.join(MAIN, r"Content\Items\Armor")
UPGRADE_DIR = os.path.join(MAIN, r"Content\Items\UpgradeTrees")
PREVIEW = r"E:\开发\.tmp-3d\preview\armor_pixels.png"

FRAME_W, FRAME_H, FRAME_COUNT = 40, 56, 20

# ---------------------------------------------------------------------------
# Placing boxes: (left, top, right, bottom), right/bottom exclusive.
# Centre of every box is 14.5 or 15.0 -> inside the self-check tolerance.
# The body starts at y20 (one row above the torso's y21) and the legs at y36, so
# the three pieces overlap and never leave a strip of bare skin at the waist.
# ---------------------------------------------------------------------------
HEAD_BOX = (9, 10, 21, 23)     # 12 wide, y10..22
BODY_BOX = (9, 19, 21, 37)     # 12 wide, y19..36 (collar sits under the helmet)
# Legs start at y32, **not** y36: 玩家实机截图里护胸底边（y33）和护腿顶边（y36）之间
# 露出了一条 6 像素宽的身色带（"把护腿的平移上去"）。上移 4 像素让裤腰塞进护胸下面，
# 覆盖窗口变成 y32..51（护胸到 y33，重叠 2 行）。脚底仍停在 y51 = 原版脚底。
LEG_BOX = (8, 32, 20, 50)      # 12 wide, y32..49

# Per-frame leg swing in px (rows: stand / walk / jump / fall / crouch / climb).
LEG_SWING = [0, 0, 0, 0,
             0, 1, 0, -1,
             0, 1, 0, -1,
             0, -1, 0, 1,
             0, 0, 0, 0,
             0, 1, 0, -1]

# Per-frame vertical offset: jump/fall/crouch (frames 12..19) sit one pixel higher,
# exactly like the torso does in vanilla's own frame table.
def frame_dy(frame):
    return 1 if frame >= 12 else 0


# ---------------------------------------------------------------------------
# Palettes. Seven role colours per set, plus two accents. They are sampled from
# the item icons (see the hex values in the comments) and then spread apart for
# contrast: vanilla armour reads crisply because the outline is far darker than
# the fill, while a low-contrast set looks muddy on both bright and dark screens.
#   o = outline  d = deep shade  D = dark  m = mid  L = light  H = highlight
#   r = accent A (rust / gold)   g = accent B (glow / gem)
# ---------------------------------------------------------------------------
def pal(o, d, D, m, L, H, r, g):
    # 'k' = the near-black outline. Maps write it as 'O' for readability, so both
    # spellings (and lower-case aliases) are accepted.
    return {"k": o, "o": o, "d": d, "D": D, "m": m,
            "L": L, "l": L, "H": H, "h": H, "r": r, "g": g}


# Pattern characters that are spelled differently from their palette key.
CHAR_KEY = {"O": "k"}


PAL_WARRIOR = pal((16, 17, 20), (44, 47, 54), (78, 82, 91),
                  (126, 131, 141), (178, 183, 192), (232, 236, 242),
                  (156, 86, 42), (255, 196, 74))
PAL_MAGE = pal((16, 12, 34), (42, 34, 78), (64, 50, 118),
               (104, 88, 186), (158, 140, 228), (228, 222, 252),
               (216, 194, 120), (150, 224, 255))
PAL_RANGER = pal((14, 13, 16), (44, 38, 28), (78, 66, 46),
                 (142, 122, 88), (200, 180, 140), (238, 226, 196),
                 (216, 168, 72), (140, 172, 200))
PAL_SUMMONER = pal((8, 22, 24), (26, 56, 56), (44, 96, 96),
                   (72, 150, 146), (140, 212, 200), (222, 248, 244),
                   (206, 168, 90), (120, 216, 200))
PAL_HEARTH = pal((22, 12, 14), (60, 30, 26), (110, 54, 40),
                 (178, 94, 58), (226, 154, 92), (250, 214, 152),
                 (150, 60, 38), (255, 172, 84))
PAL_FROST = pal((12, 16, 32), (32, 44, 70), (60, 80, 118),
                (116, 144, 180), (176, 200, 226), (226, 240, 252),
                (96, 176, 232), (255, 178, 92))
PAL_SIGNAL = pal((8, 20, 26), (24, 44, 54), (42, 76, 90),
                 (86, 138, 152), (150, 196, 206), (222, 246, 248),
                 (150, 88, 54), (120, 232, 224))

# 升级树两档（精钢战士套 → 灰烬合金 → 炉卫合金）。同一支线，所以沿用战士套的**形状**，
# 只换配色：灰烬档偏暖褐红（对应图标里的赤褐），炉卫档偏冷蓝灰 + 暖色炉火点缀。
PAL_ASH_ALLOY = pal((20, 10, 10), (56, 26, 22), (104, 52, 36),
                    (170, 96, 58), (214, 156, 104), (246, 220, 176),
                    (208, 150, 66), (255, 150, 70))
PAL_HEARTH_ALLOY = pal((10, 14, 28), (28, 40, 66), (56, 76, 112),
                       (112, 140, 178), (172, 198, 226), (228, 242, 254),
                       (255, 178, 92), (120, 208, 240))

# ---------------------------------------------------------------------------
# Sprite maps. '.' = transparent, everything else is a palette letter.
# The rows were designed to the measured widths: 10 px head, 13 px chest,
# 12 px legs (upper legs are thinner than the torso, like vanilla's).
# ---------------------------------------------------------------------------

# Warrior (kept byte-for-byte identical to the shipped 6th revision: this set has
# already been reviewed in game, so do not restyle it).
HELM_WARRIOR = (
    "...OOOOOO...",
    "..OHHLLLLO..",
    "..OHLLLLLO..",
    "..OLLMMLLO..",
    "..OLrMMrLO..",
    ".OOLLLLLLOO.",
    ".OLHHLHHLHO.",
    ".OOOOOOOOOO.",
    ".OdddddddO..",
    ".OgggggggO..",
    ".OdddddddO..",
    "..ODDMMDO...",
)

BODY_WARRIOR = (
    "OmmmmmmmmmmO.",
    "OmLmmmmmmLmO.",
    "OHDMDDODDMDDO",
    ".OHDMMDDMMDO.",
    ".OHDMLLLLMDO.",
    ".OHDMLggLMDO.",
    ".OHDMLggLMDO.",
    ".OHDDLLLLDDO.",
    ".OHDDMMMMDDO.",
    "..OHDMMMDDO..",
    "..OHDMMMDDO..",
    "..OHDMrrDO...",
    "..OHDDDDO....",
    "..OrrrrrrO...",
    "..OOOOOOOO...",
)

LEG_WARRIOR = (
    "OOOOOO..OOOOOO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OOOOOO..OOOOOO",
    "OHHHDO..ODHHHO",
    "OLLMDO..ODMLLO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMMDDO..ODDMMO",
    "OOOOOO..OOOOOO",
    "OrrrrO..OrrrrO",
    "OOOOOO..OOOOOO",
)

# --- Mage: soft hood + long robe + shin wrapping ---------------------------------
# Hood: a rounded dome (rows 0-2), a band with a gem, then a wide cowl whose middle
# is the face opening. The opening is filled with 'd' (deep) instead of being left
# transparent: a transparent "face hole" shows the skin through the hood, which
# reads as a hole in the armour.
HELM_MAGE = (
    "....OOOO....",
    "...OmmmmO...",
    "..OmmmmmmO..",
    "..OOggggOO..",
    ".OmmmmmmmmO.",
    ".OmmLmmLmmO.",
    ".OmmLggLmmO.",
    ".OmmLmmLmmO.",
    ".OmmmmmmmmO.",
    ".OmmmmmmmmO.",
    ".OOOOOOOOOO.",
)

# Robe: narrow shoulders that flare to a hem, a highlight running down the left
# side and shade on the right (the light comes from the top-left in Terraria).
BODY_MAGE = (
    "OOOHHHHHHHOOO",
    "OHLOHHHHHOLOO",
    "OHLLOHHHOLLOO",
    ".OHLLOOOLLLO.",
    ".OHLLLLLLLLO.",
    ".OHLLLrrLLLO.",
    ".OHLLLLLLLLO.",
    ".OHLLLmmLLLO.",
    ".OHLLLmmLLLO.",
    ".OHLLLmmLLLO.",
    ".OHLLLmmLLLO.",
    ".OHLLLmmLLLO.",
    "..OHLLmmLLO..",
    "..OHLLmmLLO..",
    "..OHLLmmLLO..",
    "..OHLLmmLLO..",
    "..OrrrrrrrO..",
    "..OOOOOOOOO..",
)

# Leggings: two trouser legs with a knee band and a cuff.
LEG_MAGE = (
    "OOOOOO..OOOOOO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OOOOOO..OOOOOO",
    "OHHHDO..ODHHHO",
    "OLLMDO..ODMLLO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMMDDO..ODDMMO",
    "OOOOOO..OOOOOO",
    "OrrrrO..OrrrrO",
    "OOOOOO..OOOOOO",
)

# --- Ranger: low slitted visor + strapped vest -----------------------------------
# Visor sits low on the head (rows 0-1 are short) with a horizontal eye slit and
# blue-grey lenses; the rest of the helm is the feather/leather tone.
HELM_RANGER = (
    "...OOOOOO...",
    "..OHHLLLLO..",
    ".OHHLLLLHHO.",
    ".OLLLLLLLLO.",
    ".OrrrrrrrrO.",
    ".OggggggggO.",
    ".OrrrrrrrrO.",
    ".ODDDDDDDDO.",
    ".OmLLLLLLmO.",
    "..ODDmmDDO..",
    "...OOOOOO...",
)

BODY_RANGER = (
    "OOOHHHHHHHOOO",
    "OHDOHHHHHODHO",
    "OHDDODOODDDHO",
    ".OHDLLrrLLDO.",
    ".OHDLggggLDO.",
    ".OHDLLrrLLDO.",
    ".OHDDLLLLDDO.",
    ".OHDLLLLLLDO.",
    ".OHrLLLLLLrO.",
    ".OHrLLLLLLrO.",
    "..OHDLLLLDO..",
    "..OHDLLLLDO..",
    "..ODDLLLLDO..",
    "..ODDLLLLDO..",
    "..OLDDDDDLO..",
    "..OLrrrrrLO..",
    "..ODDDDDDDO..",
    "..OOOOOOOOO..",
)

LEG_RANGER = (
    "OOOOOO..OOOOOO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OOOOOO..OOOOOO",
    "OHHHDO..ODHHHO",
    "OLLMDO..ODMLLO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMMDDO..ODDMMO",
    "OOOOOO..OOOOOO",
    "OrrrrO..OrrrrO",
    "OOOOOO..OOOOOO",
)

# --- Summoner: broad cowl + split tunic ------------------------------------------
# Cowl: dome with a crest, then a wide layered shawl. The face sits in a deep
# shadow band with two bright eyes, which is what makes it read as a cowl.
HELM_SUMMONER = (
    "...OOOOOO...",
    "..OmmggmmO..",
    ".OmmmmmmmmO.",
    ".OmLmmmmLmO.",
    ".OOmmmmmmOO.",
    ".OmmmmmmmmO.",
    ".OmmggggmmO.",
    ".OmmmmmmmmO.",
    ".OmmmmmmmmO.",
    ".OmmmmmmmmO.",
    ".OOOOOOOOOO.",
)

# Tunic: a wide shoulder cape that splits into two panels, diamond clasp in the middle.
BODY_SUMMONER = (
    "OOOHHHHHHHOOO",
    "OHDOHHHHHODHO",
    "OHDDDOOODDDHO",
    ".OHDLLggLLDO.",
    ".OHDLLLLLLDO.",
    ".OHDLLrrLLDO.",
    ".OHDDLLLLDDO.",
    ".OHDDLLLLDDO.",
    ".OHDOLLLLODO.",
    ".OHDOLLLLODO.",
    ".OHDOLLLLODO.",
    ".OHDOLLLLODO.",
    "..OHDLLLLDO..",
    "..OHDLLLLDO..",
    "..OHDLLLLDO..",
    "..OHDLLLLDO..",
    "..OHDLLLLDO..",
    "..OOOOOOOOO..",
)

LEG_SUMMONER = (
    "OOOOOO..OOOOOO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OOOOOO..OOOOOO",
    "OHHHDO..ODHHHO",
    "OLLMDO..ODMLLO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMMDDO..ODDMMO",
    "OOOOOO..OOOOOO",
    "OrrrrO..OrrrrO",
    "OOOOOO..OOOOOO",
)

# --- Ash Heart: sealed mask with a burning eye slit + ember plate ----------------
HELM_ASH = (
    "...OOOOOO...",
    "..Ommmmmo...",
    "..Ommmmmmo..",
    "..OOmmmmOO..",
    ".OmmmmmmmmO.",
    ".OOOOOOOOOO.",
    ".OmggggggmO.",
    ".OmmmmmmmmO.",
    ".OmmmmmmmmO.",
    ".OmmmmmmmmO.",
    "..ODDmmDDO..",
    "...OOOOOO...",
)

BODY_ASH = (
    "OOOHHHHHHHOOO",
    "OHDOHHHHHODHO",
    "OHDDDOOODDDHO",
    ".OHDggggggDO.",
    ".OHDooooooDO.",
    ".OHDDLLLLDDO.",
    ".OHDLLLLLLDO.",
    ".OHDLrrrrLDO.",
    ".OHDLrggrLDO.",
    ".OHDLrrrrLDO.",
    ".OHDDLLLLDDO.",
    "..OHDLLLLDO..",
    "..OHDLLLLDO..",
    "..OHDLLLLDO..",
    "..ODDLLLLDO..",
    "..ODDLLLLDO..",
    "..OLLLLLLLLO.",
    "..OOOOOOOOO..",
)

LEG_ASH = (
    "OOOOOO..OOOOOO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OOOOOO..OOOOOO",
    "OHHHDO..ODHHHO",
    "OLLMDO..ODMLLO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMMDDO..ODDMMO",
    "OOOOOO..OOOOOO",
    "OggggO..OggggO",
    "OOOOOO..OOOOOO",
)

# --- Hearth Guard: heavy cold-iron visor with a frosted brow + shield belt --------
HELM_HEARTH = (
    "...OOOOOO...",
    "..Ommmmmo...",
    "..Ommmmmmo..",
    "..OOmmmmOO..",
    ".OmmmmmmmmO.",
    ".OOOOOOOOOO.",
    ".OmmmmmmmmO.",
    ".OmggggggmO.",
    ".OmmmmmmmmO.",
    ".OmmmmmmmmO.",
    ".OmmmmmmmmO.",
    "..ODDmmDDO..",
    "...OOOOOO...",
)

BODY_HEARTH = (
    "OOOHHHHHHHOOO",
    "OHDOHHHHHODHO",
    "OHDDDOOODDDHO",
    ".OHDLLLLLLDO.",
    ".OHDLrrrrLDO.",
    ".OHDLrggrLDO.",
    ".OHDLrrrrLDO.",
    ".OHDDLLLLDDO.",
    ".OHDDLLLLDDO.",
    ".OHDDrrrrDDO.",
    ".OHDDLLLLDDO.",
    "..OHDLLLLDO..",
    "..OHDLLLLDO..",
    "..OHDLLLLDO..",
    "..ODDLLLLDO..",
    "..ODDLLLLDO..",
    "..OLDDDDDLO..",
    "..OOOOOOOOO..",
)

LEG_HEARTH = (
    "OOOOOO..OOOOOO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OOOOOO..OOOOOO",
    "OHHHDO..ODHHHO",
    "OLLMDO..ODMLLO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMMDDO..ODDMMO",
    "OOOOOO..OOOOOO",
    "OrrrrO..OrrrrO",
    "OOOOOO..OOOOOO",
)

# --- Signal Rig: lamp helm + rig vest with a chest lamp ---------------------------
HELM_SIGNAL = (
    "...OOOOOO...",
    "..Ommmmmo...",
    "..Ommmmmmo..",
    "..OOmmmmOO..",
    ".OmmmmmmmmO.",
    ".OOOOOOOOOO.",
    ".OroooooomO.",
    ".OrggggggmO.",
    ".OroooooomO.",
    ".OmmmmmmmmO.",
    "..ODDmmDDO..",
    "...OOOOOO...",
)

BODY_SIGNAL = (
    "OOOHHHHHHHOOO",
    "OHDOHHHHHODHO",
    "OHDDDOOODDDHO",
    ".OHDLLggLLDO.",
    ".OHDLLggLLDO.",
    ".OHDLLggLLDO.",
    ".OHDLLLLLLDO.",
    ".OHDLLLLLLDO.",
    ".OHDLLLLLLDO.",
    ".OHDOLLLLODO.",
    ".OHDOLLLLODO.",
    ".OHDOLLLLODO.",
    "..OHDLLLLDO..",
    "..OHDLLLLDO..",
    "..OHDLLLLDO..",
    "..OHDLLLLDO..",
    "..ODDDDDDDO..",
    "..OOOOOOOOO..",
)

LEG_SIGNAL = (
    "OOOOOO..OOOOOO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OLLMDO..ODMLLO",
    "OOOOOO..OOOOOO",
    "OHHHDO..ODHHHO",
    "OLLMDO..ODMLLO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMLLDO..ODLLMO",
    "OMMDDO..ODDMMO",
    "OOOOOO..OOOOOO",
    "OrrrrO..OrrrrO",
    "OOOOOO..OOOOOO",
)

# ---------------------------------------------------------------------------
# Sets: name -> (palette, head map, body map, legs map)
# ---------------------------------------------------------------------------
SETS = {
    "Warrior": (PAL_WARRIOR, HELM_WARRIOR, BODY_WARRIOR, LEG_WARRIOR),
    "Mage": (PAL_MAGE, HELM_MAGE, BODY_MAGE, LEG_MAGE),
    "Ranger": (PAL_RANGER, HELM_RANGER, BODY_RANGER, LEG_RANGER),
    "Summoner": (PAL_SUMMONER, HELM_SUMMONER, BODY_SUMMONER, LEG_SUMMONER),
    "AshHeart": (PAL_HEARTH, HELM_ASH, BODY_ASH, LEG_ASH),
    "HearthGuard": (PAL_FROST, HELM_HEARTH, BODY_HEARTH, LEG_HEARTH),
    "SignalRig": (PAL_SIGNAL, HELM_SIGNAL, BODY_SIGNAL, LEG_SIGNAL),
    "AshAlloy": (PAL_ASH_ALLOY, HELM_WARRIOR, BODY_WARRIOR, LEG_WARRIOR),
    "HearthAlloy": (PAL_HEARTH_ALLOY, HELM_WARRIOR, BODY_WARRIOR, LEG_WARRIOR),
}

# Set -> ((item name, part) x3). Prefixes are shared so the table stays readable;
# Scavenger's Grace is intentionally absent (that set was removed from the mod).
PREFIXES = {
    "Warrior": "SalvagedSteelWarrior",
    "Mage": "SalvagedSteelMage",
    "Ranger": "SalvagedSteelRanger",
    "Summoner": "SalvagedSteelSummoner",
}
SUFFIXES = {
    "Warrior": ("Helm", "Plate", "Greaves"),
    "Mage": ("Hood", "Robe", "Leggings"),
    "Ranger": ("Visor", "Vest", "Leggings"),
    "Summoner": ("Cowl", "Tunic", "Leggings"),
}


def pieces_for(set_name):
    """Return ((item name, part), ...) for a set.

    ⚠️ 顺序要紧：**先查 `FIXED_PIECES`**。升级树那两档（AshAlloy / HearthAlloy）名字里带
    "Ash"/"Hearth" 但并不在 `PREFIXES` 里；如果先走前缀分支，`set_name + "Head"` 会生成
    `AshAlloyHead_Head.png` 这种**根本不存在的文件名**，贴图悄悄写到错的地方、
    真正该覆盖的旧贴图一个字节都没动（这一版踩过）。
    """
    if set_name in FIXED_PIECES:
        return tuple(zip(FIXED_PIECES[set_name], ("Head", "Body", "Legs")))

    prefix, suffix = PREFIXES[set_name], SUFFIXES[set_name]
    return tuple((prefix + name, part)
                 for name, part in zip(suffix, ("Head", "Body", "Legs")))


# 名字不规则的套装：直接写全 → 三个部件名。升级树两档的装备纹理以前是旧生成器画的
# （整体偏右 5.5px、没有走路摆动），顺便一起换成同一套工艺。
# ⚠️ 装备纹理**必须和它的 `.cs` 放在同一个文件夹**：升级树那两档的类在
# `Content/Items/UpgradeTrees/`，所以它们的贴图不能写进 `Content/Items/Armor/`
# （tModLoader 按"类所在路径 + 后缀"找贴图，写错地方 = 贴图不生效）。
UPGRADE_SETS = ("AshAlloy", "HearthAlloy")

FIXED_PIECES = {
    "AshHeart": ("AshHeartMask", "AshHeartPlate", "AshHeartGreaves"),
    "HearthGuard": ("HearthGuardVisor", "HearthGuardCuirass", "HearthGuardGreaves"),
    "SignalRig": ("SignalRigHelm", "SignalRigPlate", "SignalRigGreaves"),
    "AshAlloy": ("AshAlloyWarriorHelm", "AshAlloyWarriorPlate", "AshAlloyWarriorGreaves"),
    "HearthAlloy": ("HearthAlloyWarriorHelm", "HearthAlloyWarriorPlate", "HearthAlloyWarriorGreaves"),
}


def out_dir(set_name):
    """这一套的贴图该写到哪个文件夹（与它的 `.cs` 同级）。"""
    return UPGRADE_DIR if set_name in UPGRADE_SETS else ARMOR_DIR


def put(canvas, x, y, colour):
    if 0 <= x < FRAME_W and 0 <= y < FRAME_H:
        canvas.putpixel((x, y), colour + (255,))


def rows(canvas, x0, y0, pattern, palette, dy=0):
    """Paint ``pattern`` (list of strings) at (x0, y0).

    The bottom row of a piece always becomes the deep shade: that dark separation
    from the body underneath is what makes worn armour look attached instead of
    pasted on. Accent rows (gold trim, glow) keep their own colour.
    """
    for j, line in enumerate(pattern):
        last = len(pattern) - 1

        for i, ch in enumerate(line):
            if ch in ".":
                continue

            # Pattern rows are written in the readable uppercase form; the palette
            # keys are short and lower-case.
            colour = palette[CHAR_KEY.get(ch, ch.lower())]

            if j == last and ch not in ("o", "g", "r"):
                colour = palette["d"]

            put(canvas, x0 + i, y0 + j + dy, colour)


def draw_helm(canvas, pattern, palette, dy):
    rows(canvas, HEAD_BOX[0], HEAD_BOX[1], pattern, palette, dy)


def draw_body(canvas, pattern, palette, dy):
    rows(canvas, BODY_BOX[0], BODY_BOX[1], pattern, palette, dy)


def draw_legs(canvas, pattern, palette, swing, dy):
    """Draw the two trouser legs, each with its own vertical swing.

    ``swing`` moves the leading leg up and the trailing leg down by one pixel, which
    is what the walk rows of the frame table are for. The gap between the legs is
    read from the map itself (the maps are written as ``LEFT..RIGHT``), so a skirt
    map with a solid row simply comes out as one wide piece.
    """
    leg_w = pattern[0].index(".")             # opaque columns of the left leg
    right_start = pattern[0].index(pattern[0][leg_w:].lstrip(".")) + leg_w
    gap = right_start - leg_w
    right_w = len(pattern[0]) - right_start

    for x0, width, sign in ((LEG_BOX[0], leg_w, 1),
                            (LEG_BOX[0] + right_start, right_w, -1)):
        column = [line[0:leg_w] if sign == 1 else line[right_start:right_start + right_w]
                  for line in pattern]
        rows(canvas, x0, LEG_BOX[1], column, palette, swing * sign + dy)


def build(set_name, part):
    palette, helm, body, legs = SETS[set_name]
    sheet = Image.new("RGBA", (FRAME_W, FRAME_H * FRAME_COUNT), (0, 0, 0, 0))

    for frame in range(FRAME_COUNT):
        canvas = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
        dy = frame_dy(frame)

        if part == "Head":
            draw_helm(canvas, helm, palette, dy)
        elif part == "Body":
            draw_body(canvas, body, palette, dy)
        else:
            draw_legs(canvas, legs, palette, LEG_SWING[frame], dy)

        sheet.alpha_composite(canvas, (0, frame * FRAME_H))

    return sheet


# Reference rows/centre measured from the vanilla player sprite. The self-check
# fails loudly if a regeneration drifts off these -- that is how the "centre was
# 13 instead of 14.5" bug was caught.
EXPECT = {
    "Head": {"centre": 14.5, "top": 11, "bottom": 22, "width": (9, 12)},
    "Body": {"centre": 14.5, "top": 21, "bottom": 35, "width": (12, 14)},
    # 护腿的参考范围跟着 LEG_BOX 一起上移（y32 起）：见 LEG_BOX 上面的注释。
    "Legs": {"centre": 14.5, "top": 32, "bottom": 46, "width": (12, 15)},
}


def audit_frames(sheet, part, name):
    """Per-frame checks that the old generator could not do.

    * frame 0 geometry against the measured vanilla reference;
    * every frame must be non-empty (a blank frame = an invisible pose);
    * legs must actually differ between the two walk frames (a leg sheet whose
      walk frames are identical is a static board).
    """
    import numpy as np

    problems = []
    frames = [np.asarray(sheet.crop((0, i * FRAME_H, FRAME_W, (i + 1) * FRAME_H)).convert("RGBA"))
              for i in range(FRAME_COUNT)]

    for index, frame in enumerate(frames):
        if not frame[..., 3].any():
            problems.append("%s 第 %d 帧是空的" % (name, index))

    array = frames[0][..., 3]
    ys, xs = np.nonzero(array)
    want = EXPECT[part]

    if not len(ys):
        problems.append("%s 是空的" % name)
        return problems, None

    centre = (xs.min() + xs.max()) / 2.0
    width = xs.max() - xs.min() + 1

    if abs(centre - want["centre"]) > 0.6:
        problems.append("%s 中心 %.1f 偏离参考 %.1f" % (name, centre, want["centre"]))

    if abs(ys.min() - want["top"]) > 2 or abs(ys.max() - want["bottom"]) > 2:
        problems.append("%s 纵向 %d..%d 偏离参考 %d..%d"
                        % (name, ys.min(), ys.max(), want["top"], want["bottom"]))

    if not want["width"][0] <= width <= want["width"][1]:
        problems.append("%s 宽度 %d 不在参考 %d..%d"
                        % (name, width, want["width"][0], want["width"][1]))

    # Interior holes: a transparent pixel with opaque neighbours on all four sides
    # would show bare skin through the plate.
    solid = array > 0
    holes = 0

    for y in range(1, FRAME_H - 1):
        for x in range(1, FRAME_W - 1):
            if solid[y, x]:
                continue

            if solid[y, x - 1] and solid[y, x + 1] and solid[y - 1, x] and solid[y + 1, x]:
                holes += 1

    if holes:
        problems.append("%s 有 %d 个内部空洞（游戏里会露皮肤）" % (name, holes))

    # Ragged silhouette: within each patterned row the opaque run must be solid.
    # Legs are exempt: their silhouette is deliberately two separate trouser legs,
    # so a transparent gap in the middle is correct there (and only there).
    if part != "Legs":
        for y in range(ys.min(), ys.max() + 1):
            columns = np.nonzero(solid[y])[0]

            if not len(columns):
                continue

            span = columns.max() - columns.min() + 1

            for x in range(columns.min(), columns.max() + 1):
                if not solid[y, x]:
                    problems.append("%s 第 y%d 行中间有断口 x=%d" % (name, y, x))
                    break

            if span > want["width"][1] + 3:
                problems.append("%s 第 y%d 行过宽 %d" % (name, y, span))
                break

    metrics = {"y": (int(ys.min()), int(ys.max())), "centre": centre, "width": int(width)}

    if part == "Legs":
        walk_a = frames[0].tobytes()    # standing
        walk_b = frames[5].tobytes()    # walking frame 1
        walk_c = frames[4].tobytes()
        metrics["walk_variants"] = len({walk_a, walk_b, walk_c})

        if walk_a == walk_b == walk_c:
            problems.append("%s 的走路帧和站立帧完全一样（腿不会动）" % name)

    return problems, metrics


def silhouette(sheet, part):
    """ASCII view of frame 0 for eyeballing a regenerated piece."""
    import numpy as np

    array = np.asarray(sheet.crop((0, 0, FRAME_W, FRAME_H)).convert("RGBA"))[..., 3]
    ys, xs = np.nonzero(array)
    lines = []

    for y in range(ys.min(), ys.max() + 1):
        lines.append("   y%02d %s" % (y, "".join("#" if array[y, x] else "." for x in range(FRAME_W))))

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="原版比例护甲穿身图（逐像素）")
    parser.add_argument("--set", default="all",
                        help="Warrior / Mage / Ranger / Summoner / AshHeart / HearthGuard / SignalRig，或 all")
    parser.add_argument("--check", action="store_true", help="只自检，不写文件")
    parser.add_argument("--ascii", action="store_true", help="打印第 0 帧的形状图")
    args = parser.parse_args()

    if args.set == "all":
        sets = list(SETS)
    elif args.set in SETS:
        sets = [args.set]
    else:
        print("未知套装 %s（可选：%s / all）" % (args.set, " / ".join(SETS)))
        return 2

    problems = []
    sheets_by_set = {}
    written = 0

    for set_name in sets:
        sheets = []

        for name, part in pieces_for(set_name):
            sheet = build(set_name, part)
            sheets.append(sheet)

            if not args.check:
                out = os.path.join(out_dir(set_name), "%s_%s.png" % (name, part))
                sheet.save(out)
                written += 1

            found, metrics = audit_frames(sheet, part, "%s_%s" % (name, part))
            problems += found

            if metrics:
                print("%-34s y=%d..%d 中心=%.1f 宽=%d"
                      % (name + "_" + part, metrics["y"][0], metrics["y"][1],
                         metrics["centre"], metrics["width"]))

            if args.ascii:
                print(silhouette(sheet, part))

        sheets_by_set[set_name] = sheets

    # 6x preview: every set stacked (head / body / legs) over the first 8 frames,
    # which covers stand + the whole walk cycle. Look at this before shipping.
    scale = 6
    tw, th = FRAME_W * scale, FRAME_H * scale
    frames_shown = 8
    preview = Image.new("RGBA",
                        ((tw + 6) * frames_shown, (th + 10) * 3 * len(sheets_by_set)),
                        (26, 28, 34, 255))
    y_cursor = 0

    for set_name, sheets in sheets_by_set.items():
        for part_index, sheet in enumerate(sheets):
            for frame in range(frames_shown):
                tile = sheet.crop((0, frame * FRAME_H, FRAME_W, (frame + 1) * FRAME_H))
                preview.alpha_composite(tile.resize((tw, th), Image.NEAREST),
                                        (frame * (tw + 6), y_cursor + part_index * (th + 10)))

        y_cursor += 3 * (th + 10)

    os.makedirs(os.path.dirname(PREVIEW), exist_ok=True)
    preview.save(PREVIEW)
    print("写出 %d 个穿身贴图" % written if not args.check else "只自检，未写文件")
    print("预览 %s（每 3 行一套：头 / 身 / 腿；每套前 8 帧 = 站立 + 走路循环）" % PREVIEW)

    if problems:
        print("!! 自检未通过（%d 条）：" % len(problems))
        for item in problems[:60]:
            print("   - " + item)
        return 1

    print("自检通过：中心/纵向/宽度/空洞/走路帧全部符合参考")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
