using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Items.Weapons;
using WastelandSoul.Content.Projectiles.Scavenger;

namespace WastelandSoul.Content.Items.Weapons.Boss1Scavenger.ScavengerDrops
{
	/// <summary>
	/// 污染炮（射手 · Boss 1 清道夫掉落）。
	/// <para/>弹药是**凝胶 <see cref="AmmoID.Gel"/>**：把整块凝胶当推进剂压出去，慢、重、带溅射。
	/// 炮弹 <see cref="PollutionShell"/> 的行为与贴图都复用原版**手榴弹
	/// <see cref="ProjectileID.Grenade"/>**（抛物线 + 自爆），
	/// 只在它消失时补一小片**污染云**（<c>PollutionCloud</c>，贴图复用原版
	/// <see cref="ProjectileID.ToxicCloud"/>，手绘烟雾、不新增 PNG），
	/// 云挂既有的「污染」减益并持续伤害。范围很小，不做全屏特效。
	/// </summary>
	public class PollutionCannon : ModItem
	{
		public override void SetDefaults()
		{
			Item.width = 48;
			Item.height = 48;
			Item.damage = 48;
			Item.DamageType = DamageClass.Ranged;
			Item.knockBack = 6f;
			Item.useTime = 44;               // 炮：慢
			Item.useAnimation = 44;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.noMelee = true;
			Item.autoReuse = true;
			Item.useAmmo = AmmoID.Gel;       // 弹药 = 凝胶
			Item.shoot = ModContent.ProjectileType<PollutionShell>();
			Item.shootSpeed = 9.5f;
			Item.crit = 5;                   // 初始暴击 5%
			Item.UseSound = SoundID.Item11;
			Item.value = Item.sellPrice(gold: 3);
			Item.rare = WastelandRarityTiers.EarlyLate;   // 骷髅王之后档位
		}

		public override Vector2? HoldoutOffset()
		{
			return WastelandHeldVisuals.GunOffset;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			Vector2 muzzle = position + Vector2.Normalize(velocity) * 26f;

			Projectile.NewProjectile(
				source,
				muzzle,
				velocity,
				type,
				damage,
				knockback,
				player.whoAmI,
				0f,
				PollutionShell.Mark);

			return false;
		}
	}
}
