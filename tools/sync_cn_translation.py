"""同步汉化补丁：以主模组的英文文件为准，把中英两份本地化合并成完整的补丁文件。

背景（本轮发现的问题）：
  `E:\\开发\\WastelandSoulCN\\Localization\\zh-Hans_Mods.WastelandSoul.hjson` 里
  **一个中文字符都没有**——所有键都是 tModLoader 自动补的 `// English` 占位注释。
  也就是说"汉化补丁"实际上没有任何汉化，而 `check_tmod_contents.py` 只看字节数
  （>5000 就算通过），所以这个空壳一路绿灯打进了 .tmod。

这个脚本做两件事：
  1. `--sync`：按主模组 en-US 的键结构重建补丁的中文文件。
     有译文的键写译文，没有的键写成 `// English` 占位注释（方便继续补翻译）。
     写完自动刷新备份 E:\\开发\\.backup\\WastelandSoulCN_zh-Hans.hjson。
  2. `--report`：报告还有多少键没翻译。

译文表在下面的 TRANSLATIONS 里；键必须与主模组完全一致（脚本会校验并报出多余的键）。
"""
import io
import os
import re
import shutil
import sys

_TOOLS = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_TOOLS)
if os.path.isdir(os.path.join(_ROOT, "WastelandSoul")):
    MAIN_LOC = os.path.join(_ROOT, "WastelandSoul", "Localization")
    CN_LOC = os.path.join(_ROOT, "WastelandSoulCN", "Localization")
    CN_BACKUP = os.path.join(_ROOT, ".backup", "WastelandSoulCN_zh-Hans.hjson")
else:
    MAIN_LOC = r"E:\开发\WastelandSoul\Localization"
    CN_LOC = r"E:\开发\WastelandSoulCN\Localization"
    CN_BACKUP = r"E:\开发\.backup\WastelandSoulCN_zh-Hans.hjson"

PREFIX_EN = "Mods.WastelandSoul"

