using System;
using InnoVault.StateMachines;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using WastelandSoul.Common.Systems;
using WastelandSoul.Content.Items.Bags;
using WastelandSoul.Content.Items.Decor;
using WastelandSoul.Content.Projectiles.FireplaceBoss;
using WastelandSoul.Content.Projectiles.Vfx;

namespace WastelandSoul.Content.NPCs.Bosses.FireplaceGuardian
{
	/// <summary>
	/// Boss 4：壁炉守卫。壁炉重置装置的最后一道锁，月亮领主之前。
	/// <para/>定位：**月亮事件 / 四柱那一档，最终 Boss（月亮领主）之前的最后一个原创 Boss**，本体强度压在月亮领主之下。
	/// 原版参照（Cecil 读 Terraria.NPC.SetDefaults）：四柱每根 20000/20、光之女皇 50000/80/38、
	/// 猪龙鱼公爵 60000/100/50、史莱姆皇后 70000/80/50；月亮领主本体是三段共享 145000 血
	/// （核心 50000 防 70 + 头 45000 防 50 + 双手 25000×2 防 40）。所以这里取 70000 血（等于史莱姆皇后，
	/// 是月亮领主之外原版最高的那一档）、84 接触、50 防御 —— 不超过月亮领主本体。
	/// <para/>两个阶段。一阶段横扫，并在玩家这一列打出竖直剑气（飞满 80 格消失）。
	/// 二阶段把环境换成原版暴风雪，并蓄力 1.2 秒后用本体碰撞箱冲刺。
	/// 转换时获得 12000 点护盾。子弹和魔法弹幕有 50% 被反弹，并把该弹伤害的 10% 打回主人。
	/// </summary>
	[AutoloadBossHead]
	public class FireplaceGuardian : ModNPC
	{
		public const float PhaseTwoThreshold = 0.62f;

		/// <summary>阶段转换护盾。1 万 2。</summary>
		internal const int PhaseShield = 12000;

		/// <summary>竖直剑气飞满这么多格后消失。1 格 = 16 像素。</summary>
		internal const float SwordQiTiles = 80f;

		internal const int AttackIntervalPhaseOne = 130;
		internal const int AttackIntervalPhaseTwo = 100;

		internal const int SweepWindup = 36;
		internal const int SwordQiWindup = 28;

		/// <summary>冲刺前摇 1.2 秒。</summary>
		internal const int DashWindup = 72;

		internal const int DashTicks = 48;

		internal const int ContactDamage = 84;
		internal const int DashDamage = 120;
		internal const int SweepDamage = 84;
		internal const int SwordQiDamage = 56;

		internal const float HoverDefault = 200f;
		internal const float HoverHigh = 250f;
		internal const float SlamSpeed = 15f;
		internal const float MaxTurnPerTick = 5f;

		public override void SetStaticDefaults()
		{
			Main.npcFrameCount[Type] = 1;
			NPCID.Sets.BossBestiaryPriority.Add(Type);
			NPCID.Sets.MPAllowedEnemies[Type] = true;
			Music = MusicLoader.GetMusicSlot(Mod, "Music/FireplaceGuardian");
		}

		public override void SetDefaults()
		{
			// 石巨人碰撞 140；贴图 256×307（枪盾四足）。体型为最初模型的 0.55 倍
			//（碰撞与绘制一起缩；枪盾仍露在盒子外）。
			NPC.width = 127;
			NPC.height = 168;
			NPC.scale = 0.55f;
			DrawOffsetY = -24f;
			NPC.damage = ContactDamage;
			NPC.defDamage = ContactDamage;
			NPC.defense = 50;
			NPC.lifeMax = 70000;           // 月亮领主之前的天花板档（= 史莱姆皇后），低于月亮领主本体 145000
			NPC.knockBackResist = 0f;
			NPC.noGravity = false;
			NPC.noTileCollide = false;
			NPC.boss = true;
			NPC.aiStyle = -1;
			NPC.npcSlots = 20f;
			NPC.value = Item.buyPrice(gold: 40);
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
		}

