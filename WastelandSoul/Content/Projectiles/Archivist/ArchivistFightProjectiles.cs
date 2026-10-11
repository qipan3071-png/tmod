using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.Systems;
using WastelandSoul.Content.Buffs;
using ArchivistNpc = WastelandSoul.Content.NPCs.Bosses.Archivist.Archivist;

namespace WastelandSoul.Content.Projectiles.Archivist
{
	/// <summary>大火球：朝生成时的方向飞，不跟踪，2 秒后炸成小球。</summary>
	public class ArchivistFireball : ModProjectile
	{
		public override void SetDefaults()
		{
			Projectile.width = 28;
			Projectile.height = 28;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.aiStyle = -1;
			Projectile.penetrate = -1;
			Projectile.timeLeft = ArchivistNpc.FireballFuse;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.light = 0.55f;
		}

		public override void AI()
		{
			Projectile.rotation += 0.08f;

			if (!Main.dedServ && Main.rand.NextBool(2)) { // sync-ok: visual only
				Dust dust = Dust.NewDustDirect(Projectile.position, Projectile.width, Projectile.height, DustID.Torch);
				dust.noGravity = true;
				dust.scale = 1.15f;
			}
		}

		public override void OnKill(int timeLeft)
		{
			if (!WastelandNet.IsAuthoritativeSide) {
				return;
			}

			for (int i = 0; i < ArchivistNpc.MiniFireballCount; i++) {
				float angle = MathHelper.TwoPi * i / ArchivistNpc.MiniFireballCount;
				Vector2 velocity = angle.ToRotationVector2() * ArchivistNpc.MiniFireballSpeed;

				Projectile.NewProjectile(
					Projectile.GetSource_Death(),
					Projectile.Center,
					velocity,
					ModContent.ProjectileType<ArchivistMiniFireball>(),
					BossShotDamage.Half(ArchivistNpc.MiniFireballDamage),
					0.4f,
					Main.myPlayer);
			}
		}
	}

	/// <summary>大火球裂开的跟踪小球。速度慢，寿命短。</summary>
	public class ArchivistMiniFireball : ModProjectile
	{
		public override void SetDefaults()
		{
			Projectile.width = 14;
			Projectile.height = 14;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.aiStyle = -1;
			Projectile.penetrate = 1;
			Projectile.timeLeft = 240;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.light = 0.35f;
		}

		public override void AI()
		{
			Player target = ClosestPlayerFrom(Projectile.Center, 900f);

			if (target != null) {
				Vector2 desired = target.Center - Projectile.Center;

				if (desired.LengthSquared() > 1f) {
					desired = Vector2.Normalize(desired) * ArchivistNpc.MiniFireballSpeed;
					Projectile.velocity = Vector2.Lerp(Projectile.velocity, desired, 0.04f);
				}
			}

			Projectile.rotation += 0.16f;

			if (!Main.dedServ && Main.rand.NextBool(3)) { // sync-ok: visual only
				Dust dust = Dust.NewDustDirect(Projectile.position, Projectile.width, Projectile.height, DustID.Torch);
				dust.noGravity = true;
				dust.scale = 0.85f;
			}
		}

		internal static Player ClosestPlayerFrom(Vector2 origin, float range)
		{
			Player best = null;
			float bestDistance = range;

			for (int i = 0; i < Main.maxPlayers; i++) {
				Player player = Main.player[i];

				if (!player.active || player.dead || player.ghost) {
					continue;
				}

				float distance = Vector2.Distance(player.Center, origin);

				if (distance < bestDistance) {
					bestDistance = distance;
					best = player;
				}
			}

			return best;
		}
	}

	/// <summary>地表火柱：宽约 5 格，站进去持续烧。同时最多两根。</summary>
	public class ArchivistFirePillar : ModProjectile
	{
		public override void SetDefaults()
		{
			Projectile.width = ArchivistNpc.FirePillarWidth;
			Projectile.height = 8;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.aiStyle = -1;
			Projectile.penetrate = -1;
			Projectile.timeLeft = ArchivistNpc.FirePillarDuration;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.light = 0.7f;
		}

