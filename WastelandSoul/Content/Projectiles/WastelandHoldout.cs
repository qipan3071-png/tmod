using System;
using System.IO;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ModLoader;

namespace WastelandSoul.Content.Projectiles
{
	/// <summary>
	/// 按住型手持弹幕的共用骨架（结构对齐灾厄 <c>BaseGunHoldoutProjectile</c>：
	/// 关停判定 → 贴手/转向 → 子类开火；旋转用 ExtraAI 同步）。
	/// 实现只用原版玩家字段，不搬灾厄源码。
	/// </summary>
	public abstract class WastelandHoldout : ModProjectile
	{
		public abstract int AssociatedItemID { get; }

		protected virtual float OffsetFromArm => 28f;

		protected virtual bool IsHeldItem(Item item)
		{
			return item != null && item.type == AssociatedItemID;
		}

		public override string Texture
		{
			get
			{
				ModItem item = ItemLoader.GetItem(AssociatedItemID);
				return item == null ? "Terraria/Images/Item_0" : item.Texture;
			}
		}

		public override void SetDefaults()
		{
			Projectile.width = 32;
			Projectile.height = 32;
			Projectile.friendly = true;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.netImportant = true;
			Projectile.timeLeft = 2;
			Projectile.DamageType = DamageClass.Magic;
			Projectile.ContinuouslyUpdateDamageStats = true;
		}

		public override bool? CanDamage()
		{
			return false;
		}

		public override bool ShouldUpdatePosition()
		{
			return false;
		}

		/// <summary>
		/// 玩家还能不能继续按住（灾厄 <c>CantUseHoldout</c> 同一组条件，字段全是原版的）。
		/// </summary>
		public static bool CantUseHoldout(Player player, bool needsToHold = true)
		{
			return player == null || !player.active || player.dead || player.CCed || player.noItems
				|| (needsToHold && !player.channel);
		}

		public override void AI()
		{
			Player owner = Main.player[Projectile.owner];

			if (CantUseHoldout(owner) || !IsHeldItem(owner.HeldItem)) {
				Projectile.Kill();
				return;
			}

			ManageHoldout(owner);
			HoldoutAI(owner);
		}

		private void ManageHoldout(Player owner)
		{
			Vector2 arm = owner.RotatedRelativePoint(owner.MountedCenter, true);

			if (Projectile.owner == Main.myPlayer) {
				Vector2 toMouse = Main.MouseWorld - arm;
				if (toMouse == Vector2.Zero) {
					toMouse = new Vector2(owner.direction, 0f);
				}

				Projectile.velocity = Vector2.Normalize(toMouse);
				Projectile.rotation = Projectile.velocity.ToRotation();
				int dir = Math.Sign(toMouse.X);
				if (dir == 0) {
					dir = owner.direction;
				}

				Projectile.spriteDirection = dir;
				owner.ChangeDir(dir);
				Projectile.netUpdate = true;
			}

			Projectile.Center = arm + Projectile.velocity * OffsetFromArm;
			Projectile.timeLeft = 2;
			owner.heldProj = Projectile.whoAmI;
			owner.itemTime = 2;
			owner.itemAnimation = 2;
			owner.itemRotation = (Projectile.velocity * owner.direction).ToRotation();
		}

		/// <summary>开火、扣蓝都写在这里。弹幕只在主人客户端生成。</summary>
		protected abstract void HoldoutAI(Player owner);

		protected Vector2 GunTip()
		{
			return Projectile.Center + Projectile.velocity * (Projectile.width * 0.35f);
		}

		public override bool PreDraw(ref Color lightColor)
		{
			Texture2D texture = TextureAssets.Projectile[Type].Value;
			SpriteEffects flip = Projectile.spriteDirection == -1 ? SpriteEffects.FlipVertically : SpriteEffects.None;
			Main.EntitySpriteDraw(
				texture,
				Projectile.Center - Main.screenPosition,
				null,
				Projectile.GetAlpha(lightColor),
				Projectile.rotation,
				texture.Size() * 0.5f,
				Projectile.scale,
				flip,
				0);
			return false;
		}

		public sealed override void SendExtraAI(BinaryWriter writer)
		{
			writer.Write(Projectile.rotation);
			writer.Write7BitEncodedInt(Projectile.spriteDirection);
			SendExtraAIHoldout(writer);
		}

		public sealed override void ReceiveExtraAI(BinaryReader reader)
		{
			Projectile.rotation = reader.ReadSingle();
			Projectile.spriteDirection = reader.Read7BitEncodedInt();
			ReceiveExtraAIHoldout(reader);
		}

		protected virtual void SendExtraAIHoldout(BinaryWriter writer)
		{
		}

		protected virtual void ReceiveExtraAIHoldout(BinaryReader reader)
		{
		}
	}
}
