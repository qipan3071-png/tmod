using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace WastelandSoul.Content.Projectiles.Scavenger
{
	/// <summary>
	/// 新月刃（原版 <see cref="ProjectileID.SwordBeam"/>）。
	/// 批次 83 起由壁炉守卫大剑甩出；标记仍走 <c>ai[2]</c>，原版刀光占用 <c>ai[1]</c>。
	/// </summary>
	public class ScavengerBeam : ModProjectile
	{
		/// <summary>穿透段数（能穿 4 个敌人）。</summary>
		public const int PenetrateHits = 4;

		/// <summary>带这个值的原版刀光才吃 <see cref="SwordBeamHook"/>（写在 <c>ai[2]</c>）。</summary>
		public const float Mark = 1f;

		private const int FanCount = 5;

		public static bool ShootFan(IEntitySource source, Vector2 position, Vector2 velocity, int damage, float knockback, int owner)
		{
			for (int i = 0; i < FanCount; i++) {
				float spread = MathHelper.ToRadians(5f * (i - (FanCount - 1) * 0.5f));
				Projectile.NewProjectile(
					source,
					position,
					velocity.RotatedBy(spread),
					ProjectileID.SwordBeam,
					damage,
					knockback,
					owner,
					0f,
					0f,
					Mark);
			}

			return false;
		}

		public override void SetStaticDefaults()
		{
			// 复用原版刀光贴图 —— 不新增 PNG
			TextureAssets.Projectile[Type] = TextureAssets.Projectile[ProjectileID.SwordBeam];
		}

		public override void SetDefaults()
		{
			// 数值全部交给原版 SwordBeam 的默认值；这里只兜住尺寸
			Projectile.width = 24;
			Projectile.height = 24;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Melee;
		}
	}
}
