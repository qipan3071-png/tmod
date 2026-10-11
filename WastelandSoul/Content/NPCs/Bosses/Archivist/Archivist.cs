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
using WastelandSoul.Content.Buffs;
using WastelandSoul.Content.Items.Bags;
using WastelandSoul.Content.Items.Decor;
using WastelandSoul.Content.Projectiles.Archivist;

namespace WastelandSoul.Content.NPCs.Bosses.Archivist
{
	/// <summary>
	/// Boss 2：归档者（Archivist）。
	/// <para/>「守望者计划」的审计单元，专门回收原型机外泄的记忆——它的出现解释了智械人的数据为何开始不稳定。
	/// <para/>定位：困难模式**机械三王一级**（BossChecklist 进度 7.5）。原版参照（Cecil 读 Terraria.NPC.SetDefaults）：
	/// 视网膜术士 20000/45/10、毁灭魔焰 23000/50/10、机械骷髅王 28000/47/24、毁灭者 80000/70/0（这条是特例，不跟）。
	/// 所以本体取三家中间值 24000 血、45 接触、24 防御。
	/// <para/>美术风格：档案 / 索引 / 纸页 + 骨白冷色（与清道夫的冷灰废料、灰烬之心的暖橙余烬、壁炉守卫的冷白金属区分）。
	/// <para/>行为逻辑交给 InnoVault 的状态机：两阶段共 6 个 <c>[VaultState]</c> 状态，见 <c>ArchivistStates.cs</c>。
	/// </summary>
	[AutoloadBossHead]
	public class Archivist : ModNPC
	{
		// ==================== 阶段阈值 ====================

		/// <summary>阶段二（50%）：火切到植物和水。切阶段时挂翅膀灼烧。</summary>
		public const float PhaseTwoThreshold = 0.50f;

		// ==================== 攻击间隔（越小越凶） ====================
		// 机械三王档：比原来「骷髅王后」时期整体快一档（招式更密），但仍保留前三档的明显前摇。

		internal const int AttackIntervalPhaseOne = 150;
		internal const int AttackIntervalPhaseTwo = 110;

		internal const int TelegraphTicks = 36;
		internal const int AnimIdle = 0;
		internal const int AnimTelegraph = 1;
		internal const int AnimAttack = 2;

		internal const int ArenaRadiusTiles = 80;
		internal const float ArenaRadius = ArenaRadiusTiles * 16f;
		internal const int ArenaTickDamage = 12;
		internal const int ArenaHurtInterval = 24;

		internal const int FireballFuse = 120;
		internal const float FireballSpeed = 5f;
		internal const int MiniFireballCount = 6;
		internal const float MiniFireballSpeed = 3.5f;
		internal const int FireballDamage = 36;
		internal const int MiniFireballDamage = 18;
		internal const int FireballSize = 124;

		internal const int FirePillarWidth = 80;
		internal const int FirePillarMax = 2;
		internal const int FirePillarHeightTiles = 256;
		internal const int FirePillarHeight = FirePillarHeightTiles * 16;
		internal const int FirePillarDuration = 1500;
		internal const int FirePillarGapMin = 10;
		internal const int FirePillarGapMax = 26;
		internal const int FirePillarDamage = 28;

		internal const int VenomCount = 10;
		internal const float VenomSpeed = 3.2f;
		internal const int VenomLife = 180;
		internal const int VenomDamage = 24;

		internal const int BubbleStormTicks = 1500;
		internal const int BubbleMax = 20;
		internal const float BubbleRise = -2.2f;
		internal const int BubbleDropTiles = 50;
		internal const int BubbleCeilingTiles = 50;
		internal const int BubbleTrapTicks = 72;
		internal const int BubbleDamage = 30;

		internal const int BurstHealThreshold = 2400;
		internal const int BurstHealAmount = 1200;
		internal const int BurstHealCooldown = 300;

		// ==================== 伤害（机械三王档：接触 45 / 弹幕 22~38） ====================

