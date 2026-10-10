using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.DataStructures;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace WastelandSoul.Content.Projectiles.Melee
{
	/// <summary>
	/// 近战招式（学 C.I.V.E 的方向：砍掉原版电风扇挥砍，换成朝光标的斩/刺/连击/重劈）。
	/// 自己画手里那把剑，不用对方的序列、着色器和刀光。
	/// </summary>
	public enum WastelandSwingStyle : byte
	{
		Chop = 0,
		Sweep = 1,
		Thrust = 2,
		Combo = 3,
		Smash = 4
	}

	public class WastelandMeleeSwing : ModProjectile
	{
		public override string Texture => "Terraria/Images/Item_" + ItemID.IronShortsword;

		public static void Spawn(Player player, EntitySource_ItemUse_WithAmmo source, int damage, float knockback, WastelandSwingStyle style)
		{
			Vector2 aim = Main.MouseWorld - player.MountedCenter;

			if (aim.LengthSquared() < 4f) {
				aim = new Vector2(player.direction, 0f);
			}

			aim.Normalize();
			int combo = player.GetModPlayer<WastelandMeleePlayer>().NextCombo();
			float duration = MathHelper.Max(player.itemAnimationMax, 8);

			Projectile.NewProjectile(
				source,
				player.MountedCenter,
				aim,
				ModContent.ProjectileType<WastelandMeleeSwing>(),
				damage,
				knockback,
				player.whoAmI,
				(float)style,
				duration,
				combo);
		}

		public override void SetDefaults()
		{
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Melee;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.ownerHitCheck = true;
			Projectile.ownerHitCheckDistance = 220f;
			Projectile.usesOwnerMeleeHitCD = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;
			Projectile.stopsDealingDamageAfterPenetrateHits = false;
			Projectile.aiStyle = -1;
			Projectile.hide = false;
			Projectile.noEnchantmentVisuals = true;
		}

		public override bool ShouldUpdatePosition()
		{
			return false;
		}

		public override void AI()
		{
			Player player = Main.player[Projectile.owner];

			if (!player.active || player.dead) {
				Projectile.Kill();
				return;
			}

			Projectile.localAI[0] += 1f;
			float duration = MathHelper.Max(Projectile.ai[1], 8f);
			float t = MathHelper.Clamp(Projectile.localAI[0] / duration, 0f, 1f);
			var style = (WastelandSwingStyle)(int)Projectile.ai[0];
			int combo = (int)Projectile.ai[2];

			player.heldProj = Projectile.whoAmI;
			Projectile.Center = player.RotatedRelativePoint(player.MountedCenter);
			Pose(player, style, combo, t);
			Projectile.friendly = DamagesOn(style, t);

			if (Projectile.localAI[0] >= duration) {
				Projectile.Kill();
			}
		}

		private void Pose(Player player, WastelandSwingStyle style, int combo, float t)
		{
			float aim = Projectile.velocity.ToRotation();
			float rotation;
			float reach = 0f;

			switch (style) {
				case WastelandSwingStyle.Sweep:
					rotation = MathHelper.Lerp(aim - 2.35f, aim + 2.35f, Smooth(t));
					break;
				case WastelandSwingStyle.Thrust:
					rotation = aim;
					reach = ThrustReach(t);
					break;
				case WastelandSwingStyle.Smash:
					rotation = t < 0.42f
						? MathHelper.Lerp(aim - 2.5f, aim - 2.15f, t / 0.42f)
						: MathHelper.Lerp(aim - 2.15f, aim + 1.05f, Smooth((t - 0.42f) / 0.58f));
					break;
				case WastelandSwingStyle.Combo:
					rotation = (combo & 1) == 0
						? MathHelper.Lerp(aim - 2.05f, aim + 0.9f, Smooth(t))
						: MathHelper.Lerp(aim + 2.05f, aim - 0.9f, Smooth(t));
					break;
				default:
					rotation = MathHelper.Lerp(aim - 2.05f, aim + 0.85f, Smooth(t));
					break;
			}

			Projectile.rotation = rotation;
			Projectile.localAI[1] = style == WastelandSwingStyle.Thrust ? 0.28f + 0.72f * reach : 1f;
			Projectile.Center += rotation.ToRotationVector2() * reach * 18f;
			player.itemRotation = rotation;
			player.SetCompositeArmFront(true, Player.CompositeArmStretchAmount.Full, rotation - MathHelper.PiOver2);
			player.direction = Projectile.velocity.X >= 0f ? 1 : -1;
		}

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox)
		{
			Player player = Main.player[Projectile.owner];
			float length = BladeLength(player) * MathHelper.Max(Projectile.localAI[1], 0.28f);
			float thick = 22f * player.GetAdjustedItemScale(player.HeldItem);
			Vector2 tip = Projectile.Center + Projectile.rotation.ToRotationVector2() * length;
			float unused = 0f;
			return Collision.CheckAABBvLineCollision(targetHitbox.TopLeft(), targetHitbox.Size(), Projectile.Center, tip, thick, ref unused);
		}

		public override bool PreDraw(ref Color lightColor)
		{
			Player player = Main.player[Projectile.owner];
			Item item = player.HeldItem;

			if (item == null || item.IsAir) {
				return false;
			}

			Texture2D texture = TextureAssets.Item[item.type].Value;
			bool left = player.direction < 0;
			Vector2 origin = left
				? new Vector2(texture.Width * 0.82f, texture.Height * 0.82f)
				: new Vector2(texture.Width * 0.18f, texture.Height * 0.82f);
			float scale = player.GetAdjustedItemScale(item);
			Color color = Lighting.GetColor(player.Center.ToTileCoordinates());
			Main.EntitySpriteDraw(
				texture,
				Projectile.Center - Main.screenPosition,
				null,
				color,
				Projectile.rotation + (left ? -MathHelper.PiOver4 : MathHelper.PiOver4),
				origin,
				scale,
				left ? SpriteEffects.FlipHorizontally : SpriteEffects.None,
				0f);
			return false;
		}

		private static float BladeLength(Player player)
		{
			return 58f * player.GetAdjustedItemScale(player.HeldItem);
		}

		private static float Smooth(float t)
		{
			t = MathHelper.Clamp(t, 0f, 1f);
			return t * t * (3f - 2f * t);
		}

		private static float ThrustReach(float t)
		{
			if (t < 0.32f) {
				return t / 0.32f;
			}

			if (t < 0.55f) {
				return 1f;
			}

			return MathHelper.Clamp((1f - t) / 0.45f, 0f, 1f);
		}

		private static bool DamagesOn(WastelandSwingStyle style, float t)
		{
			switch (style) {
				case WastelandSwingStyle.Smash:
					return t >= 0.42f;
				case WastelandSwingStyle.Thrust:
					return t >= 0.22f && t <= 0.78f;
				default:
					return true;
			}
		}
	}

	public class WastelandMeleePlayer : ModPlayer
	{
		private int combo;

		public int NextCombo()
		{
			combo++;
			return combo;
		}
	}

	public class WastelandMeleeSwingItem : GlobalItem
	{
		public override bool InstancePerEntity => true;

		public bool Enabled;

		public WastelandSwingStyle Style;

		public override GlobalItem Clone(Item from, Item to)
		{
			WastelandMeleeSwingItem clone = (WastelandMeleeSwingItem)base.Clone(from, to);
			clone.Enabled = Enabled;
			clone.Style = Style;
			return clone;
		}

		public override bool Shoot(Item item, Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			if (!Enabled || player.whoAmI != Main.myPlayer) {
				return true;
			}

			WastelandMeleeSwing.Spawn(player, source, damage, knockback, Style);
			return type != ModContent.ProjectileType<WastelandMeleeSwing>();
		}
	}
}
