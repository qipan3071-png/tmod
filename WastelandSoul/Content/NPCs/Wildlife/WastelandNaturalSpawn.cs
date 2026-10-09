using Terraria;
using Terraria.ModLoader;
using WastelandSoul.Common.Systems;

namespace WastelandSoul.Content.NPCs.Wildlife
{
	/// <summary>
	/// 模组野外怪的刷怪条件：**只走 tModLoader 原版自然刷怪管线**（各 <see cref="ModNPC.SpawnChance"/>），
	/// 这里集中「能不能进池子」的判断，对齐原版在挑 NPC 类型前的常见排除（安全区、事件、地牢等）。
	/// <para/>不另写 <c>NPC.NewNPC</c> 循环、不改全局刷怪率 —— 与 ExampleMod / 原版 ModNPC 文档一致。
	/// </summary>
	public static class WastelandNaturalSpawn
	{
		/// <summary>主世界最小宽度（壁炉等子世界远小于此，不刷野外怪）。</summary>
		public const int MinMainWorldWidth = 1200;

		/// <summary>当前是否为可刷野外怪的主世界。</summary>
		public static bool IsMainWorld => Main.maxTilesX >= MinMainWorldWidth;

		/// <summary>
		/// 模组自然刷怪的前置条件（原版同类排除；子世界、安全区、入侵与月亮事件等）。
		/// </summary>
		public static bool AllowsModNaturalSpawn(NPCSpawnInfo spawnInfo)
		{
			if (!IsMainWorld || !spawnInfo.Player.active || spawnInfo.Player.dead) {
				return false;
			}

			if (spawnInfo.PlayerSafe || spawnInfo.Invasion) {
				return false;
			}

			// 月亮事件期间原版会占满刷怪池，模组地表/洞穴怪不再参与（常见 tML 做法，避免和事件怪抢权重）。
			if (Main.pumpkinMoon || Main.snowMoon || Main.eclipse) {
				return false;
			}

			Player player = spawnInfo.Player;

			if (player.ZoneDungeon || player.ZoneMeteor) {
				return false;
			}

			return true;
		}

		/// <summary>地表（非洞穴/地狱）且允许自然刷怪。</summary>
		public static bool Surface(NPCSpawnInfo spawnInfo)
		{
			return AllowsModNaturalSpawn(spawnInfo) && spawnInfo.Player.ZoneOverworldHeight;
		}

		/// <summary>地下土/石层（含洞穴），不含地狱。</summary>
		public static bool Underground(NPCSpawnInfo spawnInfo)
		{
			if (!AllowsModNaturalSpawn(spawnInfo)) {
				return false;
			}

			Player player = spawnInfo.Player;

			return (player.ZoneDirtLayerHeight || player.ZoneRockLayerHeight) && !player.ZoneUnderworldHeight;
		}

		/// <summary>石层或地狱（灰烬潜行者等后期怪用）。</summary>
		public static bool CavernOrUnderworld(NPCSpawnInfo spawnInfo)
		{
			if (!AllowsModNaturalSpawn(spawnInfo)) {
				return false;
			}

			Player player = spawnInfo.Player;

			return player.ZoneRockLayerHeight || player.ZoneUnderworldHeight;
		}

		// ---------- 剧情分档（批次 10：击败 Boss 前进到下一档野外怪，与 EraMobs 一致）----------

		/// <summary>清道夫时期：尚未击败清道夫。</summary>
		public static bool EraBeforeScavenger => !WastelandStorySystem.scavengerDefeated;

		/// <summary>归档者时期：已击败清道夫、尚未击败归档者。</summary>
		public static bool EraBeforeArchivist =>
			WastelandStorySystem.scavengerDefeated && !WastelandStorySystem.archivistDefeated;

		/// <summary>灰烬之心时期：困难模式且已击败归档者、尚未击败灰烬之心。</summary>
		public static bool EraBeforeAshHeart =>
			Main.hardMode && WastelandStorySystem.archivistDefeated && !WastelandStorySystem.ashHeartDefeated;

		/// <summary>壁炉守卫时期：困难模式、已击败灰烬之心、尚未击败壁炉守卫。</summary>
		public static bool EraBeforeFireplaceGuardian =>
			Main.hardMode && WastelandStorySystem.ashHeartDefeated && !WastelandStorySystem.fireplaceGuardianDefeated;
	}
}