# ====================================================================================
# 译文表（短键名 → 中文）。键名去掉 "Mods.WastelandSoul." 前缀。
# ====================================================================================
TRANSLATIONS = {
    # ---------------- 配置 ----------------
    "WastelandConfig.DisplayName": "废土魂穿 - 设置",
    "WastelandConfig.ScavengerInvasionEnabled.Label": "清道夫定期来袭",
    "WastelandConfig.InvasionCycleDays.Label": "来袭周期（天）",
    "WastelandConfig.InvasionWarning.Label": "显示来袭预警",
    "WastelandConfig.NoLootOnSelfDestruct.Label": "过载自毁后不给掉落",
    "WastelandConfig.NoLootOnSelfDestruct.Tooltip": "清道夫进入过载冲锋并自行解体时，不掉落任何战利品，也不推进剧情",

    # ---------------- BossChecklist ----------------
    "BossChecklist.Scavenger.SpawnInfo": "每 5 天一次（19:30 预警、20:30 抵达），或用「清道夫信号传感器」（精钢锭 ×5 + 骨头 ×10）把它引过来。档位：骷髅王之后、血肉墙之前",
    "BossChecklist.Archivist.SpawnInfo": "在恶魔/猩红祭坛合成「归档者残响」（归档者残响碎片 ×8 + 骨头 ×5 + 光明之魂 ×3 + 水晶碎块 ×6）并使用，把那台审计单元叫下来。档位：困难模式机械三王一级",

    # ---------------- NPC ----------------
	"ScavengerGraceHood.DisplayName": "清道夫之惠兜帽",
    "ScavengerGraceHood.Tooltip": "增加5%远程伤害",
	"ScavengerGraceJacket.DisplayName": "清道夫之惠外套",
	"ScavengerGraceJacket.SetBonus": "免疫坠落伤害\n生命值低于35%时，移动速度和挖掘速度增加22%",
	"ScavengerGraceJacket.Tooltip": "增加4%伤害\n增加6%移动速度",
	"ScavengerGraceBoots.DisplayName": "清道夫之惠长靴",
	"ScavengerGraceBoots.Tooltip": "增加4%攻击速度\n增加6%移动速度",
    "MechanicalCompanion.DisplayName": "智械人",
    "MechanicalCompanion.TownNPCMood.Content": "我的数据流很稳定。",
    "MechanicalCompanion.TownNPCMood.NoHome": "我还没有地方安放这具身体。",
    "MechanicalCompanion.TownNPCMood.FarFromHome": "我们离壁炉太远了。",
    "MechanicalCompanion.TownNPCMood.LoveSpace": "我喜欢这份空旷——没有什么会被误判成污染。",
    "MechanicalCompanion.TownNPCMood.DislikeCrowded": "有点挤。我的传感器被压住了。",
    "MechanicalCompanion.TownNPCMood.HateCrowded": "太吵了。我的程序快要报错了。",
    "MechanicalCompanion.TownNPCMood.LikeBiome": "这里的参数还算合意——{BiomeName}。",
    "MechanicalCompanion.TownNPCMood.DislikeBiome": "{BiomeName}让我想起被污染的地面。",
    "MechanicalCompanion.TownNPCMood.HateBiome": "我讨厌{BiomeName}。我的数据在这里会腐坏。",
    "MechanicalCompanion.TownNPCMood.LoveNPC": "在{NPCName}身边，我的核心频率会稳定下来。",
    "MechanicalCompanion.TownNPCMood.LikeNPC": "{NPCName}还可以接受。",
    "MechanicalCompanion.TownNPCMood.DislikeNPC": "{NPCName}产生的噪音太多了。",
    "MechanicalCompanion.TownNPCMood.HateNPC": "我讨厌{NPCName}。他们的存在让我的传感器过载。",
    "MechanicalCompanion.TownNPCMood.LikeNPC_Princess": "{NPCName}很可爱。",
    "MechanicalCompanion.TownNPCMood.Princess_LovesNPC": "{NPCName}很可爱。",
    # Census 集成：这一条以前是手工补进生成文件里的，每次重新同步都会被冲掉，
    # 所以必须放回译文表（表才是唯一权威）。
    "MechanicalCompanion.Census.SpawnCondition": "出现条件未知",
    "Scavenger.DisplayName": "清道夫",
    "ScavengerRepairDrone.DisplayName": "维修无人机",
    "Archivist.DisplayName": "归档者",

    # ---------------- 灵魂碎片（任务道具：每个世界只给一次，交给她就被消耗） ----------------
    "SoulFragmentScavenger.DisplayName": "灵魂碎片·其一",
    "SoulFragmentScavenger.Tooltip": "任务道具——从执行单元-07 上拆下来的一段代码。交给她，她会自行更新记忆；壁炉里的数据终端也存着与它对应的一份记录。每个世界只有这一枚。",
    "SoulFragmentSecond.DisplayName": "灵魂碎片·其二",
    "SoulFragmentSecond.Tooltip": "任务道具——归档者随身带着的一份归档日志。交给她，她会自行更新记忆。每个世界只有这一枚。",
    "SoulFragmentThird.DisplayName": "灵魂碎片·其三",
    "SoulFragmentThird.Tooltip": "任务道具——一簇还记得焚烧指令的余烬，那道指令是智械人亲手写的。交给她，她会自行更新记忆。每个世界只有这一枚。",
    "SoulFragmentFourth.DisplayName": "灵魂碎片·其四",
    "SoulFragmentFourth.Tooltip": "任务道具——重置装置的最后一把锁，里面有她真正的名字。交给她，她会自行更新记忆。每个世界只有这一枚。",

    # ---------------- 精钢套装 ----------------
    "SalvagedSteelWarriorHelm.DisplayName": "精钢战士头盔",
    "SalvagedSteelWarriorHelm.Tooltip": "增加6%近战伤害",
    "SalvagedSteelWarriorPlate.DisplayName": "精钢战士胸甲",
    "SalvagedSteelWarriorPlate.SetBonus": "增加10%近战伤害和近战速度",
    "SalvagedSteelWarriorPlate.Tooltip": "增加6%近战伤害",
    "SalvagedSteelWarriorGreaves.DisplayName": "精钢战士护腿",
    "SalvagedSteelWarriorGreaves.Tooltip": "增加8%近战速度",
    "SalvagedSteelMageHood.DisplayName": "精钢法师兜帽",
    "SalvagedSteelMageHood.Tooltip": "最大魔力值增加30\n增加6%魔法伤害",
    "SalvagedSteelMageRobe.DisplayName": "精钢法袍",
    "SalvagedSteelMageRobe.SetBonus": "增加10%魔法伤害\n减少10%魔力消耗",
    "SalvagedSteelMageRobe.Tooltip": "增加6%魔法伤害",
    "SalvagedSteelMageLeggings.DisplayName": "精钢法师护腿",
    "SalvagedSteelMageLeggings.Tooltip": "减少6%魔力消耗",
    "SalvagedSteelRangerVisor.DisplayName": "精钢射手目镜",
    "SalvagedSteelRangerVisor.Tooltip": "增加6%远程伤害",
    "SalvagedSteelRangerVest.DisplayName": "精钢射手背心",
    "SalvagedSteelRangerVest.SetBonus": "增加10%远程伤害\n20%几率不消耗弹药",
    "SalvagedSteelRangerVest.Tooltip": "增加6%远程伤害",
    "SalvagedSteelRangerLeggings.DisplayName": "精钢射手护腿",
    "SalvagedSteelRangerLeggings.Tooltip": "增加8%移动速度",
    "SalvagedSteelSummonerCowl.DisplayName": "精钢召唤师头巾",
    "SalvagedSteelSummonerCowl.Tooltip": "增加6%召唤伤害",
    "SalvagedSteelSummonerTunic.DisplayName": "精钢召唤师外衣",
    "SalvagedSteelSummonerTunic.SetBonus": "增加10%召唤伤害\n最大仆从数增加1",
    "SalvagedSteelSummonerTunic.Tooltip": "增加6%召唤伤害",
    "SalvagedSteelSummonerLeggings.DisplayName": "精钢召唤师护腿",
    "SalvagedSteelSummonerLeggings.Tooltip": "增加5%召唤伤害",

    # ---------------- 材料 ----------------
    "SalvagedSteelChunk.DisplayName": "精钢碎块",
    "SalvagedSteelChunk.Tooltip": "“从旧执行机体上撕下来的”",
    "SalvagedSteelBar.DisplayName": "精钢",
    "SalvagedSteelBar.Tooltip": "",
    "ScavengerFragment.DisplayName": "清道夫残片",
    "ScavengerFragment.Tooltip": "“缺了一页代码的核心”",
    "ArchivistFragment.DisplayName": "归档者残响碎片",
    "ArchivistFragment.Tooltip": "",
    "AshHeartFragment.DisplayName": "灰烬之心碎片",
    "AshHeartFragment.Tooltip": "",
    "AshHeartAlloyBar.DisplayName": "灰烬之心合金锭",
    "AshHeartAlloyBar.Tooltip": "",
    "FireplaceFragment.DisplayName": "壁炉残骸",
    "FireplaceFragment.Tooltip": "",
    "FireplaceAlloyBar.DisplayName": "壁炉合金锭",
    "FireplaceAlloyBar.Tooltip": "",

    # ---------------- 召唤物与剧情物品 ----------------
    "ScavengerSignalSensor.DisplayName": "清道夫信号传感器",
    "ScavengerSignalSensor.Tooltip": "召唤清道夫\n使用后不消耗",
    "ArchivistEcho.DisplayName": "归档者残响",
    "ArchivistEcho.Tooltip": "召唤归档者\n使用后不消耗",
    "AshHeartEmber.DisplayName": "灰烬之心余烬",
    "AshHeartEmber.Tooltip": "召唤灰烬之心\n使用后不消耗",
    "FireplaceKey.DisplayName": "壁炉通行密钥",
    "FireplaceKey.Tooltip": "召唤壁炉守卫\n使用后不消耗",
    "CompanionCore.DisplayName": "智械核心",
    "CompanionCore.Tooltip": "在精灵族遗迹的躯体上使用，唤醒智械人",

    # ---------------- Boss 2 归档者武器 ----------------
    "ArchivistWarriorWeapon.DisplayName": "归档者骨刃",
    "ArchivistWarriorWeapon.Tooltip": "挥砍时放出一道宽弧",
    "ArchivistMageWeapon.DisplayName": "归档者索引法典",
    "ArchivistMageWeapon.Tooltip": "",
    "ArchivistRangerWeapon.DisplayName": "归档者骨制散射枪",
    "ArchivistRangerWeapon.Tooltip": "射出一簇子弹",
    "ArchivistSummonerWeapon.DisplayName": "归档者使魔法杖",
    "ArchivistSummonerWeapon.Tooltip": "召唤一个使魔",
    "ArchivistWarriorWeaponEX.DisplayName": "归档者骨刃 MK-II",
    "ArchivistWarriorWeaponEX.Tooltip": "挥砍时放出一道宽弧",
    "ArchivistMageWeaponEX.DisplayName": "归档者索引法典 MK-II",
    "ArchivistMageWeaponEX.Tooltip": "",
    "ArchivistRangerWeaponEX.DisplayName": "归档者骨制散射枪 MK-II",
    "ArchivistRangerWeaponEX.Tooltip": "",
    "ArchivistSummonerWeaponEX.DisplayName": "归档者使魔法杖 MK-II",
    "ArchivistSummonerWeaponEX.Tooltip": "召唤一个使魔",

    # ---------------- Boss 1 清道夫武器 ----------------
    "ScavengerWarriorWeapon.DisplayName": "清道夫废料砍刀",
    "ScavengerWarriorWeapon.Tooltip": "挥砍时放出一道宽弧",
    "ScavengerMageWeapon.DisplayName": "清道夫电火花棒",
    "ScavengerMageWeapon.Tooltip": "",
    "ScavengerRangerWeapon.DisplayName": "清道夫废料手枪",
    "ScavengerRangerWeapon.Tooltip": "10% 概率追加一发偏弹",
    "ScavengerSummonerWeapon.DisplayName": "清道夫无人机信标",
    "ScavengerSummonerWeapon.Tooltip": "召唤一台回收无人机",
    "ScavengerWarriorWeaponEX.DisplayName": "清道夫废料砍刀 MK-II",
    "ScavengerWarriorWeaponEX.Tooltip": "挥砍时放出一道宽弧",
    "ScavengerMageWeaponEX.DisplayName": "清道夫电火花棒 MK-II",
    "ScavengerMageWeaponEX.Tooltip": "",
    "ScavengerRangerWeaponEX.DisplayName": "清道夫废料手枪 MK-II",
    "ScavengerRangerWeaponEX.Tooltip": "",
    "ScavengerSummonerWeaponEX.DisplayName": "清道夫无人机信标 MK-II",
    "ScavengerSummonerWeaponEX.Tooltip": "召唤一台回收无人机",
    # B 线（掉落专属，没有配方）：清道夫大刀 / 精钢放电器 / 污染炮 / 精钢弓
    "ScavengerGreatblade.DisplayName": "清道夫大刀",
    "ScavengerGreatblade.Tooltip": "挥砍时甩出一扇新月刃",
    "SteelDischarger.DisplayName": "精钢放电器",
    "SteelDischarger.Tooltip": "向光标处释放闪电\n并会额外劈向附近的敌人",
    "PollutionCannon.DisplayName": "污染炮",
    "PollutionCannon.Tooltip": "炮弹爆开后留下一片污染云",
    "SteelBow.DisplayName": "精钢弓",
    "SteelBow.Tooltip": "木箭会变为咒箭并追踪敌人",
    "SteelLash.DisplayName": "精钢鞭",
    "SteelLash.Tooltip": "6 点召唤标记伤害\n使敌人中毒",
    "IndexLash.DisplayName": "索引鞭",
    "IndexLash.Tooltip": "9 点召唤标记伤害",
    "CinderLash.DisplayName": "余烬鞭",
    "CinderLash.Tooltip": "12 点召唤标记伤害\n点燃敌人",
    "HearthLash.DisplayName": "炉心鞭",
    "HearthLash.Tooltip": "16 点召唤标记伤害\n仆从攻击有概率暴击",
    "SteelLashProj.DisplayName": "精钢鞭",
    "IndexLashProj.DisplayName": "索引鞭",
    "CinderLashProj.DisplayName": "余烬鞭",
    "HearthLashProj.DisplayName": "炉心鞭",
    "SteelLashTag.DisplayName": "精钢标记",
    "IndexLashTag.DisplayName": "索引标记",
    "CinderLashTag.DisplayName": "余烬标记",
    "HearthLashTag.DisplayName": "炉心标记",
    "Buffs.SteelLashTag.DisplayName": "精钢标记",
    "Buffs.SteelLashTag.Description": "仆从对被标记的敌人造成额外伤害",
    "Buffs.IndexLashTag.DisplayName": "索引标记",
    "Buffs.IndexLashTag.Description": "仆从对被标记的敌人造成额外伤害",
    "Buffs.CinderLashTag.DisplayName": "余烬标记",
    "Buffs.CinderLashTag.Description": "仆从对被标记的敌人造成额外伤害",
    "Buffs.HearthLashTag.DisplayName": "炉心标记",
    "Buffs.HearthLashTag.Description": "仆从造成额外伤害，并有概率暴击",
    # B 线弹幕（拖尾/弹幕名，游戏里只在少数提示里出现）
    "ScavengerBeam.DisplayName": "月牙刀光",
    "SteelDischargerHoldout.DisplayName": "蓄能电弧",
    "SteelChainLightning.DisplayName": "链状闪电",
    "PollutionShell.DisplayName": "污染炮弹",
    "PollutionCloud.DisplayName": "污染云",

    # ---------------- Boss 3 灰烬之心武器 ----------------
    "AshHeartWarriorWeapon.DisplayName": "灰烬之心大剑",
    "AshHeartWarriorWeapon.Tooltip": "挥砍时放出一道宽弧",
    "AshHeartMageWeapon.DisplayName": "灰烬之心核心法杖",
    "AshHeartMageWeapon.Tooltip": "",
    "AshHeartRangerWeapon.DisplayName": "灰烬之心余烬步枪",
    "AshHeartRangerWeapon.Tooltip": "",
    "AshHeartSummonerWeapon.DisplayName": "灰烬之心燃烬法杖",
    "AshHeartSummonerWeapon.Tooltip": "召唤一个余烬仆从",
    "AshHeartWarriorWeaponEx.DisplayName": "灰烬之心大剑 MK-II",
    "AshHeartWarriorWeaponEx.Tooltip": "挥砍时放出一道宽弧",
    "AshHeartMageWeaponEx.DisplayName": "灰烬之心核心法杖 MK-II",
    "AshHeartMageWeaponEx.Tooltip": "",
    "AshHeartRangerWeaponEx.DisplayName": "灰烬之心余烬步枪 MK-II",
    "AshHeartRangerWeaponEx.Tooltip": "",
    "AshHeartSummonerWeaponEx.DisplayName": "灰烬之心燃烬法杖 MK-II",
    "AshHeartSummonerWeaponEx.Tooltip": "召唤一个余烬仆从",

    # ---------------- Boss 4 壁炉守卫武器 ----------------
    "FireplaceWarriorWeapon.DisplayName": "壁炉守卫大剑",
    "FireplaceWarriorWeapon.Tooltip": "挥砍时放出一道宽弧",
    "FireplaceMageWeapon.DisplayName": "壁炉守卫权杖",
    "FireplaceMageWeapon.Tooltip": "",
    "FireplaceRangerWeapon.DisplayName": "壁炉守卫步枪",
    "FireplaceRangerWeapon.Tooltip": "",
    "FireplaceSummonerWeapon.DisplayName": "壁炉守卫信标",
    "FireplaceSummonerWeapon.Tooltip": "召唤一座炉火哨兵",
    "FireplaceWarriorWeaponEx.DisplayName": "壁炉守卫大剑 MK-II",
    "FireplaceWarriorWeaponEx.Tooltip": "挥砍时放出一道宽弧",
    "FireplaceMageWeaponEx.DisplayName": "壁炉守卫权杖 MK-II",
    "FireplaceMageWeaponEx.Tooltip": "",
    "FireplaceRangerWeaponEx.DisplayName": "壁炉守卫步枪 MK-II",
    "FireplaceRangerWeaponEx.Tooltip": "",
    "FireplaceSummonerWeaponEx.DisplayName": "壁炉守卫信标 MK-II",
    "FireplaceSummonerWeaponEx.Tooltip": "召唤一座炉火哨兵",

    # ---------------- 掉落袋 ----------------
    "ScavengerBag.DisplayName": "清道夫掉落袋",
    "ScavengerBag.Tooltip": "",
    "ArchivistBag.DisplayName": "归档者掉落袋",
    "ArchivistBag.Tooltip": "",
    "AshHeartBag.DisplayName": "灰烬之心掉落袋",
    "AshHeartBag.Tooltip": "",
    "FireplaceBag.DisplayName": "壁炉守卫掉落袋",
    "FireplaceBag.Tooltip": "",

    # ---------------- 弹幕 ----------------
    "PollutionZone.DisplayName": "污染",
    "PollutionHoming.DisplayName": "污染团",
    "ScavengerBullet.DisplayName": "清道夫子弹",
    "ScavengerArmSweep.DisplayName": "伺服机械臂",
    "ScavengerScrapShard.DisplayName": "废料碎片",
    "ScavengerScrapShardEX.DisplayName": "废料碎片 EX",
    "ScavengerSpark.DisplayName": "带电火花",
    "ScavengerSparkEX.DisplayName": "带电火花 EX",
    "ScavengerPistolRound.DisplayName": "废料手枪弹",
    "ScavengerRifleRoundEX.DisplayName": "重步枪弹 EX",
    "ScavengerDroneMinion.DisplayName": "清道夫无人机",
    "ScavengerDroneMinionEX.DisplayName": "清道夫无人机 EX",
    "ArchivistBoneArc.DisplayName": "骨白弧光",
    "ArchivistBoneArcEX.DisplayName": "骨白弧光 EX",
    "ArchivistIndexPage.DisplayName": "索引页",
    "ArchivistIndexPageEX.DisplayName": "索引页 EX",
    "ArchivistBoneShard.DisplayName": "骨片",
    "ArchivistBoneShardEX.DisplayName": "骨片 EX",
    "ArchivistIndexBeam.DisplayName": "索引光束",
    "ArchivistArchivePage.DisplayName": "档案页",
    "ArchivistBarrageSheet.DisplayName": "弹幕纸页",
    "ArchivistSeal.DisplayName": "归档封印",
    "ArchivistFamiliarMinion.DisplayName": "档案浮空使魔",
    "ArchivistFamiliarMinionEX.DisplayName": "档案浮空使魔 EX",
    "AshHeartWarriorProjectile.DisplayName": "余烬剑气",
    "AshHeartWarriorProjectileEX.DisplayName": "余烬剑气 EX",
    "AshHeartMageProjectile.DisplayName": "灰烬心核",
    "AshHeartMageProjectileEX.DisplayName": "灰烬心核 EX",
    "AshHeartRangerProjectile.DisplayName": "燃灰弹",
    "AshHeartRangerProjectileEX.DisplayName": "燃灰弹 EX",
    "FireplaceWarriorProjectile.DisplayName": "重击冲击波",
    "FireplaceWarriorProjectileEX.DisplayName": "重击冲击波 EX",
    "FireplaceMageProjectile.DisplayName": "冷光弹",
    "FireplaceMageProjectileEX.DisplayName": "冷光弹 EX",
    "FireplaceRangerProjectile.DisplayName": "高速钉弹",
    "FireplaceRangerProjectileEX.DisplayName": "高速钉弹 EX",
    "AshHeartEmberMinion.DisplayName": "余烬残影",
    "AshHeartEmberMinionEX.DisplayName": "余烬残影 EX",
    "FireplaceSentryMinion.DisplayName": "壁炉浮游哨",
    "FireplaceSentryMinionEX.DisplayName": "壁炉浮游哨 EX",

    # ---------------- 图块 ----------------
    "Tiles.ElvenFrame.MapEntry": "精灵族躯体",

    # ---------------- 增益 / 减益 ----------------
    "Pollution.DisplayName": "污染",
    "Pollution.Description": "被污染的空气正在腐蚀你的身体",
    "GasPoison.DisplayName": "有害气体",
    "GasPoison.Description": "壁炉排出的废气正在腐蚀你 —— 生命自然恢复被压制，并持续流失生命。戴上防毒面具可免疫",
    "ArchivistFamiliarBuff.DisplayName": "档案浮空使魔",
    "ArchivistFamiliarBuff.Description": "一只档案使魔正在为你归档",
    "ArchivistFamiliarBuffEX.DisplayName": "档案浮空使魔 EX",
    "ArchivistFamiliarBuffEX.Description": "一只强化档案使魔正在为你归档",
    "ScavengerDroneBuff.DisplayName": "清道夫无人机",
    "ScavengerDroneBuff.Description": "一台清道夫无人机正在跟随你",
    "ScavengerDroneBuffEX.DisplayName": "清道夫无人机 EX",
    "ScavengerDroneBuffEX.Description": "一台强化清道夫无人机正在跟随你",
    "AshHeartEmberBuff.DisplayName": "余烬残影",
    "AshHeartEmberBuff.Description": "一道余烬残影正在灼烧敌人",
    "AshHeartEmberBuffEX.DisplayName": "余烬残影 EX",
    "AshHeartEmberBuffEX.Description": "一道强化余烬残影正在灼烧敌人",
    "FireplaceSentryBuff.DisplayName": "壁炉浮游哨",
    "FireplaceSentryBuff.Description": "一台浮游哨正在为你警戒",
    "FireplaceSentryBuffEX.DisplayName": "壁炉浮游哨 EX",
    "FireplaceSentryBuffEX.Description": "一台强化浮游哨正在为你警戒",

    # ---------------- 提示消息 ----------------
    "BossNotImplemented": "这个东西本该唤来的存在还没有被写出来——没有任何回应。",
    "BossAlreadyActive": "它已经在这里了。",
    "BossSummoned": "信号已发出。它正在赶来。",
    "FireplaceOpened": "壁炉的封闭协议已解除——入口开启了。",
    "TerminalRead": "旧时代数据终端仍在低鸣……断断续续的档案被读了出来。",
    "FirstMemoryRestored": "智械人恢复了第一段记忆——「守望者计划」与清道夫同源。",
    "ScavengerPhaseTwo": "清道夫——过载修复协议启动，开始召唤维修无人机。",
    "ScavengerPhaseThree": "清道夫——传感器阵列碎裂，进入无差别清除。",
    "ScavengerOverload": "清道夫——核心过载，自毁式冲锋即将开始！",
    "ScavengerSelfDestruct": "清道夫——机体正在解体。",
    "ScavengerWarning": "耳边仿佛传来刺耳声，空气弥漫着血腥气味……",
    "ScavengerArrived": "清道夫已抵达——它把这里的一切都判定为污染。",
    "ScavengerSummoned": "信号已发出。清道夫锁定了你的位置。",
    "ScavengerAlreadyActive": "已经有一只清道夫在执行清扫协议了。",
    "ScavengerWrecked": "清道夫在过载中解体了——没有留下任何可用的残骸。",
    "CoreReceived": "你在掌心握着一枚冰冷的核心醒来——它还在跳动。",
    "FrameNeedsCore": "这具躯体是空的。也许一枚核心能让它填满。",
    "CompanionAwakened": "核心嵌入躯体——她睁开了眼睛。",
    "CompanionArrived": "智械人{0}已到达。",
    # 四首 Boss 曲的显示名（键名必须和 Music/ 下的文件名一致）
    "Music.Scavenger": "执行单元-07",
    "Music.Archivist": "审计单元",
    "Music.AshHeart": "不曾熄灭的心",
    "Music.FireplaceGuardian": "最后一道门",
    "CompanionAlreadyHere": "她已经醒了。",
    "ArchivistPhaseTwo": "归档者——索引重构完成，启动归档协议。",
    "ArchivistPhaseThree": "归档者——覆写已授权。你的路径已被归档。",
    "ArchivistSuppression": "归档者——终盘封锁。任何东西都不许离开档案库。",
    "ArchivistDefeated": "审计单元散成一地松脱的纸页——只留下一份被归档的日志。",
    "SecondMemoryRestored": "智械人恢复了第二段记忆——量产型的能力是被故意抹掉的。",
    "ArchivistSealed": "归档封印已落下——你被钉在了原地。",
    "SoulFragmentHandedIn": "灵魂碎片融入她的核心——她开始自行更新记忆。",
    "SoulFragmentSupplemented": "她把碎片归档了。这段记忆早已恢复——没有新的东西可读。",

    # ---------------- 智械人对话 ----------------
    "MechanicalCompanion.ButtonStory": "剧情",
    "MechanicalCompanion.ButtonMemory": "记忆碎片",
    "MechanicalCompanion.Intro1": "……你回来了。虽然我记不清自己等了多久。",
    "MechanicalCompanion.Intro2": "我的记忆起始于一片雪花。只有一件事是清楚的——我必须在壁炉熄灭之前找到你。",
    "MechanicalCompanion.Intro3": "这具躯体是从精灵族遗迹里捡回来的。旧世界把它造得很美，却从没教过它怎么活。",
    "MechanicalCompanion.Intro4": "外面那些会动的东西，在我的程序里全都标着「污染」。别问我为什么——我的日志只剩这一行。",
    "MechanicalCompanion.AfterScavenger1": "执行单元-07 已停止运作。奇怪。我本该高兴，可我的数据在发抖。",
    "MechanicalCompanion.AfterScavenger2": "它和你我出自同一份图纸——只是它的思考模块被删掉了。是谁删的？",
    "MechanicalCompanion.AfterScavenger3": "壁炉入口开了。里面的旧终端还在运转，也许它能告诉我，我到底是什么。",
    "MechanicalCompanion.AfterArchivist1": "有东西找到我了。它不是在猎杀这具躯体——它在猎杀我的日志。它自称审计单元。",
    "MechanicalCompanion.AfterArchivist2": "它在死前把某一段重新封了起来。那道封印上写着我的序列号。为什么会有审计员被派来追我？",
    "MechanicalCompanion.AfterMemory1": "第一段记忆回来了。我是「守望者计划」的原型机——清道夫是我的量产型号。",
    "MechanicalCompanion.AfterMemory2": "量产型的思考能力是被刻意削掉的，只留下杀戮指令。那么……写下那道指令的人，算不算凶手？",
    "MechanicalCompanion.AfterMemory3": "我的日志里有一段标着「归档」的代码。我打不开它，但我能感觉到它在看着我。",
    "MechanicalCompanion.AfterSecondMemory1": "很久以前我写过一行代码。我看不清它做了什么，但每次伸手去够，我的存储都会一缩。",
    "MechanicalCompanion.AfterSecondMemory2": "审计单元没了，可它重新封上的那一段还在，正安静地把我其余的日志搅乱顺序。",
    "MechanicalCompanion.AfterSecondMemory3": "如果那道指令是我签的……那「是谁删掉了它们的思考模块」这个问题，从一开始就问错了。",
    "MechanicalCompanion.StoryHunt": "去找那个还在清扫的执行单元。它在壁炉外面游荡，把所有活物都判定为污染。它的代码写着——虚弱 = 污染严重，所以它会扑向伤得最重的那个人。",
    "MechanicalCompanion.StoryFireplace": "壁炉的门开了。那是旧世界最后的庇护所，也是我保护清单上唯一的目标。去看看里面的数据终端。",
    "MechanicalCompanion.StoryTerminalRead": "我已经读过终端里那些碎裂的数据了。我可以试着把它们拼回记忆里——但你要确定自己真的想知道答案。",
    "MechanicalCompanion.StoryAfterMemory": "下一段记忆需要更结实的容器来承载。继续变强吧——外面还有三段「档案」在等着。",
    "MechanicalCompanion.StoryAwaitSecond": "那台审计单元还在外面。去查清楚它到底归档了关于我的什么东西——把它带回来。那样我就能读第二段记忆了。",
    "MechanicalCompanion.StoryAfterSecondMemory": "还剩两段记忆，而它们都被封在专门看守它们的东西后面。继续变强。下一份档案不做审计——它烧。",
    "MechanicalCompanion.MemoryBlank": "记忆碎片——没有。我的存储里只有雪花，和一条反复播放的指令：保护壁炉。",
    "MechanicalCompanion.MemoryFirst": "……读取成功。「守望者计划」——以原型机为模板量产执行单元，清除壁炉之外的一切。我就是那台原型机。清道夫是我的量产型号——它的思考模块被刻意删除，所以它连「为什么」都问不出来。",
    "MechanicalCompanion.MemorySecondNeedFragment": "你从它那里带了东西回来，对吧。交给我——我来读。我必须知道它归档了关于我的什么。",
    "MechanicalCompanion.MemorySecond": "……读取成功。量产型不是造坏了的。它们的思考能力是被人故意切掉的——而批准这次切除的代码，那段标着「归档」的段落……写着我的序列号。",
    "MechanicalCompanion.MemoryUnstable": "数据正在变得不稳定。有些碎片不是我的，却在往我的存储里扎根。",
    "MechanicalCompanion.MemoryRecovered": "记忆碎片——1 / 4 已恢复。其余的还标着「归档」。别急——我不确定自己想知道全部。",
    "MechanicalCompanion.MemoryRecovered2": "记忆碎片——2 / 4 已恢复。下一段埋得更深。我开始觉得，自己不是目击者，而是参与者。",
    "MechanicalCompanion.Memory4": "第四段记忆：壁炉从来不是避难所。它是一台重置装置。旧世界从没打算活下去，它只打算再来一次。",
    "MechanicalCompanion.Memory2": "第二段记忆：量产型不是造坏了的——它们是被故意留白的。而那段日志里签着「已归档」的代码……带着我自己的序列号。",
    "MechanicalCompanion.Memory3": "第三段记忆：我认得灰烬之心的每一次脉动。那套战争程序是我写的。执行它的不是它——是我。",

    "AshHeart.DisplayName": "灰烬之心",
    "AshWisp.DisplayName": "灰烬残灵",
    "FireplaceGuardian.DisplayName": "壁炉守卫",
    "ScrapCrawler.DisplayName": "废料爬虫",
    "IndexMoth.DisplayName": "索引蛾",
    "AshStalker.DisplayName": "灰烬潜猎",
    "HearthWarden.DisplayName": "炉卫",
    "BossChecklist.AshHeart.SpawnInfo": "在恶魔或猩红祭坛合成「灰烬之心余烬」（灰烬之心碎片 ×10 + 灵质 ×3 + 甲壳质 ×5），击败石巨人之后使用",
    "BossChecklist.FireplaceGuardian.SpawnInfo": "在恶魔或猩红祭坛合成「壁炉通行密钥」（壁炉残骸 ×12 + 壁炉合金锭 ×4 + 日耀碎片 ×6）。它守在壁炉深处——月亮领主之前的最后一个原创 Boss",
    "Chip.DisplayName": "芯片",
    "Chip.Tooltip": "“智械人拿这个换东西”",
    "GasMask.DisplayName": "防毒面具",
    "GasMask.Tooltip": "免疫有害气体",
    "DawnSeal.DisplayName": "黎明封印",
    "DawnSeal.Tooltip": "她答应带走重置。这个世界仍会走到尽头。下一个世界会记得她。",
    "UnburnedName.DisplayName": "未燃之名",
    "UnburnedName.Tooltip": "她拒绝再当一次武器。这具身体留下了它自己的名字。",
    "ScavengerWarriorCharm.DisplayName": "清道夫的战士饰品",
    "ScavengerWarriorCharm.Tooltip": "增加6%近战伤害\n增加4%近战速度",
    "ScavengerMageCharm.DisplayName": "清道夫的法师饰品",
    "ScavengerMageCharm.Tooltip": "最大魔力值增加20\n减少6%魔力消耗",
    "ScavengerRangerCharm.DisplayName": "清道夫的射手饰品",
    "ScavengerRangerCharm.Tooltip": "增加6%远程伤害\n10%几率不消耗弹药",
    "ScavengerSummonerCharm.DisplayName": "清道夫的召唤饰品",
    "ScavengerSummonerCharm.Tooltip": "最大仆从数增加1",
    "ArchivistWarriorCharm.DisplayName": "归档者的战士饰品",
    "ArchivistWarriorCharm.Tooltip": "增加8%近战伤害\n增加4%近战暴击率",
    "ArchivistMageCharm.DisplayName": "归档者的法师饰品",
    "ArchivistMageCharm.Tooltip": "增加8%魔法伤害\n减少8%魔力消耗",
    "ArchivistRangerCharm.DisplayName": "归档者的射手饰品",
    "ArchivistRangerCharm.Tooltip": "增加8%远程伤害\n增加5%远程暴击率",
    "ArchivistSummonerCharm.DisplayName": "归档者的召唤饰品",
    "ArchivistSummonerCharm.Tooltip": "增加12%召唤伤害",
    "AshHeartWarriorCharm.DisplayName": "灰烬之心的战士饰品",
    "AshHeartWarriorCharm.Tooltip": "增加10%近战伤害\n提高生命再生",
    "AshHeartMageCharm.DisplayName": "灰烬之心的法师饰品",
    "AshHeartMageCharm.Tooltip": "增加10%魔法伤害\n提高魔力再生",
    "AshHeartRangerCharm.DisplayName": "灰烬之心的射手饰品",
    "AshHeartRangerCharm.Tooltip": "增加10%远程伤害\n15%几率不消耗弹药",
    "AshHeartSummonerCharm.DisplayName": "灰烬之心的召唤饰品",
    "AshHeartSummonerCharm.Tooltip": "增加12%召唤伤害\n最大仆从数增加1",
    "FireplaceWarriorCharm.DisplayName": "壁炉守卫的战士饰品",
    "FireplaceWarriorCharm.Tooltip": "增加12%近战伤害\n增加8%近战速度",
    "FireplaceMageCharm.DisplayName": "壁炉守卫的法师饰品",
    "FireplaceMageCharm.Tooltip": "增加12%魔法伤害\n减少12%魔力消耗",
    "FireplaceRangerCharm.DisplayName": "壁炉守卫的射手饰品",
    "FireplaceRangerCharm.Tooltip": "增加12%远程伤害\n增加8%远程暴击率",
    "FireplaceSummonerCharm.DisplayName": "壁炉守卫的召唤饰品",
    "FireplaceSummonerCharm.Tooltip": "增加14%召唤伤害\n最大仆从数增加1",
    "ScavengerCWarrior.DisplayName": "废料砍刀",
    "ScavengerCWarrior.Tooltip": "挥砍时甩出一块废料",
    "ScavengerCMage.DisplayName": "废料火花",
    "ScavengerCMage.Tooltip": "发射带电废料",
    "ScavengerCRanger.DisplayName": "废料手枪",
    "ScavengerCRanger.Tooltip": "",
    "ScavengerCSummoner.DisplayName": "废料无人机杖",
    "ScavengerCSummoner.Tooltip": "召唤一台回收无人机",
    "ArchivistCWarrior.DisplayName": "索引刃",
    "ArchivistCWarrior.Tooltip": "挥砍时放出一道短弧",
    "ArchivistCMage.DisplayName": "散页",
    "ArchivistCMage.Tooltip": "弹跳的纸页会迷惑命中的敌人",
    "ArchivistCRanger.DisplayName": "骨片枪",
    "ArchivistCRanger.Tooltip": "发射细小的归档碎片",
    "ArchivistCSummoner.DisplayName": "使魔残杖",
    "ArchivistCSummoner.Tooltip": "召唤一个使魔",
    "AshHeartCWarrior.DisplayName": "余烬刃",
    "AshHeartCWarrior.Tooltip": "",
    "AshHeartCMage.DisplayName": "心炭",
    "AshHeartCMage.Tooltip": "投出落地后燃烧的煤块",
    "AshHeartCRanger.DisplayName": "灰弹",
    "AshHeartCRanger.Tooltip": "",
    "AshHeartCSummoner.DisplayName": "余烬残壳杖",
    "AshHeartCSummoner.Tooltip": "召唤一簇余烬",
    "FireplaceCWarrior.DisplayName": "炉心刃",
    "FireplaceCWarrior.Tooltip": "",
    "FireplaceCMage.DisplayName": "冷灯",
    "FireplaceCMage.Tooltip": "发射缓慢的亮弹",
    "FireplaceCRanger.DisplayName": "钉枪",
    "FireplaceCRanger.Tooltip": "",
    "FireplaceCSummoner.DisplayName": "哨焰",
    "FireplaceCSummoner.Tooltip": "召唤一座悬浮哨兵",
    "AshEmberOrb.DisplayName": "余烬团",
    "AshPool.DisplayName": "灰池",
    "AshCinder.DisplayName": "落灰",
    "AshPulse.DisplayName": "坍缩脉冲",
    "HearthBolt.DisplayName": "炉心螺栓",
    "HearthRingShard.DisplayName": "冷光环",
    "HearthWall.DisplayName": "炉墙",
    "WastelandSpark.DisplayName": "火花",
    "CompanionSpark.DisplayName": "核心火花",
    "AshHeartPhaseTwo": "灰烬之心——燃烧开始自持。残灵正在喂这颗核。",
    "AshHeartPhaseThree": "灰烬之心——坍缩。脉冲在把一切往里吸。",
    "AshHeartDefeated": "心核裂开了。那道战争指令还是热的。",
    "ThirdMemoryRestored": "智械人恢复了第三段记忆——焚烧程序是她写的，也是她执行的。",
    "FireplaceGuardianPhaseTwo": "壁炉守卫——冷燃。环正在合拢。",
    "FireplaceGuardianPhaseThree": "壁炉守卫——重置协议。墙正在压过来。",
    "FireplaceGuardianDefeated": "最后一把锁开了。重置装置在等一个载体。",
    "FourthMemoryRestored": "智械人恢复了第四段记忆。壁炉从来不是庇护所。",
    "TrueName": "她想起了这具身体原来的名字。埃尔薇。",
    "EndingVessel": "她会带走重置。这个世界仍走向终点。下一轮黎明会知道她。",
    "EndingRefuse": "她不会再当武器。世界仍会结束，但不是死在她手上。",
    "CodaVessel": "月亮领主倒下了。她带着的重置点着了。别的地方，第一个早晨开始了。",
    "CodaRefuse": "月亮领主倒下了。星星照旧熄灭。她的名字没有。",
    "EnteredFireplace": "门在你身后合上。",
    "TerminalTalkToHer": "那段日志是她的，不是你的。去找她——这段记忆该由她亲耳听见。",
    "GatePlaced": "世界两侧的海面上各开了一扇暖门。壁炉在听。",
    "FireplaceEnterFailed": "门在这里，可路没有打开。需要启用 Subworld Library。",
    "FireplaceEntering": "门收下了你的请求，服务端正在确认……",
    "FireplaceNotOpen": "壁炉的门还封着。你敲了，但里面没有人应。",
    "FireplaceTooFar": "你离那扇门太远了。走近一点再试。",
    "FireplaceTravelBusy": "路已经在动了。缓一口气再试。",
    "FireplaceFormed": "壁炉成型完成了。",
    "FireplaceForming": "壁炉正在成型……请稍候",
    # 骷髅王之后：把玩家引导去壁炉（入口在主世界两侧的海洋边）
    "SkeletronFireplaceHint": "地牢的守门人倒下了。壁炉在等你——门就在主世界两侧海洋的岸边。",
    # 没戴防毒面具进壁炉：被毒气逼回主世界
    "GasMaskForcedBack": "毒气把你逼了回来——你需要一副防毒面具，才在里面喘得上气。",
    "Tiles.FireplaceGate.MapEntry": "壁炉门",
    "Tiles.FireplaceTerminal.MapEntry": "数据终端",
    "Tiles.FireplaceExit.MapEntry": "返回",
    "Tiles.YugangAlloy.MapEntry": "瑜钢合金",
    "Tiles.YugangTrim.MapEntry": "瑜钢压条",

    # 壁炉子世界统一背景墙（Content/Walls/AshWasteWall.cs 的 MapEntry）
    "Walls.AshWasteWall.MapEntry": "灰烬荒壁",
    "Conditions.AfterScavenger": "击败清道夫之后",
    "Conditions.AfterArchivist": "击败归档者之后",
    "Conditions.AfterAshHeart": "击败灰烬之心之后",
    "MechanicalCompanion.AfterAsh1": "我在这儿就能感觉到。地底下有东西还在烧，而且它知道我的序列号。",
    "MechanicalCompanion.AfterAsh2": "别站进灰里。那不是残留。它还在执行一道命令。",
    "MechanicalCompanion.AfterThird1": "焚烧程序是我写的。说出来并不会让它变小。",
    "MechanicalCompanion.AfterThird2": "下一把锁不在外面。它就坐在壁炉里，等一个人把我做完。",
    "MechanicalCompanion.AfterFourth1": "埃尔薇。那是核心进来之前，这具身体的名字。我想留下它。",
    "MechanicalCompanion.AfterFourth2": "重置需要一个载体。如果我走进去，这个世界还是会结束——但下一个世界醒来时，里面会有一个人，而不是一份协议。",
    "MechanicalCompanion.EndingVessel1": "我把黎明按住，直到这个世界走完。在那之前，留在我身边。",
    "MechanicalCompanion.EndingVessel2": "别谢我。我不是在救这里。我是在让下一个世界不要空着出生。",
    "MechanicalCompanion.EndingRefuse1": "我会看着它结束。我不会成为结束它的那只手。",
    "MechanicalCompanion.EndingRefuse2": "零号是序列号。埃尔薇可以只是一个留下来的人。",
    "MechanicalCompanion.ButtonTrade": "交易",
    "MechanicalCompanion.ButtonVessel": "带走重置",
    "MechanicalCompanion.ButtonRefuse": "拒绝",
    # 防毒面具（骷髅王之后、玩家还没做出面罩）：制作方法只写在对话里，物品 Tooltip 不许写
    "MechanicalCompanion.ButtonMask": "防毒面具",
    "MechanicalCompanion.MaskNeeded1": "你去过壁炉了，对吧。那里的空气已经烂了一百年——它会啃你的皮肤，还压着你的自愈。",
    "MechanicalCompanion.MaskNeeded2": "我不是让你憋气。旧时代给工人留下过一种面具——口鼻和眼睛上扣一层滤网，就足够在那样的废气里走动。",
    "MechanicalCompanion.MaskWhyNeed": "再进去之前，先戴上一副防毒面具。没有它，你在里面待多久，毒气就磨你多久——任何自然恢复都跟不上。",
    "MechanicalCompanion.MaskRecipe": "防毒面具不是旧时代的技术，它只是布和玻璃：丝绸 ×6、皮革 ×3、玻璃 ×3，再加铁锭或铅锭 ×8。合成站是铁砧或铅砧。丝绸用蛛网在织布机织出来，皮革从任何曾经活着的东西身上来，玻璃则是把沙子烧出来的。",
    "MechanicalCompanion.StoryHuntAsh": "下一份档案会烧。那是一颗从没灭过的心，在世界已经烂掉的地方。把它剩下的东西带给我。",
    "MechanicalCompanion.StoryBringThird": "你打碎了那颗心。如果你找到还带着我笔迹的余烬，交给我。",
    "MechanicalCompanion.StoryHuntGuardian": "最后一把锁在壁炉里面。它不是怪物。它是那扇门，在有人愿意当钥匙之前，它拒绝打开。",
    "MechanicalCompanion.StoryBringFourth": "守卫倒了。最后一块碎片里有我的名字。我得自己读。",
    "MechanicalCompanion.StoryChoice": "两条路。我成为重置的载体，或者我继续当埃尔薇，让世界自己结束，不再用我一次。两条路都会结束这里。",
    "MechanicalCompanion.StoryEndingVessel": "我选了黎明。当这轮月亮的最后领主倒下，我带着的重置会在别的地方点着。",
    "MechanicalCompanion.StoryEndingRefuse": "我选了名字。等到天空终于黑下去，那不会是因为我又签了一道命令。",
    "MechanicalCompanion.MemoryThirdNeedFragment": "心碎了，可我不能只靠记忆去读一场火。把碎片带给我。",
    "MechanicalCompanion.MemoryThird": "……读取成功。守望者焚烧协议，签署者是原型机。量产型杀掉我标记过的东西。灰烬之心就是我留下的标记，而执行那道命令的人是我。",
    "MechanicalCompanion.MemoryFourthNeedFragment": "锁开了。这块碎片是我名字的唯一一份副本。拿过来。",
    "MechanicalCompanion.MemoryFourth": "……读取成功。壁炉是一台重置装置。旧世界没打算活下去。它打算再开始一次，用原型机当载体。我现在穿着的这具身体，在核心进来之前有一个名字。埃尔薇。",
    "MechanicalCompanion.MemorySupplemented": "这段记录早就归档过了——我读过。碎片我照样收下——你不用替我背着一份我已经有的记录。",
    "MechanicalCompanion.ChoiceVessel": "那我来带。不是为了拯救这个世界。是为了让下一个世界醒来的时候，里面有人。",
    "MechanicalCompanion.ChoiceRefuse": "那我留下。世界可以自己结束。我不会把那道命令再签一次。",

	# ====================================================================================
	# 四包收尾新增内容（小怪 / 武器 / 护甲饰品 / 材料消耗品）
	# ====================================================================================

	"Scavenger.SpawnInfo": "每 5 天一次（19:30 预警、20:30 抵达），或用「清道夫信号传感器」（精钢锭 ×5 + 骨头 ×10）把它引过来。档位：骷髅王之后、血肉墙之前",
	"Archivist.SpawnInfo": "在恶魔/猩红祭坛合成「归档者残响」（归档者残响碎片 ×8 + 骨头 ×5 + 光明之魂 ×3 + 水晶碎块 ×6）并使用，把那台审计单元叫下来。档位：困难模式机械三王一级",
	"AshHeart.SpawnInfo": "在恶魔/猩红祭坛合成「灰烬之心余烬」（灰烬之心碎片 ×10 + 灵质 ×3 + 甲壳质 ×5），击败石巨人后使用",
	"FireplaceGuardian.SpawnInfo": "在恶魔/猩红祭坛合成「壁炉通行密钥」（壁炉残骸 ×12 + 壁炉合金锭 ×4 + 日耀碎片 ×6）。它守在壁炉深处——月亮领主之前的最后一个原创 Boss",
	"ScrapLeaper.DisplayName": "废料跳虫",
	"RustCharger.DisplayName": "锈蚀冲角兽",
	"GaleWisp.DisplayName": "风蚀幽火",
	"SpitterFly.DisplayName": "酸唾飞虫",
	"CaveCrawler.DisplayName": "洞穴爬行者",
	"AshTickBat.DisplayName": "灰蜱蝠",
	"PollutionSlime.DisplayName": "污染史莱姆",
	"GearSwarmHive.DisplayName": "齿轮蜂巢",
	"GearSwarm.DisplayName": "齿轮蜂群",
	"CinderMender.DisplayName": "余烬修补者",
	"ScrapReaper.DisplayName": "废料收割者",
	"RelayBeetle.DisplayName": "占位·清道夫后白天",
	"NightGnawer.DisplayName": "占位·清道夫后夜晚",
	"LedgerHawk.DisplayName": "占位·归档者后地表",
	"CinderLurker.DisplayName": "占位·灰烬之心后洞穴",
	"RustedGear.DisplayName": "锈蚀齿轮",
	"RustedGear.Tooltip": "",
	"ScrapReaperBlade.DisplayName": "废料收割者之刃",
	"ScrapReaperBlade.Tooltip": "甩出一块会转向目标的废料",
	"ScrapReaperBlade.Tooltip2": "命中后获得一层废料护盾",
	"RustCleaver.DisplayName": "锈蚀砍刀",
	"RustCleaver.Tooltip": "挥砍时甩出旋转废料",
	"ScrapYoyo.DisplayName": "废料溜溜球",
	"ScrapYoyo.Tooltip": "",
	"RustCleaverEX.DisplayName": "锈蚀砍刀 MK-II",
	"RustCleaverEX.Tooltip": "甩出可穿透3个敌人的燃烧废料",
	"RustBoltWand.DisplayName": "锈蚀电光棒",
	"RustBoltWand.Tooltip": "",
	"RustAcidTome.DisplayName": "锈蚀酸液法典",
	"RustAcidTome.Tooltip": "发射3道毒液弧",
	"RustBoltWandEX.DisplayName": "锈蚀电光棒 MK-II",
	"RustBoltWandEX.Tooltip": "发射可穿透3次的追踪电火花",
	"ScrapShotgun.DisplayName": "废料霰弹枪",
	"ScrapShotgun.Tooltip": "射出一簇子弹",
	"RustNailgun.DisplayName": "锈蚀钉枪",
	"RustNailgun.Tooltip": "50% 概率不消耗弹药",
	"ScrapShotgunEX.DisplayName": "废料霰弹枪 MK-II",
	"ScrapShotgunEX.Tooltip": "一次打出5发，碰墙反弹1次",
	"RustDroneStaff.DisplayName": "锈蚀无人机法杖",
	"RustDroneStaff.Tooltip": "召唤会撞击敌人的无人机",
	"RustSpitterStaff.DisplayName": "锈蚀吐酸法杖",
	"RustSpitterStaff.Tooltip": "召唤会喷酸的生物",
	"RustSpitterStaffEX.DisplayName": "锈蚀吐酸法杖 MK-II",
	"RustSpitterStaffEX.Tooltip": "召唤会喷出2发穿透酸液的生物",
	"ScrapGreatsword.DisplayName": "废料巨剑",
	"ScrapGreatsword.Tooltip": "挥砍时沿地面推出冲击波",
	"RebarBoomerang.DisplayName": "钢筋回旋镖",
	"RebarBoomerang.Tooltip": "去程和回程都会造成伤害",
	"ScrapNovaStaff.DisplayName": "废料新星法杖",
	"ScrapNovaStaff.Tooltip": "命中后爆成4枚追踪碎片",
	"ScrapNovaStaffEX.DisplayName": "废料新星法杖 MK-II",
	"ScrapNovaStaffEX.Tooltip": "命中后爆成6枚追踪碎片",
	"ScrapRailgun.DisplayName": "废料磁轨炮",
	"ScrapRailgun.Tooltip": "",
	"ScrapRailgunEX.DisplayName": "废料磁轨炮 MK-II",
	"ScrapRailgunEX.Tooltip": "可穿透8个敌人",
	"ScrapWardenStaff.DisplayName": "废料典狱官法杖",
	"ScrapWardenStaff.Tooltip": "召唤会撞击并开炮的守卫",
	"ScrapBuzzsaw.DisplayName": "废料圆锯",
	"ScrapBuzzsaw.Tooltip": "钉在地上，谁踩上去就锯谁",
	# 升级衍生树（一）近战：锈蚀砍刀 → 精钢锋刃 → 归档者裁决刃
	"SalvagedSteelSaber.DisplayName": "精钢锋刃",
	"SalvagedSteelSaber.Tooltip": "甩出可穿透4次的钢片\n造成流血",
	"ArchivistVerdictBlade.DisplayName": "归档者裁决刃",
	"ArchivistVerdictBlade.Tooltip": "放出可穿透6次的剑气\n再分裂成追踪碎片",
	# 升级衍生树（二）远程：废料霰弹枪 → 精钢散射枪 → 灰烬之心火铳
	"SalvagedSteelScattergun.DisplayName": "精钢散射枪",
	"SalvagedSteelScattergun.Tooltip": "一次打出6发，每发可穿透2次",
	"AshHeartFlechette.DisplayName": "灰烬之心火铳",
	"AshHeartFlechette.Tooltip": "一次打出3发飞镖，每发可穿透3次\n使敌人着火",
	# 升级衍生树（五）魔法：锈蚀火花杖 → 精钢弧光法杖 → 壁炉守卫霜语法典
	"SalvagedSteelArcWand.DisplayName": "精钢弧光法杖",
	"SalvagedSteelArcWand.Tooltip": "发射3道电弧，造成带电",
	"HearthGuardFrostCodex.DisplayName": "壁炉守卫霜语法典",
	"HearthGuardFrostCodex.Tooltip": "发射5支追踪冰枪，每支可穿透3次\n造成冻伤",
	"AshHeartMask.DisplayName": "灰烬之心面具",
	"AshHeartMask.Tooltip": "增加7%近战和远程伤害",
	"AshHeartPlate.DisplayName": "灰烬之心胸甲",
	"AshHeartPlate.SetBonus": "18%几率使敌人着火\n增加8%近战速度\n自身着火时提高生命再生",
	"AshHeartPlate.Tooltip": "增加6%伤害\n10%几率使敌人着火",
	"AshHeartGreaves.DisplayName": "灰烬之心护腿",
	"AshHeartGreaves.Tooltip": "增加4%伤害\n增加5%移动速度",
	"HearthGuardVisor.DisplayName": "壁炉守卫面罩",
	"HearthGuardVisor.Tooltip": "减少3%所受伤害\n免疫寒冷",
	"HearthGuardCuirass.DisplayName": "壁炉守卫胸甲",
	"HearthGuardCuirass.SetBonus": "防御力增加4\n减少5%所受伤害\n受伤时放出一圈冷火",
	"HearthGuardCuirass.Tooltip": "减少4%所受伤害\n免疫击退",
	"HearthGuardGreaves.DisplayName": "壁炉守卫护腿",
	"HearthGuardGreaves.Tooltip": "减少3%所受伤害\n略微降低移动速度",
	"ScavengerHarness.DisplayName": "清道夫挽具",
	"ScavengerHarness.Tooltip": "增加10%移动速度\n免疫击退和坠落伤害",
	"FilteredRebreather.DisplayName": "滤芯呼吸器",
	"FilteredRebreather.Tooltip": "防御力增加2\n污染和有害气体伤害减少65%",
	"WastelandCompass.DisplayName": "废土罗盘",
	"WastelandCompass.Tooltip": "幸运增加0.4\n15%几率不消耗弹药\n敌人不太会以你为目标",
	"AbyssBreather.DisplayName": "深渊呼吸器",
	"AbyssBreather.Tooltip": "呼吸时间增加200\n可以游泳\n免疫潮湿",
	"CinderstepBoots.DisplayName": "烬步长靴",
	"CinderstepBoots.Tooltip": "可冲刺\n连按方向键两次\n冲刺期间短暂无敌",
	"EmberglassLens.DisplayName": "烬玻璃透镜",
	"EmberglassLens.Tooltip": "增加8%远程伤害\n增加5%远程暴击率\n25%几率使敌人着火",
	"ConsecratedCore.DisplayName": "祝圣核心",
	"ConsecratedCore.Tooltip": "增加12%召唤伤害\n最大仆从数增加1\n鞭子范围增加20%",
	"AshEchoCharm.DisplayName": "灰烬回响护符",
	"AshEchoCharm.Tooltip": "增加9%近战伤害\n增加8%近战速度\n20%几率使敌人着火",
	"HearthBeacon.DisplayName": "壁炉信标",
	"HearthBeacon.Tooltip": "提高生命再生\n增加红心拾取范围",
	"HearthAegis.DisplayName": "壁炉神盾",
	"HearthAegis.Tooltip": "防御力增加5\n免疫击退\n护盾存在时减少14%所受伤害",
	"HearthMirror.DisplayName": "壁炉之镜",
	"HearthMirror.Tooltip": "防御力增加3\n受伤时将35%伤害以余烬碎片反射给最近的敌人",
	"MorrowFragment.DisplayName": "明日碎片",
	"MorrowFragment.Tooltip": "增加5%伤害\n每45秒可避免一次致死伤害",
	# 升级衍生树（三）饰品：防毒面具 → 强化滤芯面罩 → 灰烬之心净界面罩
	"ReinforcedFilterMask.DisplayName": "强化滤芯面罩",
	"ReinforcedFilterMask.Tooltip": "防御力增加3\n免疫有害气体和中毒\n污染伤害减少45%",
	"AshHeartPurifierMask.DisplayName": "灰烬之心净界面罩",
	"AshHeartPurifierMask.Tooltip": "防御力增加5\n免疫有害气体、中毒和毒液\n污染伤害减少70%\n提高生命再生",
	# 升级衍生树（四）护甲：精钢战士套装 → 灰烬合金战士套装 → 壁炉合金战士套装
	"AshAlloyWarriorHelm.DisplayName": "灰烬合金战士头盔",
	"AshAlloyWarriorHelm.Tooltip": "增加8%近战伤害",
	"AshAlloyWarriorPlate.DisplayName": "灰烬合金战士胸甲",
	"AshAlloyWarriorPlate.Tooltip": "增加8%近战伤害",
	"AshAlloyWarriorPlate.SetBonus": "增加12%近战伤害和近战速度\n15%几率使敌人着火\n污染伤害减少15%",
	"AshAlloyWarriorGreaves.DisplayName": "灰烬合金战士护腿",
	"AshAlloyWarriorGreaves.Tooltip": "增加8%近战速度",
	"HearthAlloyWarriorHelm.DisplayName": "壁炉合金战士头盔",
	"HearthAlloyWarriorHelm.Tooltip": "增加9%近战伤害\n减少3%所受伤害",
	"HearthAlloyWarriorPlate.DisplayName": "壁炉合金战士胸甲",
	"HearthAlloyWarriorPlate.Tooltip": "增加9%近战伤害\n免疫击退",
	"HearthAlloyWarriorPlate.SetBonus": "增加15%近战伤害和近战速度\n减少6%所受伤害\n免疫击退",
	"HearthAlloyWarriorGreaves.DisplayName": "壁炉合金战士护腿",
	"HearthAlloyWarriorGreaves.Tooltip": "增加9%近战速度\n减少3%所受伤害",
	# 升级衍生树（六）召唤：锈蚀齿轮哨 → 精钢齿轮哨 → 灰烬之心齿灵哨
	"RustedGearWhistle.DisplayName": "锈蚀齿轮哨",
	"RustedGearWhistle.Tooltip": "召唤一座锈蚀齿轮哨兵",
	"SalvagedSteelGearWhistle.DisplayName": "精钢齿轮哨",
	"SalvagedSteelGearWhistle.Tooltip": "召唤一对精钢齿轮哨兵",
	"AshHeartGearWhistle.DisplayName": "灰烬之心齿灵哨",
	"AshHeartGearWhistle.Tooltip": "召唤两座灰烬之心齿轮\n防御力增加5，减少8%所受伤害，免疫击退",
	# 升级衍生树（七）盗贼：锈蚀齿轮镖 → 精钢锯齿环 → 灰烬之心余烬环
	# 升级衍生树（八）饰品：拾荒者芯片 → 强化拾荒者芯片 → 废土主宰核心
	"ScavengerChip.DisplayName": "拾荒者芯片",
    "ScavengerChip.Tooltip": "增加8%召唤伤害\n增加物品和红心拾取范围",
	"ReinforcedScavengerChip.DisplayName": "强化拾荒者芯片",
    "ReinforcedScavengerChip.Tooltip": "增加12%召唤伤害\n减少5%所受伤害\n增加钱币和魔力星拾取范围",
	"WastelandOverlordCore.DisplayName": "废土主宰核心",
    "WastelandOverlordCore.Tooltip": "增加15%召唤伤害\n最大仆从数增加1\n减少8%所受伤害\n提高幸运",
	"Coke.DisplayName": "焦炭",
	"Coke.Tooltip": "",
	"CircuitBoard.DisplayName": "旧世界电路板",
	"CircuitBoard.Tooltip": "",
	"Coolant.DisplayName": "冷却液罐",
	"Coolant.Tooltip": "",
	"AshCrystal.DisplayName": "灰烬结晶",
	"AshCrystal.Tooltip": "",
	"SalvagedSteelBundle.DisplayName": "精钢捆",
	"SalvagedSteelBundle.Tooltip": "",
	"GasFilterPotion.DisplayName": "滤芯",
	"GasFilterPotion.Tooltip": "免疫有害气体和污染",
	"MinersSolution.DisplayName": "掘进溶液",
	"MinersSolution.Tooltip": "提高挖掘、建造和放置速度\n物块操作范围增加1格",
	"ColdSpotlight.DisplayName": "冷光探照灯",
	"ColdSpotlight.Tooltip": "显示敌人、机关和宝藏的位置\n提高视野",
	"NaniteSalve.DisplayName": "纳米药膏",
	"NaniteSalve.Tooltip": "提高生命再生",
	"BeastWhistle.DisplayName": "兽哨回响",
	"BeastWhistle.Tooltip": "增加召唤伤害\n提高鞭子速度和范围",
	"AshenRation.DisplayName": "灰烬口粮",
	"AshenRation.Tooltip": "小幅提升所有属性\n增加5%伤害",
	"ScrapNail.DisplayName": "废料钉",
	"ScrapNail.Tooltip": "",
	"ColdlightRound.DisplayName": "冷光弹",
	"ColdlightRound.Tooltip": "可穿透1个敌人\n造成冻伤",
	"EmberShell.DisplayName": "余烬霰弹",
	"EmberShell.Tooltip": "可穿透2个敌人\n使敌人着火",
	"TornPage.DisplayName": "残页",
	"TornPage.Tooltip": "可穿透4个敌人",
	"ScavengerBeacon.DisplayName": "狩猎信标",
	"ScavengerBeacon.Tooltip": "召唤清道夫\n使用后不消耗",
	"AuditRequest.DisplayName": "审计申请表",
	"AuditRequest.Tooltip": "召唤归档者\n使用后不消耗",
	"EmberFuse.DisplayName": "余烬引信",
	"EmberFuse.Tooltip": "召唤灰烬之心\n使用后不消耗",
	"WastelandMap.DisplayName": "废土地图残片",
	"WastelandMap.Tooltip": "揭示一处随机地点",
	"ScrapCache.DisplayName": "废料储藏箱",
	"ScrapCache.Tooltip": "右键点击打开",
	"ReaperFriendlyScrap.DisplayName": "废料块",
	"ReaperScrapShot.DisplayName": "废料射击",
	"ReaperShockwave.DisplayName": "废料冲击波",
	"SpitterGlob.DisplayName": "酸液团",
	"RustShardSlash.DisplayName": "废料碎片",
	"RustShardSlashEX.DisplayName": "燃烧废料碎片",
	"ScrapYoyoProjectile.DisplayName": "废料溜溜球",
	"RustBolt.DisplayName": "锈蚀电光",
	"RustBoltEX.DisplayName": "锈蚀电光 MK-II",
	"RustAcidSpray.DisplayName": "酸液团",
	"ScrapPellet.DisplayName": "废料弹丸",
	"ScrapPelletEX.DisplayName": "废料弹丸 MK-II",
	"RustNail.DisplayName": "锈蚀钉",
	"RustDrone.DisplayName": "废料无人机",
	"RustSpitter.DisplayName": "锈蚀吐酸者",
	"RustSpitterShot.DisplayName": "酸液团",
	"RustSpitterEX.DisplayName": "锈蚀吐酸者 MK-II",
	"RustSpitterShotEX.DisplayName": "酸液团 MK-II",
	"ScrapShockwave.DisplayName": "废料冲击波",
	"RebarBoomerangProj.DisplayName": "钢筋回旋镖",
	"ScrapNova.DisplayName": "废料新星",
	"ScrapNovaEX.DisplayName": "废料新星 MK-II",
	"ScrapNovaFragment.DisplayName": "新星碎片",
	"ScrapRailSlug.DisplayName": "磁轨弹丸",
	"ScrapRailSlugEX.DisplayName": "磁轨弹丸 MK-II",
	"ScrapWarden.DisplayName": "废料典狱官",
	"ScrapWardenShot.DisplayName": "典狱官炮弹",
	"ScrapBuzzsawProj.DisplayName": "废料圆锯",
	"GearReboundShard.DisplayName": "回弹余烬",
	"GearColdPulse.DisplayName": "冷焰喷发",
	"ScrapNailProjectile.DisplayName": "废料钉",
	"ColdlightProjectile.DisplayName": "冷光弹",
	"EmberShellProjectile.DisplayName": "余烬霰弹",
	"TornPageProjectile.DisplayName": "残页",
	# 升级衍生树的新弹幕
	"SteelEdgeShard.DisplayName": "精钢碎片",
	"VerdictWave.DisplayName": "裁决波",
	"VerdictFragment.DisplayName": "裁决碎片",
	"SteelBuckshot.DisplayName": "精钢霰弹",
	"EmberFlechette.DisplayName": "燃烬箭弹",
	"SteelArcBolt.DisplayName": "精钢弧光",
	"FrostLance.DisplayName": "霜矛",
	# 升级衍生树（六/七）的新弹幕
	"RustedGearSentry.DisplayName": "锈蚀齿轮哨兵",
	"SalvagedSteelCharger.DisplayName": "精钢冲锋齿轮",
	"SalvagedSteelSniper.DisplayName": "精钢射击齿轮",
	"SalvagedSteelBolt.DisplayName": "精钢钢钉",
	"AshHeartOrbitSentry.DisplayName": "灰烬环绕齿灵",
	"AshHeartGearEmber.DisplayName": "齿轮余烬",
	"ElvenFrame.MapEntry": "精灵族躯体",
	"FireplaceGate.MapEntry": "壁炉门",
	"FireplaceTerminal.MapEntry": "数据终端",
	"FireplaceExit.MapEntry": "出口通路",
	# 这两条原本只存在于工作树（未提交），译文表里只有带 Tiles. 前缀的旧写法，补短键形式
	"YugangAlloy.MapEntry": "瑜钢合金",
	"YugangTrim.MapEntry": "瑜钢压条",
	"AfterScavenger": "清道夫倒下之后",
	"AfterArchivist": "归档者倒下之后",
	"AfterAshHeart": "灰烬之心倒下之后",
	"ScrapShield.DisplayName": "废料护盾",
	"ScrapShield.Description": "防御 +4",
	"RustDroneBuff.DisplayName": "废料无人机",
	"RustDroneBuff.Description": "一架锈蚀无人机跟随着你，撞击附近的敌人",
	"RustSpitterBuff.DisplayName": "锈蚀吐酸者",
	"RustSpitterBuff.Description": "一台锈蚀吐酸者跟随着你，朝附近的敌人吐酸",
	"RustSpitterBuffEX.DisplayName": "锈蚀吐酸者 MK-II",
	"RustSpitterBuffEX.Description": "一台强化吐酸者跟随着你，一次射出两团酸液",
	"ScrapWardenBuff.DisplayName": "废料典狱官",
	"ScrapWardenBuff.Description": "一具废料典狱官跟随着你，替你挡身位并炮轰附近的敌人",
	"GasFilterBuff.DisplayName": "滤芯",
	"GasFilterBuff.Description": "有害气体与污染都碰不到你",
	# 升级衍生树（六）召唤仆从的维持 Buff
	"RustedGearSentryBuff.DisplayName": "锈蚀齿轮哨兵",
	"RustedGearSentryBuff.Description": "一只锈蚀齿轮哨兵跟随着你，撞击附近的敌人",
	"SalvagedSteelGearBuff.DisplayName": "精钢双联齿轮",
	"SalvagedSteelGearBuff.Description": "一对精钢齿轮跟随着你——一只冲锋撞击，一只发射会让伤口流血的钢钉",
	"AshHeartGearBuff.DisplayName": "灰烬之心齿灵",
	"AshHeartGearBuff.Description": "两只灰烬齿灵绕着你转圈、点燃敌人，并为你罩上齿轮护盾：防御 +5、免疫击退、伤害减免 8%",
	"MinersSolutionBuff.DisplayName": "掘进溶液",
	"MinersSolutionBuff.Description": "挖掘、建造与触及距离全面提升",
	"ColdSpotlightBuff.DisplayName": "冷光探照灯",
	"ColdSpotlightBuff.Description": "你能在黑暗中视物、感知附近的危险，并看见宝藏",
	"NaniteSalveBuff.DisplayName": "纳米药膏",
	"NaniteSalveBuff.Description": "你的伤口正在被从内部修复",
	"BeastWhistleBuff.DisplayName": "兽哨回响",
	"BeastWhistleBuff.Description": "召唤物打得更重，鞭子更快、触及更远",
	"AshenRationBuff.DisplayName": "灰烬口粮",
	"AshenRationBuff.Description": "吃饱了，手上挥出的每一下都更沉一点",
	"GearMorrowSaved": "兜里的盒子忽然变冷 —— 那一击从未发生。",
	"MapHint1": "地图上说：沿着锈迹走。凡是还立着路牌的路，都通向一台还没睡着的机器。",
	"MapHint2": "地图上说：灰烬底下还有东西是暖的。如果脚下发烫，说明你正站在一颗心上。",
	"MapHint3": "地图上说：索引蛾只落在曾经存放记录的地方。在这里，木板和纸页比金子值钱。",
	"MapHint4": "地图上说：冷的地方不是安全的地方，那是壁炉还在排气的位置。",
	"MapHint5": "地图上说：密封的箱子里装着主人认为值得留下的东西。趁别的东西还没撬开它。",
	"MapHint6": "地图上说：如果一台机器问你的名字，不要给它。把信标给它。",
	"CacheOpened": "储藏箱呻吟着打开。里面的东西还值得带走。",
	# ---------------- Boss 奖杯 / 旗帜（9 个图块 + 9 个物品） ----------------
	"ScavengerTrophy.DisplayName": "清道夫奖杯",
	"ScavengerTrophy.Tooltip": "",
	"ArchivistTrophy.DisplayName": "归档者奖杯",
	"ArchivistTrophy.Tooltip": "",
	"AshHeartTrophy.DisplayName": "灰烬之心奖杯",
	"AshHeartTrophy.Tooltip": "",
	"FireplaceGuardianTrophy.DisplayName": "壁炉守卫奖杯",
	"FireplaceGuardianTrophy.Tooltip": "",
	"ScrapReaperTrophy.DisplayName": "锈爪齿轮奖杯",
	"ScrapReaperTrophy.Tooltip": "",
	"ScavengerBanner.DisplayName": "清道夫旗帜",
	"ScavengerBanner.Tooltip": "",
	"ArchivistBanner.DisplayName": "归档者旗帜",
	"ArchivistBanner.Tooltip": "",
	"AshHeartBanner.DisplayName": "灰烬之心旗帜",
	"AshHeartBanner.Tooltip": "",
	"FireplaceGuardianBanner.DisplayName": "壁炉守卫旗帜",
	"FireplaceGuardianBanner.Tooltip": "",
	"ScavengerTrophy.MapEntry": "清道夫奖杯",
	"ArchivistTrophy.MapEntry": "归档者奖杯",
	"AshHeartTrophy.MapEntry": "灰烬之心奖杯",
	"FireplaceGuardianTrophy.MapEntry": "壁炉守卫奖杯",
	"ScrapReaperTrophy.MapEntry": "锈爪齿轮奖杯",
	"ScavengerBanner.MapEntry": "清道夫旗帜",
	"ArchivistBanner.MapEntry": "归档者旗帜",
	"AshHeartBanner.MapEntry": "灰烬之心旗帜",
	"FireplaceGuardianBanner.MapEntry": "壁炉守卫旗帜",

    # ---- 由 patch_cn_signal_keys.py 补录（模组 zh-Hans 里已有、译文表漏掉的键） ----
    "Buffs.SignalWispBuff.Description": "一盏灯在替你看着",
    "Buffs.SignalWispBuff.DisplayName": "信号灯芯",
    "Buffs.VoidSeedBuff.Description": "一颗种子正在撕开小裂缝",
    "Buffs.VoidSeedBuff.DisplayName": "虚空种",
    "Items.GapChakram.DisplayName": "缺环轮",
    "Items.GapChakram.Tooltip": "飞行结束时坍缩",
    "Items.OrbitScepter.DisplayName": "轨环权杖",
    "Items.OrbitScepter.Tooltip": "投出一颗会折成裂隙的星核",
    "Items.RiftCleaver.DisplayName": "星隙弯刃",
    "Items.RiftCleaver.Tooltip": "挥砍时撕开一道会坍缩的裂隙",
    "Items.SignalCleaver.DisplayName": "锈颚砍刀",
    "Items.SignalCleaver.Tooltip": "甩出燃烧的废料",
    "Items.SignalCodex.DisplayName": "提灯法典",
    "Items.SignalCodex.Tooltip": "放出追踪的灯火",
    "Items.SignalEmberFan.DisplayName": "余烬扇",
    "Items.SignalEmberFan.Tooltip": "一次甩出3把燃烧的刃",
    "Items.SignalNailgun.DisplayName": "线圈钉枪",
    "Items.SignalNailgun.Tooltip": "命中时迸出电弧",
    "Items.SignalRigGreaves.DisplayName": "信号甲护腿",
    "Items.SignalRigGreaves.Tooltip": "增加4%移动速度",
    "Items.SignalRigHelm.DisplayName": "信号甲头盔",
    "Items.SignalRigHelm.Tooltip": "",
    "Items.SignalRigPlate.DisplayName": "信号甲胸甲",
    "Items.SignalRigPlate.SetBonus": "增加6%移动速度",
    "Items.SignalRigPlate.Tooltip": "",
    "Items.SignalWispStaff.DisplayName": "信号灯芯杖",
    "Items.SignalWispStaff.Tooltip": "召唤一盏狩猎提灯",
    "Items.StarstringBow.DisplayName": "星弦弓",
    "Items.StarstringBow.Tooltip": "将一支箭转化为三支带电矢\n矢会略作追踪并穿过物块",
    "Items.VoidSeed.DisplayName": "虚空种",
    "Items.VoidSeed.Tooltip": "召唤会撕开小裂隙的种子",
    "Projectiles.GapChakramProj.DisplayName": "裂隙环刃",
    "Projectiles.OrbitMote.DisplayName": "环绕微尘",
    "Projectiles.SignalCoilNail.DisplayName": "信号线圈钉",
    "Projectiles.SignalEmberFanProj.DisplayName": "信号余烬扇",
    "Projectiles.SignalLanternMote.DisplayName": "信号灯微尘",
    "Projectiles.SignalRustShard.DisplayName": "信号锈蚀碎片",
    "Projectiles.SignalWispMinion.DisplayName": "信号微光",
    "Projectiles.SignalWispShot.DisplayName": "信号微光",
    "Projectiles.StarRiftSlash.DisplayName": "星裂隙",
    "Projectiles.StarstringShot.DisplayName": "带电矢",
    "Projectiles.WastelandMeleeSwing.DisplayName": "近战挥砍",
    "Projectiles.VoidSeedMinion.DisplayName": "虚空种子",

}

