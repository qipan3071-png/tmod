using System.Linq;
using Terraria;
using Terraria.GameContent.ItemDropRules;
using Terraria.ID;
using Terraria.ModLoader;
using Terraria.ModLoader.IO;

namespace WastelandSoul.Common.Systems
{
	/// <summary>
	/// 玩家点名：闪亮红气球从天域箱 / 天空匣 / 天蓝匣开出率上调到 3/4。
	/// 匣子在打开时掷点；天域箱在世界生成时填，已有世界第一次加载会补一次。
	/// </summary>
	public class VanillaSkyBalloonCrateLoot : GlobalItem
	{
		public override bool AppliesToEntity(Item entity, bool lateInstantiation)
		{
			return entity.type == ItemID.FloatingIslandFishingCrate
				|| entity.type == ItemID.FloatingIslandFishingCrateHard;
		}

		public override void ModifyItemLoot(Item item, ItemLoot itemLoot)
		{
			itemLoot.Add(new CommonDrop(ItemID.ShinyRedBalloon, 4, 1, 1, 3));
		}
	}

	public class VanillaSkyBalloonChestLoot : ModSystem
	{
		private const int SkywareChestStyle = 12;
		private bool existingWorldRetuned;

		public override void PostWorldGen()
		{
			RetuneSkywareChests(WorldGen.genRand);
			existingWorldRetuned = true;
		}

		public override void PostUpdateWorld()
		{
			if (existingWorldRetuned || Main.netMode == NetmodeID.MultiplayerClient) {
				return;
			}

			RetuneSkywareChests(new Terraria.Utilities.UnifiedRandom(Main.worldID));
			existingWorldRetuned = true;
		}

		public override void SaveWorldData(TagCompound tag)
		{
			tag["skyBalloonRetuned"] = existingWorldRetuned;
		}

		public override void LoadWorldData(TagCompound tag)
		{
			existingWorldRetuned = tag.GetBool("skyBalloonRetuned");
		}

		public override void OnWorldUnload()
		{
			existingWorldRetuned = false;
		}

		private static void RetuneSkywareChests(Terraria.Utilities.UnifiedRandom rng)
		{
			for (int i = 0; i < Main.maxChests; i++) {
				Chest chest = Main.chest[i];

				if (chest == null) {
					continue;
				}

				Tile tile = Main.tile[chest.x, chest.y];

				if (tile == null || !tile.HasTile || tile.TileType != TileID.Containers) {
					continue;
				}

				if (tile.TileFrameX / 36 != SkywareChestStyle) {
					continue;
				}

				if (chest.item.Any(slot => slot != null && slot.type == ItemID.ShinyRedBalloon && slot.stack > 0)) {
					continue;
				}

				if (rng.Next(4) >= 3) {
					continue;
				}

				for (int slot = 0; slot < chest.item.Length; slot++) {
					if (chest.item[slot] == null || chest.item[slot].type == ItemID.None || chest.item[slot].stack <= 0) {
						chest.item[slot] = new Item();
						chest.item[slot].SetDefaults(ItemID.ShinyRedBalloon);
						break;
					}
				}
			}
		}
	}
}
