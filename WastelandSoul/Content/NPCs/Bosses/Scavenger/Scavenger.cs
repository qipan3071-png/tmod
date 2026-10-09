using System;
using System.IO;
using InnoVault.StateMachines;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;
using WastelandSoul.Common.Effects;
using WastelandSoul.Common.Systems;
using WastelandSoul.Content.Items.Decor;
using WastelandSoul.Content.Items.Materials;
using WastelandSoul.Content.Projectiles;

namespace WastelandSoul.Content.NPCs.Bosses.Scavenger
{
	/// <summary>
	/// Boss 1：清道夫（执行单元-07）。
	/// <para/>废土风杀戮机械：圆柱/球形主体、锈蚀修补痕迹、底部破损推进器喷污染颗粒、
	/// 不完整传感器阵列、红光闪烁不稳定；武器为废土化改装（焊接炮管、带电机械臂）。
	/// <para/>定位：**骷髅王之后、血肉墙之前**的第一个原创 Boss（原版参照：骷髅王 4400/32/10、
	/// 血肉墙 8000/50/12，这里取中间档，绝不越过血肉墙）。
	/// <para/>体型：碰撞箱对齐原版克苏鲁之眼 100×110；贴图帧表 110×110 里机体只占 74×63，
	/// 因此用 <see cref="NPC.scale"/> 与 <see cref="ModNPC.DrawOffsetY"/> 把画面放大到与碰撞箱相称。
	/// <para/>行为逻辑：清除「壁炉」外的所有生命，认为它们是污染。思考能力：无，只执行杀戮指令。
	/// <para/>实现说明：状态机（含状态同步）交给 InnoVault 的
	/// <see cref="InnoVault.StateMachines.NpcStateMachine{TContext}"/>，
	/// 阶段切换交给 <see cref="PhaseController{TContext}"/>，具体状态见 <c>ScavengerStates.cs</c>。
	/// </summary>
	[AutoloadBossHead]
	public class Scavenger : ModNPC
	{
		// ==================== 数值（待定项：集中在这里便于调整） ====================
		public const float PhaseTwoThreshold = 0.60f;       // 阶段二：过载修复
		public const float PhaseThreeThreshold = 0.30f;     // 阶段三：协议崩溃
		public const float OverloadChargeThreshold = 0.12f; // 触发自毁式冲锋的血量

		private const int AttackIntervalPhaseOne = 150;
		private const int AttackIntervalPhaseTwo = 105;     // 此阶段攻击更疯狂
		private const int AttackIntervalPhaseThree = 90;

		internal const int SweepWindup = 45;                // 机械臂横扫前摇（动作不流畅、前摇明显）
		internal const int BurstWindup = 60;                // 锁定位置前的前摇
		internal const int ChargeWindup = 90;               // 过载警报
		internal const int SlamWindup = 30;                 // 机体撞击前摇

		/// <summary>常规接触伤害（阶段一/二的机体撞击会临时提高）。</summary>
		internal const int NpcContactDamage = 40;

		private const int NpcSlamDamage = 50;               // 撞击期间的接触伤害（与血肉墙接触伤害 50 齐平，但这是有前摇的一击）

		private const int MaxRepairDrones = 3;
		private const int DroneSummonCooldown = 420;
		private const int PollutionCooldown = 180;

		private const int NpcChargeDamage = 120;            // 冲锋期间的接触伤害（重击级：对骷髅王之后的玩家是重伤但不是必死）

		// ==================== 过载自毁（未在冲锋前击败）的判定 ====================

		/// <summary>过载自毁标记（写入 NPC.ai[3]）：这次结束不是玩家击杀。</summary>
		public const float OverloadFailureMarker = -1f;

		/// <summary>过载自毁，且冲锋途中撞到过玩家。</summary>
		public const float OverloadFailureHitMarker = -2f;

		/// <summary>
		/// 进入过载自毁后是否一律不发战利品、也不推进剧情。
		/// <para/>true （当前采用）= 只要进入过载自毁就没有掉落，无论是否撞到玩家；
		/// <para/>false = 只有冲锋撞到过玩家才没收掉落，玩家躲过冲锋则正常掉落。
		/// </summary>
		public static readonly bool NoLootOnAnySelfDestruct = true;

