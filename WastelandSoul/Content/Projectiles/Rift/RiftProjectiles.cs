using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ModLoader;
using WastelandSoul.Content.Buffs;
using WastelandSoul.Content.Projectiles.Scavenger;

namespace WastelandSoul.Content.Projectiles.Rift
{
	/// <summary>
	/// 星隙斩。按时间走完：蓄能、沿轨迹撕开、向中心坍缩、爆发。
	/// <c>ai[0]</c> 是规模，1 为满尺寸。只保留判定，不铺粒子。
	/// </summary>
	public class StarRiftSlash : ModProjectile
	{
		public override void SetDefaults()
		{
			Projectile.width = 28;
			Projectile.height = 28;
			Projectile.friendly = true;
			Projectile.penetrate = -1;
			Projectile.timeLeft = 48;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = 16;
		}

		public override bool? CanDamage()
		{
			float time = Projectile.ai[1];
			return time > 8f && time < 36f;
		}

		public override bool PreDraw(ref Color lightColor)
		{
			return false;
		}

		public override void AI()
		{
			if (Projectile.localAI[1] == 0f) {
				Projectile.localAI[1] = Projectile.velocity.LengthSquared() > 0.01f
					? Projectile.velocity.ToRotation()
					: 0f;
			}

			float time = Projectile.ai[1];
			Projectile.ai[1] = time + 1f;
			float power = Projectile.ai[0] <= 0f ? 1f : Projectile.ai[0];
			Vector2 forward = Projectile.localAI[1].ToRotationVector2();
			Projectile.velocity = forward;

			if (time >= 8f && time < 22f) {
				Projectile.Center += forward * (8f * power);
			}

			if (time > 46f) {
				Projectile.Kill();
			}
		}
	}

	/// <summary>权杖打出的星核，飞一会儿后原地坍成一道星隙斩。</summary>
	public class OrbitMote : ModProjectile
	{
		public override string Texture => "WastelandSoul/Content/Items/Weapons/Rift/OrbitScepter";

		public override void SetDefaults()
		{
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Magic;
			Projectile.penetrate = 1;
			Projectile.timeLeft = 28;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
		}

		public override void AI()
		{
			Projectile.rotation = Projectile.velocity.ToRotation() + MathHelper.PiOver4;
			Projectile.velocity *= 0.985f;
		}

		public override void OnKill(int timeLeft)
		{
			if (Main.dedServ) {
				return;
			}

			Projectile.NewProjectile(
				Projectile.GetSource_Death(),
				Projectile.Center,
				Projectile.velocity * 0.2f,
				ModContent.ProjectileType<StarRiftSlash>(),
				Projectile.damage,
				Projectile.knockBack,
				Projectile.owner,
				0.75f);
		}
	}

	/// <summary>星弦。钉在目标上时撕开一道较小的裂缝。</summary>
	public class StarstringShot : ModProjectile
	{
		public override void SetDefaults()
		{
			Projectile.width = 12;
			Projectile.height = 12;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Ranged;
			Projectile.penetrate = 1;
			Projectile.timeLeft = 50;
			Projectile.tileCollide = true;
			Projectile.ignoreWater = true;
			Projectile.extraUpdates = 1;
			Projectile.arrow = true;
		}

		public override void AI()
		{
			Projectile.rotation = Projectile.velocity.ToRotation() + MathHelper.PiOver2;
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone)
		{
			Open();
		}

		public override void OnKill(int timeLeft)
		{
			if (timeLeft > 0) {
				Open();
			}
		}

		private void Open()
		{
			if (Main.dedServ || Projectile.localAI[0] > 0f) {
				return;
			}

			Projectile.localAI[0] = 1f;
			Projectile.NewProjectile(
				Projectile.GetSource_Death(),
				Projectile.Center,
				Projectile.velocity * 0.15f,
				ModContent.ProjectileType<StarRiftSlash>(),
				(int)(Projectile.damage * 0.65f),
				Projectile.knockBack,
				Projectile.owner,
				0.6f);
		}
	}

	/// <summary>缺环轮。飞到尽头时坍成星隙。</summary>
	public class GapChakramProj : ModProjectile
	{
		public override string Texture => "WastelandSoul/Content/Items/Weapons/Rift/GapChakram";

		public override void SetDefaults()
		{
			Projectile.width = 22;
			Projectile.height = 22;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Throwing;
			Projectile.penetrate = 3;
			Projectile.timeLeft = 32;
			Projectile.tileCollide = true;
			Projectile.ignoreWater = true;
		}

		public override void AI()
		{
			Projectile.rotation += 0.4f;
			Projectile.velocity *= 0.98f;
		}

		public override void OnKill(int timeLeft)
		{
			if (Main.dedServ) {
				return;
			}

			Projectile.NewProjectile(
				Projectile.GetSource_Death(),
				Projectile.Center,
				Vector2.Zero,
				ModContent.ProjectileType<StarRiftSlash>(),
				Projectile.damage,
				Projectile.knockBack,
				Projectile.owner,
				0.7f);
		}
	}

	/// <summary>虚空种。跟着主人，隔一会儿撕开一道小裂缝。</summary>
	public class VoidSeedMinion : WastelandMinionBase
	{
		protected override int BuffType => ModContent.BuffType<VoidSeedBuff>();

		protected override int ShotType => ModContent.ProjectileType<StarRiftSlash>();

		protected override float AttackInterval => 84f;

		protected override float HoverHeight => 70f;

		public override void SetDefaults()
		{
			base.SetDefaults();
			Projectile.DamageType = DamageClass.Summon;
		}
	}
}