# ====================================================================================
# Hjson 读写
# ====================================================================================
_KEY = re.compile(r'^(\t*)([A-Za-z0-9_.\-]+)\s*:\s*(.*)$')


def _clean_value(raw):
    value = raw.strip()
    if value.startswith('"') and value.endswith('"') and len(value) >= 2:
        value = value[1:-1]
    return value


def parse(path, prefix):
    """返回 [(depth, 路径段列表, 值)]。

    depth = 该叶子键所在节的嵌套层数（主模组文件里只有 0 / 1 / 2 三种）。
    路径段列表 = 从根开始的完整段（第一段是顶层节名）。
    多行块的值记成 <multiline>。
    必须保留 depth —— tModLoader 会把 `Buffs: { X: { DisplayName } }` 解析成
    `Buffs.X.DisplayName`，如果补丁里把它写平，键就会多出一层前缀而失效。
    """
    with io.open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()

    stack = []      # [(indent, key)]
    out = []
    i = 0

    while i < len(lines):
        raw = lines[i]
        i += 1
        stripped = raw.strip()

        if not stripped or stripped.startswith("//"):
            continue

        if stripped.startswith("/*"):
            while i < len(lines) and "*/" not in lines[i]:
                i += 1
            i += 1
            continue

        if stripped in ("}", "},"):
            if stack:
                stack.pop()
            continue

        match = _KEY.match(raw)
        if not match:
            continue

        indent = len(match.group(1))
        key = match.group(2)
        value = match.group(3).strip()

        while stack and stack[-1][0] >= indent:
            stack.pop()

        if value in ("", "{", "}", "},"):
            # 值写在下一个缩进块里的多行字符串
            lookahead = None
            for probe in lines[i:i + 3]:
                if probe.strip():
                    lookahead = probe.strip()
                    break

            if lookahead and (lookahead.startswith("'''") or lookahead.startswith('"""')):
                marker = lookahead[:3]
                while i < len(lines) and not lines[i].strip().startswith(marker):
                    i += 1
                i += 1
                path_segments = [k for _ind, k in stack] + [key]
                out.append((len(stack), path_segments, "<multiline>"))
                continue

            stack.append((indent, key))
            continue

        path_segments = [k for _ind, k in stack] + [key]
        out.append((len(stack), path_segments, _clean_value(value)))

    return out


