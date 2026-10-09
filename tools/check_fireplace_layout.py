# -*- coding: utf-8 -*-
"""壁炉世界生成的**布局不变量**检查。

为什么需要：世界生成只在玩家**真正进入子世界**时才跑，`ws_pipeline.ps1` 的隔离加载自检
（`-server`）和客户端自检都覆盖不到它 —— 生成器里写错一个常量，要等你进门那一刻才炸，
而且是在子世界里炸（可能直接把世界卡在半成品状态）。

这个检查器把"生成前就该成立"的几何关系从源码里读出来核对：
  1. 世界尺寸（8400×2400）与各结构都在世界范围内；
  2. 堡垒 / 高塔 / 塔顶场地 / 地下通道 的嵌套与相接关系正确，通道**横贯整张图、两端都留出封板**；
  3. 门厅地板在门厅底面、出生点落在地板之上（进入壁炉不会卡在墙里/掉出去），
     而且出生点不在火塘里、也不正对堡垒竖井（不然一进门就掉下去）；
  4. 分层基准：堡垒屋顶埋在灰烬地表以下、祈塔从灰烬里钻出来、地宫整块在岩石层以下；
  5. 塔顶场地确实落在"太空"高度（worldSurface × 0.35 以上）；
  6. 塔身确实从堡垒屋顶一直通到塔顶场地（中间没有断层），层高能整除；
  7. **椭球地宫**：椭球在世界内、壳厚 4~6、平台顶面与地下通道走道面齐平、
     12 间房都落在椭球内空里、都不压堡垒投影、互不重叠、同层相邻两间之间正好是 4~6 格隔墙、
     两条升降井真的落在它们要服务的房间里；
  8. 堡垒竖井落在门厅里、落在椭球范围内、而且正好落在"一层·中央大厅"内部。
"""
import io
import os
import re
import sys
from bisect import bisect_left

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_batch_usage import methods, strip_comments  # noqa: E402

LAYOUT = r"E:\开发\WastelandSoul\Content\Subworlds\FireplaceLayout.cs"
LIGHTS = r"E:\开发\WastelandSoul\Content\Subworlds\FireplaceLights.cs"


def constants(path):
    """读出 `public const int X = 表达式;`（表达式里可以引用先前解析出来的常量）。

    多趟解析：常量在文件里的顺序不必和依赖顺序一致（例如 VaultLeft 引用了后面才
    定义的 VaultCenterX），一趟扫不出来就再扫一趟，直到没有新值为止。
    """
    text = io.open(path, encoding="utf-8-sig").read()
    declarations = []

    for match in re.finditer(r"public\s+const\s+int\s+(\w+)\s*=\s*([^;]+);", text):
        declarations.append((match.group(1), match.group(2).strip()))

    values = {}

    for _ in range(len(declarations) + 1):
        progressed = False

        for name, expression in declarations:
            if name in values:
                continue

            resolved = expression

            for known, value in values.items():
                resolved = re.sub(r"\b%s\b" % known, str(value), resolved)

            try:
                values[name] = int(eval(resolved, {"__builtins__": {}}, {}))     # noqa: S307
                progressed = True
            except Exception:
                pass

        if not progressed:
            break

    return values


def rooms(path):
    """读出地宫的房间清单（`new VaultRoom("名字", l, t, r, b)`）。"""
    text = io.open(path, encoding="utf-8-sig").read()
    pattern = re.compile(
        r'new\s+VaultRoom\(\s*"([^"]+)"\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\)')

    return [(m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))
            for m in pattern.finditer(text)]


def light_constants():
    """读出 `FireplaceLights` 里的布光步长常量（`internal const int X = N;`）。"""
    if not os.path.exists(LIGHTS):
        return {}

    text = io.open(LIGHTS, encoding="utf-8-sig").read()

    return {m.group(1): int(m.group(2))
            for m in re.finditer(r"const\s+int\s+(\w+)\s*=\s*(\d+)\s*;", text)}