		public override void AI()
		{
			FireplaceGuardianContext context = FireplaceGuardianContext.For(NPC);
			context.Target = FindTarget(NPC);

			if (context.Target == null) {
				FireplaceGuardianContext.Release(NPC.whoAmI);
				EndBlizzard();
				NPC.velocity.Y -= 0.16f;
				NPC.EncourageDespawn(30);
				return;
			}

			NPC.target = context.Target.whoAmI;
			context.Machine.Update();

			if ((int)NPC.ai[0] >= 1) {
				KeepBlizzard();
			}
			NPC.spriteDirection = context.Target.Center.X > NPC.Center.X ? 1 : -1;
			NPC.rotation = 0f;

			if (!Main.dedServ) {
				Lighting.AddLight(NPC.Center, 0.55f, 0.75f, 1.05f);
			}
		}

		internal static Player FindTarget(NPC npc)
		{
			Player best = null;
			float bestDistance = 4600f;

			for (int i = 0; i < Main.maxPlayers; i++) {
				Player player = Main.player[i];

				if (!player.active || player.dead || player.ghost) {
					continue;
				}

				float distance = Vector2.Distance(player.Center, npc.Center);

				if (distance < bestDistance) {
					bestDistance = distance;
					best = player;
				}
			}

			return best;
		}

		/// <summary>位移对齐石巨人：贴地走、玩家在上方就跳，不悬浮。</summary>
		internal static void Hover(FireplaceGuardianContext context, float distance)
		{
			if (context.Target == null) {
				return;
			}

			NPC npc = context.Npc;
			npc.noGravity = false;
			npc.noTileCollide = false;
			npc.rotation = 0f;

			Player target = context.Target;
			float walk = distance > HoverDefault ? 4.2f : 3.2f;
			float desiredX = target.Center.X > npc.Center.X ? walk : -walk;
			npc.velocity.X = MathHelper.Lerp(npc.velocity.X, desiredX, 0.12f);

			bool onGround = npc.velocity.Y == 0f
				|| Collision.SolidCollision(npc.position + new Vector2(0f, npc.height), npc.width, 4);

			if (onGround && target.Center.Y < npc.Center.Y - 48f) {
				npc.velocity.Y = -11.5f;
			}
			else if (onGround && Math.Abs(target.Center.X - npc.Center.X) > 240f && Main.GameUpdateCount % 90u == 0u) {
				npc.velocity.Y = -9f;
				npc.velocity.X = Math.Sign(target.Center.X - npc.Center.X) * 6.5f;
			}
		}

		internal static void DashTowards(FireplaceGuardianContext context)
		{
			if (context.Target == null) {
				return;
			}

			NPC npc = context.Npc;
			npc.noTileCollide = true;
			npc.noGravity = true;
			Vector2 direction = context.Target.Center - npc.Center;

			if (direction.LengthSquared() < 1f) {
				direction = Vector2.UnitY;
			}

			npc.velocity = Vector2.Normalize(direction) * SlamSpeed;
		}

		internal static void SteerSlam(FireplaceGuardianContext context)
		{
			if (context.Target == null) {
				return;
			}

			NPC npc = context.Npc;
			float speed = npc.velocity.Length();

			if (speed < 1f) {
				speed = SlamSpeed;
			}

			float current = npc.velocity.ToRotation();
			Vector2 toTarget = context.Target.Center - npc.Center;
			float wanted = toTarget.LengthSquared() > 1f ? toTarget.ToRotation() : current;
			float delta = MathHelper.WrapAngle(wanted - current);
			float maxTurn = MathHelper.ToRadians(MaxTurnPerTick);
			npc.velocity = (current + MathHelper.Clamp(delta, -maxTurn, maxTurn)).ToRotationVector2() * speed;
		}

		/// <summary>掷下一次攻击的等待帧数。
		/// <para/>⚠️ **联机安全**：不许用 <c>Main.rand</c>（服务端/客户端会掷出不同帧数 ⇒ 出招错开）。
		/// 种子只用已同步的 <c>whoAmI</c> + <c>ai[2]</c>（见 <see cref="WastelandRandom"/>）。</summary>
		internal static int RollAttackDelay(FireplaceGuardianContext context)
		{
			int seedA = context.Npc.whoAmI;
			int seedB = (int)context.Npc.ai[2];

			return (int)context.Npc.ai[0] switch {
				>= 1 => AttackIntervalPhaseTwo + WastelandRandom.Roll(seedA, seedB, -8, 9),
				_ => AttackIntervalPhaseOne + WastelandRandom.Roll(seedA, seedB, -12, 13)
			};
		}

