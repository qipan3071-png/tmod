# -*- coding: utf-8 -*-
"""椭球地宫的**连通性**检查（辅助工具，不在 ws_pipeline 的 19 项里）。

为什么需要它：地宫只在玩家进门那一刻生成，编译和别的静态检查都碰不到"门被实心墙夹住"
这类错误 —— 历史上就是靠它抓出两个真窟窿：

  1. 隔墙有 5~6 格厚，一开始只把门放在墙中间、两侧墙体没掏通，**门被墙夹死**；
  2. 一层东头那道门外面还压着**地下通道自己的侧壳**，门洞不打通它照样出不去。

做法：把 `Content/Subworlds/FireplaceVault.cs` 的写格顺序（通道 → 竖井 → 椭球壳 →
掏空腔 + 重开通道嘴 → 铺楼板/补板 → 铺平台 → 一层隔墙+门 → 二层两翼+门 → 两条升降井）
在 Python 里**照抄一遍**，再从竖井落点做洪水填充，核对：

  * 门厅 → 竖井 → 主通道 → 通道东西两端、12 间房、两条升降井，全部可达；
  * 每间房底下都是实心地板、上下边界封住（升降井与堡垒竖井开洞处除外）；
  * 每扇门下方是实心地板、门能过人、门上方还有墙；
  * 通道两端各有一块封死的合金隔板。

⚠️ 它是 FireplaceVault.cs 的镜子：**改了那份代码就要同步改这里**，
否则它会报假问题（或者漏掉真问题）。运行：
    python tools/check_fireplace_vault_connectivity.py
"""
import io
import re
import sys
from array import array

LAYOUT = r"E:\开发\WastelandSoul\Content\Subworlds\FireplaceLayout.cs"

text = io.open(LAYOUT, encoding="utf-8-sig").read()
V = {}
decls = [(m.group(1), m.group(2).strip()) for m in
         re.finditer(r"public\s+const\s+int\s+(\w+)\s*=\s*([^;]+);", text)]
for _ in range(len(decls) + 1):
    moved = False
    for name, expr in decls:
        if name in V:
            continue
        e = expr
        for k, val in V.items():
            e = re.sub(r"\b%s\b" % k, str(val), e)
        try:
            V[name] = int(eval(e, {"__builtins__": {}}, {}))
            moved = True
        except Exception:
            pass
    if not moved:
        break

ROOMS = [(m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))
         for m in re.finditer(r'new\s+VaultRoom\(\s*"([^"]+)"\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\)', text)]

W, H = V["Width"], V["Height"]
CX, CY = V["VaultCenterX"], V["VaultCenterY"]
RX, RY = V["VaultRadiusX"], V["VaultRadiusY"]
SHELL = V["VaultShell"]
TOP, BOTTOM = V["VaultTop"], V["VaultBottom"]
LEFT, RIGHT = V["VaultLeft"], V["VaultRight"]
IRX, IRY = RX - SHELL, RY - SHELL
FLOOR_Y = V["VaultFloorY"]
PLAT = V["VaultPlatformThickness"]
SLAB_TOP, SLAB_BOTTOM = V["VaultSlabTop"], V["VaultSlabBottom"]
SLAB_L, SLAB_R = V["VaultSlabLeft"], V["VaultSlabRight"]
STORY_TOP = V["VaultStoryTop"]
UPPER_TOP, UPPER_BOTTOM = V["VaultUpperTop"], V["VaultUpperBottom"]
CEIL_TOP, CEIL_BOTTOM = V["VaultCeilingTop"], V["VaultCeilingBottom"]
WING_W_L, WING_W_R = V["VaultWestWingLeft"], V["VaultWestWingRight"]
WING_E_L, WING_E_R = V["VaultEastWingLeft"], V["VaultEastWingRight"]
TUN_L, TUN_R, TUN_TOP, TUN_BOT, TUN_SHELL = (V["TunnelLeft"], V["TunnelRight"],
                                             V["TunnelTop"], V["TunnelBottom"], V["TunnelShell"])