def light_coverage(v, vault_rooms, lv, max_gap):
    """抽样核对"每个可通行点到最近光源 ≤ max_gap 格"。

    光源集与可通行面都按 **FireplaceLayout 的常量 + FireplaceLights 的步长常量**重建
    （生成器里那几条规则：可通行地面行铺连续微光走线、地面火把 / 天花吊灯按步长铺、
    竖井每 N 层平台一盏、矿洞按网格一盏）。矿洞是噪声挖的没法复刻几何，靠第 12 节前半
    那几条常量断言（CaveCell - 1 ≤ 12）保证。

    距离用**切比雪夫距离**（|dx|、|dy| 取大者）——就是"格数"的直觉口径。
    返回 (problems, (最远距离, 抽样点数))。
    """
    sample = 8
    shell = v["TowerShell"]
    step_line = lv["LineStep"]
    step_floor = lv["FloorStep"]
    step_ceil = lv["CeilingStep"]
    shaft_step = lv["ShaftStep"]
    shaft_every = lv["ShaftLightEvery"]

    rows = {}           # 光源行 y -> 该行的 x 列表（点光源）
    segments = []       # (y, x0, x1) 连续微光走线
    walk = []           # (区域名, x, y) 可通行抽样点

    def line(y, x0, x1):
        if x1 >= x0:
            segments.append((y, x0, x1))

    def dots(y, x0, x1, step):
        if x1 >= x0:
            rows.setdefault(y, []).extend(range(x0, x1 + 1, step))

    def walk_row(region, y, x0, x1):
        if x1 >= x0:
            for x in range(x0, x1 + 1, sample):
                walk.append((region, x, y))

    # ---------------- 门厅 / 中层走廊 / 两侧小房间 ----------------
    hall_l, hall_r = v["HallLeft"], v["HallRight"]
    hall_top, hall_bottom = v["HallTop"], v["HallBottom"]
    mid = hall_top + (hall_bottom - hall_top) // 2
    ceiling = v["FortTop"] + v["FortShell"] - 1

    line(hall_bottom, hall_l + 4, hall_r - 4)
    dots(hall_bottom - 1, hall_l + 12, hall_r - 12, step_floor)
    dots(ceiling + 1, hall_l + 12, hall_r - 12, step_ceil)
    walk_row("门厅地面", hall_bottom - 1, hall_l, hall_r)

    line(mid, hall_l + 12, hall_r - 12)
    dots(mid - 1, hall_l + 40, hall_r - 40, step_floor)
    walk_row("门厅中层", mid - 1, hall_l + 12, hall_r - 12)

    cursor = hall_l + 10

    for width in (70, 100, 56):
        room_left = cursor
        room_right = room_left + width - 1
        wall_right = room_right + 5

        if wall_right >= hall_r - 10:
            break

        line(mid - 1, room_left, room_right)
        dots(mid - 2, room_left + 4, room_right - 4, step_floor)
        walk_row("门厅侧房", mid - 2, room_left, room_right)
        cursor = wall_right + 1

    # ---------------- 祈塔：19 层地板 + 攀登竖井 + 每条楼板下的吊灯 ----------------
    tower_l, tower_r = v["TowerLeft"], v["TowerRight"]
    tower_top, tower_bottom = v["TowerTop"], v["TowerBottom"]
    floor_h = v["TowerFloorHeight"]
    floors = (tower_bottom - tower_top) // floor_h
    inner_l = tower_l + shell + 12
    inner_r = tower_r - shell - 2

    for i in range(floors):
        y = tower_bottom - i * floor_h

        line(y, inner_l, inner_r)
        dots(y - 1, inner_l, inner_r, step_floor)
        walk_row("塔身", y - 1, inner_l, inner_r)

    for i in range(floors):
        dots(tower_top + i * floor_h + 1, tower_l + shell + 4, tower_r - shell - 4, step_ceil)

    ladder = 0

    for platform in range(tower_bottom - 5, tower_top + 4, -5):
        walk_row("塔身攀登井", platform - 1, tower_l + shell + 1, tower_l + shell + 7)

        if ladder % shaft_every == 0:
            rows.setdefault(platform - 1, []).append(tower_l + shell)

        ladder += 1

    # ---------------- 塔顶场地 ----------------
    arena_l, arena_r = v["ArenaLeft"], v["ArenaRight"]
    arena_top, arena_bottom = v["ArenaTop"], v["ArenaBottom"]

    line(arena_bottom - 1, arena_l + 2, arena_r - 2)
    dots(arena_bottom - 2, arena_l + 6, arena_r - 6, step_floor)
    dots(arena_bottom - 2, arena_l + 40, arena_r - 40, 12)
    dots(arena_top + 2, arena_l + 18, arena_r - 18, step_ceil)

    for y in range(arena_top + 4, arena_bottom - 7, lv["WallBandStep"]):
        rows.setdefault(y, []).append(arena_l + 2)
        rows.setdefault(y, []).append(arena_r - 2)

    walk_row("塔顶场地", arena_bottom - 2, arena_l + 2, arena_r - 2)

    # ---------------- 地下通道（横贯整张图） ----------------
    tunnel_l, tunnel_r = v["TunnelLeft"], v["TunnelRight"]
    tunnel_top, tunnel_bottom = v["TunnelTop"], v["TunnelBottom"]

    line(tunnel_bottom - 2, tunnel_l + 6, tunnel_r - 6)
    dots(tunnel_bottom - 3, tunnel_l + 8, tunnel_r - 8, step_floor)
    line(tunnel_top, tunnel_l + 6, tunnel_r - 6)
    walk_row("地下通道", tunnel_bottom - 3, tunnel_l, tunnel_r)

    # ---------------- 椭球地宫：12 间房 + 两条升降井 ----------------
    for name, room_l, room_top, room_r, room_bottom in vault_rooms:
        upper = (room_top == v["VaultUpperTop"])
        floor_y = v["VaultSlabTop"] if upper else v["VaultFloorY"]
        ceil_y = v["VaultCeilingBottom"] if upper else v["VaultSlabBottom"]

        line(floor_y, room_l + 2, room_r - 2)
        dots(floor_y - 1, room_l + 3, room_r - 3, step_floor)
        dots(ceil_y + 1, room_l + 8, room_r - 8, step_ceil)
        walk_row("地宫·%s" % name, floor_y - 1, room_l, room_r)

    for left, right in ((v["VaultWestLadderX"], v["VaultWestLadderRight"]),
                        (v["VaultEastLadderX"], v["VaultEastLadderRight"])):
        ladder = 0

        for platform in range(v["VaultFloorY"] - 1 - 4, v["VaultUpperTop"] - 1, -5):
            walk_row("地宫升降井", platform - 1, left, right)

            if ladder % shaft_every == 0:
                rows.setdefault(platform - 1, []).append(left)

            ladder += 1

    # ---------------- 逐点算距离（切比雪夫） ----------------
    light_rows = [(y, sorted(set(xs))) for y, xs in rows.items()]
    problems = []
    reported = 0
    worst = 0

    for region, px, py in walk:
        best = max_gap + 1

        for y, xs in light_rows:
            dy = abs(y - py)

            if dy >= best:
                continue

            index = bisect_left(xs, px)

            for j in (index - 1, index):
                if 0 <= j < len(xs):
                    distance = max(dy, abs(px - xs[j]))

                    if distance < best:
                        best = distance

        for y, x0, x1 in segments:
            dy = abs(y - py)

            if dy >= best:
                continue

            dx = 0 if x0 <= px <= x1 else min(abs(px - x0), abs(px - x1))
            distance = max(dx, dy)

            if distance < best:
                best = distance

        if best > worst:
            worst = best

        if best > max_gap and reported < 12:
            problems.append("布光不足：%s (%d, %d) 到最近光源 %d 格 > %d"
                            % (region, px, py, best, max_gap))
            reported += 1

    return problems, (worst, len(walk))


