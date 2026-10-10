using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Items.Materials;
using WastelandSoul.Content.Items.Weapons;

namespace WastelandSoul.Content.Items.Weapons.Boss2Archivist
{
	/// <summary>
	/// 归档者 · A 线霰弹枪。对标原版霰弹枪：一次打出多发真正的子弹。
	/// </summary>
	public class ArchivistRangerWeapon : WastelandClassWeapon
	{
		protected override DamageClass Class => DamageClass.Ranged;
		protected override int Damage => 22;
		protected override int UseTime => 42;
		protected override float Knockback => 6.5f;
		protected override int Rarity => WastelandRarityTiers.EarlyLate;

		protected override int ShootType => ProjectileID.Bullet;

		protected override float ShootSpeed => 7f;

		public override void SetDefaults()
		{
			base.SetDefaults();
			WastelandWeaponKit.Ranged(Item);
			Item.UseSound = SoundID.Item36;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			for (int i = 0; i < 4; i++) {
				Vector2 spread = velocity.RotatedByRandom(MathHelper.ToRadians(15f));
				spread *= Main.rand.NextFloat(0.9f, 1.1f);
				Projectile.NewProjectile(source, position, spread, type, damage, knockback, player.whoAmI);
			}

			return false;
		}

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient<ArchivistFragment>(9)
				.AddIngredient(ItemID.MeteoriteBar, 12)
				.AddIngredient(ItemID.Bone, 10)
				.AddTile(WastelandCraftingStations.EarlyAnvil)
				.Register();
		}
	}
}
