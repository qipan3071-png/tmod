using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.Systems;

namespace WastelandSoul.Content.Projectiles.Charge
{
	/// <summary>
	/// 电荷跃动的电球。ai[0] &gt; 0 是正电（红），&lt; 0 是负电（紫蓝）。
	/// 穿墙飞行，每帧减速，穿过怪物并持续造成伤害。滑行满 0.6 秒后，异性电球会相吸爆炸，同性电球会弹开。
	/// 速度掉下去或飞满 36 格后留下辐射场。
	/// </summary>
	public class ChargeLeapOrb : ModProjectile
	{
		private const float TravelPixels = 36f * 16f;

		private const float Drag = 0.987f;

		private const float StallSpeed = 0.65f;

		/// <summary>滑行 0.6 秒（36 帧）后才允许爆炸和弹开。</summary>
		private const float ArmFrames = 36f;

		private const float ReactReach = 5f * 16f;

		private const float ExplodeDistance = 42f;

		private const float BounceDistance = 56f;

		public override void SetDefaults()
		{
			Projectile.width = 32;
			Projectile.height = 32;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Magic;
			Projectile.penetrate = -1;
			Projectile.timeLeft = 300;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = 10;
			Projectile.light = 0.45f;
			Projectile.aiStyle = 0;
		}

		public override void AI()
		{
			Projectile.ai[1] += 1f;
			Projectile.velocity *= Drag;

			if (Projectile.ai[1] >= ArmFrames && TryReact()) {
				return;
			}

			Projectile.localAI[0] += Projectile.velocity.Length();

			if (!Main.dedServ) {
				Lighting.AddLight(Projectile.Center, ChargeLeapDraw.LightColor(Projectile.ai[0]));

				if (Main.rand.NextBool(2)) { // sync-ok: visual only
					Dust dust = Dust.NewDustDirect(Projectile.position, Projectile.width, Projectile.height, ChargeLeapDraw.DustType(Projectile.ai[0]));
					dust.noGravity = true;
					dust.scale = 0.9f;
					dust.velocity *= 0.2f;
				}
			}

			bool stalled = Projectile.velocity.LengthSquared() <= StallSpeed * StallSpeed;
			bool far = Projectile.localAI[0] >= TravelPixels;

			if ((stalled || far) && Projectile.owner == Main.myPlayer) {
				Projectile.Kill();
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone)
		{
			ChargeLeapDraw.Electrify(Projectile, target);
		}

		public override void OnKill(int timeLeft)
		{
			if (Projectile.ai[2] >= 1f || Projectile.owner != Main.myPlayer) {
				return;
			}

			int full = Projectile.damage;
			int fieldDamage = System.Math.Max(1, full * ChargeLeapField.DamagePercent / 100);

			// NewProjectile 的坐标是中心，引擎会自己减去半个碰撞箱。
			Projectile.NewProjectile(
				Projectile.GetSource_Death(),
				Projectile.Center,
				Vector2.Zero,
				ModContent.ProjectileType<ChargeLeapField>(),
				fieldDamage,
				Projectile.knockBack * 0.4f,
				Projectile.owner,
				Projectile.ai[0],
				ChargeLeapField.StartRadius,
				full);
		}

		public override bool PreDraw(ref Color lightColor)
		{
			ChargeLeapDraw.DrawOrb(Projectile.Center, Projectile.ai[0], lightColor);
			return false;
		}

		/// <summary>已滑行够 0.6 秒时，靠近的异性电球爆炸，同性电球弹开。返回 true 表示这对已经炸掉。</summary>
		private bool TryReact()
		{
			Projectile explodeWith = null;
			float explodeDist = float.MaxValue;
			Vector2 bounce = Vector2.Zero;

			for (int i = 0; i < Main.maxProjectiles; i++) {
				Projectile other = Main.projectile[i];

				if (!other.active || other.whoAmI == Projectile.whoAmI || !IsChargeBody(other)) {
					continue;
				}

				if (other.type == Type && other.ai[1] < ArmFrames) {
					continue;
				}

				float dist = Vector2.Distance(Projectile.Center, other.Center);
				float sign = Projectile.ai[0] * other.ai[0];

				if (sign < 0f && dist <= ReactReach && dist < explodeDist) {
					explodeDist = dist;
					explodeWith = other;
				}
				else if (sign > 0f && dist <= BounceDistance) {
					bounce += (Projectile.Center - other.Center).SafeNormalize(Vector2.UnitX);
				}
			}

			if (explodeWith != null && explodeDist <= ExplodeDistance) {
				Explode(explodeWith);
				return true;
			}

			if (explodeWith != null) {
				Projectile.velocity += (explodeWith.Center - Projectile.Center).SafeNormalize(Vector2.Zero) * 1.15f;
			}

			if (bounce != Vector2.Zero) {
				Projectile.velocity += bounce.SafeNormalize(Vector2.Zero) * 3.4f;

				if (Projectile.velocity.LengthSquared() > 7f * 7f) {
					Projectile.velocity = Projectile.velocity.SafeNormalize(Vector2.Zero) * 7f;
				}
			}

			return false;
		}

		private void Explode(Projectile partner)
		{
			bool handler = Projectile.owner < partner.owner
				|| (Projectile.owner == partner.owner && Projectile.identity <= partner.identity);

			if (!handler) {
				return;
			}

			if (Projectile.owner == Main.myPlayer) {
				Vector2 mid = (Projectile.Center + partner.Center) * 0.5f;
				int burstDamage = System.Math.Max(1, Projectile.damage);
				float start = ChargeLeapBurst.StartRadius;

				Projectile.NewProjectile(
					Projectile.GetSource_Death(),
					mid,
					Vector2.Zero,
					ModContent.ProjectileType<ChargeLeapBurst>(),
					burstDamage,
					Projectile.knockBack,
					Projectile.owner,
					start,
					0f,
					burstDamage);
			}

			Projectile.ai[2] = 1f;

			if (partner.type == Type) {
				partner.ai[2] = 1f;
			}

			Projectile.Kill();
			partner.Kill();
		}

		private bool IsChargeBody(Projectile other)
		{
			return other.type == Type || other.type == ModContent.ProjectileType<ChargeLeapField>();
		}
	}