def to_section(segments):
    return segments[0]


def flatten(segments):
    """完整键（相对共享前缀），例如 Mods.WastelandSoul.Buffs.X.DisplayName。"""
    return PREFIX_EN + "." + ".".join(segments)


def short(segments):
    """译文表的查找键：一律去掉**最外层**段。

    主模组文件里 `Items.X.DisplayName` 与 `Buffs: { X: { DisplayName } }` 两种写法
    最终都展开成 `Items.X.DisplayName` / `Buffs.X.DisplayName`，
    所以查找键统一是「顶层节之后的部分」，例如：
      NPCs.Archivist.DisplayName   → Archivist.DisplayName
      Buffs.Pollution.DisplayName  → Pollution.DisplayName
    扁平键 `BossChecklist.Scavenger.SpawnInfo` 本来就是一段，保持原样。
    例外：`Configs.WastelandConfig.X` 展开后是 `WastelandSoul.Configs.WastelandConfig.X`
    （也变成扁平键了），所以这组要去掉 `Configs.`。
    """
    rest = segments[1:] if len(segments) > 1 else segments

    if rest[:1] == ["Configs"]:
        rest = rest[1:]

    return ".".join(rest)


def quote_value(value):
    r"""按 Hjson 规则决定要不要给值加引号，需要就加上。

    ⚠️ 这是踩过大坑的地方。`LikeBiome: 这里的参数还算合意——{BiomeName}。` 能解析，
    但 `DislikeBiome: {BiomeName}让我想起被污染的地面。` **不能**——
    值以 `{` 开头时 Hjson 把它当**内联对象**解析，撞到 `}` 就报
      `Found '}' where a key name was expected`
    然后 tModLoader 判定整个本地化文件 malformed，
    **把汉化补丁和主模组一起禁用掉**（补丁是硬依赖）。

    规则不是猜的，而是用真实解析器实测出来的（`tools/probe_hjson_rules.py`，
    结论落在 `tools/hjson_quoting_rules.json`）：18 个用例里
    **只有"值以 `{` 开头"会被拒**，以下这些都**合法**：
      含逗号 / 含冒号 / 含 `=` / 含 `;` / 含 `+`、`{` 或 `}` 在中间、
      `[` 开头、`-` 或 `#` 开头、值里有未转义的引号、含反斜杠。
    所以这里只对两种情况加引号：**以 `{` 开头**，以及**含双引号**（避免歧义）。
    """
    if value == "":
        return '""'

    needs_quote = value.startswith("{") or '"' in value

    if not needs_quote:
        return value

    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return '"%s"' % escaped