		/// <summary>
		/// 这次死亡是否算作「玩家正常击败」。
		/// <para/>掉落条件与剧情推进都用这一个判断，保证两者行为一致。
		/// </summary>
		public static bool CountsAsPlayerDefeat(NPC npc)
		{
			if (npc.type != ModContent.NPCType<Scavenger>()) {
				return true;
			}

			// 模组配置可以覆盖；配置未加载时回落到代码里的默认值
			bool noLootOnAnySelfDestruct = Common.Configs.WastelandConfig.Instance != null
				? Common.Configs.WastelandConfig.SelfDestructGivesNoLoot
				: NoLootOnAnySelfDestruct;

			if (noLootOnAnySelfDestruct) {
				return npc.ai[3] != OverloadFailureMarker && npc.ai[3] != OverloadFailureHitMarker;
			}

			return npc.ai[3] != OverloadFailureHitMarker;
		}

		/// <summary>场上是否已经存在一只清道夫（定期来袭与信号传感器都靠它做「同时仅一只」的限制）。</summary>
		public static bool AnyAlive()
		{
			for (int i = 0; i < Main.maxNPCs; i++) {
				NPC npc = Main.npc[i];

				if (npc.active && npc.type == ModContent.NPCType<Scavenger>()) {
					return true;
				}
			}

			return false;
		}

		/// <summary>
		/// **服务端 / 单机**权威生成：在玩家斜上方落点召唤清道夫（信号传感器用）。
		/// <para/>联机客户端走 <see cref="WastelandStorySystem.StoryRequest.ScavengerSummon"/> 请求包。
		/// </summary>
		public static bool TrySummonNear(Player player)
		{
			if (player == null || !player.active || AnyAlive()) {
				return false;
			}

			int salt = (int)(Main.GameUpdateCount & 0x7FFFFFFF);
			float side = WastelandRandom.Roll(player.whoAmI, salt, 0, 2) == 0 ? -1f : 1f;
			float distance = WastelandRandom.RollFloatRange(player.whoAmI, salt, 1, 520f, 760f);
			Vector2 position = player.Center + new Vector2(side * distance, -380f);

			int index = NPC.NewNPC(new EntitySource_SpawnNPC(), (int)position.X, (int)position.Y, ModContent.NPCType<Scavenger>());

			if (index >= 0 && index < Main.maxNPCs) {
				Main.npc[index].netUpdate = true;
			}

			WastelandStorySystem.AnnounceFormat("Mods.WastelandSoul.Messages.ScavengerSummoned", new Color(226, 90, 70));
			return true;
		}

		// ==================== 状态位置说明 ====================
		// ModNPC 实例是所有同类 NPC 共用的，因此状态不能放实例字段：
		//   ai[0] = 阶段序号（0/1/2），由阶段状态写入
		//   ai[1] = 状态机当前状态 ID（InnoVault NpcStateMachine 占用，自动同步）
		//   ai[2] = 污染团投放计数（**联机**：ai[] 原版会自动同步，用它给掷骰当种子，见 UpdatePollutionBarrage）
		//   ai[3] = 攻击轮换计数；过载自毁时写入负标记（掉落判定）
		//   localAI[1] = 维修无人机召唤冷却（**服务端**递减，<see cref="SendExtraAI"/> 同步）
		//   localAI[2] = 污染团投放冷却（同上）
		//   localAI[3] = 过载预警次数（仅客户端表现）

		public override void SetStaticDefaults()
		{
			Main.npcFrameCount[Type] = 6;
			NPCID.Sets.MPAllowedEnemies[Type] = true;
		}

