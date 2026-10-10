using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Items.Materials;
using WastelandSoul.Content.Items.Weapons;

namespace WastelandSoul.Content.Items.Weapons.Boss1Scavenger
{
	/// <summary>
	/// 清道夫 · B 线火枪。对标原版火枪：高伤、慢速、打真正的子弹。
	/// </summary>
	public class ScavengerRangerWeaponEX : WastelandClassWeapon
	{
		protected override DamageClass Class => DamageClass.Ranged;
		protected override int Damage => 30;
		protected override int UseTime => 32;
		protected override float Knockback => 5.25f;
		protected override int Rarity => WastelandRarityTiers.Early;

		protected override int ShootType => ProjectileID.Bullet;

		protected override float ShootSpeed => 9f;

		public override void SetDefaults()
		{
			base.SetDefaults();
			WastelandWeaponKit.Ranged(Item);
			Item.crit = 7;
			Item.UseSound = SoundID.Item40;
		}

		// B 线为专属掉落：**不写任何 AddRecipes()**，只能从清道夫的掉落袋开出。
	}
}
