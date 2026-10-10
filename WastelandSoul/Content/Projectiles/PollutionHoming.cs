using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Content.Buffs;

namespace WastelandSoul.Content.Projectiles
{
	/// <summary>
	/// 污染团：清道夫「过载修复」阶段的核心威胁。
	/// <para/>缓慢追踪玩家，隔一段时间就会撞上来；速度与转向都慢，所以跑得动就能甩开一段。
	/// <para/>可以被玩家的鞭、弹幕和近战打掉。命中玩家或自己消散时留下一小片污染区域。
	/// </summary>
	public class PollutionHoming : ModProjectile
	{
		/// <summary>追踪速度（像素/tick）。大师再慢一档。</summary>
		private const float HomingSpeed = 5.4f;
		private const float HomingSpeedMaster = 4.0f;

		public override void SetDefaults()
		{
			Projectile.width = 20;
			Projectile.height = 20;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.aiStyle = -1;
			Projectile.penetrate = 1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = Main.masterMode ? 300 : 480;
			Projectile.alpha = 30;
		}

		public override void AI()
		{
			Player target = FindTarget(Projectile.Center);
			float homingSpeed = Main.masterMode ? HomingSpeedMaster : HomingSpeed;

			if (target != null) {
				Vector2 desired = (target.Center - Projectile.Center).SafeNormalize(Vector2.UnitX) * homingSpeed;
				// 转向很慢：给出躲避空间
				Projectile.velocity = Vector2.Lerp(Projectile.velocity, desired, 0.05f);
			}
			else {
				Projectile.velocity *= 0.98f;
			}

			Projectile.rotation += Projectile.velocity.X * 0.02f;

			TryDestroyFromPlayerAttacks();

			if (!Main.dedServ && Main.rand.NextBool(3)) { // sync-ok: Dust only
				Dust.NewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Smoke, 0f, 0f, 120, default, 1.2f);
			}
		}

		/// <summary>鞭、弹幕、近战挥砍都能把污染团打掉。</summary>
		private void TryDestroyFromPlayerAttacks()
		{
			for (int i = 0; i < Main.maxProjectiles; i++) {
				Projectile other = Main.projectile[i];

				if (!other.active || other.whoAmI == Projectile.whoAmI || other.damage <= 0) {
					continue;
				}

				if (!other.friendly || other.hostile) {
					continue;
				}

				if (other.owner < 0 || other.owner >= Main.maxPlayers) {
					continue;
				}

				bool? colliding = other.Colliding(other.Hitbox, Projectile.Hitbox);

				if (colliding == false) {
					continue;
				}

				if (colliding == true || Projectile.Hitbox.Intersects(other.Hitbox)) {
					ShotDown();
					return;
				}
			}

			for (int p = 0; p < Main.maxPlayers; p++) {
				Player player = Main.player[p];

				if (!player.active || player.dead || player.itemAnimation <= 0) {
					continue;
				}

				Item item = player.HeldItem;

				if (item.noMelee || item.damage <= 0) {
					continue;
				}

				Rectangle melee = new Rectangle((int)player.itemLocation.X, (int)player.itemLocation.Y, item.width, item.height);

				if (player.direction == -1) {
					melee.X -= melee.Width;
				}

				if (player.gravDir == -1f) {
					melee.Y -= melee.Height;
				}

				if (melee.Intersects(Projectile.Hitbox)) {
					ShotDown();
					return;
				}
			}
		}

		private void ShotDown()
		{
			Projectile.localAI[1] = 1f;
			Projectile.Kill();
		}

		private static Player FindTarget(Vector2 from)
		{
			Player best = null;
			float bestDistance = float.MaxValue;

			for (int i = 0; i < Main.maxPlayers; i++) {
				Player player = Main.player[i];

				if (!player.active || player.dead || player.ghost) {
					continue;
				}

				float distance = Vector2.DistanceSquared(from, player.Center);

				if (distance < bestDistance) {
					bestDistance = distance;
					best = player;
				}
			}

			return best;
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo info)
		{
			target.AddBuff(ModContent.BuffType<Pollution>(), 300);
		}

		public override void OnKill(int timeLeft)
		{
			// 被玩家打掉就消掉；撞到人或自己消散才留污染区
			if (Projectile.localAI[1] == 0f && Main.netMode != NetmodeID.MultiplayerClient) {
				Projectile.NewProjectile(Projectile.GetSource_Death(), Projectile.Center, Vector2.Zero,
					ModContent.ProjectileType<PollutionZone>(), 14, 0f, Main.myPlayer);
			}

			if (Main.dedServ) {
				return;
			}

			for (int i = 0; i < 12; i++) {
				Vector2 velocity = Main.rand.NextVector2Circular(2.5f, 2.5f); // sync-ok: Dust only
				Dust.NewDust(Projectile.position, Projectile.width, Projectile.height, DustID.Smoke, velocity.X, velocity.Y, 100, default, 1.4f);
			}
		}
	}
}
