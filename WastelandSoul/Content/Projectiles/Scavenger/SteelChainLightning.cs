using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.Effects;

namespace WastelandSoul.Content.Projectiles.Scavenger
{
	/// <summary>
	/// 精钢放电器的链状闪电。
	/// <para/>第 1 帧锁定一条最多 4 个敌人的链（先最近的，再依次跳到附近的下一个），
	/// 立刻逐跳结算伤害（每跳 ×0.75 递减，并挂「带电」+「缓慢」），
	/// 之后十几帧把这条链用 <see cref="WastelandFxSystem.Bolt"/> 画出来。
	/// <para/>贴图复用原版 <see cref="ProjectileID.ThunderStaffShot"/>，全程手绘。
	/// </summary>
	public class SteelChainLightning : ModProjectile
	{
		/// <summary>链最多挂几个敌人。</summary>
		private const int MaxTargets = 4;

		/// <summary>找下一个目标的搜索半径。</summary>
		private const float JumpRange = 360f;

		/// <summary>每跳伤害倍率。</summary>
		private const float JumpFalloff = 0.75f;

		/// <summary>命中挂的减益时长。</summary>
		private const int DebuffTime = 240;

		public override void SetStaticDefaults()
		{
			TextureAssets.Projectile[Type] = TextureAssets.Projectile[ProjectileID.ThunderStaffShot];
		}

		public override void SetDefaults()
		{
			Projectile.width = 24;
			Projectile.height = 24;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Magic;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = 14;
			Projectile.aiStyle = -1;
		}

		public override bool? CanDamage()
		{
			return false;   // 伤害在第 1 帧直接结算，不靠碰撞
		}

		public override void AI()
		{
			if (Projectile.localAI[0] != 0f) {
				return;
			}

			Projectile.localAI[0] = 1f;
			BuildChain();
		}

		/// <summary>从起点向外找目标，逐跳结算伤害并记下折线拐点。</summary>
		private void BuildChain()
		{
			List<Vector2> anchors = new List<Vector2> { Projectile.Center };
			HashSet<int> visited = new HashSet<int>();
			Vector2 from = Projectile.Center;
			int maxTargets = System.Math.Clamp((int)Projectile.ai[0], 2, MaxTargets);
			float damageScale = 1f;
			int hits = 0;

			for (int jump = 0; jump < maxTargets; jump++) {
				NPC target = FindNext(from, visited);

				if (target == null) {
					break;
				}

				visited.Add(target.whoAmI);
				Vector2 hitPoint = ImpactPoint(target);
				anchors.Add(hitPoint);

				if (Projectile.owner == Main.myPlayer) {
					Strike(target, hitPoint, damageScale);
				}

				from = hitPoint;
				damageScale *= JumpFalloff;
				hits++;
			}

			if (hits == 0) {
				// 一个目标都没挂上：放一道空电弧，然后自己消失
				anchors.Add(Projectile.Center + Projectile.velocity.SafeNormalize(Vector2.UnitX) * 160f);
			}

			for (int i = 1; i < anchors.Count; i++) {
				Projectile.ai[i] = anchors[i].X;
				Projectile.localAI[i + 2] = anchors[i].Y;
			}

			Projectile.ai[0] = anchors.Count;
			Projectile.localAI[1] = hits;
		}

		/// <summary>离 <paramref name="from"/> 最近的、还没被这条链打过的敌人。</summary>
		private NPC FindNext(Vector2 from, HashSet<int> visited)
		{
			NPC best = null;
			float bestDistance = JumpRange * JumpRange;

			for (int i = 0; i < Main.maxNPCs; i++) {
				NPC npc = Main.npc[i];

				if (!npc.active || npc.friendly || npc.dontTakeDamage || visited.Contains(npc.whoAmI)) {
					continue;
				}

				if (!npc.CanBeChasedBy(Projectile)) {
					continue;
				}

				float distance = Vector2.DistanceSquared(npc.Center, from);

				if (distance < bestDistance) {
					bestDistance = distance;
					best = npc;
				}
			}

			return best;
		}

		/// <summary>命中点：目标碰撞箱内偏上一点，避免整条链都指着脚底。</summary>
		private static Vector2 ImpactPoint(NPC target)
		{
			Vector2 point = target.Center;
			point.Y -= target.height * 0.15f;
			point.X = MathHelper.Clamp(point.X, target.position.X + 4f, target.position.X + target.width - 4f);
			point.Y = MathHelper.Clamp(point.Y, target.position.Y + 4f, target.position.Y + target.height - 4f);

			return point;
		}

		/// <summary>对单个目标结算伤害 + 两个减益。</summary>
		private void Strike(NPC target, Vector2 hitPoint, float damageScale)
		{
			int damage = System.Math.Max((int)(Projectile.damage * damageScale), 1);
			int direction = Projectile.Center.X < target.Center.X ? 1 : -1;
			float knockback = Projectile.knockBack * damageScale;

			NPC.HitInfo hit = new NPC.HitInfo {
				Damage = damage,
				Knockback = knockback,
				HitDirection = direction,
				Crit = Main.rand.Next(100) < Projectile.CritChance,
				DamageType = DamageClass.Magic
			};

			Main.player[Projectile.owner].StrikeNPCDirect(target, hit);

			// 命中特效：一小团原地电花，不做线状拖尾
			if (!Main.dedServ) {
				WastelandFxSystem.Glow(hitPoint, new Color(150, 220, 255), 0.9f, 16);
				WastelandFxSystem.Spark(hitPoint, Main.rand.NextVector2Circular(2.5f, 2.5f), new Color(210, 240, 255), 0.8f, 14, 0.02f);
			}

			// 服务端把这一下命中广播出去（伤害数字 / 击退表现）
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.DamageNPC, -1, -1, null, target.whoAmI, damage, knockback, direction);
			}

			target.AddBuff(BuffID.Electrified, DebuffTime);
			target.AddBuff(BuffID.Slow, DebuffTime);
		}

		public override bool PreDraw(ref Color lightColor)
		{
			// ⚠️ 这条链是**机制可视化**（告诉玩家"电到了哪几个目标"），所以保留。
			// 但 `WastelandFxSystem.Bolt` 的亮芯已经不再向白色插值
			// （原来是 Lerp(颜色,白,0.72)，画出来就是白线）—— 见 开发说明.md「特效红线」。
			// 这里传的颜色是冷蓝，现在整条链都是蓝色，不会再出现白色激光。
			int anchorCount = System.Math.Clamp((int)Projectile.ai[0], 0, MaxTargets + 1);

			if (anchorCount < 2) {
				return false;
			}

			Vector2 previous = new Vector2(Projectile.ai[1], Projectile.localAI[3]);

			for (int i = 2; i <= anchorCount; i++) {
				Vector2 next = new Vector2(Projectile.ai[i], Projectile.localAI[i + 2]);
				WastelandFxSystem.Bolt(previous, next, new Color(150, 220, 255));
				previous = next;
			}

			return false;
		}
	}
}
