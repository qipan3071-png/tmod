using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Items.Materials;
using WastelandSoul.Content.Items.Weapons;
using WastelandSoul.Content.Projectiles.Fireplace;

namespace WastelandSoul.Content.Items.Weapons.Boss4Fireplace
{
	/// <summary>
	/// Fireplace Guardian Scepter MK-II（壁炉守卫 · B 线 · 专属掉落）
	/// <para/>同一套 holdout，打的是更大的冷光弹。
	/// </summary>
	public class FireplaceMageWeaponEx : WastelandClassWeapon
	{
		protected override DamageClass Class => DamageClass.Magic;
		protected override int Damage => 92;
		protected override int UseTime => 16;
		protected override float Knockback => 5.5f;
		protected override int Rarity => WastelandRarityTiers.Late;

		protected override int ShootType => ModContent.ProjectileType<FireplaceMageHoldout>();

		protected override float ShootSpeed => 11.0f;

		public override void SetDefaults()
		{
			base.SetDefaults();
			WastelandWeaponKit.Magic(Item, 20);
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

		// B 线为专属掉落：**不写任何 AddRecipes()**，只能从壁炉守卫的掉落袋开出。
	}
}
