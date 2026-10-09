using Terraria;
using Terraria.IO;
using Terraria.ModLoader;
using Terraria.WorldBuilding;
using WastelandSoul.Content.Walls;

namespace WastelandSoul.Content.Subworlds
{
	/// <summary>
	/// 壁炉子世界的**统一补墙 pass**（玩家要求：整个子世界只用「灰烬荒壁」一种背景墙，
	/// 而且**不允许有洞**）。
	///
	/// <para/>为什么单独做成一个 pass、而且**排在所有挖空 / 建筑步骤之后**
	/// （注册顺序见 <see cref="FireplaceSubworld.OnLoad"/>：灰烬原野 → 堡垒 → 祈塔 →
	/// 地下通道 → 椭球地宫 → **本 pass** → 收尾）：
	/// <list type="bullet">
	/// <item>前面的步骤会互相挖：地宫那一步会把通道内空整段重掏一遍、堡垒竖井要穿过门厅地板、
	/// 塔身要从堡垒屋顶穿出去……任何"边挖边补"的写法都得在每个后面再补一次；</item>
	/// <item>放在最后就只剩一条判据：**这一格是空气、而且在地表线以下（或落在人造结构内空里）
	/// → 给它铺墙**。前面怎么挖、怎么盖都不影响结论，所以"全局连续"是**定义上**成立的，
	/// 不需要（也无法）靠人去核对每一处镂空。</item>
	/// </list>
	///
	/// <para/>覆盖范围（<see cref="NeedsWall"/>）：
	/// <list type="bullet">
	/// <item><b>地表线以下的一切</b>（<c>y ≥ FireplaceTerrain.Surface[x]</c>）：灰烬层、岩层、
	/// 矿洞、废弃矿道、地下通道、堡垒内腔、门厅 / 走廊 / 侧房、竖井、椭球地宫 12 间房与升降井；</item>
	/// <item><b>地表线以上的人造内空</b>：祈塔塔身、塔顶接驳颈、塔顶 Boss 场地（都按 <c>FireplaceLayout</c>
	/// 的盒子上限判定）。天空（结构之外的空气）**不铺墙**，从塔里往外看仍然是星空。</item>
	/// </list>
	///
	/// <para/>⚠️ 这里是**全工程唯一**允许调 <see cref="WorldPaint.SetWall"/> 的地方。
	/// <c>tools/check_fireplace_layout.py</c> 第 11 节按"正向断言"卡住这一条：
	/// 必须存在且只存在这一处铺墙调用，别处再出现第二处就直接红。
	/// </summary>
	public static class FireplaceWalls
	{
		/// <summary>地表线以下 + 塔 / 场地内空的统一补墙。</summary>
		public static void Build(GenerationProgress progress, GameConfiguration configuration)
		{
			// 冒烟测试会传 null 进来（不构造 GameConfiguration，免得拉进 Newtonsoft 触发警告）
			progress ??= new GenerationProgress();
			FireplaceGenLog.Start("6/7 灰烬荒壁");
			progress.Message = "正在给壁炉糊上灰烬荒壁……";

			ushort wall = (ushort)ModContent.WallType<AshWasteWall>();
			long placed = 0;

			for (int x = 0; x < FireplaceLayout.Width; x++) {
				int surface = FireplaceTerrain.Surface[x];

				for (int y = 0; y < FireplaceLayout.Height; y++) {
					// 只补"空气格"：方块格后面有没有墙，画面上看不见，补了纯属浪费
					// （地表以下约 670 万格，其中空气只有一两百万格）。
					if (!NeedsWall(x, y, surface) || Main.tile[x, y].HasTile) {
						continue;
					}

					if (Main.tile[x, y].WallType == wall) {
						continue;
					}

					WorldPaint.SetWall(x, y, wall);
					placed++;
				}

				if ((x & 1023) == 0) {
					progress.Set(x / (double)FireplaceLayout.Width);
				}
			}

			FireplaceGenLog.Note(string.Format("灰烬荒壁 {0} 格（这一遍之后：地表以下 / 塔内 / 场地里一格洞都没有）", placed));
			progress.Set(1.0);
			FireplaceGenLog.Done("6/7 灰烬荒壁");
		}

		/// <summary>
		/// 这一格要不要墙（只看"位置"，不看它现在是方块还是空气）。
		/// </summary>
		private static bool NeedsWall(int x, int y, int surface)
		{
			// 1) 地表线以下：一律要（岩层 / 矿洞 / 矿道 / 通道 / 堡垒 / 地宫 / 各条竖井）
			if (y >= surface) {
				return true;
			}

			// 2) 地表线以上只有人造结构的内空要墙：塔身 + 接驳颈（塔身那一列，从场地顶一直到堡垒顶）
			if (x >= FireplaceLayout.TowerLeft && x <= FireplaceLayout.TowerRight
				&& y >= FireplaceLayout.ArenaTop - 1 && y <= FireplaceLayout.FortBottom) {
				return true;
			}

			// 3) 塔顶 Boss 场地（比塔身宽，整块都在太空线上）
			if (x >= FireplaceLayout.ArenaLeft && x <= FireplaceLayout.ArenaRight
				&& y >= FireplaceLayout.ArenaTop - 1 && y <= FireplaceLayout.ArenaBottom) {
				return true;
			}

			return false;
		}
	}
}
