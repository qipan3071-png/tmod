using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Items.Weapons;

namespace WastelandSoul.Content.Items.Weapons.Boss1Scavenger.ScavengerDrops
{
	/// <summary>
	/// 精钢弓（射手 · Boss 1 清道夫掉落）。
	/// <para/>把**普通箭**（木箭 / 火焰箭这类基础箭）改写成原版**邪箭
	/// <see cref="ItemID.UnholyArrow"/> / <see cref="ProjectileID.UnholyArrow"/>**，
	/// 并额外给这支出膛的邪箭加**缓转向追踪**（<c>ArrowHomingHook</c>）。
	/// <list type="bullet">
	/// <item>特殊箭（小丑箭 / 圣箭 / 狱炎箭 / 诅咒箭 / 霜火箭 / 灵液箭 / 叶绿箭 / 毒液箭 / 骨箭 / 微光箭…）
	/// 原样打出，**不转化**，也不吃追踪；</item>
	/// <item>原版邪箭本身的属性一个字节都不改 —— 别的弓射出来的邪箭照旧；
	/// 追踪只对**本弓当次射出的那一支**生效（OnSpawn 里按武器来源打标记）。</item>
	/// </list>
	/// </summary>
	public class SteelBow : ModItem
	{
		public override void SetDefaults()
		{
			Item.width = 48;
			Item.height = 48;
			Item.damage = 40;
			Item.DamageType = DamageClass.Ranged;
			Item.knockBack = 4f;
			Item.useTime = 26;
			Item.useAnimation = 26;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.noMelee = true;
			Item.autoReuse = true;
			Item.useAmmo = AmmoID.Arrow;
			Item.shoot = ProjectileID.WoodenArrowFriendly;
			Item.shootSpeed = 14f;
			Item.crit = 5;                   // 初始暴击 5%
			Item.UseSound = SoundID.Item5;
			Item.value = Item.sellPrice(gold: 3);
			Item.rare = WastelandRarityTiers.EarlyLate;   // 骷髅王之后档次
		}

		public override Vector2? HoldoutOffset()
		{
			return WastelandHeldVisuals.BowOffset;
		}

		/// <summary>
		/// 这一发是不是「普通箭」——是的话转成邪箭。
		/// <para/>只认基础箭：木箭 / 火焰箭 / 邪箭，以及**无尽箭袋**（箭袋配普通箭时也按普通箭算）。
		/// 小丑箭、圣箭、狱炎箭、诅咒箭、霜火箭、灵液箭、叶绿箭、毒液箭、骨箭、微光箭一律原样打出。
		/// </summary>
		private static bool IsPlainArrow(int ammoType)
		{
			return ammoType == ItemID.WoodenArrow
				|| ammoType == ItemID.FlamingArrow
				|| ammoType == ItemID.UnholyArrow
				|| ammoType == ItemID.EndlessQuiver;
		}

		/// <summary>背包里是不是只有普通箭（无尽箭袋那一路的判定，避免把特殊箭也转掉）。</summary>
		private static bool OnlyPlainArrowsInInventory(Player player)
		{
			for (int i = 0; i < player.inventory.Length; i++) {
				Item item = player.inventory[i];

				if (!item.IsAir && item.ammo == AmmoID.Arrow && !IsPlainArrow(item.type) && item.type != ItemID.EndlessQuiver) {
					return false;
				}
			}

			return true;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			// 普通箭 → 邪箭（原版弹幕，属性不动）；特殊箭保持原样
			bool plain = IsPlainArrow(source.AmmoItemIdUsed)
				|| (source.AmmoItemIdUsed == ItemID.EndlessQuiver && OnlyPlainArrowsInInventory(player));

			int shot = plain ? ProjectileID.UnholyArrow : type;

			Projectile.NewProjectile(
				source,
				position,
				velocity,
				shot,
				damage,
				knockback,
				player.whoAmI,
				0f,
				0f);

			return false;
		}
	}
}
