using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Items.Materials;
using WastelandSoul.Content.Items.Weapons;
using WastelandSoul.Content.Projectiles.Scavenger;

namespace WastelandSoul.Content.Items.Weapons.Boss4Fireplace
{
	/// <summary>
	/// Fireplace Guardian Greatblade MK-II（壁炉守卫 · B 线 · 专属掉落）
	/// <para/>与 A 线同一套新月刃，伤害和挥速更高。
	/// </summary>
	public class FireplaceWarriorWeaponEx : WastelandClassWeapon
	{
		protected override DamageClass Class => DamageClass.Melee;
		protected override int Damage => 112;
		protected override int UseTime => 20;
		protected override float Knockback => 8.0f;
		protected override int Rarity => WastelandRarityTiers.Late;

		protected override int ShootType => ProjectileID.SwordBeam;

		protected override float ShootSpeed => 13.0f;

		public override void SetDefaults()
		{
			base.SetDefaults();
			WastelandWeaponKit.Melee(Item);
		}

		public override void OnHitNPC(Player player, NPC target, NPC.HitInfo hit, int damageDone)
		{
			WastelandShoot.HitBuff(target, BuffID.Frostburn, 240);
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			return ScavengerBeam.ShootFan(source, position, velocity, damage, knockback, player.whoAmI);
		}

		// B 线为专属掉落：**不写任何 AddRecipes()**，只能从壁炉守卫的掉落袋开出。
	}
}
