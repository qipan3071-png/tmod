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
	/// 精钢放电器（法师 · Boss 1 清道夫掉落）。
	/// <para/>参照物：原版**充能爆破加农炮 <see cref="ItemID.ChargedBlasterCannon"/>** 与
	/// **雷暴法杖 <see cref="ItemID.ThunderStaff"/>**（编号见类内注释）——
	/// 按住蓄力、松手放招，弹幕是「先打到最近的敌人，再跳到附近敌人」的链状闪电。
	/// 这里只借用它们的**行为模型**，贴图复用原版
	/// <see cref="ProjectileID.ChargedBlasterOrb"/> 与 <see cref="ProjectileID.ThunderStaffShot"/>，
	/// 不新增任何 PNG。
	/// <para/>蓄力越久跳数越多（2 → 4 跳），每跳伤害递减，命中挂「带电」与「缓慢」。
	/// 特效只写在本武器自己的弹幕里（<c>SteelDischargerHoldout</c> / <c>SteelChainLightning</c>），
	/// 不做任何全局自动特效。
	/// </summary>
	public class SteelDischarger : ModItem
	{
		public override void SetDefaults()
		{
			Item.width = 48;
			Item.height = 48;
			Item.damage = 34;
			Item.DamageType = DamageClass.Magic;
			Item.knockBack = 3.5f;
			Item.mana = 12;
			Item.useTime = 60;
			Item.useAnimation = 60;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.noMelee = true;
			Item.autoReuse = true;
			Item.channel = true;            // 按住蓄力、松手放电
			Item.shoot = ModContent.ProjectileType<SteelDischargerHoldout>();
			Item.shootSpeed = 12f;
			Item.crit = 5;                  // 初始暴击 5%
			Item.UseSound = SoundID.Item20;
			Item.value = Item.sellPrice(gold: 3);
			Item.rare = WastelandRarityTiers.EarlyLate;   // 骷髅王之后档位
		}

		public override bool CanUseItem(Player player)
		{
			// 没蓝就按不动（不然蓄力到一半断线没有任何反馈）
			return player.statMana >= Item.mana;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			// 蓄力本体是一个悬浮弹幕（贴图用原版 ChargedBlasterOrb），松手时才由它放链状闪电
			Projectile.NewProjectile(
				source,
				player.MountedCenter,
				velocity,
				type,
				damage,
				knockback,
				player.whoAmI,
				0f,
				0f);

			return false;
		}
	}
}
