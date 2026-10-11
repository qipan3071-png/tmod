using System;
using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.Systems;
using WastelandSoul.Content.Items.Weapons;
using WastelandSoul.Content.Items.Weapons.Boss4Fireplace;

namespace WastelandSoul.Content.Projectiles.Fireplace
{
	/// <summary>
	/// 右键蓄力完全不走物品 UseItem / C.I.V.E。
	/// StormySlash 白名单只认物品类型，改 useStyle 挡不住它的 MouseRight 连击斩；
	/// 所以右键在 PreItemCheck 里吃掉 controlUseTile，自己刷蓄力弹幕。
	/// </summary>
	public static class FireplaceGreatbladeCharge
	{
		public const int FormTicks = 180;

		public const int MaxTicks = 300;

		public const float MinDamageRatio = 3.0f;

		public const float MaxDamageRatio = 5.5f;

		public const float HoldMinScale = 1.0f;

		public const float HoldMaxScale = 2.6f;

		public const float MinScale = 1.8f;

		public const float MaxScale = 3.2f;

		public const int FlashTicks = 24;

		public const float MinSlamRadius = 160f;

		public const float MaxSlamRadius = 224f;

		public const float DropHeight = 128f;

		public const float LockMouseRange = 720f;

		public const float LockPlayerRange = 960f;

		public static bool IsGreatblade(Item item)
		{
			return item != null && !item.IsAir
				&& (item.type == ModContent.ItemType<FireplaceWarriorWeapon>()
					|| item.type == ModContent.ItemType<FireplaceWarriorWeaponEx>());
		}

		public static bool IsCharging(Player player)
		{
			return player != null && player.ownedProjectileCounts[ModContent.ProjectileType<FireplaceCrescentCharge>()] > 0;
		}

		public static bool WantsCharge(Player player)
		{
			return player != null
				&& player.whoAmI == Main.myPlayer
				&& Main.mouseRight
				&& !player.mouseInterface
				&& !Main.ingameOptionsWindow
				&& !Main.mapFullscreen
				&& player.active
				&& !player.dead
				&& !player.CCed
				&& !player.noItems;
		}

		public static void RestoreSwing(Item item, int leftUseTime)
		{
			item.useStyle = ItemUseStyleID.Swing;
			item.channel = false;
			item.noMelee = false;
			item.noUseGraphic = false;
			item.useTime = leftUseTime;
			item.useAnimation = leftUseTime;
			item.shoot = ProjectileID.SwordBeam;
			item.UseSound = SoundID.Item1;
		}

		public static void Hold(Item item, Player player, int leftUseTime)
		{
			if (IsCharging(player)) {
				item.noMelee = true;
				item.noUseGraphic = true;
				item.channel = false;
				player.channel = false;
				return;
			}

			RestoreSwing(item, leftUseTime);
		}

		public static bool CanUse(Item item, Player player, int leftUseTime)
		{
			if (IsCharging(player) || WantsCharge(player)) {
				return false;
			}

			RestoreSwing(item, leftUseTime);
			return true;
		}

		public static void EatRightClick(Player player)
		{
			if (!IsGreatblade(player.HeldItem)) {
				return;
			}

			if (WantsCharge(player) || IsCharging(player)) {
				player.controlUseTile = false;
				player.releaseUseTile = false;
			}
		}

		public static void TryStart(Player player)
		{
			if (!WantsCharge(player) || IsCharging(player) || !IsGreatblade(player.HeldItem)) {
				return;
			}

			InterruptCive(player);

			Item item = player.HeldItem;
			Vector2 toMouse = Main.MouseWorld - player.MountedCenter;
			if (toMouse == Vector2.Zero) {
				toMouse = new Vector2(player.direction, 0f);
			}

			toMouse.Normalize();
			Projectile.NewProjectile(
				player.GetSource_ItemUse(item),
				player.MountedCenter,
				toMouse,
				ModContent.ProjectileType<FireplaceCrescentCharge>(),
				player.GetWeaponDamage(item),
				player.GetWeaponKnockback(item),
				player.whoAmI,
				-1f);
		}