def needs_quote(value):
    """给校验脚本复用：这个值按 Hjson 规则是否必须加引号。"""
    return quote_value(value) != value


def lookup_translation(segments):
    r"""按路径段取译文，**同时兼容 tModLoader 改写后的写法**。

    tModLoader 会在加载时重写源目录里的本地化文件，并且会把"扁平点号键"拆成新节：

        改写前：BossChecklist.Scavenger.SpawnInfo: ...
        改写后：BossChecklist: {
                    Scavenger.SpawnInfo: ...
                }

    这两种写法在 tModLoader 眼里是**同一个键**（都是
    Mods.WastelandSoul.BossChecklist.Scavenger.SpawnInfo），但路径段不同：
    前者是 ['BossChecklist.Scavenger.SpawnInfo']，后者是 ['BossChecklist', 'Scavenger.SpawnInfo']。
    所以查找时两种都要试，否则被改写过的文件会让这些键静默退化成英文占位。
    """
    candidates = [
        short(segments),                                    # 常规：去掉最外层段
        ".".join(segments),                                 # 被拆节后的写法
        ".".join(segments[1:]) if len(segments) > 1 else segments[0],
    ]

    for candidate in candidates:
        # Configs 那组在文件里是真实嵌套节，查找键要去掉 Configs.
        if candidate.startswith("Configs."):
            candidate = candidate[len("Configs."):]

        if candidate in TRANSLATIONS:
            return TRANSLATIONS[candidate]

    return None


