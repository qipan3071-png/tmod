using Terraria.ID;
using WastelandSoul.Common.Bosses;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Items.Materials;

namespace WastelandSoul.Content.Items.Summons
{
	/// <summary>
	/// 灰烬之心余烬：在**恶魔祭坛 / 猩红祭坛**用「灰烬之心碎片 + 灵质 + 甲壳质」合成。
	/// <para/>往一簇还在阴燃的余烬里吹一口气——它会顺着旧时代的战争信道找回来。
	/// <para/>档位：灰烬之心是**石巨人之后、拜月教邪教徒之前**，所以原版材料从肉山前的狱石锭
	/// 换成**甲壳质**（石巨人掉落）与更多**灵质**（地牢幽魂，世纪之花后）。
	/// <para/>使用后不消耗；同一时间只允许存在一只（由基类统一处理）。
	/// </summary>
	public class AshHeartEmber : WastelandSummonItem
	{
		protected override int BossType => WastelandBossRegistry.ResolveNpcType("AshHeart");

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient<AshHeartFragment>(10)
				.AddIngredient(ItemID.Ectoplasm, 3)
				.AddIngredient(ItemID.BeetleHusk, 5)
				.AddTile(WastelandCraftingStations.SummonAltar)
				.Register();
		}
	}
}
