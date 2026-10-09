using Terraria;
using Terraria.ModLoader;

namespace WastelandSoul.Content.NPCs.Wildlife
{
	/// <summary>
	/// **仅模组小怪**的自然刷怪辅助（<see cref="ModNPC.SpawnChance"/>）。
	/// <para/><b>原版小怪完全不动</b>：本模组没有 <c>GlobalNPC.EditSpawnRate</c>、没有改原版 NPC 表、
	/// 没有自写刷怪循环；只是在 tML 挑类型时<strong>多几个我们自己的候选</strong>，与僵尸/骷髅等并存。
	/// <para/>写法与 tModLoader 文档 / ExampleMod 一致：每个 <see cref="ModNPC"/> 重写
	/// <c>SpawnChance</c> 返回权重，引擎仍按原版规则掷点、上限、安全区。
	/// </summary>
	public static class WastelandNaturalSpawn
	{
		/// <summary>主世界最小宽度（壁炉子世界等小地图不刷野外模组怪）。</summary>
		public const int MinMainWorldWidth = 1200;

		/// <summary>
		/// 模组怪共用的最低门槛（与改批次 56 之前 <see cref="WildlifeAI.OutsideSubworld"/> 相同，不额外排除原版生态）。
		/// </summary>
		public static bool AllowsModNaturalSpawn(NPCSpawnInfo spawnInfo)
		{
			return Main.maxTilesX >= MinMainWorldWidth && !spawnInfo.PlayerSafe && spawnInfo.Player.active;
		}
	}
}
