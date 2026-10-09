# -*- coding: utf-8 -*-
"""检查「在 SpriteBatch 上 Draw 之前，批次到底是开着的吗」。

为什么需要它（这次的 **Main engine crash**）：

    System.InvalidOperationException: Draw was called, but Begin has not yet been called.
       at WastelandTrailRenderer.Draw(...)
       at WastelandSwingDrawSystem.PostDrawTiles()
    [Main Thread/FATAL] [tML]: Main engine crash

`ModSystem.PostDrawTiles` 里 `Main.spriteBatch` **不在 Begin 状态**（原版在这之前已经 End 了），
直接 Draw 会抛异常，而绘制发生在主线程绘制流程里 → tML 直接判定引擎崩溃、游戏退出。
表现层代码里原本还写着"不重新 Begin/End 批次"这条**错误经验**，正是它导致了这次崩溃。

判定规则（保守，只抓明确错误的写法）：

  * **批次对象**有两个来源：
      - 字面写出来的 `Main.spriteBatch`（也含裸写 `spriteBatch`）；
      - **被显式赋值过 `Main.spriteBatch` 的局部变量 / 字段** —— 例如
        `SpriteBatch batch = Main.spriteBatch;` 之后 `batch.Begin/End/Draw` 全部算数。
        别名只认"赋值来源是 Main.spriteBatch"这一种，**不认"任何变量名都算"**（那是放水），
        也不追"某个函数 return Main.spriteBatch"这种间接来源 —— 那种写法会被判红，
        方向是保守的（宁可误报，也不放过真的没开批次）。
  * 某个方法里有批次 Draw：
      - 方法名是框架**保证批次已开**的钩子（PreDraw / PostDraw / Draw / DrawTiles 之类）→ 放过；
      - 或方法**自己有**成对的 Begin / End（必须是**同一个批次对象**上的 Begin 与 End）；
      - 或这个方法的**调用点落在本文件某个方法自己的 Begin..End 区间里**，再沿"批次内方法"一层层
        往下传（批次内的方法自己不收批次，它调用的也还在同一批次里）—— 也就是说它确实是在一个
        已经开着的批次里画的。远端 2026-10 的粒子改动正是这种形状：`Draw()` 里
        `batch.Begin → try → finally → batch.End`，私有辅助方法 `DrawBolts / DrawKind /
        Particle.Draw / Particle.DrawGlow / ...` 都在批次里被调用。
        调用链按**方法实例**算（同名重载各算一份），并且认成员调用写法 `Particles[i].Draw()`。
      - 否则报错。
  * `PostDrawTiles` 特判：只要这个文件里有批次 Draw，就必须能沿**本文件的方法调用链**从
    PostDrawTiles 找到一段成对的 Begin / End（同一个批次对象），且 End 所在的方法里有 `finally`
    （异常时也不能留下"开着不关"的批次）。自己直接写、或者委托给 `Draw()` 这类开启者，都算通过。
  * 已知边界（写清楚免得下次踩）：
      - 别名只认直接赋值，不认函数返回值 / 属性 / 构造参数传进来的 SpriteBatch → 会**误报**（红）；
      - 调用链是**按方法名**在文件内解析的（同名重载不区分），且"调用点在 Begin..End 之间"是文本
        近似（同一个方法体里开多段批次时，按第一段 Begin 到最后一段 End 的区间判定）→ 理论上可能
        **误放**（绿）。当前代码里没有这种写法；真被误报时，把批次写进被调用的那个方法体里即可。
"""
import io
import os
import re
import sys

MOD = r"E:\开发\WastelandSoul"

# 框架调用这些钩子时，批次是开着的（弹幕 / 物品 / 图格绘制等）
PROVIDED_BATCH_HOOKS = (
    "PreDraw", "PostDraw", "Draw", "PreDrawTiles", "DrawTiles", "PostDrawTiles", "DrawPlayer",
)

DRAW = re.compile(r"\b(?:Main\.)?spriteBatch\.Draw\s*\(")
BEGIN = re.compile(r"\b(?:Main\.)?spriteBatch\.Begin\s*\(")
END = re.compile(r"\b(?:Main\.)?spriteBatch\.End\s*\(")