def main():
    if not os.path.exists(LAYOUT):
        print("!! 找不到 %s" % LAYOUT)
        return 1

    v = constants(LAYOUT)
    vault_rooms = rooms(LAYOUT)
    problems = []

    def need(condition, message):
        if not condition:
            problems.append(message)

    w = v["Width"]
    h = v["Height"]

    # 1) 都在世界里
    for name in ("FortLeft", "FortRight", "FortTop", "FortBottom",
                 "HallLeft", "HallRight", "HallTop", "HallBottom",
                 "TowerLeft", "TowerRight", "TowerTop", "TowerBottom",
                 "ArenaLeft", "ArenaRight", "ArenaTop", "ArenaBottom",
                 "TunnelLeft", "TunnelRight", "TunnelTop", "TunnelBottom",
                 "FortShaftLeft", "FortShaftRight",
                 "SpawnX", "SpawnY"):
        value = v.get(name)

        if value is None:
            problems.append("常量 %s 读不出来" % name)
            continue

        if name.endswith(("Left", "Right", "X")):
            if not (0 <= value < w):
                problems.append("%s=%d 超出世界宽度 0..%d" % (name, value, w - 1))

        if name.endswith(("Top", "Bottom", "Y")):
            if not (0 <= value < h):
                problems.append("%s=%d 超出世界高度 0..%d" % (name, value, h - 1))

    # 2) 嵌套 / 相接
    need(v["FortLeft"] < v["HallLeft"] < v["HallRight"] < v["FortRight"], "门厅没有落在堡垒内部")
    need(v["FortTop"] < v["HallTop"] < v["HallBottom"] < v["FortBottom"], "门厅的上下边界不在堡垒内部")
    need(v["TowerBottom"] == v["FortTop"], "塔基没有坐在堡垒屋顶上（TowerBottom 应当等于 FortTop）")
    need(v["TowerTop"] < v["TowerBottom"], "塔身高度为负")
    need(v["TowerLeft"] > v["FortLeft"] and v["TowerRight"] < v["FortRight"], "塔身比堡垒还宽，塔基落不到屋顶上")
    need(v["ArenaTop"] < v["ArenaBottom"] and v["ArenaBottom"] <= v["TowerTop"] + 4, "塔顶场地没有接在塔身上端")
    need(v["ArenaLeft"] < v["TowerLeft"] and v["ArenaRight"] > v["TowerRight"], "塔顶场地没有比塔身宽（爬上去会撞墙）")
    need(v["TunnelTop"] > v["HallBottom"], "地下通道跑到门厅上面去了")
    need(v["TunnelTop"] < v["TunnelBottom"], "通道高度为负")

    # 通道：横贯整张图，两端都要留得下"封死隔板"（Rect 会再往外扩 shell+4 格）
    need(v["TunnelLeft"] <= 16, "通道西口没有顶到世界西边缘（TunnelLeft=%d）" % v["TunnelLeft"])
    need(v["TunnelRight"] >= w - 20, "通道东口没有顶到世界东边缘（TunnelRight=%d）" % v["TunnelRight"])
    need(v["TunnelLeft"] - v["TunnelShell"] - 4 >= 0, "通道西端的封板会伸出世界")
    need(v["TunnelRight"] + v["TunnelShell"] + 4 <= w - 1, "通道东端的封板会伸出世界")

    # 3) 出生点：站在门厅地板上，不在火塘里、也不正对竖井
    need(v["HallLeft"] < v["SpawnX"] < v["HallRight"], "出生点 x 不在门厅里")
    need(v["SpawnY"] == v["HallBottom"], "出生点 y 应当就是门厅地板那一格（玩家会站在它上面）")
    need(not (v["HearthLeft"] <= v["SpawnX"] <= v["HearthRight"]), "出生点落在火塘里")
    need(not (v["FortShaftLeft"] - 2 <= v["SpawnX"] <= v["FortShaftRight"] + 2),
         "出生点正对堡垒竖井（一进门就会掉下去）")

    # 4) 分层高度：灰烬地表在堡垒屋顶之上（堡垒全埋）、祈塔从灰烬里钻出来
    surface = v["SurfaceBase"]
    need(v["FortTop"] > surface, "堡垒屋顶没有埋在灰烬地表以下")
    need(v["TowerTop"] < surface < v["TowerBottom"], "祈塔没有从灰烬地表里钻出来")
    need(surface < v["HallTop"], "门厅跑到灰烬地表上面了（门厅应当是地下的）")
    need(v["RockTop"] == surface + v["CrustDepth"], "岩石层高度与地表+壳厚不一致")
    need(v["VaultTop"] > v["RockTop"], "椭球上缘跑到灰烬层里去了（应当整块在岩石层）")

    # 5) 塔顶场地在太空（原版太空阈值 = worldSurface × 0.35）
    space_line = surface * 0.35
    need(v["ArenaTop"] > 0, "塔顶场地顶到世界天花板了")
    need(v["ArenaBottom"] < space_line,
         "塔顶场地整体不在太空高度（ArenaBottom=%d 应小于 %.1f）" % (v["ArenaBottom"], space_line))
    need(v["ArenaBottom"] <= space_line - 20,
         "塔顶场地离太空线太近（余量只有 %.1f 格）" % (space_line - v["ArenaBottom"]))

    # 6) 塔身层高能整除，楼板才不会在塔顶/塔基留半层
    span = v["TowerBottom"] - v["TowerTop"]
    need(v["TowerFloorHeight"] > 0, "塔层高必须为正")
    need(span % v["TowerFloorHeight"] == 0,
         "塔身高度 %d 不能被层高 %d 整除" % (span, v["TowerFloorHeight"]))
    need(span // v["TowerFloorHeight"] >= 12,
         "塔楼层数只有 %d 层，'尽量做大'没做到" % (span // v["TowerFloorHeight"]))

    # 7) 堡垒竖井
    need(v["FortLeft"] < v["FortShaftLeft"] and v["FortShaftRight"] < v["FortRight"],
         "堡垒竖井不在堡垒的横向范围里")
    need(v["HallLeft"] < v["FortShaftLeft"] and v["FortShaftRight"] < v["HallRight"],
         "堡垒竖井不在门厅里（下来的时候会撞在门厅墙上）")
    need(v["FortShaftRight"] > v["FortShaftLeft"], "堡垒竖井宽度为负")
    need(v["FortShaftLeft"] > v["HearthRight"] or v["FortShaftRight"] < v["HearthLeft"],
         "堡垒竖井和火塘重叠（火塘会被挖穿）")

    # 8) 椭球地宫
    cx = v["VaultCenterX"]
    cy = v["VaultCenterY"]
    rx = v["VaultRadiusX"]
    ry = v["VaultRadiusY"]
    shell = v["VaultShell"]

    need(4 <= shell <= 6, "地宫隔绝墙厚 %d 不在玩家要求的 4~6 格" % shell)
    need(12 <= v["VaultTrimStep"] <= 16, "地宫压条行距 %d 不在玩家要求的 12~16 行" % v["VaultTrimStep"])
    need(v["FortShaftLeft"] > v["VaultLeft"] and v["FortShaftRight"] < v["VaultRight"],
         "堡垒竖井不在椭球的横向范围里（竖井落不到地宫里）")

    # 椭球要落在世界里，四周留出世界边缘的余量（生成时还要靠 WorldPaint.InWorld 兜底）
    margin = 8
    need(v["VaultLeft"] >= margin, "椭球左边 %d 贴到世界边缘了" % v["VaultLeft"])
    need(v["VaultRight"] <= w - 1 - margin, "椭球右边 %d 贴到世界边缘了" % v["VaultRight"])
    need(v["VaultTop"] >= margin, "椭球上边 %d 贴到世界顶了" % v["VaultTop"])
    need(v["VaultBottom"] <= h - 1 - margin, "椭球下边 %d 贴到世界底了" % v["VaultBottom"])

    # 平台顶面必须和地下通道的走道面同高：从竖井下来一路是平的
    need(v["VaultFloorY"] == v["TunnelBottom"] - 1,
         "地宫平台顶面 %d 没有对齐通道走道面 %d" % (v["VaultFloorY"], v["TunnelBottom"] - 1))
    need(v["VaultSlabTop"] > v["VaultUpperBottom"], "二层楼板压到了二层房间的内空")
    need(v["VaultStoryTop"] > v["VaultSlabBottom"], "一层房间的内空顶行没有落在一层天花板以下")
    need(v["VaultFloorY"] > v["VaultStoryTop"], "一层房间的内空上下界反了")
    need(v["VaultCeilingTop"] < v["VaultUpperTop"], "二层顶板压到了二层房间的内空")
    need(v["VaultCeilingBottom"] >= v["VaultCeilingTop"], "二层顶板厚度为负")

    # 通道必须从椭球里穿过去（竖井下来才能走到两端的通道臂）
    need(v["VaultTop"] < v["TunnelTop"] - v["TunnelShell"], "通道顶壳跑到椭球上缘外面去了")
    need(v["TunnelBottom"] + v["TunnelShell"] < v["VaultBottom"], "通道底壳跑到椭球下缘外面去了")

    # 房间
    need(10 <= len(vault_rooms) <= 12, "地宫房间数 %d 不在要求的 10~12 间" % len(vault_rooms))

    inner_rx = rx - shell
    inner_ry = ry - shell

    def inside_ellipse(x, y, tolerance=1e-6):
        dx = (x - cx) / float(inner_rx)
        dy = (y - cy) / float(inner_ry)
        return dx * dx + dy * dy <= 1.0 + tolerance

    def in_fortress_box(x, y):
        return (v["FortLeft"] - 1 <= x <= v["FortRight"] + 1) and y <= v["FortBottom"] + 1

    # 通道禁区 = 椭球**两端外侧**那两截臂（椭球里面归地宫自己排版，见 FireplaceVault.InTunnelLane）
    def in_tunnel_lane(x, y):
        band = (v["TunnelTop"] - v["TunnelShell"] <= y <= v["TunnelBottom"] + v["TunnelShell"])
        if not band:
            return False
        return x < v["VaultLeft"] + shell or x > v["VaultRight"] - shell

    for name, left, top, right, bottom in vault_rooms:
        need(right > left and bottom > top, "房间「%s」的矩形反了" % name)
        need(right - left + 1 >= 40, "房间「%s」太窄（%d 格），家具放不下" % (name, right - left + 1))
        need(bottom - top + 1 >= 20, "房间「%s」太矮（%d 格）" % (name, bottom - top + 1))

        for x, y in ((left, top), (right, top), (left, bottom), (right, bottom)):
            need(inside_ellipse(x, y),
                 "房间「%s」的角 (%d, %d) 跑到椭球内空外面了" % (name, x, y))

        # 房间不许压到堡垒投影（否则会把门厅挖穿）与通道禁区（否则会把通道堵死）
        for x in (left, right):
            for y in (top, bottom):
                need(not in_fortress_box(x, y), "房间「%s」压到堡垒投影了：(%d, %d)" % (name, x, y))
                need(not in_tunnel_lane(x, y), "房间「%s」压到通道禁区了：(%d, %d)" % (name, x, y))

        need(0 <= left and right < w and 0 <= top and bottom < h, "房间「%s」超出世界范围" % name)

    for i in range(len(vault_rooms)):
        for j in range(i + 1, len(vault_rooms)):
            a = vault_rooms[i]
            b = vault_rooms[j]
            overlap = (a[1] <= b[3] and b[1] <= a[3] and a[2] <= b[4] and b[2] <= a[4])

            need(not overlap, "房间「%s」与「%s」重叠了" % (a[0], b[0]))

    # 8.5) 隔墙厚度：同一层里**挨着**的两间房之间的缝就是隔墙，要求 4~6 格
    #      （缝 > 20 格的是堡垒投影 / 主通道那种大空档，不是隔墙，跳过）。
    #      一层最北/最南那两间房的外侧没有墙（直接通向通道臂），所以只看相邻两间之间。
    for band_top in sorted({r[2] for r in vault_rooms}):
        band = sorted([r for r in vault_rooms if r[2] == band_top], key=lambda r: r[1])

        for a, b in zip(band, band[1:]):
            gap = b[1] - a[3] - 1

            if gap <= 20:
                need(4 <= gap <= 6,
                     "「%s」与「%s」之间隔墙只有 %d 格（要求 4~6 格实体隔墙）"
                     % (a[0], b[0], gap))

    # 8.6) 二层两翼：外墙边界、每翼的房间数、以及"房间到外墙"的隔墙厚度
    upper = sorted([r for r in vault_rooms if r[2] == v["VaultUpperTop"]], key=lambda r: r[1])
    west_wing = [r for r in upper if r[3] < v["FortLeft"]]
    east_wing = [r for r in upper if r[1] > v["FortRight"]]

    need(len(west_wing) >= 2, "二层西翼房间少于 2 间")
    need(len(east_wing) >= 2, "二层东翼房间少于 2 间")
    need(len(west_wing) + len(east_wing) == len(upper), "二层有房间压在堡垒投影上")

    if west_wing:
        need(v["VaultWestWingRight"] <= v["FortLeft"] - 1, "西翼外墙压到堡垒投影了")
        need(4 <= west_wing[0][1] - v["VaultWestWingLeft"] <= 6,
             "西翼最西那间房与外墙之间的隔墙 %d 格（要求 4~6 格）"
             % (west_wing[0][1] - v["VaultWestWingLeft"]))
        need(4 <= v["VaultWestWingRight"] - west_wing[-1][3] <= 6,
             "西翼最东那间房与外墙之间的隔墙 %d 格（要求 4~6 格）"
             % (v["VaultWestWingRight"] - west_wing[-1][3]))

    if east_wing:
        need(v["VaultEastWingLeft"] >= v["FortRight"] + 1, "东翼外墙压到堡垒投影了")
        need(4 <= east_wing[0][1] - v["VaultEastWingLeft"] <= 6,
             "东翼最西那间房与外墙之间的隔墙 %d 格（要求 4~6 格）"
             % (east_wing[0][1] - v["VaultEastWingLeft"]))
        need(4 <= v["VaultEastWingRight"] - east_wing[-1][3] <= 6,
             "东翼最东那间房与外墙之间的隔墙 %d 格（要求 4~6 格）"
             % (v["VaultEastWingRight"] - east_wing[-1][3]))

    # 9) 一层的房间要"串"在通道上：层内相邻两间必须紧邻（差 4~6），
    #    而且堡垒竖井要正好落在某一间一层房间里
    story = sorted([r for r in vault_rooms if r[2] == v["VaultStoryTop"]], key=lambda r: r[1])

    if len(story) < 2:
        problems.append("一层房间少于 2 间（主通道上应当串起一串房间）")
    else:
        need(v["TunnelLeft"] <= story[0][1] and story[-1][3] <= v["TunnelRight"],
             "一层房间没有落在通道的横向范围里")
        need(any(r[1] <= v["FortShaftLeft"] and v["FortShaftRight"] <= r[3] for r in story),
             "堡垒竖井没有落在任何一间一层房间里")

    for name, left, top, right, bottom in vault_rooms:
        if top == v["VaultStoryTop"]:
            need(bottom == v["VaultFloorY"] - 1,
                 "一层房间「%s」的底面 %d 没有贴住平台顶面 %d" % (name, bottom, v["VaultFloorY"] - 1))
        elif top == v["VaultUpperTop"]:
            need(bottom == v["VaultSlabTop"] - 1,
                 "二层房间「%s」的底面 %d 没有贴住楼板顶面 %d" % (name, bottom, v["VaultSlabTop"] - 1))
        else:
            problems.append("房间「%s」的顶行 %d 既不等于一层 %d、也不等于二层 %d"
                            % (name, top, v["VaultStoryTop"], v["VaultUpperTop"]))

    # 升降井要真的落在它服务的房间里，而且整条都在椭球内空里
    west_ladder = (v["VaultWestLadderX"], v["VaultWestLadderRight"])
    east_ladder = (v["VaultEastLadderX"], v["VaultEastLadderRight"])

    need(west_ladder[1] > west_ladder[0], "西升降井宽度为负")
    need(east_ladder[1] > east_ladder[0], "东升降井宽度为负")

    if story:
        first_story = story[0]
        need(first_story[1] <= west_ladder[0] and west_ladder[1] <= first_story[3],
             "西升降井没落在一层「%s」里" % first_story[0])

    if upper:
        east_room = max(upper, key=lambda r: r[3])
        need(east_room[1] <= east_ladder[0] and east_ladder[1] <= east_room[3],
             "东升降井没落在二层「%s」里" % east_room[0])

    for label, ladder in (("西升降井", west_ladder), ("东升降井", east_ladder)):
        for x in ladder:
            for y in (v["VaultUpperTop"], v["VaultFloorY"] - 1):
                need(inside_ellipse(x, y),
                     "%s 的列 x=%d 在 y=%d 处不在椭球内空里" % (label, x, y))

    # 10) 尺寸别退回去（这是本批的硬要求）
    need(w == 8400 and h == 2400, "世界尺寸不是玩家要求的 8400×2400（现在是 %d×%d）" % (w, h))

    # 11) 背景墙：玩家要求整个壁炉子世界**统一一种**背景墙（灰烬荒壁），而且**不允许有洞**。
    #
    #     实现方式是"**所有挖空 / 建筑步骤之后**，再跑一遍统一的补墙 pass"
    #     （FireplaceWalls.Build：凡是地表线以下的空气格、以及塔身/场地内空，一律 WorldPaint.SetWall）。
    #     所以这一节是**正向断言**（旧版是"生成器里一处铺墙都不许有"，那是上一批的临时状态）：
    #       a. 子世界生成器里必须**恰好有一处**铺墙调用；
    #       b. 它必须在 FireplaceWalls.cs 的 Build 里，而且判据里带"地表线以下"（FireplaceTerrain.Surface）
    #          与"只补空气格"（HasTile）—— 这两条就是"全局连续"的全部依据；
    #       c. 别处**一处都不许**再出现铺墙 / 拆墙调用（零散补墙 = 迟早漏一块，这正是要避免的写法）；
    #       d. 这一步必须注册在**所有挖空 / 建筑步骤之后**、收尾之前。
    #     例外：WorldPaint.cs 是底层笔刷本体，原语定义在那儿不算"调用点"。
    wall_writers = re.compile(
        r"WorldPaint\s*\.\s*(?:SetWall|WallRect|WallRectOpenOnly)\s*\("
        r"|WorldGen\s*\.\s*(?:PlaceWall|KillWall)\s*\(")

    subworld_dir = os.path.dirname(LAYOUT)
    wall_hits = {}

    for name in sorted(os.listdir(subworld_dir)):
        if not name.endswith(".cs") or name == "WorldPaint.cs":
            continue

        path = os.path.join(subworld_dir, name)
        body = strip_comments(io.open(path, encoding="utf-8-sig", errors="replace").read())

        for hit in wall_writers.finditer(body):
            line = body.count("\n", 0, hit.start()) + 1
            wall_hits.setdefault(name, []).append((line, hit.group(0).strip(), body))

    total_hits = sum(len(items) for items in wall_hits.values())
    need(total_hits == 1,
         "铺墙调用应当**恰好一处**（FireplaceWalls 的统一补墙 pass），实际 %d 处：%s"
         % (total_hits, "; ".join("%s:%d %s" % (n, line, text)
                                  for n, items in sorted(wall_hits.items())
                                  for line, text, _ in items)))

    wall_pass = "FireplaceWalls.cs"

    if total_hits != 1 or wall_pass not in wall_hits:
        need(False, "唯一那一处铺墙调用必须写在 %s 的 Build 里（现在写在 %s）"
                    % (wall_pass, ", ".join(sorted(wall_hits)) or "无"))
    else:
        body = wall_hits[wall_pass][0][2]
        owners = [name for name, method_body in methods(body) if "WorldPaint.SetWall" in method_body]
        need(owners == ["Build"], "补墙调用必须落在 FireplaceWalls.Build 里，实际落在 %s" % owners)

        for name, method_body in methods(body):
            if name != "Build":
                continue

            need("FireplaceTerrain.Surface" in method_body,
                 "统一补墙 pass 必须用「地表线以下」判据（FireplaceTerrain.Surface[x]）")
            need("HasTile" in method_body, "统一补墙 pass 必须只补**空气格**")

    # 11.d 注册顺序：补墙必须排在所有挖空 / 建筑步骤之后、收尾之前
    subworld_src = strip_comments(io.open(os.path.join(subworld_dir, "FireplaceSubworld.cs"),
                                          encoding="utf-8-sig", errors="replace").read())
    pass_order = re.findall(r'tasks\s*\.\s*Add\s*\(\s*new\s+PassLegacy\s*\(\s*"[^"]*"\s*,\s*([\w.]+)\s*\)',
                            subworld_src)
    wall_step = "FireplaceWalls.Build"

    need(wall_step in pass_order, "统一补墙 pass 没有注册进生成步骤（FireplaceSubworld.OnLoad 的 tasks）")

    if wall_step in pass_order:
        index = pass_order.index(wall_step)

        for step in ("FireplaceTerrain.Build", "FireplaceBuildings.BuildFortress",
                     "FireplaceBuildings.BuildTower", "FireplaceBuildings.BuildTunnel",
                     "FireplaceVault.Build"):
            need(step in pass_order and pass_order.index(step) < index,
                 "挖空 / 建筑步骤 %s 必须排在补墙 pass 之前（不然补完又被挖出洞）" % step)

        need("FireplaceBuildings.Finish" in pass_order
             and pass_order.index("FireplaceBuildings.Finish") > index,
             "补墙 pass 必须排在收尾（框架化）之前 —— 补完要刷墙帧")

    # 12) 布光密度：玩家要求"每个可通行点到最近光源 ≤ 12 格"。
    #
    #     全量几何校验要复刻整个生成器（矿洞是噪声挖的，没法复刻），所以这里是
    #     **抽样校验 + 结构性常量校验**两层：
    #       a. FireplaceLights 里的每一条步长都必须 ≤ MaxGap（12），横竖两条都算
    #          （竖井是 ShaftStep × ShaftLightEvery、矿洞是 CaveCell - 1）；
    #       b. 按 FireplaceLayout 的常量**重建可通行面与光源集**（生成器的规则写死在
    #          FireplaceLights 的常量里，这里照同一套规则建模），沿每条可通行行每 8 格抽一个点，
    #          算它到最近光源的切比雪夫距离，全部必须 ≤ 12；跑不到 5 秒。
    light_consts = light_constants()
    need(light_consts, "读不出 FireplaceLights 的布光常量（文件被挪了？）")

    max_gap = light_consts.get("MaxGap", 0)
    need(max_gap == 12, "布光不变量 MaxGap 必须是 12（现在是 %s）" % max_gap)

    for name in ("LineStep", "FloorStep", "CeilingStep", "WallBandStep", "CaveCell"):
        need(light_consts.get(name, 999) <= max_gap,
             "布光步长 %s = %s 超过 MaxGap=%s" % (name, light_consts.get(name), max_gap))

    need(light_consts.get("ShaftStep", 999) * light_consts.get("ShaftLightEvery", 999) <= max_gap,
         "竖井灯距 ShaftStep × ShaftLightEvery = %s 超过 MaxGap=%s"
         % (light_consts.get("ShaftStep", 999) * light_consts.get("ShaftLightEvery", 999), max_gap))

    need(light_consts.get("CaveCell", 999) - 1 <= max_gap,
         "矿洞布光网格 CaveCell-1 = %s 超过 MaxGap=%s（格内最远距离就是它）"
         % (light_consts.get("CaveCell", 999) - 1, max_gap))

    # 矿洞布光 pass 必须真的用这个网格（不然"矿洞里每 8 格一盏"只是纸面常量）
    terrain_src = strip_comments(io.open(os.path.join(subworld_dir, "FireplaceTerrain.cs"),
                                         encoding="utf-8-sig", errors="replace").read())
    need("FireplaceLights.CaveCell" in terrain_src,
         "矿洞布光必须用 FireplaceLights.CaveCell 的网格（FireplaceTerrain.LightCaverns）")

    coverage_problems, worst = light_coverage(v, vault_rooms, light_consts, max_gap)
    problems.extend(coverage_problems)

    if problems:
        print("!! 壁炉布局有 %d 处问题：" % len(problems))
        for item in problems:
            print("   -", item)
        print("CHECK FAILED")
        return 1

    print("[OK] 壁炉布局不变量成立：%dx%d，塔 %d 层 / 高 %d 格，场地 y=%d..%d（太空线 %.0f），出生点 (%d, %d)"
          % (v["Width"], v["Height"], span // v["TowerFloorHeight"], span,
             v["ArenaTop"], v["ArenaBottom"], space_line, v["SpawnX"], v["SpawnY"]))
    print("     地宫椭球 %dx%d @ (%d, %d)，壳厚 %d，房间 %d 间（一层 %d / 二层 %d），平台顶面 y=%d（对齐通道走道面）"
          % (rx * 2, ry * 2, cx, cy, shell, len(vault_rooms), len(story), len(upper), v["VaultFloorY"]))
    print("     通道 y=%d..%d 横贯 x=%d..%d（两端各留 %d 格封板），堡垒竖井 x=%d..%d"
          % (v["TunnelTop"], v["TunnelBottom"], v["TunnelLeft"], v["TunnelRight"],
             v["TunnelShell"] + 4, v["FortShaftLeft"], v["FortShaftRight"]))
    print("     背景墙：%s 一处统一补墙 pass（排在 %s 之后、收尾之前），生成器别处 0 处铺墙调用"
          % (wall_pass, pass_order[pass_order.index(wall_step) - 1] if wall_step in pass_order and pass_order.index(wall_step) > 0 else "?"))
    print("     布光：可通行点抽样 %d 个，到最近光源最远 %d 格（不变量 ≤ %d；矿洞按 %d×%d 网格布光）"
          % (worst[1], worst[0], max_gap, light_consts.get("CaveCell", 0), light_consts.get("CaveCell", 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
