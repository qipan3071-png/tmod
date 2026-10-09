using Microsoft.Xna.Framework;
using System;
using Terraria;
using Terraria.DataStructures;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;
using Microsoft.Xna.Framework.Graphics;
using ArchivistNpc = WastelandSoul.Content.NPCs.Bosses.Archivist.Archivist;

namespace WastelandSoul.Content.Projectiles.Archivist
{
	/// <summary>
	/// 索引光束：从归档者眼部射出的细长激光。
	/// <para/>过程 = 明显亮光预警（细线闪烁，玩家来得及走位）→ 横扫 → 锁定段。
	/// <para/>ai[0] = 本体 whoAmI；ai[1] = 从生成到结束的总帧数；朝向每帧从本体的 <c>ai[3]</c> 读取
	/// （角度由 <see cref="ArchivistNpc.StepBeamAngle"/> 维护，这样联网时只需要同步本体）。
	/// <para/>⚠️ 朝向**只能有一个推进者**：<c>ArchivistIndexBeamState</c> 每帧推进 <c>ai[3]</c>，
	/// 这里只读不写。以前两边各推一次，横扫速度是设计值的两倍（34 帧扫了约 200° 而不是 100°）。
	/// <para/>视觉上用 1x1 白点拉伸成激光（<c>PreDraw</c> 里画），所以贴图只作为备用亮片。
	/// <para/>伤害也完全由沿光束线段的判定负责（<see cref="Colliding"/> 已关掉默认碰撞）。
	/// </summary>
	public class ArchivistIndexBeam : ModProjectile
	{
		/// <summary>
		/// 光束最大长度（像素）。
		/// <para/>⚠️ 早期 Boss 不做成"横穿屏幕"的东西：原来 1650（约 100 格）几乎覆盖整个屏幕，
		/// 玩家除了硬吃没有别的选择。现在 620（约 39 格），配合横扫依然是"必须走位"的招。
		/// </summary>
		private const float MaxLength = 620f;

		/// <summary>光束命中宽度（像素）：细长激光，靠走位躲。</summary>
		private const float BeamHitWidth = 14f;

		/// <summary>
		/// 贴图里"纯光束"那一段的纵向比例（0~1）。
		/// <para/>`ArchivistIndexBeam.png` 是 48×20，实测非透明行只有 **y=7..11**（核心亮线在 y=9），
		/// 枪口光斑在 **x=0..5**，其余是透明留白。原来把整张贴图（含大片透明）拉伸成长条，
		/// 视觉上就是"白板"，所以这里精确取那几行：
		/// <c>Glow</c> = 整条光束（5 行），<c>Core</c> = 中间亮芯（3 行）。
		/// 想调粗细只改这两个数字。
		/// </summary>
		private const float BeamGlowVFrom = 7f / 20f;
		private const float BeamGlowVTo = 12f / 20f;
		private const float BeamCoreVFrom = 8f / 20f;
		private const float BeamCoreVTo = 11f / 20f;

		/// <summary>枪口光斑宽度占贴图的比例（实测 x=0..5，即 6/48 = 0.125）。</summary>
		private const float MuzzleUTo = 6f / 48f;

		public override void SetDefaults()
		{
			Projectile.width = 48;
			Projectile.height = 24;
			Projectile.hostile = true;
			Projectile.friendly = false;
			Projectile.aiStyle = -1;
			Projectile.penetrate = -1;      // 扫过的路径上可以打中多个玩家
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = 120;
		}

		/// <summary>
		/// 关掉默认的矩形碰撞伤害：这道激光的判伤走线段（见 <see cref="DamageAlongBeam"/>），
		/// 否则玩家贴到本体眼部时会被"小碰撞箱"多打一次。
		/// <para/>注意 tModLoader 里这个钩子的返回类型是 <c>bool?</c>（<c>null</c> = 走默认逻辑）。
		/// </summary>
		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox)
		{
			return false;
		}

		public override bool? CanDamage()
		{
			// 只有真正开火之后才判伤害；预警段不伤（否则"预警"就变成偷袭了）
			return Projectile.localAI[0] >= ArchivistNpc.BeamWindup ? null : false;
		}