		internal static IVaultState<FireplaceGuardianContext> ChooseNextState(FireplaceGuardianContext context)
		{
			int phase = (int)context.Npc.ai[0];
			int cycle = (int)context.Npc.ai[2];
			context.Npc.ai[2] += 1f;

			if (phase >= 1) {
				return new FireplaceGuardianDashState();
			}

			return cycle % 2 == 0
				? new FireplaceGuardianSweepState()
				: new FireplaceGuardianSwordQiState();
		}

		internal static void OnPhaseStart(NPC npc, int phase)
		{
			npc.ai[0] = phase;
			npc.damage = ContactDamage;
			npc.defDamage = ContactDamage;
			npc.velocity *= 0.2f;
			npc.netUpdate = true;

			if (phase == 1) {
				npc.ai[3] = PhaseShield;
				BeginBlizzard();
			}

			if (Main.dedServ) {
				return;
			}

			SoundEngine.PlaySound(SoundID.Roar, npc.Center);
			WastelandSpark.Burst(npc.Center, 22, 2, 3.6f);

			if (phase == 1) {
				Main.NewText(Language.GetTextValue("Mods.WastelandSoul.Messages.FireplaceGuardianPhaseTwo"), new Color(180, 220, 255));
			}
		}

		internal static void SpawnSwordQi(FireplaceGuardianContext context)
		{
			if (context.Target == null || Main.netMode == NetmodeID.MultiplayerClient) {
				return;
			}

			float direction = context.Target.Center.Y < context.Npc.Center.Y - 16f ? -1f : 1f;

			Projectile.NewProjectile(
				context.Npc.GetSource_FromAI(),
				new Vector2(context.Target.Center.X, context.Npc.Center.Y),
				new Vector2(0f, direction * 8f),
				ModContent.ProjectileType<HearthSwordQi>(),
				BossShotDamage.Half(SwordQiDamage),
				2f,
				Main.myPlayer);
		}

		internal static void SpawnSweep(FireplaceGuardianContext context)
		{
			if (context.Target == null || Main.netMode == NetmodeID.MultiplayerClient) {
				return;
			}

			float startAngle = (context.Target.Center - context.Npc.Center).ToRotation() - MathHelper.PiOver2;
			float sweepDirection = context.Target.Center.X >= context.Npc.Center.X ? 1f : -1f;

			Projectile.NewProjectile(
				context.Npc.GetSource_FromAI(),
				context.Npc.Center,
				Vector2.Zero,
				ModContent.ProjectileType<HearthSweep>(),
				BossShotDamage.Half(SweepDamage),
				6f,
				Main.myPlayer,
				startAngle,
				sweepDirection,
				context.Npc.whoAmI);
		}

		/// <summary>冲刺段：本体碰撞箱每 5 帧打一次，并把玩家推开。只在权威侧结算。</summary>
		internal static void StrikeDash(NPC npc)
		{
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				return;
			}

			Rectangle hitbox = npc.Hitbox;

			for (int i = 0; i < Main.maxPlayers; i++) {
				Player player = Main.player[i];

				if (!player.active || player.dead || player.ghost || !hitbox.Intersects(player.Hitbox)) {
					continue;
				}

				int direction = Math.Sign(player.Center.X - npc.Center.X);

				if (direction == 0) {
					direction = npc.spriteDirection;
				}

				player.immune = false;
				player.immuneTime = 0;
				player.Hurt(PlayerDeathReason.ByNPC(npc.whoAmI), npc.damage, direction);
				player.velocity.X = direction * 12f;
				player.velocity.Y = -4.5f;
				player.immuneTime = 4;
			}
		}

		internal static bool BlizzardLiving()
		{
			int type = ModContent.NPCType<FireplaceGuardian>();

			for (int i = 0; i < Main.maxNPCs; i++) {
				NPC npc = Main.npc[i];

				if (npc.active && npc.type == type && (int)npc.ai[0] >= 1) {
					return true;
				}
			}

			return false;
		}

		private static bool _blizzardOwned;
		private static bool _rainWasAlreadyOn;

		internal static void BeginBlizzard()
		{
			if (Main.netMode == NetmodeID.MultiplayerClient || _blizzardOwned) {
				return;
			}

			_rainWasAlreadyOn = Main.raining;
			_blizzardOwned = true;

			if (!Main.raining) {
				Main.StartRain();
			}

			Main.maxRaining = Math.Max(Main.maxRaining, 0.85f);
			Main.rainTime = Math.Max(Main.rainTime, 3600);
		}