		/// <summary>接触伤害。</summary>
		internal const int ContactDamage = 45;

		internal const float HoverDefault = 260f;
		internal const float HoverSpeedFar = 10.5f;
		internal const float HoverSpeedNear = 6.5f;

		// 旧招式弹幕类还在（武器/掉落物会读这些常量），本体 AI 已经不再生成它们。
		internal const int BeamWindup = 42;
		internal const int SealWarnTicks = 30;
		internal const int SealHoldTicks = 30;

		internal static float StepBeamAngle(ArchivistContext context, int timer)
		{
			return context.Npc.ai[3];
		}

		public override void SetStaticDefaults()
		{
			Main.npcFrameCount[Type] = 7;
			NPCID.Sets.BossBestiaryPriority.Add(Type);
			NPCID.Sets.MPAllowedEnemies[Type] = true;
		}

		public override void SetDefaults()
		{
			// ChatGPT 定稿：坐在悬浮杖上 292×292（最近邻）。碰撞只包身子和书，杖露在盒子外。
			// 玩家 2026-10-11：模型改为当时大小的 0.4 倍。
			NPC.width = 53;
			NPC.height = 67;
			NPC.scale = 0.4f;
			NPC.damage = ContactDamage;
			NPC.defDamage = ContactDamage;
			NPC.defense = 24;              // 与机械骷髅王（24）齐平
			NPC.lifeMax = 24000;           // 机械三王档：视网膜 20000 / 魔焰 23000 / 机械骷髅王 28000 之间
			NPC.knockBackResist = 0f;
			NPC.noGravity = true;
			NPC.noTileCollide = true;
			NPC.boss = true;
			NPC.aiStyle = -1;              // 自定义 AI（由状态机驱动）
			NPC.npcSlots = 12f;
			NPC.value = Item.buyPrice(gold: 12);
			NPC.HitSound = SoundID.NPCHit4;
			NPC.DeathSound = SoundID.NPCDeath14;
			Music = MusicLoader.GetMusicSlot(Mod, "Music/Archivist");
		}

		// ==================== 主 AI ====================

		public override void AI()
		{
			ArchivistContext context = ArchivistContext.For(NPC);
			context.Target = FindTarget(NPC);

			// 没有可攻击目标：缓慢上浮退场，避免卡在世界里
			if (context.Target == null) {
				ArchivistContext.Release(NPC.whoAmI);
				NPC.velocity.X *= 0.95f;
				NPC.velocity.Y -= 0.2f;
				NPC.EncourageDespawn(30);
				return;
			}

			NPC.target = context.Target.whoAmI;
			EnsureArena(context);
			TickArena(context);
			TickBurstHeal(context);
			context.Machine.Update();
			NPC.spriteDirection = context.Target.Center.X > NPC.Center.X ? 1 : -1;
			NPC.rotation = MathHelper.Clamp(NPC.velocity.X * 0.006f, -0.08f, 0.08f);

			if ((int)NPC.ai[0] >= 1) {
				ApplyWingBurn();
			}
		}