		public override void SetDefaults()
		{
			// 体型对齐原版克苏鲁之眼（NPC 4：width 100 / height 110，用 Cecil 从
			// Terraria.NPC.SetDefaults 的 IL 里读出来的）。贴图帧表是 110×110、机体只占其中
			// 74×63（底部大片空白），所以 scale 放大到 1.5 让画面约 111×95 ≈ 眼珠的观感，
			// 再用 DrawOffsetY 把机体上移，使可见机体居中在碰撞箱里（不然会垂到碰撞箱下面）。
			NPC.width = 100;
			NPC.height = 110;
			NPC.scale = 1.5f;
			DrawOffsetY = -21f;
			NPC.aiStyle = -1;                 // 自定义 AI（由状态机驱动）
			NPC.damage = NpcContactDamage;
			NPC.defDamage = NpcContactDamage;
			NPC.defense = 12;                 // 与血肉墙（12）齐平，骷髅王是 10
			NPC.lifeMax = 6000;               // 骷髅王 4400 ~ 血肉墙 8000 之间，取中间档
			NPC.knockBackResist = 0f;
			NPC.noGravity = true;             // 悬浮
			NPC.noTileCollide = true;
			NPC.boss = true;
			NPC.npcSlots = 6f;                // 与骷髅王同级（原来 2f 挡不住杂兵刷新）
			NPC.value = Item.buyPrice(gold: 6);
			NPC.HitSound = SoundID.NPCHit4;   // 金属
			NPC.DeathSound = SoundID.NPCDeath14;
			Music = MusicLoader.GetMusicSlot(Mod, "Music/Scavenger");
		}

		// ==================== 主 AI ====================

		public override void AI()
		{
			ScavengerContext ctx = ScavengerContext.For(NPC);
			Player target = FindTarget(NPC);
			ctx.Target = target;

			// 没有可攻击目标：缓慢上浮并退场，避免卡在世界里
			if (target == null) {
				ScavengerContext.Release(NPC.whoAmI);
				Despawn();
				return;
			}

			NPC.target = target.whoAmI;

			// 持续机制只在权威侧跑计时（客户端靠 SendExtraAI 收冷却，避免污染间隔用错 ai[2]）
			if (Main.netMode != NetmodeID.MultiplayerClient) {
				UpdateRepairDrones();
				UpdatePollutionBarrage();
			}

			// 状态推进 + 阶段判定（阶段由 PhaseController 在 HP 跌破阈值时一次性切过去）
			ctx.Machine.Update();
		}

		/// <summary>卡顿间隔：阶段越高动作越不连贯（阶段二最卡）。</summary>
		internal static float StutterInterval(NPC npc)
		{
			switch ((int)npc.ai[0]) {
				case 0:
					return 14f;
				case 1:
					return 20f;   // 过载修复阶段：移动更卡顿
				default:
					return 10f;   // 协议崩溃：传感器碎裂，动作反而变得急促
			}
		}

		internal static int AttackInterval(NPC npc)
		{
			switch ((int)npc.ai[0]) {
				case 0:
					return AttackIntervalPhaseOne;
				case 1:
					return AttackIntervalPhaseTwo;
				default:
					return AttackIntervalPhaseThree;
			}
		}

		/// <summary>
		/// 目标选择。
		/// <para/>阶段一/二：程序判定「虚弱目标 = 污染严重」，优先攻击血量最低的玩家。
		/// <para/>阶段三：传感器完全碎裂，改为无差别攻击最近的玩家。
		/// </summary>
		internal static Player FindTarget(NPC npc)
		{
			int phase = (int)npc.ai[0];
			Player best = null;
			float bestScore = float.MaxValue;

			for (int i = 0; i < Main.maxPlayers; i++) {
				Player player = Main.player[i];

				if (!player.active || player.dead || player.ghost) {
					continue;
				}

				float distance = Vector2.Distance(player.Center, npc.Center);

				if (distance > 3200f) {
					continue;
				}

				float score = phase >= 2 ? distance : player.statLife;

				if (score < bestScore) {
					bestScore = score;
					best = player;
				}
			}

			return best;
		}

