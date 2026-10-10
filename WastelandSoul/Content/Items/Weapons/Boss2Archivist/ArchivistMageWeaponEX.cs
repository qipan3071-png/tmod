using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Items.Materials;
using WastelandSoul.Content.Items.Weapons;
using WastelandSoul.Content.Projectiles.Archivist;

namespace WastelandSoul.Content.Items.Weapons.Boss2Archivist
{
	/// <summary>
	/// Archivist Index Tome MK-II（归档者 · B 线 · 专属掉落）
	/// <para/>按住读条打索引页（holdout）。不做白激光。
	/// </summary>
	public class ArchivistMageWeaponEX : WastelandClassWeapon
	{
		protected override DamageClass Class => DamageClass.Magic;
		protected override int Damage => 30;
		protected override int UseTime => 22;
		protected override float Knockback => 2.0f;
		protected override int Rarity => WastelandRarityTiers.EarlyLate;

		protected override int ShootType => ModContent.ProjectileType<ArchivistIndexHoldout>();

		protected override float ShootSpeed => 16.0f;

		public override void SetDefaults()
		{
			base.SetDefaults();
			WastelandWeaponKit.Magic(Item, 12);
			WastelandWeaponKit.ChannelHoldout(Item);
		}

		public override bool CanUseItem(Player player)
		{
			return player.ownedProjectileCounts[Item.shoot] <= 0;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			return WastelandShoot.SpawnHoldout(source, position, velocity, type, damage, knockback, player);
		}

		// B 线为专属掉落：**不写任何 AddRecipes()**，只能从归档者的掉落袋开出。
	}
}