	/// <summary>
	/// 辐射场。ai[0] 电荷，ai[1] 半径（像素），ai[2] 爆炸用的完整武器伤害。
	/// 每 20 帧用已经降过的伤害打一次。异性进入范围后相吸，贴到一起爆炸；
	/// 同性则把半径从 4 格拉到 7 格，并互相推开。
	/// </summary>
	public class ChargeLeapField : ModProjectile
	{
		public const int DamagePercent = 30;

		public const float StartRadius = 4f * 16f;

		public const float MaxRadius = 7f * 16f;

		private const int Life = 270;

		private const float MeetDistance = 40f;

		public override void SetDefaults()
		{
			Projectile.width = (int)(StartRadius * 2f);
			Projectile.height = (int)(StartRadius * 2f);
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Magic;
			Projectile.penetrate = -1;
			Projectile.timeLeft = Life;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = 20;
			Projectile.aiStyle = 0;
		}

		public override void AI()
		{
			if (Projectile.ai[1] < 8f) {
				Projectile.ai[1] = StartRadius;
			}

			Projectile partner = FindPartner(out float distance, out bool opposite, out bool sameNear);

			if (partner != null && opposite && distance <= MeetDistance) {
				bool handler = Projectile.owner < partner.owner
					|| (Projectile.owner == partner.owner && Projectile.identity <= partner.identity);

				if (handler && Projectile.owner == Main.myPlayer) {
					Vector2 mid = (Projectile.Center + partner.Center) * 0.5f;
					int burstDamage = System.Math.Max(1, (int)Projectile.ai[2]);
					float start = ChargeLeapBurst.StartRadius;

					Projectile.NewProjectile(
						Projectile.GetSource_Death(),
						mid,
						Vector2.Zero,
						ModContent.ProjectileType<ChargeLeapBurst>(),
						burstDamage,
						Projectile.knockBack,
						Projectile.owner,
						start,
						0f,
						burstDamage);
				}

				if (handler) {
					Projectile.Kill();
					partner.Kill();
				}

				return;
			}

			Vector2 push = Vector2.Zero;

			if (partner != null && opposite) {
				push += (partner.Center - Projectile.Center).SafeNormalize(Vector2.Zero) * 0.8f;
			}

			if (sameNear) {
				Projectile.ai[1] = System.Math.Min(MaxRadius, Projectile.ai[1] + 0.45f);
			}

			ApplyPush(push);
			FitHitbox();

			if (Projectile.owner == Main.myPlayer && Projectile.timeLeft % 30 == 0) {
				Projectile.netUpdate = true;
			}

			if (Main.dedServ) {
				return;
			}

			Lighting.AddLight(Projectile.Center, ChargeLeapDraw.LightColor(Projectile.ai[0]) * 0.65f);

			if (Main.rand.NextBool(2)) { // sync-ok: visual only
				Dust dust = Dust.NewDustDirect(Projectile.position, Projectile.width, Projectile.height, ChargeLeapDraw.DustType(Projectile.ai[0]));
				dust.noGravity = true;
				dust.scale = 0.85f;
				dust.velocity *= 0.15f;
			}
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone)
		{
			ChargeLeapDraw.Electrify(Projectile, target);
		}