		public override void AI()
		{
			float bottom = Projectile.ai[1];
			int grown = (int)MathHelper.Clamp((ArchivistNpc.FirePillarDuration - Projectile.timeLeft) * 8f, 16f, 240f);
			Projectile.height = grown;
			Projectile.position.Y = bottom - Projectile.height;

			if (!Main.dedServ && Main.rand.NextBool(2)) { // sync-ok: visual only
				Dust dust = Dust.NewDustDirect(Projectile.position, Projectile.width, Projectile.height, DustID.Torch);
				dust.noGravity = true;
				dust.velocity.Y = -2.2f;
				dust.scale = 1.3f;
			}
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo info)
		{
			target.AddBuff(BuffID.OnFire, 120);
		}
	}

	/// <summary>毒液弹：跟踪 3 秒后消失。粉，行为对齐世纪之花二阶段种子。</summary>
	public class ArchivistVenomSeed : ModProjectile
	{
		public override void SetDefaults()
		{
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.aiStyle = -1;
			Projectile.penetrate = 1;
			Projectile.timeLeft = ArchivistNpc.VenomLife;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
		}

		public override void AI()
		{
			Player target = ArchivistMiniFireball.ClosestPlayerFrom(Projectile.Center, 1200f);

			if (target != null) {
				Vector2 desired = target.Center - Projectile.Center;

				if (desired.LengthSquared() > 1f) {
					desired = Vector2.Normalize(desired) * ArchivistNpc.VenomSpeed;
					Projectile.velocity = Vector2.Lerp(Projectile.velocity, desired, 0.055f);
				}
			}

			Projectile.rotation = Projectile.velocity.ToRotation() + MathHelper.PiOver2;

			if (!Main.dedServ && Main.rand.NextBool(4)) { // sync-ok: visual only
				Dust dust = Dust.NewDustDirect(Projectile.position, Projectile.width, Projectile.height, DustID.Plantera_Pink);
				dust.noGravity = true;
				dust.scale = 0.8f;
			}
		}
	}

	/// <summary>升空水泡。不跟踪。第一次接触有伤，之后把人困 1.2 秒。</summary>
	public class ArchivistBubble : ModProjectile
	{
		public override void SetDefaults()
		{
			Projectile.width = 52;
			Projectile.height = 52;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.aiStyle = -1;
			Projectile.penetrate = -1;
			Projectile.timeLeft = 360;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.alpha = 40;
		}

		public override void AI()
		{
			if (Projectile.ai[0] >= 1f) {
				int who = (int)Projectile.ai[1];

				if (who >= 0 && who < Main.maxPlayers && Main.player[who].active && !Main.player[who].dead) {
					Player trapped = Main.player[who];
					Projectile.Center = trapped.Center;
					trapped.velocity = Vector2.Zero;
				}
				else {
					Projectile.Kill();
				}

				return;
			}

			Projectile.velocity.Y = ArchivistNpc.BubbleRise;
			Projectile.velocity.X *= 0.98f;

			if (!Main.dedServ && Main.rand.NextBool(6)) { // sync-ok: visual only
				Dust dust = Dust.NewDustDirect(Projectile.position, Projectile.width, Projectile.height, DustID.DungeonWater);
				dust.noGravity = true;
				dust.scale = 0.7f;
			}
		}

		public override void OnHitPlayer(Player target, Player.HurtInfo info)
		{
			if (Projectile.ai[0] >= 1f) {
				return;
			}

			Projectile.ai[0] = 1f;
			Projectile.ai[1] = target.whoAmI;
			Projectile.damage = 0;
			Projectile.timeLeft = ArchivistNpc.BubbleTrapTicks;
			target.AddBuff(ModContent.BuffType<ArchivistBubbleTrap>(), ArchivistNpc.BubbleTrapTicks);
		}

		public override bool CanHitPlayer(Player target)
		{
			return Projectile.ai[0] < 1f;
		}
	}