# 别名来源：`<name> = Main.spriteBatch`（局部变量或字段）。`(?!=)` 用来避开 `a == Main.spriteBatch`。
ALIAS = re.compile(r"(?<![\w.])(\w+)\s*=(?!=)\s*(?:Main\.)?spriteBatch\b")

# 方法体里出现的调用名。**故意允许前面有点号**，这样 `Particles[i].Draw()` 这种成员调用也算一条边
# （别名/局部变量的方法调用链断在这里，就会把批次内的私有辅助方法误判成"没开批次"）。
# 只用它跟本文件已有的方法名取交集，所以 `Main.rand.NextFloat(` 之类不会污染调用链。
CALL = re.compile(r"\b(\w+)\s*\(")


def strip_comments(text):
    """去掉 // 行注释与 /* */ 块注释 —— 不剥的话 `//spriteBatch.Begin(` 会被当成真的 Begin
    （第一次反向验证就是这么被骗过去的）。字符串字面量里的 // 极少见，这里不考虑。"""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def methods(text):
    """粗略切出「方法名 + 方法体」：靠大括号配对，够用且不会误伤。"""
    found = []
    header = re.compile(r"(?:public|private|protected|internal)[^;{}()]*\b(\w+)\s*\([^;{}]*\)\s*(?:where[^{]*)?\{")

    for match in header.finditer(text):
        name = match.group(1)
        start = match.end() - 1
        depth = 0
        index = start

        while index < len(text):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1

                if depth == 0:
                    break

            index += 1

        found.append((name, text[start:index + 1]))

    return found


def aliases_in(text):
    """`<name> = Main.spriteBatch` 收集出来的批次别名（变量名 / 字段名）。"""
    return set(match.group(1) for match in ALIAS.finditer(text))


def batch_targets(body, aliases, op):
    """body 里出现 `<批次对象>.<op>(` 的批次对象名集合（'spriteBatch' 或某个别名）。"""
    found = set()

    if re.search(r"(?<![\w.])(?:Main\.)?spriteBatch\s*\.\s*%s\s*\(" % op, body):
        found.add("spriteBatch")

    for alias in aliases:
        if re.search(r"(?<![\w.])%s\s*\.\s*%s\s*\(" % (re.escape(alias), op), body):
            found.add(alias)

    return found


def batch_positions(body, aliases, op):
    """body 里所有 `<批次对象>.<op>(` 的位置，用来判断调用点是否夹在 Begin..End 之间。"""
    positions = [match.start() for match in
                 re.finditer(r"(?<![\w.])(?:Main\.)?spriteBatch\s*\.\s*%s\s*\(" % op, body)]

    for alias in aliases:
        positions += [match.start() for match in
                      re.finditer(r"(?<![\w.])%s\s*\.\s*%s\s*\(" % (re.escape(alias), op), body)]

    return positions


def draws(body, aliases):
    return bool(batch_targets(body, aliases, "Draw"))


def paired_batch(body, aliases):
    """同一个批次对象上 Begin 与 End 都有，才算成对。"""
    return batch_targets(body, aliases, "Begin") & batch_targets(body, aliases, "End")


def calls_in(body, known):
    return set(match.group(1) for match in CALL.finditer(body)) & known


def called_inside_batch(caller_body, aliases, name):
    """`name` 是否在 caller_body 的 Begin..End 区间里被调用（文本近似）。"""
    begins = batch_positions(caller_body, aliases, "Begin")
    ends = batch_positions(caller_body, aliases, "End")

    if not begins or not ends:
        return False

    lower = min(begins)
    upper = max(ends)

    for match in re.finditer(r"\b%s\s*\(" % re.escape(name), caller_body):
        if lower < match.start() < upper:
            return True

    return False


def reachable(start_names, calls_of):
    """本文件内从 start_names 出发能调到的所有方法名。"""
    seen = set()
    stack = [name for name in start_names if name in calls_of]

    while stack:
        for callee in calls_of.get(stack.pop(), ()):
            if callee not in seen:
                seen.add(callee)
                stack.append(callee)

    return seen