		public override void AI()
		{
			int bossIndex = (int)Projectile.ai[0];

			if (bossIndex < 0 || bossIndex >= Main.maxNPCs || !Main.npc[bossIndex].active) {
				Projectile.Kill();
				return;
			}

			NPC boss = Main.npc[bossIndex];

			Projectile.localAI[0] += 1f;

			if (Projectile.localAI[0] > Projectile.ai[1]) {
				Projectile.Kill();
				return;
			}

			Vector2 origin = BeamOrigin(boss);

			// 只读本体的 ai[3]：推进由状态类负责（见类型注释里的"只能有一个推进者"）
			float angle = boss.ai[3];

			Projectile.Center = origin;
			Projectile.velocity = Vector2.Zero;
			Projectile.rotation = angle;

			// 命中判定自己走线段（贴图只是视觉，长度随脉冲变化）
			DamageAlongBeam(origin, angle);

			if (!Main.dedServ) {
				EmitBeamDust(origin, angle);
				bool charging = Projectile.localAI[0] < ArchivistNpc.BeamWindup;

				if (!charging && (int)Projectile.localAI[0] % 4 == 0) {
					// ⚠️ 这里原来还叠了一道 620px 长的折线闪电（WastelandFxSystem.Bolt，
					// origin → origin + direction * MaxLength，近白色）。光束自己已经有贴图了，
					// 那道白线纯属"影响视线的光线"，玩家明确要求去掉 —— **以后合并也不许加回来**。
					// 只保留枪口那一点小光斑。
					Common.Effects.WastelandFxSystem.Glow(origin, new Color(210, 230, 255), 1.4f, 6);
				}
			}
		}

		/// <summary>眼部位置：本体中心朝面向方向偏一点，看起来是从传感器射出来的。</summary>
		private static Vector2 BeamOrigin(NPC boss)
		{
			return boss.Center + new Vector2(boss.spriteDirection * 26f, -14f);
		}

		/// <summary>沿光束线段逐个检测玩家（比矩形碰撞可靠，也不受贴图长短影响）。</summary>
		private void DamageAlongBeam(Vector2 origin, float angle)
		{
			// 伤害只由服务端结算：客户端的 Hurt 调用会让血条抖动并与服务端打架
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				return;
			}

			Vector2 end = origin + angle.ToRotationVector2() * MaxLength;

