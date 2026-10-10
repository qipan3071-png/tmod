using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.Systems;

namespace WastelandSoul.Content.Projectiles.Scavenger
{
	/// <summary>
	/// 精钢放电器的瞬间电弧（一端在玩家，一端在 <c>ai[0]/ai[1]</c>）。
	/// <para/>碰撞用线段判定，无限穿透、无伤害递减；同类型电弧共享 10 嘀嗒静态无敌帧
	/// （对齐电弧涌动：每两道才打中同一目标一次）。命中挂「带电」4～7 秒。
	/// 画面只用沿线电尘标出命中线段，不拉 MagicPixel 光柱、不套原版雷杖贴图。
	/// </summary>
	public class SteelChainLightning : ModProjectile
	{
		public override void SetDefaults()
		{
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Magic;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = 8;
			Projectile.aiStyle = -1;
			Projectile.hide = true;
			Projectile.usesIDStaticNPCImmunity = true;
			Projectile.idStaticNPCHitCooldown = 10;
		}

		public override void AI()
		{
			Projectile.velocity = Vector2.Zero;

			if (Projectile.localAI[0] != 0f) {
				return;
			}

			Projectile.localAI[0] = 1f;

			if (Main.dedServ) {
				return;
			}

			Vector2 start = Projectile.Center;
			Vector2 end = EndPoint();
			Vector2 delta = end - start;
			float length = delta.Length();

			if (length < 4f) {
				return;
			}

			Vector2 step = delta / length;

			for (float d = 0f; d <= length; d += 18f) {
				Dust dust = Dust.NewDustPerfect(start + step * d, DustID.Electric, Vector2.Zero, 150, default, 0.7f);
				dust.noGravity = true;
				dust.velocity *= 0.15f;
			}
		}

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox)
		{
			float collisionPoint = 0f;

			return Collision.CheckAABBvLineCollision(
				targetHitbox.TopLeft(),
				targetHitbox.Size(),
				Projectile.Center,
				EndPoint(),
				10f,
				ref collisionPoint);
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone)
		{
			int duration = WastelandRandom.Roll(Projectile.identity, target.whoAmI, Projectile.owner, 240, 421);
			target.AddBuff(BuffID.Electrified, duration);
		}

		public override bool PreDraw(ref Color lightColor)
		{
			return false;
		}

		private Vector2 EndPoint()
		{
			return new Vector2(Projectile.ai[0], Projectile.ai[1]);
		}

		/// <summary>沿线采样：实心物块与液体都会截断电弧。</summary>
		public static Vector2 ClipArc(Vector2 start, Vector2 end)
		{
			Vector2 delta = end - start;
			float length = delta.Length();

			if (length < 4f) {
				return end;
			}

			Vector2 step = delta / length;
			float lastSafe = 0f;

			for (float d = 4f; d <= length; d += 8f) {
				Vector2 point = start + step * d;
				Point tilePos = point.ToTileCoordinates();

				if (!WorldGen.InWorld(tilePos.X, tilePos.Y)) {
					return start + step * lastSafe;
				}

				Tile tile = Framing.GetTileSafely(tilePos.X, tilePos.Y);

				if (tile.HasUnactuatedTile && Main.tileSolid[tile.TileType] && !Main.tileSolidTop[tile.TileType]) {
					return start + step * lastSafe;
				}

				if (tile.LiquidAmount > 32) {
					return start + step * lastSafe;
				}

				lastSafe = d;
			}

			return end;
		}

		/// <summary>这条线段有没有打到这个 NPC（给武器端排除「主弧已经劈过」的额外目标）。</summary>
		public static bool HitsLine(Vector2 from, Vector2 to, NPC npc)
		{
			float collisionPoint = 0f;

			return Collision.CheckAABBvLineCollision(
				npc.position,
				npc.Size,
				from,
				to,
				10f,
				ref collisionPoint);
		}
	}
}
