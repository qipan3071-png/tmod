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
	/// Archivist Index Tome（归档者 · A 线 · 可合成）
	/// <para/>左键单页弹墙；右键一次扇出三页（灾厄 AltFunctionUse 那种结构）。
	/// <para/>制作站点：铁砧（前期装备站点）
	/// </summary>
	public class ArchivistMageWeapon : WastelandClassWeapon
	{
		private const int LeftMana = 9;

		private const int RightMana = 16;

		protected override DamageClass Class => DamageClass.Magic;
		protected override int Damage => 21;
		protected override int UseTime => 17;
		protected override float Knockback => 4.5f;
		protected override int Rarity => WastelandRarityTiers.EarlyLate;

		protected override int ShootType => ModContent.ProjectileType<Content.Projectiles.Archivist.ArchivistIndexPage>();

		protected override float ShootSpeed => 8.0f;

		public override void SetDefaults()
		{
			base.SetDefaults();
			WastelandWeaponKit.Magic(Item, LeftMana);
		}

		public override bool AltFunctionUse(Player player)
		{
			return true;
		}

		public override bool CanUseItem(Player player)
		{
			if (player.altFunctionUse == 2) {
				Item.mana = RightMana;
				Item.useTime = 28;
				Item.useAnimation = 28;
			}
			else {
				Item.mana = LeftMana;
				Item.useTime = 17;
				Item.useAnimation = 17;
			}

			return true;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			if (player.altFunctionUse == 2) {
				return WastelandShoot.EvenFan(source, position, velocity, type, (int)(damage * 0.72f), knockback, player.whoAmI, 3, 0.42f);
			}

			return true;
		}

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient<ArchivistFragment>(10)
				.AddIngredient(ItemID.MeteoriteBar, 12)
				.AddIngredient(ItemID.Bone, 12)
				.AddTile(WastelandCraftingStations.EarlyAnvil)
				.Register();
		}
	}
}
