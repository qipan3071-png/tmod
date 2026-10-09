using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.Systems;

namespace WastelandSoul.Content.NPCs.Wildlife
{
	// 批次 57：只锁【生成窗口】。名字/AI/贴图/掉落都是占位，玩家定设定后再补。
	// 不改 EraMobs / Wildlife* 既有 SpawnChance。原版小怪不动。

	/// <summary>占位槽：清道夫后 · 肉前 · 白天地表。设定待补。</summary>
	public class RelayBeetle : EraMob
	{
		protected override int ChipMin => 1;
		protected override int ChipMax => 2;

		protected override int[] RareWeapons => System.Array.Empty<int>();

		public override void SetDefaults()
		{
			NPC.width = 40;
			NPC.height = 30;
			NPC.damage = 20;
			NPC.defense = 6;
			NPC.lifeMax = 95;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = 55f;
			NPC.knockBackResist = 0.55f;
			NPC.aiStyle = 3;
			AIType = NPCID.Zombie;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo)
		{
			if (!OutsideSubworld(spawnInfo) || !WastelandStorySystem.scavengerDefeated || Main.hardMode) {
				return 0f;
			}

			if (!Main.dayTime || !spawnInfo.Player.ZoneOverworldHeight) {
				return 0f;
			}

			return 0.045f;
		}
	}

	/// <summary>占位槽：清道夫后 · 肉前 · 夜晚地表。设定待补。</summary>
	public class NightGnawer : EraMob
	{
		protected override int ChipMin => 1;
		protected override int ChipMax => 2;

		protected override int[] RareWeapons => System.Array.Empty<int>();

		public override void SetDefaults()
		{
			NPC.width = 40;
			NPC.height = 30;
			NPC.damage = 22;
			NPC.defense = 7;
			NPC.lifeMax = 110;
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			NPC.value = 65f;
			NPC.knockBackResist = 0.5f;
			NPC.aiStyle = 3;
			AIType = NPCID.Zombie;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo)
		{
			if (!OutsideSubworld(spawnInfo) || !WastelandStorySystem.scavengerDefeated || Main.hardMode) {
				return 0f;
			}

			if (Main.dayTime || !spawnInfo.Player.ZoneOverworldHeight) {
				return 0f;
			}

			return 0.05f;
		}
	}

	/// <summary>占位槽：归档者后 · 地表。设定待补。</summary>
	public class LedgerHawk : EraMob
	{
		protected override int ChipMin => 1;
		protected override int ChipMax => 3;

		protected override int[] RareWeapons => System.Array.Empty<int>();

		public override void SetDefaults()
		{
			NPC.width = 36;
			NPC.height = 36;
			NPC.damage = 36;
			NPC.defense = 12;
			NPC.lifeMax = 200;
			NPC.HitSound = SoundID.NPCHit1;
			NPC.DeathSound = SoundID.NPCDeath1;
			NPC.value = 120f;
			NPC.knockBackResist = 0.45f;
			NPC.noGravity = true;
			NPC.aiStyle = 2;
			AIType = NPCID.DemonEye;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo)
		{
			if (!OutsideSubworld(spawnInfo) || !WastelandStorySystem.archivistDefeated) {
				return 0f;
			}

			if (!spawnInfo.Player.ZoneOverworldHeight) {
				return 0f;
			}

			return 0.045f;
		}
	}

	/// <summary>占位槽：灰烬之心后 · 泥土/岩石层。设定待补。</summary>
	public class CinderLurker : EraMob
	{
		protected override int ChipMin => 2;
		protected override int ChipMax => 4;

		protected override int[] RareWeapons => System.Array.Empty<int>();

		public override void SetDefaults()
		{
			NPC.width = 36;
			NPC.height = 36;
			NPC.damage = 52;
			NPC.defense = 20;
			NPC.lifeMax = 420;
			NPC.HitSound = SoundID.NPCHit2;
			NPC.DeathSound = SoundID.NPCDeath1;
			NPC.value = 240f;
			NPC.knockBackResist = 0.3f;
			NPC.noGravity = true;
			NPC.aiStyle = 14;
			AIType = NPCID.CaveBat;
			NPC.lavaImmune = true;
		}

		public override float SpawnChance(NPCSpawnInfo spawnInfo)
		{
			if (!OutsideSubworld(spawnInfo) || !WastelandStorySystem.ashHeartDefeated) {
				return 0f;
			}

			if (!spawnInfo.Player.ZoneDirtLayerHeight && !spawnInfo.Player.ZoneRockLayerHeight) {
				return 0f;
			}

			return 0.04f;
		}
	}
}