FORT_L, FORT_R, FORT_BOTTOM = V["FortLeft"], V["FortRight"], V["FortBottom"]
SHAFT_L, SHAFT_R = V["FortShaftLeft"], V["FortShaftRight"]
HALL_BOTTOM = V["HallBottom"]
LAD_W_L, LAD_W_R = V["VaultWestLadderX"], V["VaultWestLadderRight"]
LAD_E_L, LAD_E_R = V["VaultEastLadderX"], V["VaultEastLadderRight"]

# 0 = 未知（原岩，当实心）/ 1 = 实体 / 2 = 空气 / 3 = 门（可通行）/ 4 = 平台（可通行）
SOLID, AIR, DOOR, PLATFORM = 1, 2, 3, 4
grid = bytearray(W * H)


def get(x, y):
    if 0 <= x < W and 0 <= y < H:
        return grid[y * W + x]
    return 0


def setv(x, y, val):
    if 0 <= x < W and 0 <= y < H:
        grid[y * W + x] = val


def solid(x, y):
    """实心（原岩 0 也算实心）。"""
    return get(x, y) in (0, SOLID)


def walkable(x, y):
    return get(x, y) in (AIR, DOOR, PLATFORM)


def carve(l, t, r, b, val=AIR):
    for y in range(t, b + 1):
        for x in range(l, r + 1):
            setv(x, y, val)


def hline(l, r, y, val):
    for x in range(l, r + 1):
        setv(x, y, val)


def in_ellipse(x, y, rx, ry):
    dx = (x - CX) / float(rx)
    dy = (y - CY) / float(ry)
    return dx * dx + dy * dy <= 1.0


def in_outer(x, y):
    return in_ellipse(x, y, RX, RY)


def in_inner(x, y):
    return in_ellipse(x, y, IRX, IRY)


def in_fort(x, y):
    return FORT_L - 1 <= x <= FORT_R + 1 and y <= FORT_BOTTOM + 1


def in_tunnel_lane(x, y):
    """椭球**两端外侧**那两截通道臂（椭球里面归地宫自己排版）。"""
    band = TUN_TOP - TUN_SHELL <= y <= TUN_BOT + TUN_SHELL
    if not band:
        return False
    return x < LEFT + SHELL or x > RIGHT - SHELL


def can_build(x, y):
    return in_inner(x, y) and not in_fort(x, y) and not in_tunnel_lane(x, y)


def in_shaft(x, y):
    return SHAFT_L - 1 <= x <= SHAFT_R + 1 and HALL_BOTTOM <= y <= SLAB_BOTTOM


# =====================================================================================
#  1) 地下通道（先做：地宫的壳与楼板要压在它上面）
# =====================================================================================
carve(TUN_L - TUN_SHELL, TUN_TOP - TUN_SHELL, TUN_R + TUN_SHELL, TUN_BOT + TUN_SHELL)
for t in range(TUN_SHELL):
    for x in range(TUN_L - TUN_SHELL + t, TUN_R + TUN_SHELL - t + 1):
        setv(x, TUN_TOP - TUN_SHELL + t, SOLID)
        setv(x, TUN_BOT + TUN_SHELL - t, SOLID)
    for y in range(TUN_TOP - TUN_SHELL + t, TUN_BOT + TUN_SHELL - t + 1):
        setv(TUN_L - TUN_SHELL + t, y, SOLID)
        setv(TUN_R + TUN_SHELL - t, y, SOLID)
hline(TUN_L, TUN_R, TUN_TOP, SOLID)          # 顶压条
hline(TUN_L, TUN_R, TUN_BOT - 1, SOLID)      # 走道面压条

# 通道两端的封死隔板（C# 里是 Rect(right+1 .. right+shell+4) / Rect(left-shell-4 .. left-1)）
carve(TUN_R + 1, TUN_TOP - TUN_SHELL, TUN_R + TUN_SHELL + 4, TUN_BOT + TUN_SHELL, SOLID)
carve(TUN_L - TUN_SHELL - 4, TUN_TOP - TUN_SHELL, TUN_L - 1, TUN_BOT + TUN_SHELL, SOLID)

