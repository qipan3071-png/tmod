using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace WastelandSoul.Common.Systems
{
	/// <summary>
	/// 给原版物品追加本模组合成路径。不改原版掉落/生成，只 <see cref="Recipe.Create"/> 多一条配方。
	/// </summary>
	public class VanillaExtraRecipes : ModSystem
	{
		public override void AddRecipes()
		{
			// 提炼机：原版地下小屋才刷，这里加一条早期可做的路。
			Recipe.Create(ItemID.Extractinator)
				.AddIngredient(ItemID.LeadBar, 5)
				.AddIngredient(ItemID.SiltBlock, 20)
				.AddTile(TileID.HeavyWorkBench)
				.Register();
		}
	}
}
