using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Buffs;
using WastelandSoul.Content.Subworlds;

namespace WastelandSoul.Content.Items.Accessories
{
	/// <summary>
	/// **防毒面具**：戴着它进壁炉世界就不会被有害气体侵蚀（<see cref="GasPoison"/>）。
	///
	/// <para/>=== 配方为什么在这一轮改掉了（材料链死循环）===
	/// 旧配方是 <c>精钢锭 ×5 + 玻璃 ×3 @ 铁砧</c>，而**精钢只能由精钢碎块熔出来，
	/// 精钢碎块只有子世界里的清道夫（Boss 1）掉**。也就是说：
	/// 「要进壁炉 → 必须有面罩 → 面罩要清道夫掉的精钢 → 而清道夫在壁炉里」——
	/// 玩家永远拿不到第一副面罩，那条"提示你去壁炉"的引导会直接死在门口。
	///
	/// <para/>所以改成**进子世界之前就能凑齐**的旧时代劳保件（全部在主世界可获取，无需任何 Boss）：
	/// <code>
	/// 丝绸 ×6（蛛网织，织布机 / 工作台）
	/// 皮革 ×3（地表与洞穴的普通怪掉落）
	/// 玻璃 ×3（沙 → 熔炉）
	/// 铁锭或铅锭 ×8（铁矿 / 铅矿 → 熔炉）
	/// 合成站：铁砧 / 铅砧
	/// </code>
	/// 材料量刻意压在"早期挖一趟矿 + 打几只怪"的量级：它是**主线卡点**，
	/// 不应该变成第二个刷子。铁/铅用原版 <see cref="RecipeGroup.IronBar"/> 组，
	/// 所以两种矿脉的世界都做得出来。
	///
	/// <para/>⚠️ 制作方法**只写在智械人的对话里**（<c>Dialogue.MechanicalCompanion.MaskRecipe</c>），
	/// 不写进 <c>Tooltip</c> —— 检查器 <c>check_tooltip_no_crafting</c> 明确不许介绍里出现工作台。
	/// </summary>
	public class GasMask : WastelandAccessory
	{
		protected override int Rarity => WastelandRarityTiers.Early;

		protected override int SellPrice => Item.sellPrice(gold: 1);

		protected override void UpdateWastelandAccessory(Player player, bool hideVisual)
		{
			FireplaceAtmospherePlayer atmosphere = player.GetModPlayer<FireplaceAtmospherePlayer>();
			atmosphere.gasMaskEquipped = true;
			atmosphere.anyFilterMaskEquipped = true;
		}

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient(ItemID.Silk, 6)
				.AddIngredient(ItemID.Leather, 3)
				.AddIngredient(ItemID.Glass, 3)
				.AddRecipeGroup(RecipeGroupID.IronBar, 8)
				.AddTile(TileID.Anvils)
				.Register();
		}
	}
}
