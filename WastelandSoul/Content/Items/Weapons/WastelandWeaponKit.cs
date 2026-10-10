using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Content.Projectiles.Melee;

namespace WastelandSoul.Content.Items.Weapons
{
	/// <summary>
	/// 40 把 Boss 武器的共用「手感」参数：形态、声音、弹药、召唤增益。
	/// <para/>数值（伤害 / 使用时间 / 击退 / 稀有度 / 弹幕）一律由各武器类自己 override，
	/// 这里只负责把不同职业的通用形态写在一处，避免 40 个类里重复同一段样板。
	/// <para/>注意：本类不是 ModItem，不会被 tModLoader 自动加载，因此不需要贴图。
	/// </summary>
	public static class WastelandWeaponKit
	{
		/// <summary>
		/// 近战：关掉原版电风扇挥砍，改用朝光标的斩/刺/连击/重劈（自己画剑，不搬 C.I.V.E 源码）。
		/// </summary>
		public static void Melee(Item item, WastelandSwingStyle style = WastelandSwingStyle.Chop)
		{
			item.useStyle = ItemUseStyleID.Swing;
			item.autoReuse = true;
			item.UseSound = SoundID.Item1;
			EnableSwing(item, style);
		}

		public static void EnableSwing(Item item, WastelandSwingStyle style)
		{
			item.noMelee = true;
			item.noUseGraphic = true;
			item.shootsEveryUse = true;
			WastelandMeleeSwingItem extra = item.GetGlobalItem<WastelandMeleeSwingItem>();
			extra.Enabled = true;
			extra.Style = style;

			if (item.shoot <= 0) {
				item.shoot = ModContent.ProjectileType<WastelandMeleeSwing>();
				item.shootSpeed = 8f;
			}
		}

		/// <summary>
		/// 法师：法杖 / 法典，朝鼠标方向施法并消耗魔力。
		/// 法杖的 <c>Item.staff</c> 与枪的 <c>HoldoutOffset</c> 在
		/// <c>WastelandClassWeapon</c> 里按类名套上，这里只负责手感。
		/// </summary>
		public static void Magic(Item item, int mana)
		{
			item.useStyle = ItemUseStyleID.Shoot;
			item.noMelee = true;
			item.noUseGraphic = false;
			item.autoReuse = true;
			item.mana = mana;
			item.UseSound = SoundID.Item20;
		}

		/// <summary>射手：枪械，消耗火枪子弹，打出弹药自己的弹幕（流星弹等会正常转化）。</summary>
		public static void Ranged(Item item)
		{
			item.useStyle = ItemUseStyleID.Shoot;
			item.noMelee = true;
			item.noUseGraphic = false;
			item.autoReuse = true;
			item.useAmmo = AmmoID.Bullet;
			item.shoot = ProjectileID.Bullet;
			item.UseSound = SoundID.Item11;
		}

		/// <summary>
		/// 召唤师：举起召唤杖，把仆从增益挂到玩家身上。
		/// <para/>
		/// <c>buffTime</c> 只是「用出来那一帧」的初值；真正无限靠各仆从 Buff 的
		/// <c>Update</c> 每帧续到 18000。不要写成 3600，物品介绍会多出「1 分钟」。
		/// </summary>
		public static void Summon(Item item, int buffType, int mana)
		{
			item.useStyle = ItemUseStyleID.Swing;
			item.noMelee = true;
			item.noUseGraphic = false;
			item.autoReuse = true;
			item.mana = mana;
			item.buffType = buffType;
			item.buffTime = 2;
			item.UseSound = SoundID.Item44;
		}
	}
}