		public static void InterruptCive(Player player)
		{
			if (WastelandCiveBridge.Cive != null
				&& WastelandCiveBridge.Cive.TryFind("CIVESword", out ModProjectile sword)) {
				for (int i = 0; i < Main.maxProjectiles; i++) {
					Projectile projectile = Main.projectile[i];
					if (projectile.active && projectile.owner == player.whoAmI && projectile.type == sword.Type) {
						projectile.Kill();
					}
				}
			}

			player.itemAnimation = 0;
			player.itemTime = 0;
			player.reuseDelay = 0;
		}

		public static float ChargeLerp(float ticks)
		{
			return MathHelper.Clamp((ticks - FormTicks) / (MaxTicks - FormTicks), 0f, 1f);
		}

		public static float HoldScale(float ticks)
		{
			return MathHelper.Lerp(HoldMinScale, HoldMaxScale, MathHelper.Clamp(ticks / MaxTicks, 0f, 1f));
		}

		public static float GrowScale(float ticks)
		{
			return MathHelper.Lerp(MinScale, MaxScale, MathHelper.Clamp(ticks / MaxTicks, 0f, 1f));
		}

		public static float DamageRatio(float ticks)
		{
			return MathHelper.Lerp(MinDamageRatio, MaxDamageRatio, ChargeLerp(ticks));
		}

		public static float SlamRadius(float ticks)
		{
			return MathHelper.Lerp(MinSlamRadius, MaxSlamRadius, ChargeLerp(ticks));
		}

		public static float TicksFromLerp(float lerp)
		{
			return FormTicks + MathHelper.Clamp(lerp, 0f, 1f) * (MaxTicks - FormTicks);
		}
	}

	/// <summary>按住时自己画手里的大剑并放大。不到 3 秒松手消散；蓄满生命水晶音 + 武器闪白。</summary>
	public class FireplaceCrescentCharge : ModProjectile
	{
		public override string Texture => "WastelandSoul/Content/Projectiles/Fireplace/FireplaceGiantCrescent";

		public override void SetDefaults()
		{
			Projectile.width = 48;
			Projectile.height = 64;
			Projectile.friendly = true;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.netImportant = true;
			Projectile.timeLeft = 2;
			Projectile.hide = true;
			Projectile.DamageType = DamageClass.Melee;
		}

		public override bool? CanDamage()
		{
			return false;
		}

		public override bool ShouldUpdatePosition()
		{
			return false;
		}

		public override void AI()
		{
			Player owner = Main.player[Projectile.owner];

			if (owner == null || !owner.active || owner.dead || owner.CCed || owner.noItems || !FireplaceGreatbladeCharge.IsGreatblade(owner.HeldItem)) {
				Projectile.Kill();
				return;
			}

			if (Projectile.owner == Main.myPlayer
				&& (!Main.mouseRight || owner.mouseInterface || Main.ingameOptionsWindow || Main.mapFullscreen)) {
				Projectile.Kill();
				return;
			}

			Projectile.ai[1] += 1f;
			UpdateLock(owner);

			NPC locked = LockedNpc();
			if (Projectile.owner == Main.myPlayer) {
				Vector2 aim = locked != null ? locked.Center : Main.MouseWorld;
				int dir = Math.Sign(aim.X - owner.Center.X);
				if (dir == 0) {
					dir = owner.direction;
				}

				owner.ChangeDir(dir);
			}

			Projectile.Center = owner.MountedCenter + new Vector2(owner.direction * 10f, 6f);
			Projectile.scale = FireplaceGreatbladeCharge.HoldScale(Projectile.ai[1]);
			Projectile.timeLeft = 2;

			if (Projectile.ai[1] > FireplaceGreatbladeCharge.MaxTicks) {
				Projectile.ai[1] = FireplaceGreatbladeCharge.MaxTicks;
			}

			if (Projectile.ai[1] >= FireplaceGreatbladeCharge.MaxTicks && Projectile.localAI[0] == 0f) {
				Projectile.localAI[0] = 1f;
				Projectile.localAI[1] = FireplaceGreatbladeCharge.FlashTicks;
				if (!Main.dedServ) {
					SoundEngine.PlaySound(SoundID.Item4, owner.Center);
				}
			}

			if (Projectile.localAI[1] > 0f) {
				Projectile.localAI[1] -= 1f;
			}
		}