def main():
    if not os.path.isdir(MOD):
        print("!! 找不到工程目录: %s" % MOD)
        return 1

    problems = []
    checked = 0

    for dirpath, dirs, files in os.walk(MOD):
        dirs[:] = [d for d in dirs if d not in ("obj", "bin", ".vs")]

        for name in files:
            if not name.endswith(".cs"):
                continue

            path = os.path.join(dirpath, name)
            text = strip_comments(io.open(path, encoding="utf-8-sig", errors="replace").read())
            relative = os.path.relpath(path, MOD)
            bodies = methods(text)
            aliases = aliases_in(text)

            file_draws = bool(DRAW.search(text))
            if not file_draws:
                for alias in aliases:
                    if re.search(r"(?<![\w.])%s\s*\.\s*Draw\s*\(" % re.escape(alias), text):
                        file_draws = True
                        break

            # 同名重载合并成一份，只给 PostDrawTiles 的跨方法调用链用。
            by_name = {}
            for method, body in bodies:
                by_name[method] = by_name.get(method, "") + body

            known = set(by_name)
            calls_of = dict((method, calls_in(body, known) - set([method]))
                            for method, body in by_name.items())

            # 方法实例级别的调用链（同名重载各算一份）。
            instances = list(bodies)
            openers = [index for index, (_, body) in enumerate(instances)
                       if paired_batch(body, aliases)]
            guarded_names = set(instances[index][0] for index in openers
                                if "finally" in instances[index][1])

            # 「在已开批次里画」的方法实例：
            #   1) 调用点落在某个开启者自己的 Begin..End 之间；
            #   2) 已经在批次里的方法实例，它调用的实例也还在同一批次里（一层层往下传）。
            batched = set()
            changed = True
            while changed:
                changed = False

                for opener in openers:
                    opener_body = instances[opener][1]

                    for index, (callee, _) in enumerate(instances):
                        if index == opener or index in batched:
                            continue

                        if called_inside_batch(opener_body, aliases, callee):
                            batched.add(index)
                            changed = True

                for index in list(batched):
                    for callee in calls_of.get(instances[index][0], ()):
                        for other, (name, _) in enumerate(instances):
                            if other in batched or other in openers:
                                continue

                            if name == callee:
                                batched.add(other)
                                changed = True

            # PostDrawTiles 特判：自己写，或沿本文件调用链找到成对的 Begin/End（End 在 finally 里）。
            for method, body in instances:
                if method != "PostDrawTiles" or not file_draws:
                    continue

                if paired_batch(body, aliases):
                    if "finally" not in body:
                        problems.append("%s: PostDrawTiles 的 End 没有放在 finally 里"
                                        "（绘制异常会留下开着不关的批次）" % relative)

                    continue

                if not (reachable(["PostDrawTiles"], calls_of) & guarded_names):
                    problems.append("%s: PostDrawTiles 必须自己 Begin/End（该文件里有 spriteBatch.Draw）"
                                    "—— 否则 Draw 会抛 InvalidOperationException 并导致 Main engine crash"
                                    % relative)

            for index, (method, body) in enumerate(instances):
                if not draws(body, aliases):
                    continue

                checked += 1

                if method == "PostDrawTiles":
                    continue

                begins = batch_targets(body, aliases, "Begin")
                ends = batch_targets(body, aliases, "End")

                if (begins or ends) and not (begins & ends):
                    problems.append("%s: %s 里 Begin/End 不成对" % (relative, method))

                if begins & ends:
                    continue

                if method in PROVIDED_BATCH_HOOKS:
                    continue

                if index in batched:
                    continue

                problems.append("%s: %s 里直接 Draw 但方法内没有 Begin —— 除非这是框架保证批次已开的钩子"
                                "（%s）" % (relative, method, ", ".join(PROVIDED_BATCH_HOOKS[:3])))

    if not checked:
        print("!! 一个 spriteBatch.Draw 都没扫到 —— 检查器路径写错了？")
        return 1

    if problems:
        print("!! 发现 %d 处 SpriteBatch 用法问题:" % len(problems))
        for item in problems:
            print("   -", item)
        print("CHECK FAILED")
        return 1

    print("[OK] 扫过 %d 处 spriteBatch.Draw：批次状态都有保证（PostDrawTiles 自己 Begin/End、"
          "钩子交给框架）" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