	/// <summary>10 秒内从地面冒泡。自己不挡出招。</summary>
	public class ArchivistBubbleStorm : ModProjectile
	{
		public override void SetDefaults()
		{
			Projectile.width = 8;
			Projectile.height = 8;
			Projectile.hostile = false;
			Projectile.friendly = false;
			Projectile.hide = true;
			Projectile.aiStyle = -1;
			Projectile.timeLeft = ArchivistNpc.BubbleStormTicks;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
		}

		public override void AI()
		{
			if (!WastelandNet.IsAuthoritativeSide) {
				return;
			}

			if (Projectile.timeLeft % 18 != 0) {
				return;
			}

			int alive = 0;

			for (int i = 0; i < Main.maxProjectiles; i++) {
				Projectile other = Main.projectile[i];

				if (other.active && other.type == ModContent.ProjectileType<ArchivistBubble>()) {
					alive++;
				}
			}

			if (alive >= ArchivistNpc.BubbleMax) {
				return;
			}

			int npcWho = (int)Projectile.ai[0];

			if (npcWho < 0 || npcWho >= Main.maxNPCs || !Main.npc[npcWho].active) {
				Projectile.Kill();
				return;
			}

			NPC npc = Main.npc[npcWho];
			float worldX = npc.Center.X + WastelandRandom.RollFloatRange(npc.whoAmI, Projectile.timeLeft, alive, -ArchivistNpc.ArenaRadius * 0.7f, ArchivistNpc.ArenaRadius * 0.7f);
			Vector2 ground = ArchivistNpc.FindSurface(worldX, npc.Center.Y);

			Projectile.NewProjectile(
				Projectile.GetSource_FromThis(),
				ground + new Vector2(0f, -26f),
				new Vector2(0f, ArchivistNpc.BubbleRise),
				ModContent.ProjectileType<ArchivistBubble>(),
				Projectile.damage,
				0.2f,
				Main.myPlayer);
		}
	}

	/// <summary>圆场薄雾：圈沿扬尘，人在圈外时在身边再扬一层。不是激光。</summary>
	public class ArchivistArenaMist : ModProjectile
	{
		public override void SetDefaults()
		{
			Projectile.width = 8;
			Projectile.height = 8;
			Projectile.hostile = false;
			Projectile.friendly = false;
			Projectile.hide = true;
			Projectile.aiStyle = -1;
			Projectile.timeLeft = 2;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
		}

		public override void AI()
		{
			int npcWho = (int)Projectile.ai[0];

			if (npcWho >= 0 && npcWho < Main.maxNPCs && Main.npc[npcWho].active) {
				Projectile.timeLeft = 2;
				Projectile.Center = new Vector2(Projectile.ai[1], Projectile.ai[2]);
			}
			else {
				Projectile.Kill();
				return;
			}

			if (Main.dedServ) {
				return;
			}

			Vector2 center = Projectile.Center;
			const int Ring = 18;

			for (int i = 0; i < Ring; i++) {
				float angle = MathHelper.TwoPi * i / Ring + Main.GameUpdateCount * 0.01f;
				Vector2 pos = center + angle.ToRotationVector2() * ArchivistNpc.ArenaRadius;
				Dust dust = Dust.NewDustPerfect(pos, DustID.Cloud, Vector2.Zero, 180, new Color(200, 206, 216), 1.35f);
				dust.noGravity = true;
				dust.velocity = angle.ToRotationVector2().RotatedBy(1.1f) * 0.4f;
			}

			Player mine = Main.LocalPlayer;

			if (mine.active && !mine.dead && Vector2.Distance(mine.Center, center) > ArchivistNpc.ArenaRadius) {
				for (int i = 0; i < 3; i++) {
					Vector2 pos = mine.Center + Main.rand.NextVector2Circular(40f, 40f); // sync-ok: visual only
					Dust dust = Dust.NewDustPerfect(pos, DustID.Cloud, new Vector2(0f, -0.4f), 160, new Color(198, 204, 214), 1.5f);
					dust.noGravity = true;
				}
			}
		}
	}
}
