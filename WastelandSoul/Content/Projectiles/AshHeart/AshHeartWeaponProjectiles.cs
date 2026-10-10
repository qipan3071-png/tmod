using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace WastelandSoul.Content.Projectiles.AshHeart
{
	// ====================================================================================
	// Boss3「灰烬之心」专属弹幕（A 线四职业 + B 线继承强化版）。
	// 主题：余烬 —— 暖橙/暗红、命中留灼烧、弹道偏"沉"，与清道夫的废料感区分开。
	// B 线一律**继承 A 线**，只改尺寸/穿透/存活/发光，行为自动复用。
	// （两个召唤师仆从尚未做，见武器类里的 TODO。）
	// ====================================================================================

	/// <summary>战士：余烬剑气。慢速、穿透 2、命中挂灼烧。</summary>
	public class AshHeartWarriorProjectile : ModProjectile
	{
		public override void SetDefaults()
		{
			Projectile.width = 26;
			Projectile.height = 26;
			Projectile.friendly = true;
			Projectile.penetrate = 2;
			Projectile.timeLeft = 60;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.light = 0.5f;
			Projectile.aiStyle = 0;
		}

		public override void AI()
		{
			Projectile.rotation = Projectile.velocity.ToRotation();
			Projectile.velocity *= 0.975f;
			Projectile.alpha = (int)MathHelper.Lerp(0f, 190f, 1f - Projectile.timeLeft / 60f);

			if (Main.rand.NextBool(3)) { // sync-ok: visual only
				Dust dust = Dust.NewDustDirect(Projectile.position, Projectile.width, Projectile.height, DustID.Torch);
				dust.noGravity = true;
				dust.scale = 0.9f;
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone)
		{
			target.AddBuff(BuffID.OnFire, 180);
		}
	}

	/// <summary>法师：灰烬心核。轻微下坠，命中挂灼烧。</summary>
	public class AshHeartMageProjectile : ModProjectile
	{
		public override void SetDefaults()
		{
			Projectile.width = 20;
			Projectile.height = 20;
			Projectile.friendly = true;
			Projectile.penetrate = 1;
			Projectile.timeLeft = 180;
			Projectile.tileCollide = true;
			Projectile.ignoreWater = true;
			Projectile.light = 0.7f;
			Projectile.aiStyle = 0;
		}

		public override void AI()
		{
			Projectile.rotation += 0.1f * Projectile.direction;
			Projectile.velocity.Y += 0.08f;

			if (Projectile.velocity.Y > 10f) {
				Projectile.velocity.Y = 10f;
			}

			if (Main.rand.NextBool(3)) { // sync-ok: visual only
				Dust dust = Dust.NewDustDirect(Projectile.position, Projectile.width, Projectile.height, DustID.Torch);
				dust.noGravity = true;
				dust.scale = 1.1f;
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone)
		{
			target.AddBuff(BuffID.OnFire, 240);
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
				ModContent.ProjectileType<AshHeartEmberCloud>(),
				(int)(Projectile.damage * 0.4f),
				0f,
				Projectile.owner);
		}
	}

	/// <summary>射手：燃灰弹。高速直线，命中挂灼烧。</summary>
	public class AshHeartRangerProjectile : ModProjectile
	{
		public override void SetDefaults()
		{
			Projectile.width = 10;
			Projectile.height = 10;
			Projectile.friendly = true;
			Projectile.penetrate = 1;
			Projectile.timeLeft = 120;
			Projectile.tileCollide = true;
			Projectile.ignoreWater = true;
			Projectile.light = 0.6f;
			Projectile.extraUpdates = 1;
			Projectile.aiStyle = 0;
		}

		public override void AI()
		{
			Projectile.rotation = Projectile.velocity.ToRotation();

			if (Main.rand.NextBool(2)) { // sync-ok: visual only
				Dust dust = Dust.NewDustDirect(Projectile.position, Projectile.width, Projectile.height, DustID.FireworkFountain_Red);
				dust.noGravity = true;
				dust.scale = 0.8f;
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone)
		{
			target.AddBuff(BuffID.OnFire, 150);
		}
	}

	// ---------------------------- B 线：继承 A 线做强化 ----------------------------

	/// <summary>专属·余烬巨刃波：更大、穿透 4、活更久。</summary>
	public class AshHeartWarriorProjectileEX : AshHeartWarriorProjectile
	{
		public override void SetDefaults()
		{
			base.SetDefaults();
			Projectile.width = 34;
			Projectile.height = 34;
			Projectile.penetrate = 4;
			Projectile.timeLeft = 80;
			Projectile.light = 0.8f;
		}
	}

	/// <summary>专属·炉心心核：悬停半秒后炸成 6 枚余烬（不留云）。</summary>
	public class AshHeartMageProjectileEX : AshHeartMageProjectile
	{
		private const int HoverFrames = 30;

		private const int ShardCount = 6;

		public override void SetDefaults()
		{
			base.SetDefaults();
			Projectile.width = 26;
			Projectile.height = 26;
			Projectile.penetrate = 2;
			Projectile.timeLeft = 220;
			Projectile.light = 1f;
		}

		public override void AI()
		{
			Projectile.ai[0] += 1f;
			Projectile.rotation += 0.16f * Projectile.direction;
			Projectile.velocity *= 0.9f;

			if (Main.rand.NextBool(2)) { // sync-ok: visual only
				Dust dust = Dust.NewDustDirect(Projectile.position, Projectile.width, Projectile.height, DustID.Torch);
				dust.noGravity = true;
				dust.scale = 1.2f;
			}

			if (Projectile.ai[0] < HoverFrames) {
				return;
			}

			BurstShards();
			Projectile.Kill();
		}

		public override void OnKill(int timeLeft)
		{
			BurstShards();
		}

		private void BurstShards()
		{
			if (Projectile.owner != Main.myPlayer || Projectile.ai[1] != 0f) {
				return;
			}

			Projectile.ai[1] = 1f;
			int damage = (int)(Projectile.damage * 0.35f);
			for (int i = 0; i < ShardCount; i++) {
				Vector2 vel = Vector2.UnitX.RotatedBy(MathHelper.TwoPi * i / ShardCount) * 7.5f;
				Projectile.NewProjectile(
					Projectile.GetSource_Death(),
					Projectile.Center,
					vel,
					ModContent.ProjectileType<AshHeartEmberShard>(),
					damage,
					Projectile.knockBack * 0.4f,
					Projectile.owner);
			}
		}
	}

	/// <summary>灰烬云：心核消失后留 5 秒，大约每秒结算一次。</summary>
	public class AshHeartEmberCloud : ModProjectile
	{
		public override string Texture => "WastelandSoul/Content/Items/Weapons/Boss3AshHeart/AshHeartMageWeapon";

		public override void SetDefaults()
		{
			Projectile.width = 56;
			Projectile.height = 56;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Magic;
			Projectile.penetrate = -1;
			Projectile.timeLeft = 300;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = 60;
			Projectile.alpha = 80;
		}

		public override void AI()
		{
			Projectile.velocity = Vector2.Zero;
			Projectile.rotation += 0.02f;
			Lighting.AddLight(Projectile.Center, 0.45f, 0.16f, 0.04f);

			if (Main.rand.NextBool()) { // sync-ok: visual only
				Dust dust = Dust.NewDustDirect(Projectile.position, Projectile.width, Projectile.height, DustID.Torch);
				dust.noGravity = true;
				dust.velocity *= 0.3f;
				dust.scale = 1.1f;
			}
		}

		public override bool PreDraw(ref Color lightColor)
		{
			return false;
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone)
		{
			target.AddBuff(BuffID.OnFire, 120);
		}
	}

	/// <summary>余烬破片：炸开后略追踪。</summary>
	public class AshHeartEmberShard : ModProjectile
	{
		public override string Texture => "WastelandSoul/Content/Items/Weapons/Boss3AshHeart/AshHeartMageWeapon";

		public override void SetDefaults()
		{
			Projectile.width = 12;
			Projectile.height = 12;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Magic;
			Projectile.penetrate = 1;
			Projectile.timeLeft = 90;
			Projectile.tileCollide = true;
			Projectile.ignoreWater = true;
			Projectile.extraUpdates = 1;
		}

		public override void AI()
		{
			Projectile.rotation = Projectile.velocity.ToRotation();
			Lighting.AddLight(Projectile.Center, 0.35f, 0.12f, 0.02f);

			NPC target = null;
			float reach = 420f;
			for (int i = 0; i < Main.maxNPCs; i++) {
				NPC npc = Main.npc[i];
				if (!npc.CanBeChasedBy(this)) {
					continue;
				}

				float dist = Projectile.Distance(npc.Center);
				if (dist >= reach || !Collision.CanHit(Projectile.Center, 1, 1, npc.Center, 1, 1)) {
					continue;
				}

				reach = dist;
				target = npc;
			}

			if (target != null) {
				Vector2 want = Vector2.Normalize(target.Center - Projectile.Center) * 10f;
				Projectile.velocity = Vector2.Lerp(Projectile.velocity, want, 0.12f);
			}

			if (Main.rand.NextBool(2)) { // sync-ok: visual only
				Dust dust = Dust.NewDustDirect(Projectile.position, Projectile.width, Projectile.height, DustID.FireworkFountain_Red);
				dust.noGravity = true;
				dust.scale = 0.7f;
			}
		}

		public override bool PreDraw(ref Color lightColor)
		{
			return false;
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone)
		{
			target.AddBuff(BuffID.OnFire, 150);
		}
	}

	/// <summary>专属·燃灰重弹：更粗、穿透 2、飞得更稳。</summary>
	public class AshHeartRangerProjectileEX : AshHeartRangerProjectile
	{
		public override void SetDefaults()
		{
			base.SetDefaults();
			Projectile.width = 14;
			Projectile.height = 14;
			Projectile.penetrate = 2;
			Projectile.extraUpdates = 2;
			Projectile.light = 0.8f;
		}
	}
}
