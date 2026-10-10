using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ModLoader;

namespace WastelandSoul.Content.Items.Weapons
{
	/// <summary>
	/// 武器「身份」写在官方钩子里，不另做挥砍框架。
	/// <para/>学的是灾厄那套<b>思路</b>（每把武器一个明确契约：扇形就自己 <c>NewProjectile</c> 再 <c>return false</c>；
	/// 真近战身份写在物品 <c>OnHitNPC</c>），实现只用 tML / 原版 API，阔剑形态仍交给 C.I.V.E。
	/// </summary>
	public static class WastelandShoot
	{
		/// <summary>
		/// 均匀扇形。吞掉原版那一发（必须 <c>return</c> 本方法的返回值）。
		/// </summary>
		public static bool EvenFan(IEntitySource source, Vector2 position, Vector2 velocity, int type, int damage,
			float knockback, int owner, int count, float totalSpread)
		{
			if (count <= 1) {
				Projectile.NewProjectile(source, position, velocity, type, damage, knockback, owner);
				return false;
			}

			float start = -totalSpread * 0.5f;
			float step = totalSpread / (count - 1);

			for (int i = 0; i < count; i++) {
				Vector2 shot = velocity.RotatedBy(start + step * i);
				Projectile.NewProjectile(source, position, shot, type, damage, knockback, owner);
			}

			return false;
		}

		public static void HitBuff(NPC target, int buff, int time)
		{
			if (target == null || !target.active || target.friendly || target.dontTakeDamage) {
				return;
			}

			target.AddBuff(buff, time);
		}
	}
}