		/// <summary>目标选择：最近的存活玩家（归档者不做"优先攻击弱者"那套，它只归档最近的样本）。</summary>
		internal static Player FindTarget(NPC npc)
		{
			Player best = null;
			float bestDistance = 3600f;

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

		// ==================== 运动辅助（供状态类调用） ====================

		/// <summary>位移对齐拜月教邪教徒：停在玩家身侧、略高于胸口，不钉在头顶。过近就换边，隔一段时间瞬移一次。</summary>
		internal static void Hover(ArchivistContext context, float distance)
		{
			NPC npc = context.Npc;

			if (context.Target == null) {
				return;
			}

			Player target = context.Target;
			float side = npc.Center.X >= target.Center.X ? 1f : -1f;
			float standoff = 288f;

			if (Vector2.Distance(npc.Center, target.Center) < 96f) {
				side = target.Center.X >= npc.Center.X ? 1f : -1f;
				standoff = 368f;
			}

			Vector2 perch = target.Center + new Vector2(side * standoff, -40f);

			if (Main.GameUpdateCount % 280u == 0u) {
				npc.Center = perch;
				npc.velocity = Vector2.Zero;
				npc.netUpdate = true;
				return;
			}

			Vector2 offset = perch - npc.Center;
			float speed = offset.Length() > 420f ? HoverSpeedFar : HoverSpeedNear;

			if (offset.LengthSquared() > 64f) {
				npc.velocity = (npc.velocity * 10f + Vector2.Normalize(offset) * speed) / 11f;
			}
			else {
				npc.velocity *= 0.92f;
			}
		}

		internal static void SetContactDamage(NPC npc, int damage)
		{
			npc.damage = damage;
			npc.defDamage = damage;
		}

		internal static void SetAnim(NPC npc, int anim)
		{
			if ((int)npc.ai[3] == anim) {
				return;
			}

			npc.ai[3] = anim;
			npc.frameCounter = 0.0;
			int start = anim == AnimTelegraph ? 3 : anim == AnimAttack ? 4 : 0;
			npc.frame.Y = start * npc.frame.Height;
		}

		internal static int RollAttackDelay(ArchivistContext context)
		{
			NPC npc = context.Npc;
			int baseDelay = (int)npc.ai[0] >= 1 ? AttackIntervalPhaseTwo : AttackIntervalPhaseOne;
			return baseDelay + WastelandRandom.Roll(npc.whoAmI, (int)npc.ai[2], -12, 13);
		}

		internal static IVaultState<ArchivistContext> ChooseNextState(ArchivistContext context)
		{
			NPC npc = context.Npc;
			int cycle = (int)npc.ai[2];
			npc.ai[2] += 1f;

			if ((int)npc.ai[0] >= 1) {
				return (cycle % 4) switch {
					0 => new ArchivistFireballState(),
					1 => new ArchivistFirePillarState(),
					2 => new ArchivistVenomState(),
					_ => new ArchivistBubbleStormState()
				};
			}

			return cycle % 2 == 0 ? new ArchivistFireballState() : new ArchivistFirePillarState();
		}

		internal static void OnPhaseStart(NPC npc, int phase)
		{
			npc.ai[0] = phase;
			SetContactDamage(npc, ContactDamage);
			npc.velocity *= 0.3f;
			npc.netUpdate = true;

			if (Main.dedServ) {
				return;
			}

			SoundEngine.PlaySound(SoundID.Roar, npc.Center);
			Main.NewText(Language.GetTextValue("Mods.WastelandSoul.Messages.ArchivistPhaseTwo"), 160, 120, 190);

			for (int i = 0; i < 24; i++) {
				Vector2 velocity = Main.rand.NextVector2Circular(3.2f, 3.2f); // sync-ok: Dust only
				Dust.NewDust(npc.position, npc.width, npc.height, DustID.Plantera_Pink, velocity.X, velocity.Y, 80, default, 1.2f);
			}
		}

		internal static void PlayCastSound(NPC npc)
		{
			if (!Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item24, npc.Center);
			}
		}

		internal static void ApplyWingBurn()
		{
			for (int i = 0; i < Main.maxPlayers; i++) {
				Player player = Main.player[i];

				if (player.active && !player.dead && !player.ghost) {
					player.AddBuff(ModContent.BuffType<ArchivistWingBurn>(), 90);
				}
			}
		}

		internal static void SpawnFireball(ArchivistContext context)
		{
			if (!WastelandNet.IsAuthoritativeSide || context.Target == null) {
				return;
			}

			Vector2 delta = context.Target.Center - context.Npc.Center;
			Vector2 velocity = delta.LengthSquared() > 1f
				? Vector2.Normalize(delta) * FireballSpeed
				: new Vector2(0f, FireballSpeed);

			Projectile.NewProjectile(
				context.Npc.GetSource_FromAI(),
				context.Npc.Center,
				velocity,
				ModContent.ProjectileType<ArchivistFireball>(),
				BossShotDamage.Half(FireballDamage),
				1.2f,
				Main.myPlayer);
		}