		/// <summary>悬浮跟随目标（stutterGated = true 时套用"卡顿"节流）。</summary>
		internal static void Hover(ScavengerContext ctx, bool stutterGated)
		{
			NPC npc = ctx.Npc;

			if (ctx.Target == null) {
				return;
			}

			if (stutterGated && Main.GameUpdateCount % (uint)StutterInterval(npc) != 0u) {
				return;   // 卡顿：这一帧不更新速度，机体"僵"在原地（用世界帧，联机同值）
			}

			// 主动贴近玩家：
			// 阶段一/二把悬停点压到玩家身侧（几乎贴脸），机体自己会一直往里压，
			// 而不是挂在远处等玩家过来。阶段三稍微抬高，配合锁定射击。
			int phase = (int)npc.ai[0];
			Vector2 hoverPoint = phase >= 2
				? ctx.Target.Center + new Vector2(0f, -120f)
				: ctx.Target.Center + new Vector2(0f, -80f);
			Vector2 direction = hoverPoint - npc.Center;
			float distance = direction.Length();

			if (distance > 16f) {
				direction = Vector2.Normalize(direction);
			}
			else {
				direction = Vector2.Zero;
			}

			float speed = (int)npc.ai[0] >= 1 ? 5.2f : 6.4f;

			// 抖动 **联机安全**：这里改的是 NPC.velocity（同步字段），而服务端与客户端都会跑这段 AI ——
			// 用 Main.rand 的话两边抖的方向不同，机体就会轻微来回跳。
			// 种子取 whoAmI + 世界帧数（都不是随机的），三方同值。
			Vector2 jitter = new Vector2(
				WastelandRandom.RollFloat(npc.whoAmI, (int)Main.GameUpdateCount, 11) * 1.2f - 0.6f,
				WastelandRandom.RollFloat(npc.whoAmI, (int)Main.GameUpdateCount, 23) * 1.2f - 0.6f);

			Vector2 desiredVelocity = direction * speed + jitter;

			npc.velocity = Vector2.Lerp(npc.velocity, desiredVelocity, 0.18f);
		}

		/// <summary>压进到指定距离之内（用于让近战横扫真的能打到人）。</summary>
		internal static void LungeTowards(NPC npc, Player target, float desiredDistance, float speed)
		{
			if (target == null) {
				return;
			}

			Vector2 offset = target.Center - npc.Center;
			float distance = offset.Length();

			if (distance > desiredDistance) {
				Vector2 direction = distance > 1f ? offset / distance : Vector2.Zero;
				npc.velocity = Vector2.Lerp(npc.velocity, direction * speed, 0.25f);
			}
			else {
				npc.velocity *= 0.88f;
			}
		}

		/// <summary>
		/// 过载冲锋的转向：保持速度不变，每 tick 朝目标转一个上限角度，
		/// 因此冲锋可以拐向任意方向、但不会被瞬间贴脸锁死。
		/// </summary>
		internal static void SteerCharge(NPC npc, Player target)
		{
			float speed = npc.velocity.Length();

			if (speed < 1f) {
				speed = 22f;
			}

			float currentAngle = npc.velocity.ToRotation();
			Vector2 toTarget = target.Center - npc.Center;
			float targetAngle = toTarget.LengthSquared() > 1f ? toTarget.ToRotation() : currentAngle;

			float delta = MathHelper.WrapAngle(targetAngle - currentAngle);
			float maxTurn = MathHelper.ToRadians(4.5f);
			float newAngle = currentAngle + MathHelper.Clamp(delta, -maxTurn, maxTurn);

			npc.velocity = newAngle.ToRotationVector2() * speed;
		}

		internal static bool ChargeBlocked(NPC npc)
		{
			return Collision.SolidCollision(npc.position, npc.width, npc.height);
		}

		// ==================== 阶段切换（由 PhaseController 触发对应状态） ====================

		/// <summary>阶段开始时的表现与重置（服务端与客户端都会在状态进入时执行）。</summary>
		internal static void OnPhaseStart(NPC npc, int phase)
		{
			npc.ai[0] = phase;

			if (Main.netMode != NetmodeID.MultiplayerClient) {
				npc.localAI[1] = 60f;    // 阶段二马上开始召唤维修无人机
				npc.netUpdate = true;
			}

			if (Main.dedServ) {
				return;
			}

			SoundEngine.PlaySound(SoundID.Roar, npc.Center);

			if (phase == 1) {
				Main.NewText(Language.GetTextValue("Mods.WastelandSoul.Messages.ScavengerPhaseTwo"), 235, 160, 70);
			}
			else if (phase == 2) {
				Main.NewText(Language.GetTextValue("Mods.WastelandSoul.Messages.ScavengerPhaseThree"), 235, 70, 60);
			}

			for (int i = 0; i < 40; i++) {
				Vector2 velocity = Main.rand.NextVector2Circular(4f, 4f); // sync-ok: Dust only
				Dust.NewDust(npc.position, npc.width, npc.height, DustID.Smoke, velocity.X, velocity.Y, 100, default, 1.6f);
				Dust.NewDust(npc.position, npc.width, npc.height, DustID.Torch, velocity.X, velocity.Y, 100, default, 1.2f);
			}

			WastelandFxSystem.Impact(npc.Center, new Color(255, 168, 70), 1.2f);

			for (int i = 0; i < 4; i++) {
				Vector2 drift = Main.rand.NextVector2Circular(0.9f, 0.4f); // sync-ok: WastelandFx only
				drift.Y -= 0.55f;
				WastelandFxSystem.Smoke(npc.Center, drift, new Color(86, 82, 76), Main.rand.NextFloat(0.8f, 1.3f), Main.rand.Next(26, 40)); // sync-ok
			}

			// ⚠️ 这里原来还会随机甩 2 道 72px 的白色闪电（WastelandFxSystem.Bolt）。
			// 它不表示任何机制，只是"白线糊屏"——玩家明令禁止这类视觉污染，已删除。
			// 见 开发说明.md「特效红线」。**不要加回来。**
		}

