using System;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace WastelandSoul.Common.ItemBases
{
	/// <summary>
	/// 手持外观（对照原版 ExampleStaff / 灾厄 AngelicShotgun）：
	/// 同一张物品 PNG 既是背包图标也是手里那把。
	/// 枪把握把放在贴图左侧，再用 <see cref="ModItem.HoldoutOffset"/> 拉进手掌；
	/// 法杖贴图朝右上，并打 <c>Item.staff[Type]</c>，引擎才会绕杖柄转向光标。
	/// 法典 / 拳套 / 魔法刀不走法杖 45°，按枪同款偏移对着光标。
	/// </summary>
	public static class WastelandHeldVisuals
	{
		public static readonly Vector2 GunOffset = new Vector2(-10f, 2f);

		public static readonly Vector2 BowOffset = new Vector2(-4f, 0f);

		public static readonly Vector2 TomeOffset = new Vector2(-6f, 2f);

		/// <summary>
		/// 枪贴图大约 44×44，原版人物只有四十来像素高，1:1 画在手里会跟人体差不多大。
		/// 只改手持/掉落缩放，背包格仍按贴图适配。
		/// </summary>
		public const float GunHoldScale = 0.58f;

		public static bool NameLooksLikeStaff(string typeName)
		{
			if (string.IsNullOrEmpty(typeName)) {
				return false;
			}

			if (Contains(typeName, "Tome") || Contains(typeName, "Codex") || Contains(typeName, "Book")
				|| Contains(typeName, "Discharger") || Contains(typeName, "Gauntlet")) {
				return false;
			}

			if (Contains(typeName, "Archivist") && Contains(typeName, "Mage")) {
				return false;
			}

			return Contains(typeName, "Wand") || Contains(typeName, "Staff") || Contains(typeName, "Rod")
				|| Contains(typeName, "Mage") || Contains(typeName, "Scepter") || Contains(typeName, "Blade");
		}

		public static Vector2? ShootHoldoutOffset(Item item)
		{
			if (item.noUseGraphic || item.useStyle != ItemUseStyleID.Shoot) {
				return null;
			}

			if (Item.staff[item.type]) {
				return null;
			}

			if (item.useAmmo == AmmoID.Arrow) {
				return BowOffset;
			}

			string name = item.ModItem?.Name;
			if (name != null && (Contains(name, "Tome") || Contains(name, "Codex") || Contains(name, "Book")
				|| (Contains(name, "Archivist") && Contains(name, "Mage")))) {
				return TomeOffset;
			}

			return GunOffset;
		}

		public static bool IsHeldGun(Item item)
		{
			if (item.noUseGraphic || item.useStyle != ItemUseStyleID.Shoot) {
				return false;
			}

			if (Item.staff[item.type] || item.useAmmo == AmmoID.Arrow) {
				return false;
			}

			string name = item.ModItem?.Name;

			if (string.IsNullOrEmpty(name)) {
				return false;
			}

			if (Contains(name, "Tome") || Contains(name, "Codex") || Contains(name, "Book")
				|| Contains(name, "Discharger")
				|| (Contains(name, "Archivist") && Contains(name, "Mage"))) {
				return false;
			}

			if (item.useAmmo == AmmoID.Bullet || item.useAmmo == AmmoID.Gel) {
				return true;
			}

			return Contains(name, "Ranger") || Contains(name, "Shotgun") || Contains(name, "Nailgun")
				|| Contains(name, "Railgun") || Contains(name, "Cannon") || Contains(name, "Scatter")
				|| Contains(name, "Flechette");
		}

		private static bool Contains(string haystack, string needle)
		{
			return haystack.IndexOf(needle, StringComparison.OrdinalIgnoreCase) >= 0;
		}
	}

	public sealed class WastelandGunHoldScale : GlobalItem
	{
		public override void SetDefaults(Item item)
		{
			if (item.ModItem != null && WastelandHeldVisuals.IsHeldGun(item)) {
				item.scale = WastelandHeldVisuals.GunHoldScale;
			}
		}
	}
}