		internal static void SpawnFirePillars(ArchivistContext context)
		{
			if (!WastelandNet.IsAuthoritativeSide || context.Target == null) {
				return;
			}

			int alive = CountProjectiles(ModContent.ProjectileType<ArchivistFirePillar>());
			int want = FirePillarMax - alive;

			if (want <= 0) {
				return;
			}

			NPC npc = context.Npc;
			int gapTiles = WastelandRandom.Roll(npc.whoAmI, (int)npc.ai[2], 17, FirePillarGapMin, FirePillarGapMax);
			float gap = gapTiles * 16f;
			float mid = context.Target.Center.X;
			float left = mid - gap * 0.5f;
			float right = mid + gap * 0.5f;
			float[] xs = want >= 2 ? new[] { left, right } : new[] { npc.Center.X >= mid ? right : left };

			for (int i = 0; i < xs.Length; i++) {
				Vector2 top = new Vector2(xs[i] - FirePillarWidth * 0.5f, context.Target.Center.Y - FirePillarHeight * 0.5f);
				int identity = Projectile.NewProjectile(
					npc.GetSource_FromAI(),
					top,
					Vector2.Zero,
					ModContent.ProjectileType<ArchivistFirePillar>(),
					BossShotDamage.Half(FirePillarDamage),
					0.5f,
					Main.myPlayer,
					npc.whoAmI);
				Main.projectile[identity].netUpdate = true;
			}
		}

		internal static void SpawnVenomRing(ArchivistContext context)
		{
			if (!WastelandNet.IsAuthoritativeSide) {
				return;
			}

			for (int i = 0; i < VenomCount; i++) {
				float angle = MathHelper.TwoPi * i / VenomCount;
				Vector2 velocity = angle.ToRotationVector2() * VenomSpeed;
				Projectile.NewProjectile(
					context.Npc.GetSource_FromAI(),
					context.Npc.Center,
					velocity,
					ModContent.ProjectileType<ArchivistVenomSeed>(),
					BossShotDamage.Half(VenomDamage),
					0.4f,
					Main.myPlayer);
			}
		}

		internal static void StartBubbleStorm(ArchivistContext context)
		{
			if (!WastelandNet.IsAuthoritativeSide) {
				return;
			}

			if (CountProjectiles(ModContent.ProjectileType<ArchivistBubbleStorm>()) > 0) {
				return;
			}

			int identity = Projectile.NewProjectile(
				context.Npc.GetSource_FromAI(),
				context.Npc.Center,
				Vector2.Zero,
				ModContent.ProjectileType<ArchivistBubbleStorm>(),
				BossShotDamage.Half(BubbleDamage),
				0.2f,
				Main.myPlayer,
				context.Npc.whoAmI);
			Main.projectile[identity].netUpdate = true;
		}

		internal static void EnsureArena(ArchivistContext context)
		{
			if (!context.ArenaReady) {
				context.ArenaCenter = context.Npc.Center;
				context.ArenaReady = true;
			}

			if (!WastelandNet.IsAuthoritativeSide) {
				return;
			}

			if (CountProjectiles(ModContent.ProjectileType<ArchivistArenaMist>()) > 0) {
				return;
			}

			int identity = Projectile.NewProjectile(
				context.Npc.GetSource_FromAI(),
				context.ArenaCenter,
				Vector2.Zero,
				ModContent.ProjectileType<ArchivistArenaMist>(),
				0,
				0f,
				Main.myPlayer,
				context.Npc.whoAmI,
				context.ArenaCenter.X,
				context.ArenaCenter.Y);
			Main.projectile[identity].netUpdate = true;
		}

