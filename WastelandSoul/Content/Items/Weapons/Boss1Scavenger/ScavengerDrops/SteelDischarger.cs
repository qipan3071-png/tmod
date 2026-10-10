using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Common.Systems;
using WastelandSoul.Content.Items.Weapons;
using WastelandSoul.Content.Projectiles.Scavenger;

namespace WastelandSoul.Content.Items.Weapons.Boss1Scavenger.ScavengerDrops
{
	/// <summary>
	/// 精钢放电器（法师 · Boss 1 清道夫掉落）。
	/// <para/>行为对齐原版<strong>电弧涌动</strong>：点按即向光标打出瞬间命中的电弧，
	/// 并可再向最多 2 个附近敌人各劈一道（视线、夹角、矩形范围与原版同一套条件）。
	/// 数值仍是清道夫档（34 伤 / 12 蓝），不是石巨人后那把 180 伤。
	/// <para/>内部 <c>useTime = 6</c> / <c>useAnimation = 18</c>，一次按下打 3 轮。
	/// 电弧不穿墙、不进液体；人泡在水/蜂蜜/微光里按不出来。
	/// </summary>
	public class SteelDischarger : ModItem
	{
		/// <summary>光标电弧可达范围（像素），对齐原版 1920×1200。</summary>
		private const float ReachWidth = 1920f;

		private const float ReachHeight = 1200f;

		/// <summary>额外电弧搜索框：62.5 格宽 × 50 格高。</summary>
		private const float ExtraWidth = 62.5f * 16f;

		private const float ExtraHeight = 50f * 16f;

		/// <summary>玩家→光标 与 玩家→敌人 的最大夹角。</summary>
		private const float ExtraArcAngle = MathHelper.Pi / 3f;

		private const int ExtraArcCount = 2;

		public override void SetDefaults()
		{
			Item.width = 48;
			Item.height = 48;
			Item.damage = 34;
			Item.DamageType = DamageClass.Magic;
			Item.knockBack = 4f;
			Item.mana = 12;
			Item.useTime = 6;
			Item.useAnimation = 18;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.noMelee = true;
			Item.autoReuse = true;
			Item.channel = false;
			Item.shoot = ModContent.ProjectileType<SteelChainLightning>();
			Item.shootSpeed = 8f;
			Item.crit = 5;
			Item.UseSound = SoundID.Item122;
			Item.value = Item.sellPrice(gold: 3);
			Item.rare = WastelandRarityTiers.EarlyLate;
		}

		public override bool CanUseItem(Player player)
		{
			if (player.wet && !player.lavaWet) {
				return false;
			}

			return player.statMana >= Item.mana;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			Vector2 origin = player.MountedCenter;
			Vector2 cursor = LimitPoint(player, Main.MouseWorld);
			Vector2 aim = cursor - origin;
			Vector2 mainEnd = SteelChainLightning.ClipArc(origin, cursor);

			player.ChangeDir(aim.X < 0f ? -1 : 1);

			SpawnArc(source, origin, mainEnd, damage, knockback, player.whoAmI);

			List<NPC> extras = CollectExtraTargets(player, origin, aim, mainEnd);

			int take = System.Math.Min(ExtraArcCount, extras.Count);

			if (take == extras.Count) {
				for (int i = 0; i < extras.Count; i++) {
					SpawnArc(source, origin, SteelChainLightning.ClipArc(origin, extras[i].Center), damage, knockback, player.whoAmI);
				}

				return false;
			}

			int salt = player.itemAnimation;
			int first = WastelandRandom.Roll(player.whoAmI, salt, 0, 0, extras.Count);
			int second = WastelandRandom.Roll(player.whoAmI, salt, 1, 0, extras.Count - 1);

			if (second >= first) {
				second++;
			}

			SpawnArc(source, origin, SteelChainLightning.ClipArc(origin, extras[first].Center), damage, knockback, player.whoAmI);
			SpawnArc(source, origin, SteelChainLightning.ClipArc(origin, extras[second].Center), damage, knockback, player.whoAmI);

			return false;
		}

		private static void SpawnArc(IEntitySource source, Vector2 from, Vector2 to, int damage, float knockback, int owner)
		{
			Projectile.NewProjectile(source, from, Vector2.Zero, ModContent.ProjectileType<SteelChainLightning>(), damage, knockback, owner, to.X, to.Y);
		}

		/// <summary>把光标限制在玩家周围 1920×1200 的可达框内，框本身还会被推进世界边界。</summary>
		private static Vector2 LimitPoint(Player player, Vector2 point)
		{
			float left = player.Center.X - ReachWidth * 0.5f;
			float top = player.Center.Y - ReachHeight * 0.5f;
			float worldW = Main.maxTilesX * 16f;
			float worldH = Main.maxTilesY * 16f;

			if (left < 0f) {
				left = 0f;
			}

			if (top < 0f) {
				top = 0f;
			}

			if (left + ReachWidth > worldW) {
				left = worldW - ReachWidth;
			}

			if (top + ReachHeight > worldH) {
				top = worldH - ReachHeight;
			}

			point.X = MathHelper.Clamp(point.X, left, left + ReachWidth);
			point.Y = MathHelper.Clamp(point.Y, top, top + ReachHeight);

			return point;
		}

		/// <summary>
		/// 额外电弧目标：视线通、在 62.5×50 格框内、与瞄准方向夹角 &lt; 60°，
		/// 且主电弧这一轮还没劈到它。
		/// </summary>
		private static List<NPC> CollectExtraTargets(Player player, Vector2 origin, Vector2 aim, Vector2 mainEnd)
		{
			List<NPC> found = new List<NPC>();
			bool aimOk = aim.LengthSquared() >= 16f;
			float aimRot = aimOk ? aim.ToRotation() : 0f;
			float halfW = ExtraWidth * 0.5f;
			float halfH = ExtraHeight * 0.5f;

			for (int i = 0; i < Main.maxNPCs; i++) {
				NPC npc = Main.npc[i];

				if (!npc.active || npc.friendly || npc.dontTakeDamage || !npc.CanBeChasedBy()) {
					continue;
				}

				Vector2 toNpc = npc.Center - origin;

				if (System.Math.Abs(toNpc.X) > halfW || System.Math.Abs(toNpc.Y) > halfH) {
					continue;
				}

				if (!Collision.CanHitLine(origin, 1, 1, npc.Center, 1, 1)) {
					continue;
				}

				if (aimOk) {
					float delta = System.Math.Abs(MathHelper.WrapAngle(toNpc.ToRotation() - aimRot));

					if (delta > ExtraArcAngle) {
						continue;
					}
				}

				if (SteelChainLightning.HitsLine(origin, mainEnd, npc)) {
					continue;
				}

				found.Add(npc);
			}

			return found;
		}
	}
}
