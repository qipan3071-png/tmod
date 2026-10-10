using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.ModLoader;
using WastelandSoul.Content.Items.Weapons.Boss2Archivist;

namespace WastelandSoul.Content.Projectiles.Archivist
{
	/// <summary>
	/// 归档者法典 MK-II 的按住手持体：持续从书沿打出索引页（设计里的读条输出，不用白激光）。
	/// </summary>
	public class ArchivistIndexHoldout : WastelandHoldout
	{
		public override int AssociatedItemID => ModContent.ItemType<ArchivistMageWeaponEX>();

		protected override float OffsetFromArm => 24f;

		protected override void HoldoutAI(Player owner)
		{
			if (Projectile.owner != Main.myPlayer) {
				return;
			}

			Projectile.localAI[0] += 1f;
			int interval = System.Math.Max(8, owner.HeldItem.useTime / 2);
			if (Projectile.localAI[0] < interval) {
				return;
			}

			Projectile.localAI[0] = 0f;

			if (!owner.CheckMana(owner.HeldItem, pay: true)) {
				Projectile.Kill();
				return;
			}

			owner.manaRegenDelay = MathHelper.Max(owner.manaRegenDelay, 40f);
			SoundEngine.PlaySound(owner.HeldItem.UseSound, Projectile.Center);

			int damage = owner.GetWeaponDamage(owner.HeldItem);
			float knockback = owner.GetWeaponKnockback(owner.HeldItem);
			Vector2 velocity = Projectile.velocity * owner.HeldItem.shootSpeed;

			Projectile.NewProjectile(
				owner.GetSource_ItemUse(owner.HeldItem),
				GunTip(),
				velocity,
				ModContent.ProjectileType<ArchivistIndexPageEX>(),
				damage,
				knockback,
				owner.whoAmI);
		}
	}
}
