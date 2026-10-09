using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.GameContent;

namespace WastelandSoul.Content.Projectiles.Scavenger
{
	/// <summary>
	/// 清道夫大刀的月牙刀光。
	/// <para/>本体就是**原版 <see cref="ProjectileID.SwordBeam"/>**（AI、判定照旧），
	/// 贴图指到原版刀光资源，并把「穿透 4 段」记在 <c>ai[2]</c> 上，
	/// 由 <see cref="SwordBeamHook"/> 对本武器打出的那一批生效。
	/// <para/>⚠️ 标记**刻意放在 <c>ai[2]</c>**：原版刀光的 AI 自己会写
	/// <c>ai[1]</c>（它在 <c>ai[1] == 0</c> 时把该位设成 1，当作「已经响过音」的内部标志，
	/// 见 <c>Projectile.VanillaAI()</c> 里 <c>type == 116</c> 的分支）。
	/// 两边都用 1 虽然眼下不冲突，但跟原版共用一个槽位太脆 —— 换个语义干净的槽位。
	/// </summary>
	public class ScavengerBeam : ModProjectile
	{
		/// <summary>穿透段数（能穿 4 个敌人）。</summary>
		public const int PenetrateHits = 4;

		/// <summary>标记：只有大刀甩出的刀光带这个值（写在 <c>ai[2]</c>，原版不碰这个槽）。</summary>
		public const float Mark = 1f;

		public override void SetStaticDefaults()
		{
			// 复用原版刀光贴图 —— 不新增 PNG
			TextureAssets.Projectile[Type] = TextureAssets.Projectile[ProjectileID.SwordBeam];
		}

		public override void SetDefaults()
		{
			// 数值全部交给原版 SwordBeam 的默认值；这里只兜住尺寸
			Projectile.width = 24;
			Projectile.height = 24;
			Projectile.friendly = true;
			Projectile.DamageType = DamageClass.Melee;
		}
	}
}
