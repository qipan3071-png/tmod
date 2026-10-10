using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Projectiles.Fireplace;

namespace WastelandSoul.Content.Items.Weapons.Boss1Scavenger.ScavengerDrops
{
	/// <summary>
	/// 清道夫大刀（战士 · Boss 1 清道夫掉落）。
	/// <para/>宽刃、挥砍偏慢。远程板块与壁炉守卫大剑对调：挥砍推出一道渐隐冲击波
	/// （原壁炉大剑那发），不再甩新月刃。
	/// </summary>
	public class ScavengerGreatblade : ModItem
	{
		public override void SetDefaults()
		{
			Item.width = 48;
			Item.height = 48;
			Item.damage = 46;
			Item.DamageType = DamageClass.Melee;
			Item.knockBack = 6.5f;
			Item.useTime = 26;
			Item.useAnimation = 26;
			Item.useStyle = ItemUseStyleID.Swing;
			Item.autoReuse = true;
			Item.noMelee = false;
			Item.noUseGraphic = false;
			Item.UseSound = SoundID.Item1;
			Item.shoot = ModContent.ProjectileType<FireplaceWarriorProjectile>();
			Item.shootSpeed = 12f;
			Item.crit = 5;
			Item.value = Item.sellPrice(gold: 3);
			Item.rare = WastelandRarityTiers.EarlyLate;
		}
	}
}
