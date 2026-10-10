using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Items.Materials;
using WastelandSoul.Content.Items.Weapons;

namespace WastelandSoul.Content.Items.Weapons.Rust
{
	// ====================================================================================
	// 「锈蚀」线 · 射手武器（前期 / 铁砧）
	// 全部消耗火枪子弹（AmmoID.Bullet），但**发射自己的弹幕**（在 Shoot 里手动生成并返回 false）。
	// 三把的区别：霰弹（一次 4 颗、散布大）/ 射钉枪（极快、单发低伤、穿透 2）/ 强化霰弹（5 颗、能弹一次墙）
	// ====================================================================================

	/// <summary>
	/// 废料霰弹枪。对标三发猎枪：一次打出多发真正的子弹。
	/// </summary>
	public class ScrapShotgun : WastelandClassWeapon
	{
		protected override DamageClass Class => DamageClass.Ranged;
		protected override int Damage => 14;
		protected override int UseTime => 40;
		protected override float Knockback => 5.75f;
		protected override int Rarity => WastelandRarityTiers.Early;
		protected override int SellPrice => Item.sellPrice(gold: 2);
		protected override int ShootType => ProjectileID.Bullet;
		protected override float ShootSpeed => 5.35f;

		/// <summary>弹丸数量。</summary>
		protected virtual int PelletCount => 4;

		/// <summary>散布角度（度）。</summary>
		protected virtual float SpreadDegrees => 14f;

		public override void SetDefaults()
		{
			base.SetDefaults();
			WastelandWeaponKit.Ranged(Item);
			Item.width = 44;
			Item.height = 18;
			Item.UseSound = SoundID.Item36;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			int shot = ShootType == ProjectileID.Bullet ? type : ShootType;

			for (int i = 0; i < PelletCount; i++) {
				Vector2 spread = velocity.RotatedByRandom(MathHelper.ToRadians(SpreadDegrees));
				Vector2 speed = spread * Main.rand.NextFloat(0.88f, 1.12f);

				Projectile.NewProjectile(source, position, speed, shot, damage, knockback, player.whoAmI);
			}

			return false;
		}

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient(ItemID.IronBar, 14)
				.AddIngredient(ItemID.Wood, 16)
				.AddIngredient(ItemID.Gel, 8)
				.AddIngredient<SalvagedSteelChunk>(6)
				.AddTile(WastelandCraftingStations.EarlyAnvil)
				.Register();

			CreateRecipe()
				.AddIngredient(ItemID.LeadBar, 14)
				.AddIngredient(ItemID.Wood, 16)
				.AddIngredient(ItemID.Gel, 8)
				.AddIngredient<SalvagedSteelChunk>(6)
				.AddTile(WastelandCraftingStations.EarlyAnvil)
				.Register();
		}
	}

	/// <summary>
	/// 锈蚀射钉枪。对标迷你鲨：超快射速、打真正的子弹、半数弹药不消耗。
	/// </summary>
	public class RustNailgun : WastelandClassWeapon
	{
		protected override DamageClass Class => DamageClass.Ranged;
		protected override int Damage => 7;
		protected override int UseTime => 8;
		protected override float Knockback => 0f;
		protected override int Rarity => WastelandRarityTiers.Early;
		protected override int SellPrice => Item.sellPrice(gold: 7);
		protected override int ShootType => ProjectileID.Bullet;
		protected override float ShootSpeed => 7f;

		public override void SetDefaults()
		{
			base.SetDefaults();
			WastelandWeaponKit.Ranged(Item);
			Item.width = 36;
			Item.height = 18;
			Item.UseSound = SoundID.Item11;
		}

		public override bool CanConsumeAmmo(Item ammo, Player player)
		{
			return Main.rand.NextFloat() >= 0.5f;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			Vector2 spread = velocity.RotatedByRandom(MathHelper.ToRadians(6f));

			Projectile.NewProjectile(source, position, spread, type, damage, knockback, player.whoAmI);

			return false;
		}

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient<SalvagedSteelChunk>(10)
				.AddIngredient(ItemID.IronBar, 10)
				.AddIngredient(ItemID.Gel, 10)
				.AddTile(WastelandCraftingStations.EarlyAnvil)
				.Register();

			CreateRecipe()
				.AddIngredient<SalvagedSteelChunk>(10)
				.AddIngredient(ItemID.LeadBar, 10)
				.AddIngredient(ItemID.Gel, 10)
				.AddTile(WastelandCraftingStations.EarlyAnvil)
				.Register();
		}
	}

	/// <summary>
	/// 废料霰弹枪 MK-II。对标原版霰弹枪：5 发散弹、打真正的子弹。
	/// </summary>
	public class ScrapShotgunEX : ScrapShotgun
	{
		protected override int Damage => 18;
		protected override int UseTime => 38;
		protected override float Knockback => 6.5f;
		protected override int SellPrice => Item.sellPrice(gold: 5);
		protected override int ShootType => ProjectileID.Bullet;
		protected override float ShootSpeed => 7f;
		protected override int PelletCount => 5;
		protected override float SpreadDegrees => 12f;

		public override void SetDefaults()
		{
			base.SetDefaults();
			Item.width = 46;
			Item.height = 20;
		}

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient<ScrapShotgun>()
				.AddIngredient<SalvagedSteelBar>(8)
				.AddIngredient(ItemID.Gel, 12)
				.AddTile(WastelandCraftingStations.EarlyAnvil)
				.Register();
		}
	}
}
