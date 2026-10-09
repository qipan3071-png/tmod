using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Content.Items.Weapons.Boss1Scavenger.ScavengerDrops;

namespace WastelandSoul.Content.Projectiles.Scavenger
{
	// ====================================================================================
	// Boss 1「清道夫」B 线（掉落武器）的三个「只对本武器生效」接线钩子。
	//
	// 全部按标记判定，绝不会影响原版 / 别的模组的弹幕：
	//   · SwordBeamHook      —— 只认 ai[2] == ScavengerBeam.Mark 的原版刀光（ai[1] 留给原版）
	//   · ArrowHomingHook    —— 只认「本弓射出的邪箭」（OnSpawn 按武器来源打标记）
	//   · PollutionShellHook —— 只认污染炮自己的炮弹弹幕类型
	//
	// 每帧钩子（AI / PostAI）只改数值、做一次性小特效，**不做**自动拖尾或线状特效
	// （tools/check_no_auto_trails.py 会拦）。
	//
	// ── 关于「标记要不要额外补一次联网同步」的结论（已按 tModLoader.dll 的 IL 核实）──
	// 原版 `Projectile.NewProjectile` 的尾部顺序是：
	//     636 ApplyStatsFromSource(source)
	//     638 ProjectileLoader.OnSpawn(projectile, source)   ← 我们的标记就是在这里写的
	//     644 NetMessage.SendData(27 /* SyncProjectile */, ...)  ← 同一次调用里紧接着发包
	// 而 `MessageID.SyncProjectile` 的载荷（SendData 里那一段）会按位写入
	// `ai[0]/ai[1]/ai[2]`（只要该槽 != 0 就会带上对应标志位并写入这个 float）。
	// 所以：**在 OnSpawn 里写的标记，天然就跟着「生成时那一条同步包」过去了**，
	// 不需要再补 `netUpdate`。补了反而会让这些弹幕多收一条冗余包（每条只多一次，
	// 不会每帧发，但纯属多余，而且对刀光/炮弹还会把原版槽位的值一起推过去）。
	// ====================================================================================

	/// <summary>清道夫大刀刀光：穿透 4 段 + 一点点金属火花。</summary>
	public class SwordBeamHook : GlobalProjectile
	{
		public override void AI(Projectile projectile)
		{
			if (projectile.type != ProjectileID.SwordBeam || projectile.ai[2] != ScavengerBeam.Mark) {
				return;
			}

			if (projectile.penetrate != ScavengerBeam.PenetrateHits) {
				projectile.penetrate = ScavengerBeam.PenetrateHits;
			}

			if (!Main.dedServ && Main.rand.NextBool(4)) {
				Dust dust = Dust.NewDustDirect(projectile.position, projectile.width, projectile.height, DustID.Iron, projectile.velocity.X * 0.2f, projectile.velocity.Y * 0.2f);
				dust.noGravity = true;
				dust.scale = 0.8f;
			}
		}
	}

	/// <summary>精钢弓：把本弓射出的邪箭变成缓转向追踪箭。</summary>
	public class ArrowHomingHook : GlobalProjectile
	{
		/// <summary>标记：本弓射出的那支箭。</summary>
		public const float HomingMark = 1f;

		/// <summary>锁定半径。</summary>
		private const float SearchRange = 680f;

		/// <summary>每帧最多转多少弧度 —— 缓转向，不是瞬间锁头。</summary>
		private const float MaxTurnPerFrame = 0.055f;

		/// <summary>巡航速度上限。</summary>
		private const float CruiseSpeed = 14f;

		public override void OnSpawn(Projectile projectile, IEntitySource source)
		{
			// 只给「本弓射出来的」那支邪箭打标记：武器来源正是本模组的精钢弓
			if (projectile.type != ProjectileID.UnholyArrow) {
				return;
			}

			if (source is not EntitySource_ItemUse_WithAmmo itemSource) {
				return;
			}

			if (itemSource.Item.type != ModContent.ItemType<SteelBow>()) {
				return;
			}

			// 标记写在 ai[1]（非 0）。**这里不需要补 netUpdate**：
			// OnSpawn 在 Projectile.NewProjectile 里跑在发包之前（IL 顺序 638 → 644），
			// 而 SyncProjectile 的载荷本身就会带上非 0 的 ai[1]，
			// 所以服务端和别的客户端收到时已经带着这个标记了（详见本文件顶部结论）。
			projectile.ai[1] = HomingMark;
		}

		public override void AI(Projectile projectile)
		{
			if (projectile.type != ProjectileID.UnholyArrow || projectile.ai[1] != HomingMark) {
				return;
			}

			if (projectile.velocity.LengthSquared() < 0.01f) {
				return;
			}

			NPC target = projectile.FindTargetWithinRange(SearchRange, false);

			if (target == null) {
				return;
			}

			// 缓转向：每帧最多转 MaxTurnPerFrame，转过头之后再补一点速度
			float current = projectile.velocity.ToRotation();
			float desired = (target.Center - projectile.Center).ToRotation();
			float next = Utils.AngleTowards(current, desired, MaxTurnPerFrame);

			projectile.velocity = next.ToRotationVector2() * MathHelper.Min(projectile.velocity.Length() + 0.08f, CruiseSpeed);
			projectile.rotation = next + MathHelper.PiOver2;
		}
	}

	/// <summary>
	/// 污染炮：炮弹消失时在原地留一小片污染云。
	/// <para/>认弹幕**类型**（<see cref="PollutionShell"/>）而不是 ai 槽：
	/// 原版手榴弹的 AI 只写 <c>localAI[0]/localAI[1]</c>（已核对 IL），不碰 <c>ai</c>，
	/// 所以炮弹上的标记也不用担心被原版覆盖。
	/// </summary>
	public class PollutionShellHook : GlobalProjectile
	{
		/// <summary>云伤害 = 炮弹伤害 × 0.35（溅射，别抢直击）。</summary>
		private const float CloudDamageRatio = 0.35f;

		/// <summary>炮弹剩多少帧时开始布云（原版手榴弹靠 AI 自己倒计时爆炸）。</summary>
		private const int CloudLeadFrames = 6;

		public override void PostAI(Projectile projectile)
		{
			if (projectile.type != ModContent.ProjectileType<PollutionShell>()) {
				return;
			}

			if (projectile.timeLeft > CloudLeadFrames || projectile.owner != Main.myPlayer) {
				return;
			}

			projectile.ai[1] = 0f;   // 只布一次

			Projectile.NewProjectile(
				projectile.GetSource_FromAI(),
				projectile.Center,
				Vector2.Zero,
				ModContent.ProjectileType<PollutionCloud>(),
				(int)(projectile.damage * CloudDamageRatio),
				0f,
				projectile.owner,
				0f,
				0f);
		}
	}
}
