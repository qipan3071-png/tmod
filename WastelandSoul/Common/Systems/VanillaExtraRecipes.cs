using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace WastelandSoul.Common.Systems
{
	/// <summary>
	/// 原版「只能获得、不能合成」的道具：在<strong>本模组</strong>里追加合成路径。
	/// <para/>玩家 2026-10-10：会陆续给大多数这类原版道具加配方，一律遵守下面口径。
	/// </summary>
	/// <remarks>
	/// 要做：只 <see cref="Recipe.Create"/> 多一条；材料/工作台以玩家点名为准；全写在本文件。
	/// 不做：改原版掉落/箱子/提炼表/生成；删或替换原版已有配方；把合成写进 Tooltip（<c>check_tooltip_no_crafting</c>）；
	/// 没点名就猜铁/铅双矿、没点名就改工作台。
	/// </remarks>
	public class VanillaExtraRecipes : ModSystem
	{
		public override void AddRecipes()
		{
			// 提炼机：原版地下小屋才刷。5 铅锭 + 20 泥沙块 @ 重型工作台。
			Recipe.Create(ItemID.Extractinator)
				.AddIngredient(ItemID.LeadBar, 5)
				.AddIngredient(ItemID.SiltBlock, 20)
				.AddTile(TileID.HeavyWorkBench)
				.Register();
		}
	}
}