			for (int i = 0; i < Main.maxPlayers; i++) {
				Player player = Main.player[i];

				if (!player.active || player.dead || player.ghost || player.immune) {
					continue;
				}

				if (DistanceToSegment(player.Center, origin, end) > BeamHitWidth + player.width * 0.35f) {
					continue;
				}

				PlayerDeathReason reason = PlayerDeathReason.ByProjectile(player.whoAmI, Projectile.whoAmI);
				// 手动结算不走原版的"敌对弹幕加倍"通道 → 用 ManualHit 把生成处折半的那一份乘回来
					player.Hurt(reason, BossShotDamage.ManualHit(Projectile.damage),
						angle.ToRotationVector2().X >= 0f ? 1 : -1);
			}
		}

		/// <summary>点到线段的距离。</summary>
		private static float DistanceToSegment(Vector2 point, Vector2 start, Vector2 end)
		{
			Vector2 segment = end - start;
			float lengthSquared = segment.LengthSquared();

			if (lengthSquared < 1f) {
				return Vector2.Distance(point, start);
			}

			float t = MathHelper.Clamp(Vector2.Dot(point - start, segment) / lengthSquared, 0f, 1f);
			return Vector2.Distance(point, start + segment * t);
		}

		private void EmitBeamDust(Vector2 origin, float angle)
		{
			Vector2 direction = angle.ToRotationVector2();
			bool charging = Projectile.localAI[0] < ArchivistNpc.BeamWindup;

			if (charging) {
				// 亮光预警：越接近开火，眼部聚光越亮、越密
				float progress = Projectile.localAI[0] / ArchivistNpc.BeamWindup;

				for (int i = 0; i < (progress > 0.6f ? 3 : 1); i++) {
					Vector2 position = origin + direction * Main.rand.NextFloat(20f, 260f * progress + 20f); // sync-ok: visual only
					Dust dust = Dust.NewDustDirect(position, 4, 4, DustID.BlueTorch, 0f, 0f);
					dust.noGravity = true;
					dust.scale = 1.2f + progress;
				}

				return;
			}

			// 开火后：沿光束喷出纸屑与冷光
			for (int i = 0; i < 4; i++) {
				Vector2 position = origin + direction * Main.rand.NextFloat(0f, MaxLength); // sync-ok: visual only
				Dust dust = Dust.NewDustDirect(position, 4, 4, Main.rand.NextBool(3) ? DustID.Bone : DustID.BlueTorch, -direction.X * 2f, -direction.Y * 2f);
				dust.noGravity = true;
				dust.scale = 1.1f;
			}
		}

		/// <summary>
		/// 光束视觉：预警段是短而细的聚光线，开火段拉满设计长度。
		/// <para/>⚠️ 这里以前用 `TextureAssets.MagicPixel`（1x1 白点）拉伸成实心矩形，
		/// 实测就是"大量白线 + 白色板块"的来源 —— 那张 48x20 的光束贴图**当时根本没被用到**。
		/// 现在一律从贴图取"中间那条细光束"来做（外层暗、内层亮），
		/// 枪口另画一次原始比例的贴图光斑。**不要再改回拉伸白点。**
		/// <para/>UV 方向说明：贴图是**从左向右**画的（左端枪口、右端渐细），
		/// 而我们的光束是从眼部向右射；当光束朝左（角度接近 π 或 −π）时贴图会左右镜像，
		/// 枪口就跑到远端去。所以朝左时把 U 反过来取。
		/// </summary>
		public override bool PreDraw(ref Color lightColor)
		{
			float angle = Projectile.rotation;
			bool charging = Projectile.localAI[0] < ArchivistNpc.BeamWindup;
			float length = charging ? 60f + Projectile.localAI[0] * 8f : MaxLength;

			Vector2 direction = angle.ToRotationVector2();

			Texture2D beamTexture = TextureAssets.Projectile[Type].Value;
			int textureWidth = beamTexture.Width;
			int textureHeight = beamTexture.Height;

			// 光束横条只取有像素的那几行（透明上下留白绝不能一起拉伸）
			int glowTop = (int)(textureHeight * BeamGlowVFrom);
			int glowBottom = (int)(textureHeight * BeamGlowVTo);
			int coreTop = (int)(textureHeight * BeamCoreVFrom);
			int coreBottom = (int)(textureHeight * BeamCoreVTo);
			int muzzleWidth = Math.Max(1, (int)(textureWidth * MuzzleUTo));

			Rectangle glowSource = new Rectangle(0, glowTop, textureWidth, Math.Max(1, glowBottom - glowTop));
			Rectangle coreSource = new Rectangle(0, coreTop, textureWidth, Math.Max(1, coreBottom - coreTop));
			Rectangle muzzleSource = new Rectangle(0, 0, muzzleWidth, textureHeight);

			// 起点前移半个枪口宽度，让贴图左端的枪口光斑正好落在眼部
			Vector2 origin = Projectile.Center - Main.screenPosition;
			float muzzleLength = muzzleWidth * 0.5f;
			Vector2 drawOrigin = origin + direction * muzzleLength;

			// 光束横条在贴图里的中心行（约 y=9），据此对齐旋转轴
			float glowAxisV = (glowTop + glowBottom) * 0.5f;
			float coreAxisV = (coreTop + coreBottom) * 0.5f;

			Color glow = (charging ? new Color(120, 170, 255) : new Color(132, 190, 255)) * 0.8f;
			Color core = charging ? new Color(180, 210, 255) : new Color(226, 240, 255);

			// 外层辉光：拉满设计长度、纵向略放
			Main.EntitySpriteDraw(beamTexture, drawOrigin, glowSource, glow, angle,
				new Vector2(0f, glowAxisV), new Vector2(length / glowSource.Width, charging ? 0.7f : 1.15f),
				SpriteEffects.None, 0f);

			// 亮芯：更细、更亮
			Main.EntitySpriteDraw(beamTexture, drawOrigin, coreSource, core, angle,
				new Vector2(0f, coreAxisV), new Vector2(length / coreSource.Width, charging ? 0.35f : 0.6f),
				SpriteEffects.None, 0f);

			// 枪口光斑：原始比例再画一次（充能时随进度胀大）
			Main.EntitySpriteDraw(beamTexture, origin, muzzleSource, Color.White, angle,
				new Vector2(0f, textureHeight * 0.5f),
				charging ? 0.7f + Projectile.localAI[0] / ArchivistNpc.BeamWindup * 0.6f : 1.15f,
				SpriteEffects.None, 0f);

			return false;
		}
	}
}