		internal static void KeepBlizzard()
		{
			if (Main.netMode == NetmodeID.MultiplayerClient || !_blizzardOwned) {
				return;
			}

			if (!Main.raining) {
				Main.StartRain();
			}

			Main.maxRaining = Math.Max(Main.maxRaining, 0.85f);
			Main.rainTime = Math.Max(Main.rainTime, 600);
		}

		internal static void EndBlizzard()
		{
			if (Main.netMode == NetmodeID.MultiplayerClient || !_blizzardOwned || BlizzardLiving()) {
				return;
			}

			if (!_rainWasAlreadyOn && Main.raining) {
				Main.StopRain();
			}

			_blizzardOwned = false;
		}

		private static bool IsReflectable(Projectile projectile)
		{
			if (!projectile.friendly || projectile.hostile || projectile.damage <= 0 || projectile.minion || projectile.sentry) {
				return false;
			}

			if (ProjectileID.Sets.MinionShot[projectile.type]) {
				return false;
			}

			if (projectile.DamageType.CountsAsClass(DamageClass.Magic)) {
				return true;
			}

			return !projectile.arrow && projectile.DamageType.CountsAsClass(DamageClass.Ranged);
		}

		public override bool? CanBeHitByProjectile(Projectile projectile)
		{
			if (!IsReflectable(projectile)) {
				return null;
			}

			if (projectile.localAI[1] == NPC.whoAmI + 1f) {
				return false;
			}

			if (WastelandRandom.Roll(NPC.whoAmI, projectile.identity, projectile.owner, 0, 2) != 0) {
				return null;
			}

			projectile.localAI[1] = NPC.whoAmI + 1f;

			if (Main.netMode != NetmodeID.MultiplayerClient) {
				projectile.velocity *= -1f;

				if (projectile.velocity.LengthSquared() < 1f) {
					projectile.velocity = (projectile.Center - NPC.Center).SafeNormalize(Vector2.UnitY) * 8f;
				}

				projectile.position += projectile.velocity * 3f;
				projectile.netUpdate = true;

				Player owner = Main.player[projectile.owner];

				if (owner.active && !owner.dead && !owner.ghost) {
					int bite = Math.Max(1, (int)(projectile.damage * 0.1f));
					int direction = Math.Sign(owner.Center.X - NPC.Center.X);

					if (direction == 0) {
						direction = NPC.spriteDirection;
					}

					owner.Hurt(PlayerDeathReason.ByNPC(NPC.whoAmI), bite, direction);
				}
			}

			return false;
		}

		public override void OnHitByItem(Player player, Item item, NPC.HitInfo hit, int damageDone)
		{
			AbsorbShield(damageDone);
		}

		public override void OnHitByProjectile(Projectile projectile, NPC.HitInfo hit, int damageDone)
		{
			AbsorbShield(damageDone);
		}

		public override bool CheckDead()
		{
			if (NPC.ai[3] > 0f) {
				NPC.life = 1;
				return false;
			}

			return true;
		}

		private void AbsorbShield(int damageDone)
		{
			int shield = (int)NPC.ai[3];

			if (shield <= 0 || damageDone <= 0) {
				return;
			}

			int taken = Math.Min(shield, damageDone);
			NPC.ai[3] = shield - taken;
			NPC.life += taken;

			if (NPC.life > NPC.lifeMax) {
				NPC.life = NPC.lifeMax;
			}

			NPC.netUpdate = true;
		}

		public override bool CanHitPlayer(Player target, ref int cooldownSlot)
		{
			return NPC.localAI[0] < 1f;
		}

		public override void FindFrame(int frameHeight)
		{
			NPC.frameCounter += 1.0;

			if (NPC.frameCounter >= 7.0) {
				NPC.frameCounter = 0.0;
				NPC.frame.Y += frameHeight;

				if (NPC.frame.Y >= Main.npcFrameCount[Type] * frameHeight) {
					NPC.frame.Y = 0;
				}
			}
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot)
		{
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<FireplaceBag>(), 1));
			// 10% 奖杯（与原版 Boss 掉落奖杯的做法一致）
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<FireplaceGuardianTrophy>(), 10));
		}

		public override void OnKill()
		{
			FireplaceGuardianContext.Release(NPC.whoAmI);
			EndBlizzard();
			WastelandStorySystem.MarkFireplaceGuardianDefeated();
		}

		public override bool CheckActive()
		{
			return false;
		}

		public override void BossHeadRotation(ref float rotation)
		{
			rotation = NPC.rotation;
		}
	}
}