# =====================================================================================
#  2) 堡垒竖井（C#：OpenFortressShaft 先挖，楼板再绕开它）
# =====================================================================================
carve(SHAFT_L, HALL_BOTTOM, SHAFT_R, TUN_TOP + 1)

# 门厅内部当空气（只到竖井列为止，够验证"能从门厅走下来"）
carve(SHAFT_L, HALL_BOTTOM - 40, SHAFT_R, HALL_BOTTOM - 1)

# =====================================================================================
#  3) 椭球壳（5 格厚；内表面每 VaultTrimStep 行一条压条 —— 只影响观感，这里当实心）
# =====================================================================================
for y in range(TOP, BOTTOM + 1):
    for x in range(LEFT, RIGHT + 1):
        if in_outer(x, y) and not in_inner(x, y) and not in_fort(x, y):
            setv(x, y, SOLID)

# =====================================================================================
#  4) 掏空腔（平台底面以上）+ 重开通道嘴
# =====================================================================================
for y in range(TOP, FLOOR_Y + PLAT):
    for x in range(LEFT, RIGHT + 1):
        if can_build(x, y):
            setv(x, y, AIR)

carve(LEFT, TUN_TOP + 1, RIGHT, TUN_BOT - 2)

# =====================================================================================
#  5) 楼板（铺满整个椭球内空）+ 堡垒底下的补板
# =====================================================================================
for y in range(SLAB_TOP, SLAB_BOTTOM + 1):
    for x in range(SLAB_L, SLAB_R + 1):
        if can_build(x, y) and not in_shaft(x, y):
            setv(x, y, SOLID)

for y in range(FORT_BOTTOM + 1, SLAB_TOP):
    for x in range(FORT_L, FORT_R + 1):
        if not in_shaft(x, y):
            setv(x, y, SOLID)

# =====================================================================================
#  6) 主平台（顶面 = 通道走道面）
# =====================================================================================
for y in range(FLOOR_Y, FLOOR_Y + PLAT):
    for x in range(LEFT, RIGHT + 1):
        if can_build(x, y):
            setv(x, y, SOLID)

hline(LEFT, RIGHT, FLOOR_Y, SOLID)

# =====================================================================================
#  7) 一层：相邻两间之间一道隔墙 + 一扇门
# =====================================================================================
STORY = sorted([r for r in ROOMS if r[2] == STORY_TOP], key=lambda r: r[1])
UPPER = sorted([r for r in ROOMS if r[2] == UPPER_TOP], key=lambda r: r[1])


def fill_wall(left, right, top, bottom):
    for x in range(left, right + 1):
        for y in range(top, bottom + 1):
            if in_inner(x, y):
                setv(x, y, SOLID)


DOORS = []

