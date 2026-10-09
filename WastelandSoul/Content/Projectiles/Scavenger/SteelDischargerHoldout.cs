using System;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Content.Items.Weapons.Boss1Scavenger.ScavengerDrops;

namespace WastelandSoul.Content.Projectiles.Scavenger
{
	/// <summary>
	/// 精钢放电器的蓄力本体（悬浮弹幕）。
	/// <para/>贴图复用原版 <see cref="ProjectileID.ChargedBlasterOrb"/>。
	/// 蓄力时不攻击，只负责：贴手、随蓄力变大发光、按段扣蓝；
	/// 玩家松手（或蓝见底）时放出 <see cref="SteelChainLightning"/>。
	/// </summary>
	public class SteelDischargerHoldout : ModProjectile
	{
		/// <summary>蓄满所需帧数。</summary>
		private const int FullCharge = 90;

		/// <summary>每 4 帧扣 1 点蓝。</summary>
		private const int ManaDrainInterval = 4;

		/// <summary>低于这个蓝量就不放电。</summary>
		private const int MinManaToFire = 12;

		public override void SetStaticDefaults()
		{
			TextureAssets.Projectile[Type] = TextureAssets.Projectile[ProjectileID.ChargedBlasterOrb];
		}

		public override void SetDefaults()
		{
			Projectile.width = 30;
			Projectile.height = 30;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Magic;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.netImportant = true;
			Projectile.aiStyle = -1;          // 不用原版 AI_075：那套会自己发充能激光
			Projectile.timeLeft = 2;          // 由 AI 每帧续命，玩家一松手就自然消失
		}

		public override bool? CanDamage()
		{
			return false;   // 蓄力本体不造成伤害
		}

		public override void AI()
		{
			Player player = Main.player[Projectile.owner];

			if (!player.active || player.dead) {
				Projectile.Kill();
				return;
			}

			Item heldItem = player.HeldItem;

			if (!player.channel || heldItem.type != ModContent.ItemType<SteelDischarger>()) {
				Release(player);
				return;
			}

			Projectile.timeLeft = 2;

			if (Projectile.owner == Main.myPlayer) {
				Projectile.ai[0] = MathHelper.Min(Projectile.ai[0] + 1f, FullCharge);
			}

			// 蓝量：蓄满约 22 点，和 12 点基础耗蓝同一档
			if (Projectile.ai[0] % ManaDrainInterval == 0f && player.statMana > 0) {
				player.statMana--;
				player.manaRegenDelay = MathHelper.Max(player.manaRegenDelay, 40f);
			}

			if (Projectile.ai[0] % 15f == 0f) {
				SoundEngine.PlaySound(SoundID.Item15 with { Volume = 0.4f }, Projectile.Center);
			}

			// 贴手 + 指向鼠标
			float aim = (Main.MouseWorld - player.MountedCenter).ToRotation();
			player.ChangeDir(Main.MouseWorld.X < player.MountedCenter.X ? -1 : 1);
			Projectile.rotation = aim;
			Projectile.velocity = aim.ToRotationVector2() * 12f;
			Projectile.Center = player.MountedCenter + aim.ToRotationVector2() * 18f;
			Projectile.direction = Projectile.spriteDirection = player.direction;
		}

		/// <summary>松手：蓄够了就放链状闪电，不然只有一声空响。</summary>
		private void Release(Player player)
		{
			bool enough = player.statMana >= MinManaToFire;
			float charge = Projectile.ai[0];
			int damage = Projectile.damage;
			float knockback = Projectile.knockBack;
			Vector2 center = Projectile.Center;
			Vector2 velocity = Projectile.velocity;
			int owner = Projectile.owner;

			Projectile.Kill();

			if (owner != Main.myPlayer || !enough) {
				return;
			}

			int finalDamage = (int)(damage * MathHelper.Lerp(0.7f, 1.45f, charge / FullCharge));

			Projectile.NewProjectile(
				Projectile.GetSource_FromAI(),
				center,
				velocity,
				ModContent.ProjectileType<SteelChainLightning>(),
				finalDamage,
				knockback,
				player.whoAmI,
				JumpCount(charge),
				0f);

			SoundEngine.PlaySound(SoundID.Item122 with { Volume = 0.7f }, center);
		}

		/// <summary>跳数：2 跳起步，蓄满 4 跳。</summary>
		private static float JumpCount(float charge)
		{
			float ratio = charge / FullCharge;

			if (ratio >= 0.66f) {
				return 4f;
			}

			if (ratio >= 0.33f) {
				return 3f;
			}

			return 2f;
		}

		public override bool PreDraw(ref Color lightColor)
		{
			Texture2D texture = TextureAssets.Projectile[ProjectileID.ChargedBlasterOrb].Value;
			Vector2 origin = texture.Size() / 2f;
			float ratio = Projectile.ai[0] / FullCharge;
			float pulse = 0.45f + 0.55f * ratio;
			float scale = pulse * (1f + 0.06f * (float)Math.Sin(Main.GameUpdateCount * 0.35f));
			Color color = new Color(150, 220, 255, 0) * MathHelper.Clamp(0.5f + ratio * 0.5f, 0f, 1f);

			Main.EntitySpriteDraw(
				texture,
				Projectile.Center - Main.screenPosition,
				null,
				color,
				Projectile.rotation,
				origin,
				scale,
				SpriteEffects.None,
				0f);

			return false;   // 上面已经画完了，不再走默认绘制
		}
	}
}
