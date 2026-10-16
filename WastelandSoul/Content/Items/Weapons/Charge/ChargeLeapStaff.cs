using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Items.Weapons;
using WastelandSoul.Content.Items.Weapons.Boss1Scavenger.ScavengerDrops;
using WastelandSoul.Content.Items.Weapons.CLine;
using WastelandSoul.Content.Items.Weapons.Rust;
using WastelandSoul.Content.Projectiles.Charge;

namespace WastelandSoul.Content.Items.Weapons.Charge
{
	/// <summary>
	/// 电荷跃动。材料停在前期后段：锈蚀电光棒、精钢放电器（单发电弧 34）、废料火花，
	/// 再加光明之魂和暗影之魂。这一档在模组里是浅红，低于灰烬之心的 62。
	/// 先按这个时期填一版：伤害 36、使用 28、耗蓝 10。球会留下辐射，所以射得比电弧杖慢。
	/// </summary>
	public class ChargeLeapStaff : WastelandClassWeapon
	{
		protected override DamageClass Class => DamageClass.Magic;
		protected override int Damage => 36;
		protected override int UseTime => 28;
		protected override float Knockback => 3.5f;
		protected override int Rarity => WastelandRarityTiers.EarlyLate;
		protected override int SellPrice => Item.sellPrice(gold: 4);
		protected override int ShootType => ModContent.ProjectileType<ChargeLeapOrb>();
		protected override float ShootSpeed => 5.5f;

		public override void SetDefaults()
		{
			base.SetDefaults();
			WastelandWeaponKit.Magic(Item, 10);
			Item.width = 48;
			Item.height = 48;
			Item.UseSound = SoundID.Item122;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			float charge = player.GetModPlayer<ChargeLeapPlayer>().TakeCharge();

			Projectile.NewProjectile(source, position, velocity, type, damage, knockback, player.whoAmI, charge);
			return false;
		}

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient<RustBoltWand>()
				.AddIngredient<SteelDischarger>()
				.AddIngredient<ScavengerCMage>()
				.AddIngredient(ItemID.SoulofNight, 8)
				.AddIngredient(ItemID.SoulofLight, 8)
				.AddTile(WastelandCraftingStations.EarlyAnvil)
				.Register();
		}
	}

	/// <summary>每个玩家自己交替正负电。只在本人施法时翻转，不参与联机掷骰。</summary>
	public class ChargeLeapPlayer : ModPlayer
	{
		private bool _positive = true;

		public float TakeCharge()
		{
			float charge = _positive ? 1f : -1f;

			_positive = !_positive;
			return charge;
		}
	}
}
