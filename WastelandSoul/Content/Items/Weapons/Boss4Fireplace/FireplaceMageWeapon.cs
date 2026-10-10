using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Items.Materials;
using WastelandSoul.Content.Items.Weapons;
using WastelandSoul.Content.Projectiles.Fireplace;

namespace WastelandSoul.Content.Items.Weapons.Boss4Fireplace
{
	/// <summary>
	/// Fireplace Guardian Scepter（壁炉守卫 · A 线 · 可合成）
	/// <para/>按住持续从杖尖打冷光弹（holdout 骨架）。命中缓慢。
	/// <para/>制作站点：秘银砧（血肉墙之后装备站点）
	/// </summary>
	public class FireplaceMageWeapon : WastelandClassWeapon
	{
		protected override DamageClass Class => DamageClass.Magic;
		protected override int Damage => 74;
		protected override int UseTime => 18;
		protected override float Knockback => 5.0f;
		protected override int Rarity => WastelandRarityTiers.Late;

		protected override int ShootType => ModContent.ProjectileType<FireplaceMageHoldout>();

		protected override float ShootSpeed => 10.0f;

		public override void SetDefaults()
		{
			base.SetDefaults();
			WastelandWeaponKit.Magic(Item, 18);
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

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient<FireplaceAlloyBar>(12)
				.AddIngredient(ItemID.ChlorophyteBar, 10)
				.AddIngredient(ItemID.Ectoplasm, 14)
				.AddIngredient(ItemID.HallowedBar, 8)
				.AddTile(WastelandCraftingStations.HardmodeAnvil)
				.Register();
		}
	}
}
