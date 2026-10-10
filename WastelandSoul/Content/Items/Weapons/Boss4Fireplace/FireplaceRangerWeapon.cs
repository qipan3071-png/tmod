using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Items.Materials;
using WastelandSoul.Content.Items.Weapons;

namespace WastelandSoul.Content.Items.Weapons.Boss4Fireplace
{
	/// <summary>
	/// 壁炉守卫 · A 线机枪。对标巨兽鲨 / 链式机枪：高速连射真正的子弹，略有散布。
	/// </summary>
	public class FireplaceRangerWeapon : WastelandClassWeapon
	{
		protected override DamageClass Class => DamageClass.Ranged;
		protected override int Damage => 42;
		protected override int UseTime => 6;
		protected override float Knockback => 2.0f;
		protected override int Rarity => WastelandRarityTiers.Late;

		protected override int ShootType => ProjectileID.Bullet;

		protected override float ShootSpeed => 12f;

		public override void SetDefaults()
		{
			base.SetDefaults();
			WastelandWeaponKit.Ranged(Item);
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			Vector2 spread = velocity.RotatedByRandom(MathHelper.ToRadians(5f));
			Projectile.NewProjectile(source, position, spread, type, damage, knockback, player.whoAmI);
			return false;
		}

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient<FireplaceAlloyBar>(12)
				.AddIngredient(ItemID.ChlorophyteBar, 14)
				.AddIngredient(ItemID.HallowedBar, 10)
				.AddIngredient(ItemID.Ectoplasm, 8)
				.AddTile(WastelandCraftingStations.HardmodeAnvil)
				.Register();
		}
	}
}
