using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Items.Weapons;
using WastelandSoul.Content.Projectiles.Melee;
using WastelandSoul.Content.Projectiles.Scavenger;

namespace WastelandSoul.Content.Items.Weapons.Boss1Scavenger.ScavengerDrops
{
	/// <summary>
	/// 清道夫大刀（战士 · Boss 1 清道夫掉落）。
	/// <para/>手感对齐原版村正大刀那一档：宽刃、挥砍偏慢、单下重、靠刀光拉开身位。
	/// 挥砍时甩出 5 片月牙刀光（原版 <see cref="ProjectileID.SwordBeam"/>，扇形撒开 → 越远越散），
	/// 每片穿透 4 个敌人；穿透与火花由 <c>ScavengerDropGlobals.cs</c> 的
	/// <c>SwordBeamHook</c> 只对**本武器标记过的**刀光生效。
	/// <para/>标记写在新弹幕的 <c>ai[2]</c>（<see cref="ScavengerBeam.Mark"/>）：
	/// 原版刀光 AI 自己会用 <c>ai[1]</c> 当内部标志，不跟它抢槽位。
	/// </summary>
	public class ScavengerGreatblade : ModItem
	{
		/// <summary>甩出的刀光数量。</summary>
		private const int BeamCount = 5;

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
			Item.UseSound = SoundID.Item1;
			WastelandWeaponKit.EnableSwing(Item, WastelandSwingStyle.Sweep);
			Item.shoot = ProjectileID.SwordBeam;
			Item.shootSpeed = 12f;
			Item.crit = 5;                 // 初始暴击 5%
			Item.value = Item.sellPrice(gold: 3);
			Item.rare = WastelandRarityTiers.EarlyLate;   // 骷髅王之后档位
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			// 沿瞄准方向扇形甩出多片刀光：中间的直飞，两侧偏出去
			for (int i = 0; i < BeamCount; i++) {
				float spread = MathHelper.ToRadians(5f * (i - (BeamCount - 1) * 0.5f));
				Vector2 beamVelocity = velocity.RotatedBy(spread);

				Projectile.NewProjectile(
					source,
					position,
					beamVelocity,
					ProjectileID.SwordBeam,
					damage,
					knockback,
					player.whoAmI,
					0f,                    // ai0：原版刀光自己用
					0f,                    // ai1：留给原版（它会拿这个槽当内部标志）
					ScavengerBeam.Mark);   // ai2：我们的「这是大刀刀光」标记
			}

			return false;
		}
	}
}
