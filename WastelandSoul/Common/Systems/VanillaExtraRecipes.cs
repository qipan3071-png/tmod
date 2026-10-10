using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace WastelandSoul.Common.Systems
{
	/// <summary>
	/// 原版「只能获得、不能合成」的道具：在<strong>本模组</strong>里追加合成路径。
	/// <para/>玩家 2026-10-10：会陆续给大多数这类原版道具加配方，一律遵守下面口径。
	/// </summary>
	/// <remarks>
	/// 要做：只 <see cref="Recipe.Create"/> 多一条；材料/工作台以玩家点名为准；全写在本文件。
	/// 原版双矿/等价组（铁铅、铜锡、金银铂、魔矿猩红、三王矿等）用配方组，一条配方两种都能交。
	/// 不做：改原版掉落/箱子/提炼表/生成（玩家点名的掉落改率除外）；删或替换原版已有配方；把合成写进 Tooltip。
	/// 没点名就改工作台、或把不等价的材料擅自互换。
	/// </remarks>
	public class VanillaExtraRecipes : ModSystem
	{
		public const string GoldBarGroup = "WastelandSoul:GoldBar";
		public const string CobaltBarGroup = "WastelandSoul:CobaltBar";

		public override void AddRecipeGroups()
		{
			RecipeGroup gold = new RecipeGroup(
				() => $"{Language.GetTextValue("LegacyMisc.37")} {Lang.GetItemNameValue(ItemID.GoldBar)}",
				ItemID.GoldBar, ItemID.PlatinumBar);
			RecipeGroup.RegisterGroup(GoldBarGroup, gold);

			RecipeGroup cobalt = new RecipeGroup(
				() => $"{Language.GetTextValue("LegacyMisc.37")} {Lang.GetItemNameValue(ItemID.CobaltBar)}",
				ItemID.CobaltBar, ItemID.PalladiumBar);
			RecipeGroup.RegisterGroup(CobaltBarGroup, cobalt);
		}

		public override void AddRecipes()
		{
			// 提炼机：5 铁/铅锭 + 20 泥沙块 @ 重型工作台。
			Recipe.Create(ItemID.Extractinator)
				.AddRecipeGroup(RecipeGroupID.IronBar, 5)
				.AddIngredient(ItemID.SiltBlock, 20)
				.AddTile(TileID.HeavyWorkBench)
				.Register();

			// 幸运马掌：5 琥珀 + 1 破布 + 3 铁/铅锭 @ 工匠作坊。
			Recipe.Create(ItemID.LuckyHorseshoe)
				.AddIngredient(ItemID.Amber, 5)
				.AddIngredient(ItemID.TatteredCloth, 1)
				.AddRecipeGroup(RecipeGroupID.IronBar, 3)
				.AddTile(TileID.TinkerersWorkbench)
				.Register();

			// 云朵瓶：10 云 + 1 玻璃瓶 + 2 金/铂金锭 + 5 坠落之星 @ 工匠作坊。
			Recipe.Create(ItemID.CloudinaBottle)
				.AddIngredient(ItemID.Cloud, 10)
				.AddIngredient(ItemID.Bottle, 1)
				.AddRecipeGroup(GoldBarGroup, 2)
				.AddIngredient(ItemID.FallenStar, 5)
				.AddTile(TileID.TinkerersWorkbench)
				.Register();

			// 钴护盾：1 钴/钯金锭 @ 秘银砧（含山铜砧）。
			Recipe.Create(ItemID.CobaltShield)
				.AddRecipeGroup(CobaltBarGroup, 1)
				.AddTile(TileID.MythrilAnvil)
				.Register();
		}
	}
}