		public override bool PreDraw(ref Color lightColor)
		{
			ChargeLeapDraw.DrawOrb(Projectile.Center, Projectile.ai[0], lightColor);
			return false;
		}

		private void ApplyPush(Vector2 push)
		{
			for (int i = 0; i < Main.maxProjectiles; i++) {
				Projectile other = Main.projectile[i];

				if (!IsField(other) || other.ai[0] * Projectile.ai[0] <= 0f) {
					continue;
				}

				Vector2 delta = Projectile.Center - other.Center;
				float reach = Projectile.ai[1] + other.ai[1];

				if (delta.LengthSquared() > reach * reach) {
					continue;
				}

				push += delta.SafeNormalize(Vector2.UnitX) * 0.55f;
			}

			Projectile.velocity = (Projectile.velocity + push) * 0.94f;

			if (Projectile.velocity.LengthSquared() > 5f * 5f) {
				Projectile.velocity = Projectile.velocity.SafeNormalize(Vector2.Zero) * 5f;
			}
		}

		private Projectile FindPartner(out float distance, out bool opposite, out bool sameNear)
		{
			Projectile nearestOpposite = null;
			distance = float.MaxValue;
			opposite = false;
			sameNear = false;

			for (int i = 0; i < Main.maxProjectiles; i++) {
				Projectile other = Main.projectile[i];

				if (!IsField(other)) {
					continue;
				}

				float reach = Projectile.ai[1] + other.ai[1];
				float dist = Vector2.Distance(Projectile.Center, other.Center);

				if (dist > reach) {
					continue;
				}

				if (other.ai[0] * Projectile.ai[0] < 0f) {
					if (dist < distance) {
						distance = dist;
						nearestOpposite = other;
						opposite = true;
					}
				}
				else {
					sameNear = true;
				}
			}

			return nearestOpposite;
		}

		private bool IsField(Projectile other)
		{
			return other.active
				&& other.whoAmI != Projectile.whoAmI
				&& other.type == Projectile.type;
		}

		private void FitHitbox()
		{
			Vector2 center = Projectile.Center;
			int size = (int)(Projectile.ai[1] * 2f);

			Projectile.width = size;
			Projectile.height = size;
			Projectile.Center = center;
		}
	}

	/// <summary>
	/// 异性电球贴住时的震荡波。从爆炸点向外扩，像声波只伤害当前这一圈。
	/// ai[0] 是外半径，ai[2] 是中心那一圈的完整伤害。最远 32 格，每向外 4 格伤害乘 0.75。
	/// 同一个敌人只吃到抵达他的那一圈。
	/// </summary>
	public class ChargeLeapBurst : ModProjectile
	{
		public const float StartRadius = 20f;

		private const float MaxRadius = 32f * 16f;

		private const float ExpandSpeed = 24f;

		/// <summary>每跨过这么远，伤害乘一次 0.75。范围是原来的 4 倍，所以一圈也是原来的 4 倍。</summary>
		private const float RingStep = 64f;

		/// <summary>贴图环的内径 / 外径。碰撞只留这一圈，避免波已经过去的中心再结算。</summary>
		private const float InnerRatio = 0.78f;

		private const float TextureRadius = 12.5f;