		public override void OnKill(int timeLeft)
		{
			Player owner = Main.player[Projectile.owner];
			if (owner != null && owner.heldProj == Projectile.whoAmI) {
				owner.heldProj = -1;
			}

			if (Projectile.owner == Main.myPlayer) {
				owner.channel = false;
			}

			if (Projectile.owner != Main.myPlayer || !Formed()) {
				return;
			}

			NPC locked = LockedNpc();
			Vector2 impact = locked != null ? locked.Center : Main.MouseWorld;
			float ticks = Projectile.ai[1];
			int damage = (int)(Projectile.damage * FireplaceGreatbladeCharge.DamageRatio(ticks));
			float lerp = FireplaceGreatbladeCharge.ChargeLerp(ticks);

			Projectile.NewProjectile(
				owner.GetSource_ItemUse(owner.HeldItem),
				Projectile.Center,
				Vector2.Zero,
				ModContent.ProjectileType<FireplaceGiantCrescent>(),
				damage,
				Projectile.knockBack * MathHelper.Lerp(1.1f, 1.6f, lerp),
				Projectile.owner,
				impact.X,
				impact.Y,
				lerp);
		}

		public override bool PreDraw(ref Color lightColor)
		{
			Player owner = Main.player[Projectile.owner];
			float flash = Projectile.localAI[1] / FireplaceGreatbladeCharge.FlashTicks;
			DrawHeldBlade(owner, Projectile.scale, lightColor, flash);
			return false;
		}

		private void UpdateLock(Player owner)
		{
			if (Projectile.owner != Main.myPlayer) {
				return;
			}

			NPC current = LockedNpc();
			if (current != null) {
				return;
			}

			int best = -1;
			float bestDist = FireplaceGreatbladeCharge.LockMouseRange;
			for (int i = 0; i < Main.maxNPCs; i++) {
				NPC npc = Main.npc[i];
				if (!npc.CanBeChasedBy()) {
					continue;
				}

				if (npc.Distance(owner.Center) > FireplaceGreatbladeCharge.LockPlayerRange) {
					continue;
				}

				float dist = npc.Distance(Main.MouseWorld);
				if (dist < bestDist) {
					bestDist = dist;
					best = npc.whoAmI;
				}
			}

			if ((int)Projectile.ai[0] != best) {
				Projectile.ai[0] = best;
				Projectile.netUpdate = true;
			}
		}

		private NPC LockedNpc()
		{
			int index = (int)Projectile.ai[0];
			if (index < 0 || index >= Main.maxNPCs) {
				return null;
			}

			NPC npc = Main.npc[index];
			return npc.active && npc.CanBeChasedBy() ? npc : null;
		}

		private bool Formed()
		{
			return Projectile.ai[1] >= FireplaceGreatbladeCharge.FormTicks;
		}

		internal static void DrawHeldBlade(Player owner, float scale, Color lightColor, float flash, List<DrawData> cache = null)
		{
			if (owner == null || owner.HeldItem == null) {
				return;
			}

			int itemType = owner.HeldItem.type;
			Main.instance.LoadItem(itemType);
			Texture2D texture = TextureAssets.Item[itemType].Value;
			Vector2 origin = new Vector2(texture.Width * 0.22f, texture.Height * 0.78f);
			SpriteEffects flip = SpriteEffects.None;
			float rotation = -0.35f;
			if (owner.direction < 0) {
				flip = SpriteEffects.FlipHorizontally;
				origin.X = texture.Width - origin.X;
				rotation = 0.35f;
			}

			Vector2 hand = owner.MountedCenter + new Vector2(owner.direction * 10f, 6f);
			AddBlade(cache, texture, hand, lightColor, rotation, origin, scale, flip);

			if (flash <= 0f) {
				return;
			}

			// 蓄满提示：武器闪白一下，不是激光（check_no_white_fx）
			Color shine = new Color(232, 232, 235) * flash;
			AddBlade(cache, texture, hand, shine, rotation, origin, scale * 1.05f, flip);
		}

		private static void AddBlade(List<DrawData> cache, Texture2D texture, Vector2 hand, Color color, float rotation, Vector2 origin, float scale, SpriteEffects flip)
		{
			DrawData data = new DrawData(
				texture,
				hand - Main.screenPosition,
				null,
				color,
				rotation,
				origin,
				scale,
				flip,
				0);

			if (cache != null) {
				cache.Add(data);
				return;
			}

			Main.EntitySpriteDraw(data);
		}