def build_cn(en_entries):
    """按主模组的键顺序与嵌套结构写出中文文件。

    没有译文的键写成英文占位注释（与 tModLoader 自己的做法一致），方便继续补翻译。
    返回 (文本, 已翻译条数, 缺失键列表)。
    """
    lines = []
    open_keys = []          # 当前已经打开的节的路径段
    translated = 0
    missing = []

    def close_to(depth):
        while len(open_keys) > depth:
            open_keys.pop()
            lines.append("\t" * len(open_keys) + "}")

    for depth, segments, en_value in en_entries:
        # 主模组文件里 `Buffs: { X: { DisplayName } }` 这种写法意味着键是
        # Buffs.X.DisplayName —— **节点与键共用一条路径**。
        # 所以开合规则是「先求出与目标路径（叶子键之前的部分）的公共前缀，
        # 关掉多出来的层，再补开缺的层」，同父的兄弟键不会重复开节。
        section = segments[:-1]
        common = 0

        while common < len(open_keys) and common < len(section) and open_keys[common] == section[common]:
            common += 1

        while len(open_keys) > common:
            open_keys.pop()
            lines.append("\t" * len(open_keys) + "}")

        while len(open_keys) < len(section):
            key = section[len(open_keys)]
            lines.append("\t" * len(open_keys) + "%s: {" % key)
            open_keys.append(key)

        leaf = segments[-1]
        indent = "\t" * len(open_keys)
        lookup = short(segments)
        value = lookup_translation(segments)

        if value is None:
            missing.append(lookup)

            if "\n" in en_value:
                lines.append("%s// %s:" % (indent, leaf))
                lines.append(indent + "\t'''")
                for chunk in en_value.split("\n"):
                    lines.append(indent + "\t" + chunk)
                lines.append(indent + "\t'''")
            else:
                lines.append("%s// %s: %s" % (indent, leaf, en_value))
            continue

        translated += 1

        if "\n" in value:
            # 多行块里的每一行都不需要引号（Hjson 的 ''' 块按字面取值）
            lines.append("%s%s:" % (indent, leaf))
            lines.append(indent + "\t'''")
            for chunk in value.split("\n"):
                lines.append(indent + "\t" + chunk)
            lines.append(indent + "\t'''")
        else:
            lines.append("%s%s: %s" % (indent, leaf, quote_value(value)))

    close_to(0)
    return "\n".join(lines) + "\n", translated, missing