		public override void SetDefaults()
		{
			Projectile.width = (int)(StartRadius * 2f);
			Projectile.height = (int)(StartRadius * 2f);
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Magic;
			Projectile.penetrate = -1;
			Projectile.timeLeft = 40;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = 40;
			Projectile.aiStyle = 0;
		}

		public override void AI()
		{
			Projectile.velocity = Vector2.Zero;

			if (Projectile.ai[0] < 8f) {
				Projectile.ai[0] = StartRadius;
			}

			float previous = Projectile.ai[0];
			if (previous >= MaxRadius) {
				Projectile.Kill();
				return;
			}

			float next = previous + ExpandSpeed;

			if (next > MaxRadius) {
				next = MaxRadius;
			}

			if (Projectile.localAI[1] == 0f) {
				Projectile.localAI[0] = 0f;
				Projectile.localAI[1] = 1f;
			}
			else {
				Projectile.localAI[0] = previous * InnerRatio;
			}

			Projectile.ai[0] = next;

			int ring = (int)((next - StartRadius) / RingStep);

			if (ring < 0) {
				ring = 0;
			}

			float factor = (float)System.Math.Pow(0.75, ring);
			Projectile.damage = System.Math.Max(1, (int)(Projectile.ai[2] * factor));

			Vector2 center = Projectile.Center;
			int size = (int)(next * 2f);
			Projectile.width = size;
			Projectile.height = size;
			Projectile.Center = center;
		}

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox)
		{
			Vector2 center = Projectile.Center;
			float closestX = MathHelper.Clamp(center.X, targetHitbox.Left, targetHitbox.Right);
			float closestY = MathHelper.Clamp(center.Y, targetHitbox.Top, targetHitbox.Bottom);
			float distSq = Vector2.DistanceSquared(center, new Vector2(closestX, closestY));
			float outer = Projectile.ai[0];
			float inner = Projectile.localAI[0];

			if (distSq > outer * outer) {
				return false;
			}

			float farX = center.X < targetHitbox.Center.X ? targetHitbox.Left : targetHitbox.Right;
			float farY = center.Y < targetHitbox.Center.Y ? targetHitbox.Top : targetHitbox.Bottom;
			float farSq = Vector2.DistanceSquared(center, new Vector2(farX, farY));

			return farSq >= inner * inner;
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone)
		{
			ChargeLeapDraw.Electrify(Projectile, target);
		}

		public override bool PreDraw(ref Color lightColor)
		{
			Texture2D texture = Terraria.GameContent.TextureAssets.Projectile[Type].Value;
			float scale = Projectile.ai[0] / TextureRadius;
			float progress = MathHelper.Clamp((Projectile.ai[0] - StartRadius) / (MaxRadius - StartRadius), 0f, 1f);
			Color color = lightColor * (1f - progress * 0.4f);

			Main.EntitySpriteDraw(
				texture,
				Projectile.Center - Main.screenPosition,
				null,
				color,
				0f,
				texture.Size() * 0.5f,
				scale,
				SpriteEffects.None,
				0);
			return false;
		}
	}

	internal static class ChargeLeapDraw
	{
		public const float OrbScale = 2f;

		public static int DustType(float charge)
		{
			return charge < 0f ? DustID.PurpleTorch : DustID.RedTorch;
		}

		public static Vector3 LightColor(float charge)
		{
			return charge < 0f ? new Vector3(0.28f, 0.16f, 0.7f) : new Vector3(0.7f, 0.16f, 0.12f);
		}

		public static void Electrify(Projectile projectile, NPC target)
		{
			int duration = WastelandRandom.Roll(projectile.identity, target.whoAmI, projectile.owner, 240, 421);

			target.AddBuff(BuffID.Electrified, duration);
		}

		public static void DrawOrb(Vector2 center, float charge, Color lightColor)
		{
			string path = charge < 0f
				? "WastelandSoul/Content/Projectiles/Charge/ChargeLeapNegative"
				: "WastelandSoul/Content/Projectiles/Charge/ChargeLeapPositive";
			Texture2D texture = ModContent.Request<Texture2D>(path).Value;

			Main.EntitySpriteDraw(
				texture,
				center - Main.screenPosition,
				null,
				lightColor,
				0f,
				texture.Size() * 0.5f,
				ChargeLeapDraw.OrbScale,
				SpriteEffects.None,
				0);
		}
	}
}