		internal static void DrawCrescent(Vector2 world, float scale, Color lightColor, float alpha)
		{
			int type = ModContent.ProjectileType<FireplaceGiantCrescent>();
			Main.instance.LoadProjectile(type);
			Texture2D texture = TextureAssets.Projectile[type].Value;
			Color tint = lightColor * alpha;
			tint.R = (byte)Math.Min((int)tint.R, 210);
			tint.G = (byte)Math.Min((int)tint.G, 220);
			tint.B = (byte)Math.Min((int)tint.B, 230);
			Main.EntitySpriteDraw(
				texture,
				world - Main.screenPosition,
				null,
				tint,
				MathHelper.PiOver2,
				texture.Size() * 0.5f,
				scale,
				SpriteEffects.None,
				0);
		}
	}

	/// <summary>成型后的巨刃：飞到目标上方砸下，圆形范围高伤。没有爆炸特效。</summary>
	public class FireplaceGiantCrescent : ModProjectile
	{
		public override void SetDefaults()
		{
			Projectile.width = 80;
			Projectile.height = 110;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Melee;
			Projectile.penetrate = -1;
			Projectile.timeLeft = 120;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;
		}

		public override bool? CanDamage()
		{
			return Projectile.localAI[0] >= 1f;
		}

		public override void ModifyDamageHitbox(ref Rectangle hitbox)
		{
			int radius = (int)SlamRadius();
			hitbox.Width = radius * 2;
			hitbox.Height = radius * 2;
			hitbox.X = (int)Projectile.Center.X - radius;
			hitbox.Y = (int)Projectile.Center.Y - radius;
		}

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox)
		{
			float radius = SlamRadius();
			Vector2 closest = new Vector2(
				MathHelper.Clamp(Projectile.Center.X, targetHitbox.Left, targetHitbox.Right),
				MathHelper.Clamp(Projectile.Center.Y, targetHitbox.Top, targetHitbox.Bottom));
			return Vector2.DistanceSquared(Projectile.Center, closest) <= radius * radius;
		}

		public override void AI()
		{
			float ticks = FireplaceGreatbladeCharge.TicksFromLerp(Projectile.ai[2]);
			Projectile.scale = FireplaceGreatbladeCharge.GrowScale(ticks);
			Projectile.rotation = MathHelper.PiOver2;

			Vector2 impact = new Vector2(Projectile.ai[0], Projectile.ai[1]);
			Vector2 hover = new Vector2(impact.X, impact.Y - FireplaceGreatbladeCharge.DropHeight);

			if (Projectile.localAI[0] < 1f) {
				Vector2 toHover = hover - Projectile.Center;
				float dist = toHover.Length();
				if (dist < 18f) {
					Projectile.Center = hover;
					Projectile.velocity = new Vector2(0f, 12f);
					Projectile.localAI[0] = 1f;
				}
				else {
					toHover.Normalize();
					Projectile.velocity = toHover * 22f;
				}
			}
			else if (Projectile.localAI[0] < 2f) {
				Projectile.velocity.Y += 1.6f;
				if (Projectile.velocity.Y > 28f) {
					Projectile.velocity.Y = 28f;
				}

				Projectile.velocity.X = (impact.X - Projectile.Center.X) * 0.12f;

				if (Projectile.Center.Y >= impact.Y) {
					Projectile.Center = impact;
					Projectile.velocity = Vector2.Zero;
					Projectile.localAI[0] = 2f;
					Projectile.timeLeft = 8;
					if (!Main.dedServ) {
						SoundEngine.PlaySound(SoundID.Item1, Projectile.Center);
					}
				}
			}

			if (!Main.dedServ && Main.rand.NextBool(2)) { // sync-ok: visual only
				Dust dust = Dust.NewDustDirect(Projectile.position, Projectile.width, Projectile.height, DustID.IceTorch);
				dust.noGravity = true;
				dust.velocity.Y = 2.2f;
				dust.scale = 1.15f;
			}
		}

		public override bool PreDraw(ref Color lightColor)
		{
			FireplaceCrescentCharge.DrawCrescent(Projectile.Center, Projectile.scale, lightColor, 1f);
			return false;
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone)
		{
			WastelandShoot.HitBuff(target, BuffID.Frostburn, 240);
		}

		private float SlamRadius()
		{
			return FireplaceGreatbladeCharge.SlamRadius(FireplaceGreatbladeCharge.TicksFromLerp(Projectile.ai[2]));
		}
	}
}