		// ==================== 攻击选择与执行（供状态机调用） ====================

		/// <summary>待机结束后挑下一个攻击状态。</summary>
		internal static IVaultState<ScavengerContext> ChooseNextState(ScavengerContext ctx)
		{
			NPC npc = ctx.Npc;
			int phase = (int)npc.ai[0];
			int cycle = (int)npc.ai[3];
			npc.ai[3] += 1f;

			// 阶段三残血：进入自毁式冲锋（谁也别想拖）
			if (phase >= 2 && npc.life / (float)npc.lifeMax <= OverloadChargeThreshold) {
				return new ScavengerChargeWindupState();
			}

			// 阶段三：锁定射击 / 机械臂横扫 / 机体撞击 三选一轮换
			if (phase >= 2) {
				switch (cycle % 3) {
					case 0:
						return new ScavengerBurstWindupState();
					case 1:
						return new ScavengerSweepWindupState();
					default:
						return new ScavengerSlamWindupState();
				}
			}

			// 阶段一/二：机械臂横扫 与 机体撞击 轮换。
			// 只靠悬浮 + 横扫的话机体永远碰不到玩家，撞击才是真正会压上来的手段。
			return cycle % 2 == 0 ? new ScavengerSweepWindupState() : new ScavengerSlamWindupState();
		}

