using Terraria;
using Terraria.GameContent;
using Terraria.ID;
using Terraria.ModLoader;

namespace WastelandSoul.Content.Projectiles.Scavenger
{
	/// <summary>
	/// 污染炮的炮弹。
	/// <para/>**行为就是原版手榴弹**（<see cref="ProjectileID.Grenade"/>：抛物线、碰墙弹跳、
	/// 倒计时到了自爆），贴图也复用它的资源；只是单独占一个弹幕类型，
	/// 好在 <see cref="PollutionShellHook"/> 里精确认出「这是污染炮打出的那一发」。
	/// </summary>
	public class PollutionShell : ModProjectile
	{
		/// <summary>标记：污染炮打出的炮弹。</summary>
		public const float Mark = 1f;

		public override void SetStaticDefaults()
		{
			TextureAssets.Projectile[Type] = TextureAssets.Projectile[ProjectileID.Grenade];
		}

		public override void SetDefaults()
		{
			// 完全照抄原版手榴弹的形态，只换一个类型号
			Projectile.CloneDefaults(ProjectileID.Grenade);
			Projectile.aiStyle = 14;   // 原版手榴弹 AI
			Projectile.width = 14;
			Projectile.height = 14;
			Projectile.friendly = true;
			Projectile.hostile = false;
			Projectile.DamageType = DamageClass.Ranged;
		}
	}
}
