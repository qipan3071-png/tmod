using Microsoft.Xna.Framework;
using Terraria;
using Terraria.Audio;
using Terraria.ModLoader;
using WastelandSoul.Content.Items.Weapons.Boss4Fireplace;

namespace WastelandSoul.Content.Projectiles.Fireplace
{
	/// <summary>
	/// 壁炉权杖的按住手持体：贴手转向，按物品 <c>useTime</c> 从杖尖打冷光弹。
	/// A / B 线共用这一发，打哪种子弹看手里那把。
	/// </summary>
	public class FireplaceMageHoldout : WastelandHoldout
	{
		public override int AssociatedItemID => ModContent.ItemType<FireplaceMageWeapon>();

		protected override float OffsetFromArm => 34f;

		protected override bool IsHeldItem(Item item)
		{
			return item.type == AssociatedItemID || item.type == ModContent.ItemType<FireplaceMageWeaponEx>();
		}

		protected override void HoldoutAI(Player owner)
		{
			if (Projectile.owner != Main.myPlayer) {
				return;
			}

			Projectile.localAI[0] += 1f;
			int interval = System.Math.Max(8, owner.HeldItem.useTime);
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

			int shot = owner.HeldItem.type == ModContent.ItemType<FireplaceMageWeaponEx>()
				? ModContent.ProjectileType<FireplaceMageProjectileEX>()
				: ModContent.ProjectileType<FireplaceMageProjectile>();
			int damage = owner.GetWeaponDamage(owner.HeldItem);
			float knockback = owner.GetWeaponKnockback(owner.HeldItem);
			Vector2 velocity = Projectile.velocity * owner.HeldItem.shootSpeed;

			Projectile.NewProjectile(
				owner.GetSource_ItemUse(owner.HeldItem),
				GunTip(),
				velocity,
				shot,
				damage,
				knockback,
				owner.whoAmI);
		}
	}
}
