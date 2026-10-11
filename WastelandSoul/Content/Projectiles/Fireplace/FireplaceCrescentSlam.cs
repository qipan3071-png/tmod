using System;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.Audio;
using Terraria.DataStructures;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Content.Items.Weapons;

namespace WastelandSoul.Content.Projectiles.Fireplace
{
	/// <summary>
	/// 壁炉守卫大剑右键：蓄力满 3 秒才成型，5 秒打满；松开后巨刃从锁定目标上方砸下，落地范围爆炸。
	/// 左键仍走 C.I.V.E 挥砍 + 三片新月刃。
	/// </summary>
	public static class FireplaceGreatbladeCharge
	{
		public const int FormTicks = 180;

		public const int MaxTicks = 300;

		public const float MinDamageRatio = 2.0f;

		public const float MaxDamageRatio = 3.6f;

		public const float MinScale = 2.2f;

		public const float MaxScale = 3.4f;

		public const float MinBurstRadius = 160f;

		public const float MaxBurstRadius = 224f;

		public const float DropHeight = 352f;

		public const float LockMouseRange = 720f;

		public const float LockPlayerRange = 960f;

		public static bool CanUse(Item item, Player player)
		{
			if (player.altFunctionUse == 2) {
				item.useStyle = ItemUseStyleID.HoldUp;
				item.channel = true;
				item.noMelee = true;
				item.noUseGraphic = false;
				item.shoot = ModContent.ProjectileType<FireplaceCrescentCharge>();
				item.UseSound = SoundID.Item28;
				return player.ownedProjectileCounts[item.shoot] <= 0;
			}

			item.useStyle = ItemUseStyleID.Swing;
			item.channel = false;
			item.noMelee = false;
			item.noUseGraphic = false;
			item.shoot = ProjectileID.SwordBeam;
			item.UseSound = SoundID.Item1;
			return true;
		}

		public static bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			if (player.ownedProjectileCounts[type] > 0) {
				return false;
			}

			Projectile.NewProjectile(source, position, velocity, type, damage, knockback, player.whoAmI, -1f);
			return false;
		}

		public static float ChargeLerp(float ticks)
		{
			return MathHelper.Clamp((ticks - FormTicks) / (MaxTicks - FormTicks), 0f, 1f);
		}

		public static float DamageRatio(float ticks)
		{
			return MathHelper.Lerp(MinDamageRatio, MaxDamageRatio, ChargeLerp(ticks));
		}

		public static float BladeScale(float ticks)
		{
			return MathHelper.Lerp(MinScale, MaxScale, ChargeLerp(ticks));
		}

