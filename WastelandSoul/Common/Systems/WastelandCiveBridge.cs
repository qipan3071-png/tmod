using System;
using System.Collections;
using System.Reflection;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ModLoader;

namespace WastelandSoul.Common.Systems
{
	/// <summary>
	/// 软依赖调用 C.I.V.E（CoolerItemVisualEffect）。
	/// 没装照样加载；装了就把本模组阔剑挂进它的预设招式（斩 / 横扫 / 刺 / 连击 / 重劈）。
	/// 不搬它的序列 XML，只按名字引用它已经打好的预设。
	/// </summary>
	public sealed class WastelandCiveBridge : ModSystem
	{
		public const string CiveModName = "CoolerItemVisualEffect";

		internal static Mod Cive;

		public override void PostSetupContent()
		{
			Cive = null;

			if (!ModLoader.TryGetMod(CiveModName, out Cive)) {
				Mod.Logger.Info("未检测到 C.I.V.E，阔剑仍用原版挥砍。");
				return;
			}

			try {
				object registered = Cive.Call(
					"RegisterModifyWeaponTex",
					(Func<Item, Texture2D>)GetWastelandMeleeTexture,
					0.25f);

				if (!Equals(registered, true)) {
					Mod.Logger.Warn("C.I.V.E Call RegisterModifyWeaponTex 未返回 true。");
				}
			}
			catch (Exception exception) {
				Mod.Logger.Warn("调用 C.I.V.E RegisterModifyWeaponTex 失败：" + exception.Message);
			}
		}

		public override void Unload()
		{
			Cive = null;
		}

		private static Texture2D GetWastelandMeleeTexture(Item item)
		{
			if (item?.ModItem == null || item.ModItem.Mod.Name != "WastelandSoul") {
				return null;
			}

			if (item.noMelee || item.noUseGraphic || item.useStyle != Terraria.ID.ItemUseStyleID.Swing) {
				return null;
			}

			Main.instance.LoadItem(item.type);
			return TextureAssets.Item[item.type].Value;
		}
	}

	public sealed class WastelandCivePlayer : ModPlayer
	{
		private const string GroupPrefix = "WastelandSoul.";

		public override void OnEnterWorld()
		{
			if (Player.whoAmI != Main.myPlayer) {
				return;
			}

			if (WastelandCiveBridge.Cive == null && !ModLoader.TryGetMod(WastelandCiveBridge.CiveModName, out WastelandCiveBridge.Cive)) {
				return;
			}

			try {
				int groups = AttachPresetGroups(Player);

				if (groups > 0 && !Main.dedServ) {
					Main.NewText($"废土魂穿：已把 {groups} 组阔剑交给 C.I.V.E 接管招式。", Color.CornflowerBlue);
				}
			}
			catch (Exception exception) {
				Mod.Logger.Warn("给 C.I.V.E 挂阔剑分组失败：" + exception.Message);
			}
		}

		private static int AttachPresetGroups(Player player)
		{
			Mod cive = WastelandCiveBridge.Cive;
			Type playerType = cive.Code.GetType("CoolerItemVisualEffect.Common.MeleeModify.MeleeModifyPlayer");
			Type groupType = cive.Code.GetType("CoolerItemVisualEffect.Common.WeaponGroup.WeaponGroup");
			Type seqType = cive.Code.GetType("CoolerItemVisualEffect.Common.MeleeModify.CIVESequenceDefinition");

			if (playerType == null || groupType == null || seqType == null) {
				return 0;
			}

			ModPlayer meleePlayer = FindModPlayer(player, playerType);

			if (meleePlayer == null) {
				return 0;
			}

			IList groups = playerType.GetProperty("WeaponGroups")?.GetValue(meleePlayer) as IList;
			IDictionary cache = playerType.GetProperty("CachedGrouping")?.GetValue(meleePlayer) as IDictionary;

			if (groups == null) {
				return 0;
			}

			RemoveOldGroups(groups, groupType);
			cache?.Clear();

			(string preset, string[] items)[] map = {
				("PureSlash", new[] {
					"ScavengerWarriorWeapon", "ScavengerWarriorWeaponEX", "RustCleaver", "RustCleaverEX", "ScavengerCWarrior"
				}),
				("StormySlash", new[] {
					"ScavengerGreatblade", "FireplaceWarriorWeapon", "FireplaceWarriorWeaponEx", "FireplaceCWarrior"
				}),
				("PureStab", new[] { "SignalCleaver" }),
				("TripleSlash", new[] {
					"SalvagedSteelSaber", "ArchivistVerdictBlade", "ArchivistWarriorWeapon", "ArchivistWarriorWeaponEX", "ArchivistCWarrior"
				}),
				("HeavyChop", new[] {
					"ScrapGreatsword", "AshHeartWarriorWeapon", "AshHeartWarriorWeaponEx", "AshHeartCWarrior", "RiftCleaver"
				})
			};

			int added = 0;

			for (int i = map.Length - 1; i >= 0; i--) {
				object group = MakeGroup(groupType, seqType, cive, map[i].preset, map[i].items);

				if (group == null) {
					continue;
				}

				groups.Insert(0, group);
				added++;
			}

			return added;
		}

		private static ModPlayer FindModPlayer(Player player, Type type)
		{
			foreach (ModPlayer extra in player.ModPlayers) {
				if (type.IsInstanceOfType(extra)) {
					return extra;
				}
			}

			return null;
		}

		private static void RemoveOldGroups(IList groups, Type groupType)
		{
			FieldInfo nameField = groupType.GetField("Name");

			for (int i = groups.Count - 1; i >= 0; i--) {
				object group = groups[i];
				string name = nameField?.GetValue(group) as string;

				if (name != null && name.StartsWith(GroupPrefix, StringComparison.Ordinal)) {
					groups.RemoveAt(i);
				}
			}
		}

		private static object MakeGroup(Type groupType, Type seqType, Mod cive, string preset, string[] itemNames)
		{
			object group = Activator.CreateInstance(groupType);

			if (group == null) {
				return null;
			}

			groupType.GetField("Name")?.SetValue(group, GroupPrefix + preset);
			groupType.GetProperty("BasedOnDefaultCondition")?.SetValue(group, false);
			groupType.GetProperty("WhiteList")?.SetValue(group, true);
			groupType.GetProperty("IsModifyActive")?.SetValue(group, true);
			groupType.GetProperty("IsGroupActive")?.SetValue(group, true);

			string key = ResolveSequenceKey(cive, preset);
			object sequence = Activator.CreateInstance(seqType, key);
			groupType.GetProperty("SwooshActionStyle")?.SetValue(group, sequence);

			if (groupType.GetProperty("WeaponList")?.GetValue(group) is IList list) {
				foreach (string itemName in itemNames) {
					list.Add("WastelandSoul/" + itemName);
				}
			}

			return group;
		}

		private static string ResolveSequenceKey(Mod cive, string preset)
		{
			Type manager = cive.Code.GetType("CoolerItemVisualEffect.Common.MeleeModify.MeleeSequenceManager");
			object available = manager?.GetMethod("GetAvailableSequences")?.Invoke(null, null);

			if (available is IEnumerable pairs) {
				foreach (object pair in pairs) {
					string key = pair.GetType().GetProperty("Key")?.GetValue(pair) as string;

					if (key == preset || key != null && key.EndsWith("/" + preset, StringComparison.Ordinal)) {
						return key;
					}
				}
			}

			return preset;
		}
	}
}