		internal static void TickArena(ArchivistContext context)
		{
			if (!context.ArenaReady || !WastelandNet.IsAuthoritativeSide) {
				return;
			}

			if (Main.GameUpdateCount % ArenaHurtInterval != 0) {
				return;
			}

			for (int i = 0; i < Main.maxPlayers; i++) {
				Player player = Main.player[i];

				if (!player.active || player.dead || player.ghost) {
					continue;
				}

				if (Vector2.Distance(player.Center, context.ArenaCenter) <= ArenaRadius) {
					continue;
				}

				player.Hurt(PlayerDeathReason.ByNPC(context.Npc.whoAmI), ArenaTickDamage, 0);
			}
		}

		internal static void TickBurstHeal(ArchivistContext context)
		{
			context.TickBurstWindow();

			if ((int)context.Npc.ai[0] < 1) {
				return;
			}

			if (!WastelandNet.IsAuthoritativeSide || context.HealCooldown > 0) {
				return;
			}

			if (context.BurstSum() < BurstHealThreshold) {
				return;
			}

			NPC npc = context.Npc;
			npc.life = Math.Min(npc.lifeMax, npc.life + BurstHealAmount);
			context.HealCooldown = BurstHealCooldown;
			npc.netUpdate = true;
			CombatText.NewText(npc.Hitbox, new Color(140, 210, 150), Language.GetTextValue("Mods.WastelandSoul.Messages.ArchivistLightRegen"));
		}

		internal static Vector2 FindSurface(float worldX, float worldY)
		{
			int tileX = (int)(worldX / 16f);
			int tileY = (int)(worldY / 16f);
			tileX = Utils.Clamp(tileX, 20, Main.maxTilesX - 20);
			tileY = Utils.Clamp(tileY, 20, Main.maxTilesY - 20);

			for (int y = tileY; y < Main.maxTilesY - 20 && y < tileY + 90; y++) {
				Tile tile = Framing.GetTileSafely(tileX, y);

				if (tile.HasUnactuatedTile && Main.tileSolid[tile.TileType]) {
					return new Vector2(tileX * 16f + 8f, y * 16f);
				}
			}

			return new Vector2(worldX, worldY + 320f);
		}

		internal static int CountProjectiles(int type)
		{
			int count = 0;

			for (int i = 0; i < Main.maxProjectiles; i++) {
				Projectile projectile = Main.projectile[i];

				if (projectile.active && projectile.type == type) {
					count++;
				}
			}

			return count;
		}

		public override void FindFrame(int frameHeight)
		{
			int anim = (int)NPC.ai[3];
			int start = anim == AnimTelegraph ? 3 : anim == AnimAttack ? 4 : 0;
			int count = anim == AnimTelegraph ? 1 : 3;
			int local = NPC.frame.Y / frameHeight - start;

			if (local < 0 || local >= count) {
				NPC.frame.Y = start * frameHeight;
				NPC.frameCounter = 0.0;
				return;
			}

			NPC.frameCounter += 1.0;

			if (NPC.frameCounter >= 8.0) {
				NPC.frameCounter = 0.0;
				local = (local + 1) % count;
				NPC.frame.Y = (start + local) * frameHeight;
			}
		}

		public override void OnHitByItem(Player player, Item item, NPC.HitInfo hit, int damageDone)
		{
			ArchivistContext.For(NPC).AddBurstDamage(hit.Damage);
		}

		public override void OnHitByProjectile(Projectile projectile, NPC.HitInfo hit, int damageDone)
		{
			ArchivistContext.For(NPC).AddBurstDamage(hit.Damage);
		}

		public override void ModifyNPCLoot(NPCLoot npcLoot)
		{
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<ArchivistBag>(), 1));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<ArchivistTrophy>(), 10));
		}

		public override void OnKill()
		{
			int pillar = ModContent.ProjectileType<ArchivistFirePillar>();
			int storm = ModContent.ProjectileType<ArchivistBubbleStorm>();

			for (int i = 0; i < Main.maxProjectiles; i++) {
				Projectile projectile = Main.projectile[i];

				if (projectile.active && (projectile.type == pillar || projectile.type == storm)) {
					projectile.Kill();
				}
			}

			ArchivistContext.Release(NPC.whoAmI);
			WastelandStorySystem.MarkArchivistDefeated();
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
