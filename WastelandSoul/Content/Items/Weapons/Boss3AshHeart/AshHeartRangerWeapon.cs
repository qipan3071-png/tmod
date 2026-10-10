using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Items.Materials;
using WastelandSoul.Content.Items.Weapons;

namespace WastelandSoul.Content.Items.Weapons.Boss3AshHeart
{
	/// <summary>
	/// 灰烬之心 · A 线步枪。对标金星马格南：连射、打真正的子弹。
	/// </summary>
	public class AshHeartRangerWeapon : WastelandClassWeapon
	{
		protected override DamageClass Class => DamageClass.Ranged;
		protected override int Damage => 50;
		protected override int UseTime => 9;
		protected override float Knockback => 4.0f;
		protected override int Rarity => WastelandRarityTiers.MidLate;

		protected override int ShootType => ProjectileID.Bullet;

		protected override float ShootSpeed => 13.5f;

		public override void SetDefaults()
		{
			base.SetDefaults();
			WastelandWeaponKit.Ranged(Item);
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			return WastelandShoot.EvenFan(source, position, velocity, type, (int)(damage * 0.55f), knockback, player.whoAmI, 3, 0.22f);
		}

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient<AshHeartAlloyBar>(10)
				.AddIngredient(ItemID.ChlorophyteBar, 12)
				.AddIngredient(ItemID.HallowedBar, 8)
				.AddIngredient(ItemID.Ectoplasm, 6)
				.AddTile(WastelandCraftingStations.HardmodeAnvil)
				.Register();
		}
	}
}
