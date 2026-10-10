using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.Systems;

namespace WastelandSoul.Content.Projectiles.Whips
{
	public abstract class WastelandWhipProj : ModProjectile
	{
		protected abstract int TagBuff { get; }

		protected abstract float Falloff { get; }

		protected abstract int VanillaWhipLook { get; }

		protected abstract float RangeMultiplier { get; }

		protected abstract int Segments { get; }

		public override void SetStaticDefaults()
		{
			ProjectileID.Sets.IsAWhip[Type] = true;
			TextureAssets.Projectile[Type] = TextureAssets.Projectile[VanillaWhipLook];
		}

		public override void SetDefaults()
		{
			Projectile.DefaultToWhip();
			Projectile.WhipSettings.RangeMultiplier = RangeMultiplier;
			Projectile.WhipSettings.Segments = Segments;
		}

		public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone)
		{
			target.AddBuff(TagBuff, 240);
			Main.player[Projectile.owner].MinionAttackTargetNPC = target.whoAmI;
			OnWhipHit(target);
			Projectile.damage = (int)(Projectile.damage * (1f - Falloff));
		}

		protected virtual void OnWhipHit(NPC target)
		{
		}

		public override bool PreDraw(ref Color lightColor)
		{
			List<Vector2> points = new List<Vector2>();
			Projectile.FillWhipControlPoints(Projectile, points);
			Main.DrawWhip_WhipBland(Projectile, points);
			return false;
		}
	}

	public class SteelLashProj : WastelandWhipProj
	{
		protected override int TagBuff => ModContent.BuffType<SteelLashTag>();
		protected override float Falloff => 0.20f;
		protected override int VanillaWhipLook => ProjectileID.ThornWhip;
		protected override float RangeMultiplier => 1.15f;
		protected override int Segments => 18;

		protected override void OnWhipHit(NPC target)
		{
			target.AddBuff(BuffID.Poisoned, 240);
		}
	}

	public class IndexLashProj : WastelandWhipProj
	{
		protected override int TagBuff => ModContent.BuffType<IndexLashTag>();
		protected override float Falloff => 0.20f;
		protected override int VanillaWhipLook => ProjectileID.SwordWhip;
		protected override float RangeMultiplier => 1.45f;
		protected override int Segments => 22;

		protected override void OnWhipHit(NPC target)
		{
			Main.player[Projectile.owner].AddBuff(BuffID.SwordWhipPlayerBuff, 240);
		}
	}

	public class CinderLashProj : WastelandWhipProj
	{
		protected override int TagBuff => ModContent.BuffType<CinderLashTag>();
		protected override float Falloff => 0.15f;
		protected override int VanillaWhipLook => ProjectileID.CoolWhip;
		protected override float RangeMultiplier => 1.65f;
		protected override int Segments => 26;

		protected override void OnWhipHit(NPC target)
		{
			target.AddBuff(BuffID.OnFire, 240);
		}
	}

	public class HearthLashProj : WastelandWhipProj
	{
		protected override int TagBuff => ModContent.BuffType<HearthLashTag>();
		protected override float Falloff => 0.08f;
		protected override int VanillaWhipLook => ProjectileID.MaceWhip;
		protected override float RangeMultiplier => 1.85f;
		protected override int Segments => 30;
	}

	public abstract class WastelandWhipTag : ModBuff
	{
		public override void SetStaticDefaults()
		{
			Main.debuff[Type] = true;
			Main.buffNoSave[Type] = true;
			Main.buffNoTimeDisplay[Type] = true;
			BuffID.Sets.IsATagBuff[Type] = true;
		}
	}

	public class SteelLashTag : WastelandWhipTag
	{
	}

	public class IndexLashTag : WastelandWhipTag
	{
	}

	public class CinderLashTag : WastelandWhipTag
	{
	}

	public class HearthLashTag : WastelandWhipTag
	{
	}

	public class WastelandWhipTagNpc : GlobalNPC
	{
		public override void ModifyHitByProjectile(NPC npc, Projectile projectile, ref NPC.HitModifiers modifiers)
		{
			if (!projectile.minion && !ProjectileID.Sets.MinionShot[projectile.type]) {
				return;
			}

			if (npc.HasBuff(ModContent.BuffType<SteelLashTag>())) {
				modifiers.FlatBonusDamage += 6;
			}

			if (npc.HasBuff(ModContent.BuffType<IndexLashTag>())) {
				modifiers.FlatBonusDamage += 9;
			}

			if (npc.HasBuff(ModContent.BuffType<CinderLashTag>())) {
				modifiers.FlatBonusDamage += 12;
			}

			if (npc.HasBuff(ModContent.BuffType<HearthLashTag>())) {
				modifiers.FlatBonusDamage += 16;

				if (WastelandRandom.Roll(npc.whoAmI, projectile.identity, projectile.owner, 0, 10) == 0) {
					modifiers.SetCrit();
				}
			}
		}
	}
}
