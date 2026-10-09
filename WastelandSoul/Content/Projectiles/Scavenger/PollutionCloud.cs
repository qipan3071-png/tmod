using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Content.Buffs;

namespace WastelandSoul.Content.Projectiles.Scavenger
{
	/// <summary>
	/// 污染云：炮弹落地 / 命中后原地留下的一小片持续伤害区域。
	/// <para/>半径小（80px）、存在 4 秒；每 0.5 秒对范围内的敌人结算一次伤害并挂既有「污染」减益。
	/// 贴图复用原版 <see cref="ProjectileID.ToxicCloud"/>，全程手绘。
	/// </summary>
	public class PollutionCloud : ModProjectile
	{
		/// <summary>持续时间（tick）。</summary>
		private const int Lifetime = 240;

		/// <summary>伤害间隔（tick）。</summary>
		private const int TickInterval = 30;

		/// <summary>伤害半径。</summary>
		private const float Radius = 80f;

		public override void SetStaticDefaults()
		{
			TextureAssets.Projectile[Type] = TextureAssets.Projectile[ProjectileID.ToxicCloud];
		}

		public override void SetDefaults()
		{
			Projectile.width = 72;
			Projectile.height = 72;
			Projectile.friendly = true;
			Projectile.hostile = false;
			Projectile.DamageType = DamageClass.Ranged;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.timeLeft = Lifetime;
			Projectile.aiStyle = -1;
		}

		public override bool? CanDamage()
		{
			return false;   // 伤害走自己的计时器，不走碰撞
		}

		public override void AI()
		{
			Projectile.velocity *= 0.9f;

			if (!Main.dedServ && Main.rand.NextBool(3)) {
				Dust dust = Dust.NewDustDirect(Projectile.position, Projectile.width, Projectile.height, DustID.Smoke, 0f, -0.6f, 130, default, 1.1f);
				dust.noGravity = true;
			}

			if (Projectile.owner != Main.myPlayer || Projectile.timeLeft % TickInterval != 0) {
				return;
			}

			for (int i = 0; i < Main.maxNPCs; i++) {
				NPC npc = Main.npc[i];

				if (!npc.active || npc.friendly || npc.dontTakeDamage) {
					continue;
				}

				if (!npc.CanBeChasedBy(Projectile)) {
					continue;
				}

				if (Vector2.Distance(npc.Center, Projectile.Center) > Radius + npc.width * 0.5f) {
					continue;
				}

				NPC.HitInfo hit = new NPC.HitInfo {
					Damage = Projectile.damage,
					Knockback = 0f,
					HitDirection = npc.Center.X < Projectile.Center.X ? 1 : -1,
					Crit = false,
					DamageType = DamageClass.Ranged
				};

				Main.player[Projectile.owner].StrikeNPCDirect(npc, hit);

				if (Main.netMode == NetmodeID.Server) {
					NetMessage.SendData(MessageID.DamageNPC, -1, -1, null, npc.whoAmI, Projectile.damage, 0f, hit.HitDirection);
				}

				npc.AddBuff(ModContent.BuffType<Pollution>(), 180);
			}
		}

		public override bool PreDraw(ref Color lightColor)
		{
			Texture2D texture = TextureAssets.Projectile[ProjectileID.ToxicCloud].Value;
			Vector2 origin = texture.Size() / 2f;
			float fade = MathHelper.Clamp(Projectile.timeLeft / 45f, 0f, 1f);
			float grow = MathHelper.Lerp(0.55f, 1f, 1f - Projectile.timeLeft / (float)Lifetime);

			Main.EntitySpriteDraw(
				texture,
				Projectile.Center - Main.screenPosition,
				null,
				new Color(190, 230, 140, 0) * (0.75f * fade),
				Main.GameUpdateCount * 0.01f,
				origin,
				grow,
				SpriteEffects.None,
				0f);

			return false;
		}
	}
}
