using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Items.Materials;
using WastelandSoul.Content.Items.Weapons;

namespace WastelandSoul.Content.Items.Weapons.Scrap
{
	// ====================================================================================
	// 「废铁重工」线 · 射手武器（前期后段 / 铁砧）
	//   ScrapRailgun     一枪一发的高穿透电磁弹（42 伤害、穿透 6、使用时间 44）
	//   ScrapRailgunEX   强化版（继承）：56 伤害、穿透 8、射速更快
	// 两把都消耗火枪子弹（AmmoID.Bullet），但发射自己的弹幕。
	// ====================================================================================

	/// <summary>
	/// 废铁电磁炮。对标火枪：高伤慢速，打真正的子弹。
	/// </summary>
	public class ScrapRailgun : WastelandClassWeapon
	{
		protected override DamageClass Class => DamageClass.Ranged;
		protected override int Damage => 36;
		protected override int UseTime => 32;
		protected override float Knockback => 6f;
		protected override int Rarity => WastelandRarityTiers.EarlyLate;
		protected override int SellPrice => Item.sellPrice(gold: 4);
		protected override int ShootType => ProjectileID.Bullet;
		protected override float ShootSpeed => 12f;

		public override void SetDefaults()
		{
			base.SetDefaults();
			WastelandWeaponKit.Ranged(Item);
			Item.width = 48;
			Item.height = 22;
			Item.UseSound = SoundID.Item40;
			Item.crit = 7;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			Projectile.NewProjectile(source, position, velocity, type, damage, knockback, player.whoAmI);

			return false;
		}

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient<SalvagedSteelBar>(12)
				.AddIngredient<ArchivistFragment>(8)
				.AddIngredient(ItemID.IronBar, 20)
				.AddTile(WastelandCraftingStations.EarlyAnvil)
				.Register();

			CreateRecipe()
				.AddIngredient<SalvagedSteelBar>(12)
				.AddIngredient<ArchivistFragment>(8)
				.AddIngredient(ItemID.LeadBar, 20)
				.AddTile(WastelandCraftingStations.EarlyAnvil)
				.Register();
		}
	}

	/// <summary>
	/// 废铁电磁炮 MK-II。对标火枪强化：更高伤、仍打真正的子弹。
	/// </summary>
	public class ScrapRailgunEX : ScrapRailgun
	{
		protected override int Damage => 44;
		protected override int UseTime => 30;
		protected override float Knockback => 7f;
		protected override int SellPrice => Item.sellPrice(gold: 6);
		protected override int ShootType => ProjectileID.Bullet;
		protected override float ShootSpeed => 14f;

		public override void SetDefaults()
		{
			base.SetDefaults();
			Item.width = 50;
			Item.height = 24;
			Item.crit = 7;
		}

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient<ScrapRailgun>()
				.AddIngredient<SalvagedSteelBar>(14)
				.AddIngredient<ArchivistFragment>(12)
				.AddTile(WastelandCraftingStations.EarlyAnvil)
				.Register();
		}
	}
}