		/// <summary>机体撞击：把速度甩向目标，撞击期间接触伤害提高一档。</summary>
		internal static void ExecuteSlam(NPC npc, Player target)
		{
			npc.damage = NpcSlamDamage;
			npc.defDamage = NpcSlamDamage;

			Vector2 direction = target.Center - npc.Center;

			if (direction.LengthSquared() < 1f) {
				direction = Vector2.UnitY;
			}

			npc.velocity = Vector2.Normalize(direction) * 16f;

			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Roar, npc.Center);
			}
		}

		/// <summary>撞击途中的转向：比过载冲锋灵活得多，能被拉开但不会一味直线。</summary>
		internal static void SteerSlam(NPC npc, Player target)
		{
			float speed = npc.velocity.Length();

			if (speed < 1f) {
				speed = 16f;
			}

			float currentAngle = npc.velocity.ToRotation();
			Vector2 toTarget = target.Center - npc.Center;
			float targetAngle = toTarget.LengthSquared() > 1f ? toTarget.ToRotation() : currentAngle;

			float delta = MathHelper.WrapAngle(targetAngle - currentAngle);
			float maxTurn = MathHelper.ToRadians(9f);
			npc.velocity = (currentAngle + MathHelper.Clamp(delta, -maxTurn, maxTurn)).ToRotationVector2() * speed;
		}

		/// <summary>撞击结束后恢复正常接触伤害。</summary>
		internal static void EndSlam(NPC npc)
		{
			npc.damage = NpcContactDamage;
			npc.defDamage = NpcContactDamage;
		}

		internal static void PlayWindupSound(NPC npc)
		{
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item1, npc.Center);
			}
		}

		/// <summary>阶段一/二的近战范围技：机械臂横扫，范围大、前摇明显。</summary>
		internal static void ExecuteSweep(NPC npc, Player target)
		{
			if (target == null || Main.netMode == NetmodeID.MultiplayerClient) {
				return;
			}

			float startAngle = (target.Center - npc.Center).ToRotation() - MathHelper.PiOver2;
			float sweepDirection = target.Center.X >= npc.Center.X ? 1f : -1f;

			Projectile.NewProjectile(npc.GetSource_FromAI(), npc.Center, Vector2.Zero,
				ModContent.ProjectileType<ScavengerArmSweep>(), BossShotDamage.Half(44), 4f, Main.myPlayer,
				startAngle, sweepDirection, npc.whoAmI);
		}

		/// <summary>
		/// 阶段三：每 3 秒锁定一次「当下」位置后发射子弹。
		/// <para/>锁定位置后不再追踪，配合成组出膛的随机延迟模拟设备老化造成的卡顿。
		/// </summary>
		internal static void FireBurst(NPC npc, Player target)
		{
			if (target == null || Main.netMode == NetmodeID.MultiplayerClient) {
				return;
			}

			Vector2 lockedPosition = target.Center;

			int cycle = (int)npc.ai[2];

			for (int i = 0; i < 3; i++) {
				float delay = 15f + i * 18f + WastelandRandom.RollFloatRange(npc.whoAmI, cycle, i, -6f, 6f);
				Vector2 spawnPosition = npc.Center + WastelandRandom.RollVector2Circular(npc.whoAmI, cycle, 50 + i, 50f, 50f);

				Projectile.NewProjectile(npc.GetSource_FromAI(), spawnPosition, Vector2.Zero,
					ModContent.ProjectileType<ScavengerBullet>(), BossShotDamage.Half(26), 2f, Main.myPlayer,
					lockedPosition.X, lockedPosition.Y, delay);
			}
		}

		internal static void PlayOverloadWarning(ScavengerContext ctx)
		{
			NPC npc = ctx.Npc;
			npc.localAI[3] += 1f; // sync-ok: client-only overload bark counter (no gameplay branch)

			if (Main.dedServ) {
				return;
			}

			SoundEngine.PlaySound(SoundID.Roar, npc.Center);
			Main.NewText(Language.GetTextValue("Mods.WastelandSoul.Messages.ScavengerOverload"), 255, 60, 40);
		}

		internal static void EmitOverloadDust(NPC npc)
		{
			if (!Main.dedServ && Main.rand.NextBool(2)) { // sync-ok: Dust only
				Dust.NewDust(npc.position, npc.width, npc.height, DustID.Smoke, 0f, 0f, 120, default, 1.4f);
			}
		}

		/// <summary>最终手段：因过载自毁式冲锋。</summary>
		internal static void ExecuteCharge(NPC npc, Player target)
		{
			npc.damage = NpcChargeDamage;
			npc.defDamage = NpcChargeDamage;

			Vector2 direction = target.Center - npc.Center;

			if (direction.LengthSquared() < 1f) {
				direction = Vector2.UnitY;
			}

			npc.velocity = Vector2.Normalize(direction) * 22f;

			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item14, npc.Center);
			}
		}

		/// <summary>记录冲锋是否撞到过玩家（用于「被撞死没有掉落」的判定）。</summary>
		internal static void MarkChargeHit(NPC npc)
		{
			if (npc.ai[3] != OverloadFailureMarker) {
				return;
			}

			for (int i = 0; i < Main.maxPlayers; i++) {
				Player player = Main.player[i];

				if (player.active && !player.dead && player.Hitbox.Intersects(npc.Hitbox)) {
					npc.ai[3] = OverloadFailureHitMarker;
					return;
				}
			}
		}

		internal static void BeginSelfDestruct(NPC npc)
		{
			npc.damage = 0;
			npc.defDamage = 0;

			if (!Main.dedServ) {
				Main.NewText(Language.GetTextValue("Mods.WastelandSoul.Messages.ScavengerSelfDestruct"), 255, 90, 60);
			}
		}

		/// <summary>过载爆炸：大范围伤害后机体解体。</summary>
		internal static void Explode(NPC npc)
		{
			if (Main.netMode != NetmodeID.MultiplayerClient) {
				for (int i = 0; i < Main.maxPlayers; i++) {
					Player player = Main.player[i];

					if (!player.active || player.dead) {
						continue;
					}

					if (Vector2.Distance(player.Center, npc.Center) > 260f) {
						continue;
					}

					PlayerDeathReason reason = PlayerDeathReason.ByNPC(npc.whoAmI);
					player.Hurt(reason, 90, player.Center.X < npc.Center.X ? -1 : 1);
				}
			}

			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item14, npc.Center);

				for (int i = 0; i < 60; i++) {
					Vector2 velocity = Main.rand.NextVector2Circular(8f, 8f); // sync-ok: Dust only
					Dust.NewDust(npc.position, npc.width, npc.height, DustID.Smoke, velocity.X, velocity.Y, 80, default, 2f);
					Dust.NewDust(npc.position, npc.width, npc.height, DustID.Torch, velocity.X, velocity.Y, 80, default, 2f);
				}
			}

			// 无论玩家是否被击中，机体都在过载中解体
			npc.StrikeInstantKill();
		}

		// ==================== 阶段二：维修无人机 ====================

		/// <summary>
		/// 召唤维修无人机：只给 Boss 回血、不攻击玩家，玩家必须优先清理它们。
		/// </summary>
		private void UpdateRepairDrones()
		{
			// 只在阶段二（过载修复）召唤。
			// 阶段三起一律不再维修：否则无人机会把血量顶回阶段二阈值以上，看起来就像退回了二阶段。
			if ((int)NPC.ai[0] != 1) {
				return;
			}

			NPC.localAI[1] -= 1f;

			if (NPC.localAI[1] > 0f) {
				return;
			}

			NPC.localAI[1] = DroneSummonCooldown;
			NPC.netUpdate = true;

			int alive = 0;

			for (int i = 0; i < Main.maxNPCs; i++) {
				NPC other = Main.npc[i];

				if (other.active && other.type == ModContent.NPCType<ScavengerRepairDrone>() && (int)other.ai[0] == NPC.whoAmI) {
					alive++;
				}
			}

			if (alive >= MaxRepairDrones) {
				return;
			}

			int slot = alive;
			Vector2 spawnPosition = NPC.Center + WastelandRandom.RollVector2Circular(NPC.whoAmI, slot, (int)NPC.ai[2], 70f, 70f);

			int droneIndex = NPC.NewNPC(NPC.GetSource_FromAI(), (int)spawnPosition.X, (int)spawnPosition.Y,
				ModContent.NPCType<ScavengerRepairDrone>(), 0, NPC.whoAmI, slot);

			if (droneIndex >= 0 && droneIndex < Main.maxNPCs && !Main.dedServ) {
				Main.npc[droneIndex].netUpdate = true;
			}
		}

		// ==================== 破损推进器的污染 ====================

		/// <summary>
		/// 阶段二起，破损推进器不断喷出会追踪玩家的「污染团」。
		/// <para/>投放间隔带随机浮动，对应设备老化造成的卡顿与不规则。
		///
		/// <para/>⚠️ **联机安全**（2026-10-09 修）：这里的冷却**必须每台机器都算成同一个值** ——
		/// 旧代码用 <c>Main.rand.Next</c> 掷间隔，服务端和客户端的冷却会不一样长
		/// （客户端虽然不生成弹幕，但它一样在跑这段 AI：冷却不同步会让服务端的下一发
		/// "看起来"比客户端预期的更早/更晚）。现在用 <see cref="WastelandRandom"/>，
		/// 种子取已同步的 <c>whoAmI</c> + 阶段 <c>ai[0]</c> + c冷却序号，三方同值。
		/// </summary>
		private void UpdatePollutionBarrage()
		{
			if ((int)NPC.ai[0] < 1) {
				return;
			}

			NPC.localAI[2] -= 1f;

			if (NPC.localAI[2] > 0f) {
				return;
			}

			// ai[2] = 投放计数；冷却掷骰必须在服务端用递增后的序号，再同步给客户端。
			NPC.ai[2] += 1f;
			NPC.localAI[2] = PollutionCooldown
				+ WastelandRandom.Roll(NPC.whoAmI, (int)NPC.ai[0], (int)NPC.ai[2], -45, 46);
			NPC.netUpdate = true;

			int count = (int)NPC.ai[0] >= 2 ? 3 : 2;

			int barrageCycle = (int)NPC.ai[2];

			for (int i = 0; i < count; i++) {
				Vector2 spawnPosition = NPC.Center + WastelandRandom.RollVector2Circular(NPC.whoAmI, barrageCycle, i * 2, 56f, 56f);
				Vector2 velocity = WastelandRandom.RollVector2Circular(NPC.whoAmI, barrageCycle, i * 2 + 1, 2.4f, 2.4f);

				Projectile.NewProjectile(NPC.GetSource_FromAI(), spawnPosition, velocity,
					ModContent.ProjectileType<PollutionHoming>(), BossShotDamage.Half(24), 1f, Main.myPlayer);
			}
		}

		// ==================== 退场 ====================

		private void Despawn()
		{
			NPC.velocity.X *= 0.95f;
			NPC.velocity.Y -= 0.2f;
			NPC.EncourageDespawn(30);
		}

		/// <inheritdoc/>
		public override void SendExtraAI(BinaryWriter writer)
		{
			writer.Write(NPC.localAI[1]);
			writer.Write(NPC.localAI[2]);
		}

		/// <inheritdoc/>
		public override void ReceiveExtraAI(BinaryReader reader)
		{
			NPC.localAI[1] = reader.ReadSingle();
			NPC.localAI[2] = reader.ReadSingle();
		}

		// ==================== 帧动画 ====================

		public override void FindFrame(int frameHeight)
		{
			NPC.frameCounter += 1.0;

			// 迟滞的悬浮动画：帧切换本身就慢一拍
			if (NPC.frameCounter >= 8.0) {
				NPC.frameCounter = 0.0;
				NPC.frame.Y += frameHeight;

				if (NPC.frame.Y >= Main.npcFrameCount[Type] * frameHeight) {
					NPC.frame.Y = 0;
				}
			}
		}

		// ==================== 掉落与剧情推进 ====================

		public override void ModifyNPCLoot(NPCLoot npcLoot)
		{
			// 掉落条件：只有「被玩家正常击败」才掉落。
			// 进入过载自毁（没能在冲锋前击败它）则一件战利品都不给——
			// 由于清道夫每 5 天会再来一次，这不是死路。想改判定见 NoLootOnAnySelfDestruct。
			LeadingConditionRule defeatedProperly = new LeadingConditionRule(new DefeatedByPlayerCondition());

			// Boss 掉落统一装进掉落袋：打开后保底材料 + 必定灵魂碎片 + 随机词条装备
			defeatedProperly.OnSuccess(ItemDropRule.Common(ModContent.ItemType<Content.Items.Bags.ScavengerBag>(), 1));

			// 10% 奖杯（与原版 Boss 掉落奖杯的做法一致）：同样挂在"被玩家正常击败"的条件上，
			// 过载自毁依旧什么都不掉。
			defeatedProperly.OnSuccess(ItemDropRule.Common(ModContent.ItemType<ScavengerTrophy>(), 10));

			npcLoot.Add(defeatedProperly);
		}

		/// <summary>
		/// 掉落条件：这次死亡不是过载自毁造成的。
		/// <para/>ModifyNPCLoot 只在加载期运行一次，动态判定必须放进规则本身（即这个条件）。
		/// </summary>
		private class DefeatedByPlayerCondition : IItemDropRuleCondition
		{
			public bool CanDrop(DropAttemptInfo info)
			{
				return CountsAsPlayerDefeat(info.npc);
			}

			public bool CanShowItemDropInUI()
			{
				return true;
			}

			public string GetConditionDescription()
			{
				return null;
			}
		}

		public override void OnKill()
		{
			ScavengerContext.Release(NPC.whoAmI);

			// 过载自毁 = 没能在冲锋前击败它：不推进剧情（掉落同样被上面条件拦住）
			if (!CountsAsPlayerDefeat(NPC)) {
				if (!Main.dedServ) {
					Main.NewText(Language.GetTextValue("Mods.WastelandSoul.Messages.ScavengerWrecked"), 190, 100, 80);
				}

				return;
			}

			// 正常击败后「壁炉」入口开启（壁炉结构本体见开发优先级 4）
			WastelandStorySystem.MarkScavengerDefeated();
		}
	}
}
