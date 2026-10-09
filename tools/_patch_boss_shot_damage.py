# -*- coding: utf-8 -*-
"""一次性补丁：把四个 Boss 的所有弹幕生成点折半（见 Content/BossShotDamage.cs）。"""
import io
import sys

BOSS = r"E:\开发\WastelandSoul\Content\NPCs\Bosses"
PROJ = r"E:\开发\WastelandSoul\Content\Projectiles"

EDITS = [
    # ---- 清道夫 ----
    (BOSS + r"\Scavenger\Scavenger.cs",
     "ModContent.ProjectileType<ScavengerArmSweep>(), 44, 4f, Main.myPlayer",
     "ModContent.ProjectileType<ScavengerArmSweep>(), BossShotDamage.Half(44), 4f, Main.myPlayer"),
    (BOSS + r"\Scavenger\Scavenger.cs",
     "ModContent.ProjectileType<ScavengerBullet>(), 26, 2f, Main.myPlayer",
     "ModContent.ProjectileType<ScavengerBullet>(), BossShotDamage.Half(26), 2f, Main.myPlayer"),
    (BOSS + r"\Scavenger\Scavenger.cs",
     "ModContent.ProjectileType<PollutionHoming>(), 24, 1f, Main.myPlayer",
     "ModContent.ProjectileType<PollutionHoming>(), BossShotDamage.Half(24), 1f, Main.myPlayer"),
    # ---- 归档者 ----
    (BOSS + r"\Archivist\Archivist.cs",
     "\t\t\t\tModContent.ProjectileType<ArchivistIndexBeam>(),\n\t\t\t\tBeamDamage,",
     "\t\t\t\tModContent.ProjectileType<ArchivistIndexBeam>(),\n\t\t\t\tBossShotDamage.Half(BeamDamage),"),
    (BOSS + r"\Archivist\Archivist.cs",
     "\t\t\t\t\tModContent.ProjectileType<ArchivistArchivePage>(),\n\t\t\t\t\tPageDamage,",
     "\t\t\t\t\tModContent.ProjectileType<ArchivistArchivePage>(),\n\t\t\t\t\tBossShotDamage.Half(PageDamage),"),
    (BOSS + r"\Archivist\Archivist.cs",
     "\t\t\t\t\tModContent.ProjectileType<ArchivistBarrageSheet>(),\n\t\t\t\t\tdamage,",
     "\t\t\t\t\tModContent.ProjectileType<ArchivistBarrageSheet>(),\n\t\t\t\t\tBossShotDamage.Half(damage),"),
    (BOSS + r"\Archivist\Archivist.cs",
     "\t\t\t\tModContent.ProjectileType<ArchivistSeal>(),\n\t\t\t\t0,",
     "\t\t\t\tModContent.ProjectileType<ArchivistSeal>(),\n\t\t\t\tBossShotDamage.Half(0),"),
    (BOSS + r"\Archivist\Archivist.cs",
     "\t\t\t\tModContent.ProjectileType<ArchivistBarrageSheet>(),\n\t\t\t\tSuppressionDamage,",
     "\t\t\t\tModContent.ProjectileType<ArchivistBarrageSheet>(),\n\t\t\t\tBossShotDamage.Half(SuppressionDamage),"),
    # ---- 灰烬之心 ----
    (BOSS + r"\AshHeart\AshHeart.cs",
     "\t\t\t\t\tModContent.ProjectileType<AshEmberOrb>(),\n\t\t\t\t\tOrbDamage,",
     "\t\t\t\t\tModContent.ProjectileType<AshEmberOrb>(),\n\t\t\t\t\tBossShotDamage.Half(OrbDamage),"),
    (BOSS + r"\AshHeart\AshHeart.cs",
     "\t\t\t\tModContent.ProjectileType<AshPool>(),\n\t\t\t\tPoolDamage,",
     "\t\t\t\tModContent.ProjectileType<AshPool>(),\n\t\t\t\tBossShotDamage.Half(PoolDamage),"),
    (BOSS + r"\AshHeart\AshHeart.cs",
     "\t\t\t\t\tModContent.ProjectileType<AshCinder>(),\n\t\t\t\t\tRainDamage,",
     "\t\t\t\t\tModContent.ProjectileType<AshCinder>(),\n\t\t\t\t\tBossShotDamage.Half(RainDamage),"),
    (BOSS + r"\AshHeart\AshHeart.cs",
     "\t\t\t\tModContent.ProjectileType<AshPulse>(),\n\t\t\t\tPulseDamage,",
     "\t\t\t\tModContent.ProjectileType<AshPulse>(),\n\t\t\t\tBossShotDamage.Half(PulseDamage),"),
    # ---- 壁炉守卫 ----
    (BOSS + r"\FireplaceGuardian\FireplaceGuardian.cs",
     "\t\t\t\t\tModContent.ProjectileType<HearthBolt>(),\n\t\t\t\t\tBoltDamage,",
     "\t\t\t\t\tModContent.ProjectileType<HearthBolt>(),\n\t\t\t\t\tBossShotDamage.Half(BoltDamage),"),
    (BOSS + r"\FireplaceGuardian\FireplaceGuardian.cs",
     "\t\t\t\t\tModContent.ProjectileType<HearthRingShard>(),\n\t\t\t\t\tRingDamage,",
     "\t\t\t\t\tModContent.ProjectileType<HearthRingShard>(),\n\t\t\t\t\tBossShotDamage.Half(RingDamage),"),
    (BOSS + r"\FireplaceGuardian\FireplaceGuardian.cs",
     "\t\t\t\t\tModContent.ProjectileType<HearthWall>(),\n\t\t\t\t\tWallDamage,",
     "\t\t\t\t\tModContent.ProjectileType<HearthWall>(),\n\t\t\t\t\tBossShotDamage.Half(WallDamage),",
     2),
    # ---- 两个"手动结算"的弹幕：把折半的那一份补回来 ----
    (PROJ + r"\Archivist\ArchivistIndexBeam.cs",
     "player.Hurt(reason, Projectile.damage, angle.ToRotationVector2().X >= 0f ? 1 : -1);",
     "// 手动结算不走原版的\"敌对弹幕加倍\"通道 → 用 ManualHit 把生成处折半的那一份乘回来\n\t\t\t\t\tplayer.Hurt(reason, BossShotDamage.ManualHit(Projectile.damage),\n\t\t\t\t\t\tangle.ToRotationVector2().X >= 0f ? 1 : -1);"),
    (PROJ + r"\AshHeartBoss\AshHeartBossProjectiles.cs",
     "player.Hurt(reason, Projectile.damage, direction);",
     "// 手动结算不走原版的\"敌对弹幕加倍\"通道 → 用 ManualHit 把生成处折半的那一份乘回来\n\t\t\t\t\tplayer.Hurt(reason, BossShotDamage.ManualHit(Projectile.damage), direction);"),
]

problems = []
for item in EDITS:
    path, old, new = item[0], item[1], item[2]
    expected = item[3] if len(item) > 3 else 1

    text = io.open(path, encoding="utf-8-sig").read()
    found = text.count(old)

    if found != expected:
        problems.append("%s: 期望 %d 处，实际 %d 处 -> %s" % (path, expected, found, old[:60]))
        continue

    text = text.replace(old, new)
    io.open(path, "w", encoding="utf-8-sig", newline="").write(text)
    print("OK %-34s x%d" % (path.split("\\")[-1], found))

if problems:
    print("\n!! 有 %d 处没按预期匹配：" % len(problems))
    for p in problems:
        print("   -", p)
    sys.exit(1)

print("\n全部 %d 条替换完成" % len(EDITS))