for i in range(len(STORY) - 1):
    wall_l = STORY[i][3] + 1
    wall_r = STORY[i + 1][1] - 1
    fill_wall(wall_l, wall_r, STORY_TOP, FLOOR_Y - 1)
    DOORS.append(((wall_l + wall_r) // 2, FLOOR_Y, wall_l, wall_r))

# =====================================================================================
#  8) 二层两翼（顶板 + 外墙 + 隔墙 + 门；靠阁楼那面外墙再开一扇）
# =====================================================================================
def build_wing(outer_l, outer_r, wing, attic_door_on_west):
    if not wing:
        return

    for y in range(CEIL_TOP, CEIL_BOTTOM + 1):
        for x in range(outer_l, outer_r + 1):
            if in_inner(x, y):
                setv(x, y, SOLID)

    for i in range(len(wing) - 1):
        wall_l = wing[i][3] + 1
        wall_r = wing[i + 1][1] - 1
        fill_wall(wall_l, wall_r, CEIL_TOP, UPPER_BOTTOM)
        DOORS.append(((wall_l + wall_r) // 2, SLAB_TOP, wall_l, wall_r))

    west_l, west_r = outer_l, wing[0][1] - 1
    east_l, east_r = wing[-1][3] + 1, outer_r

    fill_wall(west_l, west_r, CEIL_TOP, UPPER_BOTTOM)
    fill_wall(east_l, east_r, CEIL_TOP, UPPER_BOTTOM)

    if attic_door_on_west:
        DOORS.append((west_l + 1, SLAB_TOP, west_l, west_r))
    else:
        DOORS.append((east_r - 1, SLAB_TOP, east_l, east_r))


WEST_WING = [r for r in UPPER if r[3] < FORT_L]
EAST_WING = [r for r in UPPER if r[1] > FORT_R]
build_wing(WING_W_L, WING_W_R, WEST_WING, True)
build_wing(WING_E_L, WING_E_R, EAST_WING, False)

# =====================================================================================
#  9) 两条升降井（最后挖：它会打穿楼板）
# =====================================================================================
def ladder(left, right, floor_y, top_y):
    for y in range(top_y, floor_y + 1):
        for x in range(left, right + 1):
            setv(x, y, AIR)

    for y in range(floor_y - 4, top_y - 1, -5):
        for x in range(left, right + 1):
            setv(x, y, PLATFORM)


ladder(LAD_W_L, LAD_W_R, FLOOR_Y - 1, UPPER_TOP)
ladder(LAD_E_L, LAD_E_R, FLOOR_Y - 1, UPPER_TOP)

# =====================================================================================
#  10) 门（门洞要打穿整堵墙，门卡在中间那一列）
# =====================================================================================
for x, floor_y, wall_l, wall_r in DOORS:
    for y in range(floor_y - 3, floor_y):
        for wx in range(wall_l, wall_r + 1):
            setv(wx, y, AIR)

    for y in range(floor_y - 3, floor_y):
        setv(x, y, DOOR)

# =====================================================================================
#  11) 洪水填充
# =====================================================================================
start = (SHAFT_L + 2, FLOOR_Y - 20)

if get(*start) != AIR:
    print("!! 落点不是空气：%s -> %s" % (start, get(*start)))
    sys.exit(1)

seen = bytearray(W * H)
stack = array("i", [start[1] * W + start[0]])
seen[start[1] * W + start[0]] = 1
count = 0

while stack:
    cur = stack.pop()
    count += 1
    x = cur % W
    y = cur // W

    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if not (0 <= nx < W and 0 <= ny < H):
            continue
        nidx = ny * W + nx
        if seen[nidx]:
            continue
        if grid[nidx] in (AIR, DOOR, PLATFORM):
            seen[nidx] = 1
            stack.append(nidx)

problems = []


def reached(x, y):
    return 0 <= x < W and 0 <= y < H and seen[y * W + x] == 1


def need_reach(x, y, label):
    if not reached(x, y):
        problems.append("走不到：%s (%d, %d)" % (label, x, y))


# ---- 11.0) 堡垒竖井必须整条通（门厅 → 通道 → 地宫的唯一入口）----
blocked_shaft = [(x, y) for y in range(SLAB_TOP, TUN_TOP + 2) for x in range(SHAFT_L, SHAFT_R + 1)
                 if get(x, y) != AIR]

if blocked_shaft:
    problems.append("堡垒竖井被填死了 %d 格（例如 %s）—— 门厅到地下通道/地宫会不通"
                    % (len(blocked_shaft), blocked_shaft[:4]))

# ---- 11.1) 门厅（竖井上口）----
need_reach(SHAFT_L + 2, HALL_BOTTOM - 5, "门厅 → 竖井")

# ---- 11.2) 通道东西两端都通到接近世界边缘，而且两端都被封板堵死 ----
mid = (TUN_TOP + TUN_BOT) // 2
need_reach(TUN_L + 30, mid, "通道西段")
need_reach(TUN_R - 30, mid, "通道东段")

for label, x in (("西端封板", TUN_L - 1), ("东端封板", TUN_R + TUN_SHELL + 4)):
    if not solid(x, mid):
        problems.append("通道%s (%d, %d) 不是实心的（通道没有封死）" % (label, x, mid))

# ------------------------------------------------
# 通道臂必须一路连续（中间不能有实心格把路掐断）：
# 每 40 格取一个窗口，窗口内至少有一格能走
# ------------------------------------------------
for x0 in range(TUN_L + 2, TUN_R - 2, 40):
    if not any(walkable(x, mid) for x in range(x0, min(x0 + 3, TUN_R))):
        problems.append("通道在 x=%d 附近被掐断了（%s）"
                        % (x0, [get(x, mid) for x in range(x0, x0 + 3)]))
        break

# ---- 11.3) 每个房间的中心 + 房间底面必须有实心地板 ----
for name, left, top, right, bottom in ROOMS:
    cx = (left + right) // 2
    need_reach(cx, (top + bottom) // 2, "房间「%s」内部" % name)
    need_reach(cx, bottom, "房间「%s」底面那格" % name)

    if not solid(cx, bottom + 1):
        problems.append("房间「%s」底下不是实心地板：(%d, %d)=%s"
                        % (name, cx, bottom + 1, get(cx, bottom + 1)))

# ---- 11.4) 每条升降井的顶端 ----
for label, x in (("西升降井", LAD_W_L + 1), ("东升降井", LAD_E_L + 1)):
    need_reach(x, UPPER_TOP + 1, "%s 顶端" % label)

# ---- 11.5) 每扇门都要能站人（门下方实心、门本身可通行、上方还有墙）----
for x, floor_y, wall_l, wall_r in DOORS:
    if not solid(x, floor_y):
        problems.append("门 (%d, %d) 下方不是实心地板" % (x, floor_y))
    if not reached(x, floor_y - 1):
        problems.append("门 (%d, %d) 过不去" % (x, floor_y))
    if not solid(x, floor_y - 4):
        problems.append("门 (%d, %d) 上面没有墙" % (x, floor_y))

# ---- 11.6) 房间上下边界必须封住（升降井与堡垒竖井开洞处除外）----
def hole_column(x):
    """这些列本来就要在楼板/地面上开洞。"""
    if LAD_W_L <= x <= LAD_W_R or LAD_E_L <= x <= LAD_E_R:
        return True
    return SHAFT_L <= x <= SHAFT_R


leaks = []

for name, left, top, right, bottom in ROOMS:
    for x in range(left, right + 1):
        for y in (top - 1, bottom + 1):
            if hole_column(x):
                continue
            if not solid(x, y) and not walkable(x, y):
                leaks.append((name, x, y, get(x, y)))

if leaks:
    problems.append("房间上下边界有 %d 格不是实心（楼板/地面有洞），例如 %s"
                    % (len(leaks), leaks[:4]))

# ---- 11.7) 二层房间的顶板必须封住（顶板是单独一层，不在房间矩形里）----
ceil_leaks = []

for name, left, top, right, bottom in ROOMS:
    if top != UPPER_TOP:
        continue

    for x in range(left, right + 1):
        if hole_column(x):
            continue
        if not solid(x, CEIL_TOP) and not solid(x, CEIL_BOTTOM):
            ceil_leaks.append((name, x, CEIL_TOP, get(x, CEIL_TOP)))

if ceil_leaks:
    problems.append("二层房间有 %d 格头顶没有顶板，例如 %s" % (len(ceil_leaks), ceil_leaks[:4]))

print("房间数: %d（一层 %d / 二层 %d），门: %d，可通行格: %d"
      % (len(ROOMS), len(STORY), len(UPPER), len(DOORS), count))

if problems:
    print("!! 地宫连通性有 %d 处问题：" % len(problems))
    for p in problems:
        print("   -", p)
    sys.exit(1)

print("[OK] 地宫连通性：门厅 -> 竖井 -> 主通道 -> 12 间房 / 通道东西两端 / 两条升降井全部可达，"
      "每间房都有地板、门与顶板，通道两端封死")
