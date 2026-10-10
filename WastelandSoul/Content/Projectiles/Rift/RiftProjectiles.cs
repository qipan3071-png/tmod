using Microsoft.Xna.Framework;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
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
			if (Projectile.owner != Main.myPlayer) {
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

	/// <summary>
	/// 星弦弓的带电矢。外形和飞行手感参考原版脉冲矢：不受重力、不怕水。
	/// 锁定一名敌人追踪一次，不穿透，无视物块。
	/// </summary>
	public class StarstringShot : ModProjectile
	{
		private const float HomingRange = 640f;

		public override void SetStaticDefaults()
		{
			TextureAssets.Projectile[Type] = TextureAssets.Projectile[ProjectileID.PulseBolt];
		}

		public override void SetDefaults()
		{
			Projectile.width = 14;
			Projectile.height = 14;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Ranged;
			Projectile.penetrate = 1;
			Projectile.timeLeft = 240;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.extraUpdates = 2;
			Projectile.arrow = true;
		}

		public override void AI()
		{
			if (Projectile.ai[0] <= 0f) {
				int who = FindTarget();

				if (who >= 0) {
					Projectile.ai[0] = who + 1;
				}
			}

			int locked = (int)Projectile.ai[0] - 1;

			if ((uint)locked < Main.maxNPCs) {
				NPC npc = Main.npc[locked];

				if (npc.active && npc.CanBeChasedBy(Projectile)) {
					float speed = Projectile.velocity.Length();

					if (speed < 1f) {
						speed = 12f;
					}

					Vector2 desired = (npc.Center - Projectile.Center).SafeNormalize(Vector2.UnitX) * speed;
					Projectile.velocity = Vector2.Lerp(Projectile.velocity, desired, 0.14f);
				}
			}

			Projectile.rotation = Projectile.velocity.ToRotation() + MathHelper.PiOver2;

			if (!Main.dedServ && Main.rand.NextBool(2)) { // sync-ok: Dust only
				Dust dust = Dust.NewDustDirect(Projectile.position, Projectile.width, Projectile.height, DustID.Electric);
				dust.noGravity = true;
				dust.scale = 0.7f;
				dust.velocity *= 0.3f;
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone)
		{
			target.AddBuff(BuffID.Electrified, 240);
		}

		private int FindTarget()
		{
			int best = -1;
			float bestDistance = HomingRange;

			for (int i = 0; i < Main.maxNPCs; i++) {
				NPC npc = Main.npc[i];

				if (!npc.CanBeChasedBy(Projectile)) {
					continue;
				}

				float distance = Vector2.Distance(npc.Center, Projectile.Center);

				if (distance < bestDistance) {
					bestDistance = distance;
					best = i;
				}
			}

			return best;
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
			if (Projectile.owner != Main.myPlayer) {
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
