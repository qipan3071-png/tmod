using Terraria.ID;
using WastelandSoul.Common.Bosses;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Items.Materials;

namespace WastelandSoul.Content.Items.Summons
{
	// ====================================================================================
	// 召唤物扩充（3 个）。全部派生自 WastelandSummonItem：
	//   * 使用后**不消耗**；
	//   * 同一时间只允许存在一只对应的 Boss（基类统一判定并给出提示）；
	//   * 生成点在玩家斜上方 520~760 距离处。
	// 指向的 Boss 都用 WastelandBossRegistry.ResolveNpcType("代号") 解析，
	// 这样 Boss 本体没做/没启用的时候不会编译失败，而是给玩家一句提示。
	// ⚠️ 物品介绍里不许写制作方法。
	// ====================================================================================

	/// <summary>
	/// 猎杀信标：把清道夫的"清除程序"重新点亮一次，它会顺着信标找过来。
	/// <para/>定位：Boss 1（<c>Scavenger</c>）的**早期可重复召唤物**——
	/// 原版的入侵周期是 5 天一次，等不起的玩家可以用这个直接开。
	/// </summary>
	public class ScavengerBeacon : WastelandSummonItem
	{
		protected override int BossType => WastelandBossRegistry.ResolveNpcType("Scavenger");

		protected override float SpawnHeight => -320f;

		public override void AddRecipes()
		{
			// 档位：清道夫 = 骷髅王之后、血肉墙之前。骨头（骷髅王 / 地牢）是这道门槛。
			CreateRecipe()
				.AddIngredient<RustedGear>(8)
				.AddIngredient<CircuitBoard>(3)
				.AddIngredient(ItemID.Bone, 8)
				.AddIngredient(ItemID.DemoniteBar, 5)
				.AddTile(WastelandCraftingStations.SummonAltar)
				.Register();

			// 猩红世界用猩红矿，走同一条配方
			CreateRecipe()
				.AddIngredient<RustedGear>(8)
				.AddIngredient<CircuitBoard>(3)
				.AddIngredient(ItemID.Bone, 8)
				.AddIngredient(ItemID.CrimtaneBar, 5)
				.AddTile(WastelandCraftingStations.SummonAltar)
				.Register();
		}
	}

	/// <summary>
	/// 审计申请单：一张填好的、要求"复核原型机记忆"的申请书。
	/// <para/>定位：Boss 2（<c>Archivist</c>）的**替代召唤路径**，
	/// 比原来的「归档者回响」便宜一点，但需要旧世界电路板（要打过索引蛾）。
	/// <para/>档位：归档者已定档到困难模式机械三王一级，所以两条召唤路径都要求
	/// 困难模式材料（光明/暗影之魂 + 水晶碎块）。
	/// </summary>
	public class AuditRequest : WastelandSummonItem
	{
		protected override int BossType => WastelandBossRegistry.ResolveNpcType("Archivist");

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient<ArchivistFragment>(6)
				.AddIngredient<CircuitBoard>(4)
				.AddIngredient(ItemID.Book, 2)
				.AddIngredient(ItemID.Bone, 8)
				.AddIngredient(ItemID.SoulofLight, 3)
				.AddIngredient(ItemID.CrystalShard, 5)
				.AddTile(WastelandCraftingStations.SummonAltar)
				.Register();
		}
	}

	/// <summary>
	/// 余烬引信：一根还在阴燃的引信，插进灰里就能把灰烬之心重新叫醒。
	/// <para/>定位：Boss 3（<c>AshHeart</c>）的**替代召唤路径**，
	/// 材料偏消耗品（焦炭 + 灰烬结晶），适合刷材料时反复用。
	/// <para/>档位：灰烬之心已定档到石巨人之后，所以原版材料换成**甲壳质**（石巨人掉落）
	/// 与**灵质**（地牢幽魂，世纪之花后），不再是肉山前的狱石锭 / 暗影之魂。
	/// </summary>
	public class EmberFuse : WastelandSummonItem
	{
		protected override int BossType => WastelandBossRegistry.ResolveNpcType("AshHeart");

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient<AshCrystal>(6)
				.AddIngredient<Coke>(10)
				.AddIngredient(ItemID.BeetleHusk, 3)
				.AddIngredient(ItemID.Ectoplasm, 2)
				.AddTile(WastelandCraftingStations.SummonAltar)
				.Register();
		}
	}
}