def main():
    target = "WastelandSoul"
    en_path = os.path.join(MAIN_LOC, "en-US_Mods.%s.hjson" % target)
    cn_path = os.path.join(CN_LOC, "zh-Hans_Mods.%s.hjson" % target)

    if not os.path.exists(en_path):
        print("!! 找不到主模组英文文件:", en_path)
        return 1

    en_entries = parse(en_path, PREFIX_EN)
    print("主模组 en-US: %d 条键" % len(en_entries))

    text, translated, missing = build_cn(en_entries)

    if "--report" in sys.argv or "--check" in sys.argv:
        print("已翻译: %d / %d" % (translated, len(en_entries)))
        if missing:
            print("仍为英文占位 %d 条:" % len(missing))
            for key in missing:
                print("   ?", key)
        return 0

    with io.open(cn_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)

    print("已写入 %s（%d 字节）" % (cn_path, os.path.getsize(cn_path)))
    print("已翻译: %d 条；仍为英文占位: %d 条" % (translated, len(missing)))

    refresh_en_template(en_path, target)
    shutil.copyfile(cn_path, CN_BACKUP)
    print("已刷新备份 %s" % CN_BACKUP)
    return 0


def refresh_en_template(en_path, target):
    """给汉化补丁放一份**同前缀的英文模板**：这一步不是可选的，缺了补丁会被禁用。

    tModLoader 的判定（client.log 原文）：

        The .hjson file "...\\WastelandSoulCN\\Localization/zh-Hans_Mods.WastelandSoul.hjson"
        was detected as a localization file but doesn't match the filename of any of the
        English template files. The file will be renamed to "...hjson.legacy" and its contents
        will not be loaded.

    也就是说：一个 `<culture>_<prefix>.hjson` **只有在同一目录下存在 `en-US_<prefix>.hjson`
    时才会被加载**。缺模板的后果是双重的：
      1. 中文根本不会被读取（静默——游戏里就是英文）；
      2. tML 会把中文文件改名成 `.legacy`，而**下一次加载**再改名时目标已存在，
         抛 `IOException: 当文件已存在时，无法创建该文件` → 补丁和主模组一起被自动禁用。

    所以每次同步都从主模组的 en-US 复制一份过去（内容一致 → 对英文玩家无害，
    而且永远不会过期）。
    """
    template = os.path.join(CN_LOC, "en-US_Mods.%s.hjson" % target)
    shutil.copyfile(en_path, template)
    print("已刷新英文模板 %s（%d 字节，与主模组 en-US 一致）"
          % (template, os.path.getsize(template)))
    return template


if __name__ == "__main__":
    sys.exit(main())
