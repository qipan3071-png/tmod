using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Common.Systems;
using WastelandSoul.Content.Items.Materials;
using WastelandSoul.Content.Items.Weapons;

namespace WastelandSoul.Content.Items.Weapons.Boss1Scavenger
{
	/// <summary>
	/// 清道夫 · A 线手枪。对标原版手枪 / 夺命枪：打真正的子弹，10% 再出一发偏弹。
	/// </summary>
	public class ScavengerRangerWeapon : WastelandClassWeapon
	{
		protected override DamageClass Class => DamageClass.Ranged;
		protected override int Damage => 24;
		protected override int UseTime => 16;
		protected override float Knockback => 3.0f;
		protected override int Rarity => WastelandRarityTiers.Early;

		protected override int ShootType => ProjectileID.Bullet;

		protected override float ShootSpeed => 10f;

		public override void SetDefaults()
		{
			base.SetDefaults();
			WastelandWeaponKit.Ranged(Item);
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			Projectile.NewProjectile(source, position, velocity, type, damage, knockback, player.whoAmI);

			if (WastelandRandom.Roll(player.whoAmI, player.itemAnimation, 0, 0, 10) == 0) {
				Vector2 extra = velocity.RotatedBy(MathHelper.ToRadians(8f));
				Projectile.NewProjectile(source, position, extra, type, (int)(damage * 0.6f), knockback, player.whoAmI);
			}

			return false;
		}

		public override void AddRecipes()
		{
			// 分支 1：ScavengerScrap / IronBar / Gel / Wood
			CreateRecipe()
				.AddIngredient<SalvagedSteelChunk>(12)
				.AddIngredient(ItemID.IronBar, 14)
				.AddIngredient(ItemID.Gel, 6)
				.AddIngredient(ItemID.Wood, 14)
				.AddTile(WastelandCraftingStations.EarlyAnvil)
				.Register();

			// 分支 2：ScavengerScrap / LeadBar / Gel / Wood
			CreateRecipe()
				.AddIngredient<SalvagedSteelChunk>(12)
				.AddIngredient(ItemID.LeadBar, 14)
				.AddIngredient(ItemID.Gel, 6)
				.AddIngredient(ItemID.Wood, 14)
				.AddTile(WastelandCraftingStations.EarlyAnvil)
				.Register();
		}
	}
}