		public static float BurstRadius(float ticks)
		{
			return MathHelper.Lerp(MinBurstRadius, MaxBurstRadius, ChargeLerp(ticks));
		}
	}

	/// <summary>右键按住的蓄力体：不造成伤害，只锁怪、计时、在目标上方画出成型的巨刃。</summary>
	public class FireplaceCrescentCharge : ModProjectile
	{
		public override string Texture => "WastelandSoul/Content/Projectiles/Fireplace/FireplaceGiantCrescent";

		public override void SetDefaults()
		{
			Projectile.width = 16;
			Projectile.height = 16;
			Projectile.friendly = true;
			Projectile.penetrate = -1;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.netImportant = true;
			Projectile.timeLeft = 2;
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

			if (WastelandHoldout.CantUseHoldout(owner) || !IsGreatblade(owner.HeldItem)) {
				Projectile.Kill();
				return;
			}

			Projectile.Center = owner.MountedCenter;
			Projectile.timeLeft = 2;
			owner.heldProj = Projectile.whoAmI;
			owner.itemTime = 2;
			owner.itemAnimation = 2;
			owner.itemRotation = 0f;

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

			if (Formed() && locked != null && Projectile.localAI[0] == 0f) {
				Projectile.localAI[0] = 1f;
				if (!Main.dedServ) {
					SoundEngine.PlaySound(SoundID.Item28, HoverPosition(locked));
				}
			}

			if (Formed() && locked != null && !Main.dedServ && Main.rand.NextBool(4)) { // sync-ok: visual only
				Vector2 hover = HoverPosition(locked);
				Dust dust = Dust.NewDustDirect(hover - new Vector2(18f), 36, 36, DustID.IceTorch);
				dust.noGravity = true;
				dust.velocity.Y = -1.2f;
				dust.scale = 1.05f;
			}

			if (Projectile.ai[1] >= FireplaceGreatbladeCharge.MaxTicks) {
				Projectile.Kill();
			}
		}

		public override void OnKill(int timeLeft)
		{
			if (Projectile.owner != Main.myPlayer || !Formed()) {
				return;
			}

			NPC locked = LockedNpc();
			if (locked == null) {
				return;
			}

			float ticks = Projectile.ai[1];
			int damage = (int)(Projectile.damage * FireplaceGreatbladeCharge.DamageRatio(ticks));
			float lerp = FireplaceGreatbladeCharge.ChargeLerp(ticks);
			Vector2 impact = locked.Center;
			Vector2 spawn = new Vector2(impact.X, impact.Y - FireplaceGreatbladeCharge.DropHeight);
			Player owner = Main.player[Projectile.owner];

			Projectile.NewProjectile(
				owner.GetSource_ItemUse(owner.HeldItem),
				spawn,
				new Vector2(0f, 10f),
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
			if (!Formed()) {
				return false;
			}

			NPC locked = LockedNpc();
			if (locked == null) {
				return false;
			}

			DrawCrescent(HoverPosition(locked), FireplaceGreatbladeCharge.BladeScale(Projectile.ai[1]), lightColor, 0.82f);
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
			return Projectile.ai[1] >= FireplaceGreatbladeCharge.FormTicks && LockedNpc() != null;
		}

		private static Vector2 HoverPosition(NPC npc)
		{
			return new Vector2(npc.Center.X, npc.Center.Y - FireplaceGreatbladeCharge.DropHeight);
		}

		private static bool IsGreatblade(Item item)
		{
			return item != null && (item.type == ModContent.ItemType<Content.Items.Weapons.Boss4Fireplace.FireplaceWarriorWeapon>()
				|| item.type == ModContent.ItemType<Content.Items.Weapons.Boss4Fireplace.FireplaceWarriorWeaponEx>());
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

	/// <summary>成型后的巨新月刃：从锁定点上方落下，抵达后炸开。</summary>
	public class FireplaceGiantCrescent : ModProjectile
	{
		public override void SetDefaults()
		{
			Projectile.width = 72;
			Projectile.height = 96;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Melee;
			Projectile.penetrate = -1;
			Projectile.timeLeft = 90;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;
		}

		public override bool? CanDamage()
		{
			return false;
		}

		public override void AI()
		{
			float lerp = Projectile.ai[2];
			Projectile.scale = FireplaceGreatbladeCharge.BladeScale(
				FireplaceGreatbladeCharge.FormTicks + lerp * (FireplaceGreatbladeCharge.MaxTicks - FireplaceGreatbladeCharge.FormTicks));
			Projectile.rotation = MathHelper.PiOver2;

			Vector2 impact = new Vector2(Projectile.ai[0], Projectile.ai[1]);
			Projectile.velocity.Y += 1.4f;
			if (Projectile.velocity.Y > 26f) {
				Projectile.velocity.Y = 26f;
			}

			Projectile.velocity.X = (impact.X - Projectile.Center.X) * 0.12f;

			if (!Main.dedServ && Main.rand.NextBool(2)) { // sync-ok: visual only
				Dust dust = Dust.NewDustDirect(Projectile.position, Projectile.width, Projectile.height, DustID.IceTorch);
				dust.noGravity = true;
				dust.velocity.Y = 2.4f;
				dust.scale = 1.2f;
			}

			if (Projectile.Center.Y >= impact.Y) {
				Projectile.Center = impact;
				Projectile.Kill();
			}
		}

		public override void OnKill(int timeLeft)
		{
			if (Projectile.owner != Main.myPlayer) {
				return;
			}

			float lerp = Projectile.ai[2];
			float radius = FireplaceGreatbladeCharge.BurstRadius(
				FireplaceGreatbladeCharge.FormTicks + lerp * (FireplaceGreatbladeCharge.MaxTicks - FireplaceGreatbladeCharge.FormTicks));

			Projectile.NewProjectile(
				Projectile.GetSource_Death(),
				Projectile.Center,
				Vector2.Zero,
				ModContent.ProjectileType<FireplaceCrescentBurst>(),
				Projectile.damage,
				Projectile.knockBack,
				Projectile.owner,
				radius);
		}

		public override bool PreDraw(ref Color lightColor)
		{
			FireplaceCrescentCharge.DrawCrescent(Projectile.Center, Projectile.scale, lightColor, 1f);
			return false;
		}
	}

	/// <summary>落地爆炸：圆形范围、每人只结算一次，挂霜火。</summary>
	public class FireplaceCrescentBurst : ModProjectile
	{
		public override string Texture => "WastelandSoul/Content/Projectiles/Fireplace/FireplaceGiantCrescent";

		public override void SetDefaults()
		{
			Projectile.width = 160;
			Projectile.height = 160;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Melee;
			Projectile.penetrate = -1;
			Projectile.timeLeft = 16;
			Projectile.tileCollide = false;
			Projectile.ignoreWater = true;
			Projectile.usesLocalNPCImmunity = true;
			Projectile.localNPCHitCooldown = -1;
			Projectile.hide = true;
		}

		public override void AI()
		{
			if (Projectile.localAI[0] == 0f) {
				Projectile.localAI[0] = 1f;
				int size = (int)(Projectile.ai[0] * 2f);
				Projectile.position = Projectile.Center - new Vector2(size * 0.5f);
				Projectile.width = size;
				Projectile.height = size;
				if (!Main.dedServ) {
					SoundEngine.PlaySound(SoundID.Item14, Projectile.Center);
					SoundEngine.PlaySound(SoundID.Item27, Projectile.Center);
				}
			}

			Lighting.AddLight(Projectile.Center, 0.22f, 0.40f, 0.62f);

			if (Main.dedServ) {
				return;
			}

			float radius = Projectile.ai[0];
			int sparks = Projectile.timeLeft > 12 ? 10 : 4;
			for (int i = 0; i < sparks; i++) {
				Vector2 offset = Main.rand.NextVector2Circular(radius, radius * 0.55f); // sync-ok: visual only
				Dust dust = Dust.NewDustDirect(Projectile.Center + offset, 4, 4, DustID.IceTorch);
				dust.noGravity = true;
				dust.velocity = offset * 0.04f;
				dust.scale = 1.35f;
			}
		}

		public override bool? Colliding(Rectangle projHitbox, Rectangle targetHitbox)
		{
			float radius = Projectile.ai[0];
			Vector2 closest = new Vector2(
				MathHelper.Clamp(Projectile.Center.X, targetHitbox.Left, targetHitbox.Right),
				MathHelper.Clamp(Projectile.Center.Y, targetHitbox.Top, targetHitbox.Bottom));
			return Vector2.DistanceSquared(Projectile.Center, closest) <= radius * radius;
		}

		public override bool PreDraw(ref Color lightColor)
		{
			return false;
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone)
		{
			WastelandShoot.HitBuff(target, BuffID.Frostburn, 240);
		}
	}
}
