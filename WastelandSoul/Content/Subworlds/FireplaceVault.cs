using System;
using System.Collections.Generic;
using Terraria;
using Terraria.ID;
using Terraria.IO;
using Terraria.ModLoader;
using Terraria.WorldBuilding;
using WastelandSoul.Content.Tiles;

namespace WastelandSoul.Content.Subworlds
{
	/// <summary>
	/// 堡垒下方的**椭球地宫**：一个 3000×400 的瑜钢合金椭球空腔，隔绝墙 5 格厚，
	/// 内表面每 14 行嵌一条 <see cref="YugangTrim"/> 压条（青银间色）。
	///
	/// <para/>玩家原话：「底下的部分太空旷」+「用通道把每一层的房间的路连起来」。
	/// 所以里面分成 **12 间大小不一的房间**（一层 6 间串在主通道上、二层两翼各 3 间），
	/// 每间都有原版木门，通路是：
	/// <code>
	///   门厅 → 堡垒竖井（x=4020~4040）→ 地宫主通道（就是横贯全图的通道在椭球里的那一段）
	///        → 一层 6 间（一间一间串起来，隔墙 5 格 + 一扇门）
	///        → 西升降井（x=2952~2955）→ 二层阁楼 → 西翼 3 间（门）
	///        → 东升降井（x=5200~5203）→ 东翼 3 间（门）
	/// </code>
	///
	/// <para/>为什么不直接写 <c>Main.tile[x, y]</c>：见 <see cref="WorldPaint"/> 的注释
	/// （索引器只读 / 结构体副本两种写法都编译不过或者静默无效），这里一律走 <see cref="WorldPaint"/>。
	///
	/// <para/>⚠️ 生成步骤**只在真正进入子世界时**跑一次，没法在编辑器里试。所以：
	/// <list type="bullet">
	/// <item>所有循环都先过 <see cref="WorldPaint.InWorld"/> 或 <see cref="CanBuild"/>，越界一律跳过；</item>
	/// <item>堡垒投影（<see cref="InFortressBox"/>）是**禁区**；通道那一条横带里只有
	/// "椭球两端外侧"的两截臂是禁区（见 <see cref="InTunnelLane"/>）；</item>
	/// <item>多格家具（门 / 书架 / 吊灯）放不进去时原版只是静默返回 false，
	/// 所以 <see cref="PlaceDoor"/> / <see cref="PlaceFurniture"/> 会**按实际落位核对**，
	/// 失败就在日志里留一条，绝不留下"看着生成了其实门没放上"的坑；</item>
	/// <item>几何不变量（房间在椭球内、不压禁区、平台与通道走道面齐平……）由
	/// <c>tools/check_fireplace_layout.py</c> 静态核对，连通性由
	/// <c>tools/check_fireplace_vault_connectivity.py</c> 洪水填充核对。</item>
	/// </list>
	/// </summary>
	public static class FireplaceVault
	{
		private static ushort Alloy => (ushort)ModContent.TileType<YugangAlloy>();

		private static ushort Trim => (ushort)ModContent.TileType<YugangTrim>();

		// ====================================================================================
		//  几何判定
		// ====================================================================================

		private static bool InEllipse(int x, int y, float radiusX, float radiusY)
		{
			float dx = (x - FireplaceLayout.VaultCenterX) / radiusX;
			float dy = (y - FireplaceLayout.VaultCenterY) / radiusY;

			return (dx * dx) + (dy * dy) <= 1f;
		}

		/// <summary>椭球外表面以内（含壳）。</summary>
		public static bool InOuterVault(int x, int y)
		{
			return WorldPaint.InWorld(x, y)
				&& InEllipse(x, y, FireplaceLayout.VaultRadiusX, FireplaceLayout.VaultRadiusY);
		}

		/// <summary>椭球内表面以内（不含壳）—— 空腔本体。</summary>
		public static bool InInnerVault(int x, int y)
		{
			return WorldPaint.InWorld(x, y)
				&& InEllipse(x, y,
					FireplaceLayout.VaultRadiusX - FireplaceLayout.VaultShell,
					FireplaceLayout.VaultRadiusY - FireplaceLayout.VaultShell);
		}

		/// <summary>
		/// 堡垒投影（含 1 格外扩）：地宫在这一块里**一格都不写**。
		/// 椭球上缘（y=1018）比堡垒底（1120）还高，不设这块禁区的话壳体会直接砌进门厅里。
		/// </summary>
		public static bool InFortressBox(int x, int y)
		{
			return x >= FireplaceLayout.FortLeft - 1
				&& x <= FireplaceLayout.FortRight + 1
				&& y <= FireplaceLayout.FortBottom + 1;
		}

		/// <summary>
		/// 地下通道的走廊带：**椭球两端外侧**的通道臂（含内衬与端头）。
		///
		/// <para/>⚠️ 新尺寸下通道是横贯整张图的一条直道，"椭球内部那一段"就是地宫的
		/// **主通道**：房间、隔墙、平台都排在那里，所以那一段不能算禁区
		/// （否则 <see cref="CanBuild"/> 会把整个一层都拒掉，地宫一层会变成一片虚空）。
		/// 判定因此收成"这条横带里、且在椭球左右两端之外"：
		/// 椭球外面的两截臂必须原样保住（壳、补板都不许堵），椭球里面归地宫自己排版。
		/// </summary>
		public static bool InTunnelLane(int x, int y)
		{
			if (y < FireplaceLayout.TunnelTop - FireplaceLayout.TunnelShell
				|| y > FireplaceLayout.TunnelBottom + FireplaceLayout.TunnelShell) {
				return false;
			}

			return x < FireplaceLayout.VaultLeft + FireplaceLayout.VaultShell
				|| x > FireplaceLayout.VaultRight - FireplaceLayout.VaultShell;
		}

		/// <summary>
		/// **堡垒竖井**那一条（含两侧压条）——地宫的补板要绕开它。
		///
		/// <para/>⚠️ 这是一个真 bug 的修法（玩家反馈"进地宫的路被合金堵死"）：
		/// 旧顺序是 <see cref="OpenFortressShaft"/>（开挖）→ <see cref="BuildSlab"/>。
		/// 而 `InFortressBox` 的判定是 `y &lt;= FortBottom + 1`，竖井那几行既不在堡垒盒里、
		/// 也不在通道带里，于是 <see cref="BuildSlab"/> 的"东侧补板"正好把竖井填死 ——
		/// 门厅到地下通道/地宫**彻底不通**。
		///
		/// <para/>⚠️ 新尺寸下这里**必须一路盖到楼板底面**（<c>VaultSlabBottom</c>）：
		/// 楼板有 29 行厚（2111~2139），竖井的开挖只到 <c>TunnelTop + 1 = 2131</c>，
		/// 只保护到 <c>TunnelTop + 1</c> 的话 2132~2139 会被楼板填回去、照样堵死。
		/// </summary>
		private static bool InFortressShaft(int x, int y)
		{
			return x >= FireplaceLayout.FortShaftLeft - 1
				&& x <= FireplaceLayout.FortShaftRight + 1
				&& y >= FireplaceLayout.HallBottom
				&& y <= FireplaceLayout.VaultSlabBottom;
		}

		/// <summary>地宫结构可以写的格子：在椭球内、且不碰堡垒与通道两块禁区。</summary>
		private static bool CanBuild(int x, int y)
		{
			return InInnerVault(x, y) && !InFortressBox(x, y) && !InTunnelLane(x, y);
		}

		// ====================================================================================
		//  主流程
		// ====================================================================================

		public static void Build(GenerationProgress progress, GameConfiguration configuration)
		{
			// 冒烟测试会传 null 进来（不构造 GameConfiguration，免得拉进 Newtonsoft 触发警告）
			progress ??= new GenerationProgress();
			FireplaceGenLog.Start("5/7 椭球地宫");
			progress.Message = "正在浇铸堡垒下方的椭球地宫……";

			OpenFortressShaft();
			progress.Set(0.10);

			BuildShell();
			progress.Set(0.30);

			BuildCavity();
			progress.Set(0.45);

			BuildSlab();
			BuildPlatform();
			MarkShaftLips();
			progress.Set(0.60);

			BuildStoryWalls();
			progress.Set(0.68);

			BuildWings();
			progress.Set(0.78);

			BuildLadders();
			progress.Set(0.86);

			Decorate();
			progress.Set(0.92);

			// ⚠️ 必须放在最后：`BuildCavity` 的"重开通道嘴"是把通道内空整段再掏一遍
			// （椭球壳会正好压在通道上），它顺手也会把**通道自己的立柱**（瑜钢压条，
			// 一层 1818 格）一起挖掉 —— 几何复刻数出来的。立柱归通道那一步管，
			// 所以掏完嘴之后按同一套写法补回来（幂等，重复进生成也不会叠）。
			FireplaceBuildings.BuildTunnelPillars();

			// 堡垒竖井的照明同理：`OpenFortressShaft` 会把整条井再掏一遍，
			// 井壁那几格微光方块也一起没了 —— 必须在它之后补。
			FireplaceBuildings.LightFortressShaft();
			progress.Set(1.0);

			FireplaceGenLog.Note(string.Format("地宫：房间 {0} 间，椭球 {1}x{2} @ ({3}, {4})，壳厚 {5}",
				FireplaceLayout.VaultRooms.Length,
				FireplaceLayout.VaultRadiusX * 2, FireplaceLayout.VaultRadiusY * 2,
				FireplaceLayout.VaultCenterX, FireplaceLayout.VaultCenterY,
				FireplaceLayout.VaultShell));
			FireplaceGenLog.Done("5/7 椭球地宫");
		}

		/// <summary>
		/// 打通堡垒竖井：门厅地板（<see cref="FireplaceLayout.HallBottom"/>）那一行原本是合金，
		/// 竖井只挖到 <c>TunnelTop - 2</c>，通道顶壳又被通道那一步重新砌上，
		/// 于是"门厅 → 竖井 → 通道"中间隔着两层，谁也下不去。
		/// 这里一次挖到通道内空（<c>TunnelTop + 1</c>），地宫才有唯一的入口。
		/// </summary>
		private static void OpenFortressShaft()
		{
			WorldPaint.Carve(FireplaceLayout.FortShaftLeft, FireplaceLayout.HallBottom,
				FireplaceLayout.FortShaftRight, FireplaceLayout.TunnelTop + 1);
		}

		/// <summary>
		/// 井口的青银缘口：井道两侧各一条压条，下来的人一眼能看出这是"入口"。
		///
		/// <para/>⚠️ 必须排在 <see cref="BuildSlab"/> **之后**：缘口就画在楼板那 29 行里，
		/// 先画的话会被楼板整段盖掉（旧顺序就是这样，玩家在井口看不到缘口）。
		/// </summary>
		private static void MarkShaftLips()
		{
			WorldPaint.VLine(FireplaceLayout.FortShaftLeft - 2, FireplaceLayout.VaultSlabTop,
				FireplaceLayout.TunnelTop, Trim);
			WorldPaint.VLine(FireplaceLayout.FortShaftRight + 2, FireplaceLayout.VaultSlabTop,
				FireplaceLayout.TunnelTop, Trim);
		}

		/// <summary>椭球外壳：5 格厚合金，内表面每 14 行一条压条（青银间色）。</summary>
		private static void BuildShell()
		{
			int step = FireplaceLayout.VaultTrimStep;

			for (int y = FireplaceLayout.VaultTop; y <= FireplaceLayout.VaultBottom; y++) {
				bool band = (y - FireplaceLayout.VaultTop) % step == 0;

				for (int x = FireplaceLayout.VaultLeft; x <= FireplaceLayout.VaultRight; x++) {
					if (!InOuterVault(x, y) || InInnerVault(x, y) || InFortressBox(x, y)) {
						continue;
					}

					WorldPaint.Retile(x, y, band ? Trim : Alloy);
				}
			}
		}

		/// <summary>
		/// 掏出空腔（平台底面以上），随后把被壳体压住的地下通道内空**重开一遍**：
		/// 通道横贯整张图，椭球东西两端的壳会正好砌在它身上，不重开就走不进来。
		/// </summary>
		private static void BuildCavity()
		{
			int bottom = FireplaceLayout.VaultFloorY + FireplaceLayout.VaultPlatformThickness - 1;

			for (int y = FireplaceLayout.VaultTop; y <= bottom; y++) {
				for (int x = FireplaceLayout.VaultLeft; x <= FireplaceLayout.VaultRight; x++) {
					if (!CanBuild(x, y)) {
						continue;
					}

					WorldPaint.ClearTile(x, y);
				}
			}

			// 通道嘴：只重开内空（不动通道自己的壳与压条，通道仍是"笔直一条"）。
			// 挖到 TunnelBottom-2 为止：再往下那一行是通道的走道面压条，留着不挖，
			// 免得通道尽头出现一格台阶。范围覆盖整个椭球（东西两端各一个"嘴"）。
			WorldPaint.Carve(FireplaceLayout.VaultLeft, FireplaceLayout.TunnelTop + 1,
				FireplaceLayout.VaultRight, FireplaceLayout.TunnelBottom - 2);
		}

		/// <summary>
		/// 一层天花板 / 二层楼板：整段填合金，房间的墙与门就从这块楼板里"抠"出来。
		///
		/// <para/>新尺寸下楼板**铺满整个椭球内空**（不再分"中间楼板 + 东侧补板"两段，
		/// 左右端也不留观景口）：一层 6 间房的天花板因此是齐的。
		///
		/// <para/>⚠️ 两条修补（都是几何复刻 + 洪水填充抓出来的）：
		/// <list type="number">
		/// <item>必须绕开**堡垒竖井**（见 <see cref="InFortressShaft"/>）：竖井的
		/// 2132~2139 落在堡垒盒与通道带之间的缝里，楼板有 29 行厚，不绕开就会被填死；</item>
		/// <item>顺手把堡垒底壳（2100）到楼板顶（2111）之间那一段**灌实**：
		/// 堡垒那一步的 `Carve(left-1, top-1, right+1, bottom+2)` 在壳体外面留了施工余量，
		/// 不补的话堡垒底下是一条 10 格高的空腔，看着像悬空的。只补现在是空气的格子。</item>
		/// </list>
		/// </summary>
		private static void BuildSlab()
		{
			for (int y = FireplaceLayout.VaultSlabTop; y <= FireplaceLayout.VaultSlabBottom; y++) {
				for (int x = FireplaceLayout.VaultSlabLeft; x <= FireplaceLayout.VaultSlabRight; x++) {
					if (!CanBuild(x, y) || InFortressShaft(x, y)) {
						continue;
					}

					WorldPaint.Retile(x, y, Alloy);
				}
			}

			// 堡垒底壳与楼板之间那一段空腔：只补现在还是空气的格子（不动竖井）
			for (int y = FireplaceLayout.FortBottom + 1; y < FireplaceLayout.VaultSlabTop; y++) {
				for (int x = FireplaceLayout.FortLeft; x <= FireplaceLayout.FortRight; x++) {
					if (InFortressShaft(x, y) || WorldPaint.HasTile(x, y)) {
						continue;
					}

					WorldPaint.Retile(x, y, Alloy);
				}
			}
		}

		/// <summary>主平台：地宫一层的整块地面，顶面与地下通道的走道面齐平（检查器核对）。</summary>
		private static void BuildPlatform()
		{
			int bottom = FireplaceLayout.VaultFloorY + FireplaceLayout.VaultPlatformThickness - 1;

			for (int y = FireplaceLayout.VaultFloorY; y <= bottom; y++) {
				for (int x = FireplaceLayout.VaultLeft; x <= FireplaceLayout.VaultRight; x++) {
					if (!CanBuild(x, y)) {
						continue;
					}

					WorldPaint.Retile(x, y, y == FireplaceLayout.VaultFloorY ? Trim : Alloy);
				}
			}

			// 通道嘴那一段的地面在重开通道时被挖掉了，这里按同一条走道面补回来（一路平）
			WorldPaint.HLine(FireplaceLayout.VaultLeft, FireplaceLayout.VaultRight,
				FireplaceLayout.VaultFloorY, Trim);
		}

		// ====================================================================================
		//  一层：主通道上串起来的 6 间房（分隔墙 + 门）
		// ====================================================================================

		/// <summary>取某一层（按 <c>Top</c> 区分）的房间，按 x 从左到右排序。</summary>
		private static List<FireplaceLayout.VaultRoom> RoomsWithTop(int top)
		{
			List<FireplaceLayout.VaultRoom> list = new List<FireplaceLayout.VaultRoom>();

			foreach (FireplaceLayout.VaultRoom room in FireplaceLayout.VaultRooms) {
				if (room.Top == top) {
					list.Add(room);
				}
			}

			list.Sort((a, b) => a.Left.CompareTo(b.Left));
			return list;
		}

		/// <summary>
		/// 一层：**一间挨着一间串在主通道上**，相邻两间之间就是一道 5 格厚隔墙 + 一扇门。
		/// 最西 / 最东那两间的外侧没有墙 —— 那里直接通向通往世界东西边缘的通道臂
		/// （"一进门就在堡垒里，往两边走都能一直走到世界尽头"）。
		/// </summary>
		private static void BuildStoryWalls()
		{
			List<FireplaceLayout.VaultRoom> rooms = RoomsWithTop(FireplaceLayout.VaultStoryTop);

			if (rooms.Count < 2) {
				return;
			}

			int top = FireplaceLayout.VaultStoryTop;
			int bottom = FireplaceLayout.VaultFloorY - 1;

			for (int i = 0; i + 1 < rooms.Count; i++) {
				int wallLeft = rooms[i].Right + 1;
				int wallRight = rooms[i + 1].Left - 1;

				FillWall(wallLeft, wallRight, top, bottom);
				PlaceDoor((wallLeft + wallRight) / 2, FireplaceLayout.VaultFloorY, wallLeft, wallRight);
			}
		}

		/// <summary>填一道隔墙：两侧外皮用压条（青银相间），中间是本体合金。</summary>
		private static void FillWall(int left, int right, int top, int bottom)
		{
			if (right < left) {
				return;
			}

			for (int x = left; x <= right; x++) {
				ushort type = (x == left || x == right) ? Trim : Alloy;

				for (int y = top; y <= bottom; y++) {
					if (!InInnerVault(x, y)) {
						continue;
					}

					WorldPaint.Retile(x, y, type);
				}
			}
		}

		// ====================================================================================
		//  二层：两翼的房间
		// ====================================================================================

		/// <summary>
		/// 二层两翼：堡垒投影（x=3700~4700）那 1000 格地宫**一格都不写**，
		/// 所以二层只能做成左右两翼，每翼 3 间（自内向外串起来，靠外墙那侧再开一扇通往穹顶阁楼）。
		/// </summary>
		private static void BuildWings()
		{
			List<FireplaceLayout.VaultRoom> upper = RoomsWithTop(FireplaceLayout.VaultUpperTop);

			if (upper.Count < 2) {
				return;
			}

			List<FireplaceLayout.VaultRoom> west = new List<FireplaceLayout.VaultRoom>();
			List<FireplaceLayout.VaultRoom> east = new List<FireplaceLayout.VaultRoom>();

			foreach (FireplaceLayout.VaultRoom room in upper) {
				if (room.Right < FireplaceLayout.FortLeft) {
					west.Add(room);
				}
				else if (room.Left > FireplaceLayout.FortRight) {
					east.Add(room);
				}
			}

			// 西翼靠阁楼那面（西）开门；东翼靠阁楼那面（东）开门
			BuildWing(FireplaceLayout.VaultWestWingLeft, FireplaceLayout.VaultWestWingRight, west, true);
			BuildWing(FireplaceLayout.VaultEastWingLeft, FireplaceLayout.VaultEastWingRight, east, false);
		}

		private static void BuildWing(int outerLeft, int outerRight, List<FireplaceLayout.VaultRoom> rooms,
			bool atticDoorOnWest)
		{
			if (rooms.Count == 0) {
				return;
			}

			int top = FireplaceLayout.VaultCeilingTop;
			int bottom = FireplaceLayout.VaultUpperBottom;

			// 顶板
			for (int y = top; y <= FireplaceLayout.VaultCeilingBottom; y++) {
				for (int x = outerLeft; x <= outerRight; x++) {
					if (!InInnerVault(x, y)) {
						continue;
					}

					WorldPaint.Retile(x, y, Alloy);
				}
			}

			// 房间之间的隔墙 + 门
			for (int i = 0; i + 1 < rooms.Count; i++) {
				int wallLeft = rooms[i].Right + 1;
				int wallRight = rooms[i + 1].Left - 1;

				FillWall(wallLeft, wallRight, top, bottom);
				PlaceDoor((wallLeft + wallRight) / 2, FireplaceLayout.VaultSlabTop, wallLeft, wallRight);
			}

			// 两端外墙
			int westWallLeft = outerLeft;
			int westWallRight = rooms[0].Left - 1;
			int eastWallLeft = rooms[rooms.Count - 1].Right + 1;
			int eastWallRight = outerRight;

			FillWall(westWallLeft, westWallRight, top, bottom);
			FillWall(eastWallLeft, eastWallRight, top, bottom);

			// 靠阁楼那面外墙再开一扇（阁楼是从升降井上来的，得能进房间）
			if (atticDoorOnWest) {
				PlaceDoor(westWallLeft + 1, FireplaceLayout.VaultSlabTop, westWallLeft, westWallRight);
			}
			else {
				PlaceDoor(eastWallRight - 1, FireplaceLayout.VaultSlabTop, eastWallLeft, eastWallRight);
			}
		}

		// ====================================================================================
		//  竖井 / 升降井
		// ====================================================================================

		/// <summary>
		/// 两条升降井：西井从一层西头房间里打穿楼板通到二层阁楼；
		/// 东井从主通道（通道顶壳）打穿到二层右翼房间。井里每 5 格一层原版木平台当梯子
		/// （和祈塔里的爬升做法一致）。
		/// </summary>
		private static void BuildLadders()
		{
			LadderShaft(FireplaceLayout.VaultWestLadderX, FireplaceLayout.VaultWestLadderRight,
				FireplaceLayout.VaultFloorY - 1, FireplaceLayout.VaultUpperTop);
			LadderShaft(FireplaceLayout.VaultEastLadderX, FireplaceLayout.VaultEastLadderRight,
				FireplaceLayout.VaultFloorY - 1, FireplaceLayout.VaultUpperTop);
		}

		private static void LadderShaft(int left, int right, int floorY, int topY)
		{
			if (right < left || topY > floorY) {
				return;
			}

			for (int y = topY; y <= floorY; y++) {
				for (int x = left; x <= right; x++) {
					if (!WorldPaint.InWorld(x, y)) {
						continue;
					}

					WorldPaint.ClearTile(x, y);
				}
			}

			int ladderPlatforms = 0;

			for (int y = floorY - 4; y >= topY; y -= 5) {
				for (int x = left; x <= right; x++) {
					if (!WorldPaint.InWorld(x, y)) {
						continue;
					}

					WorldGen.PlaceTile(x, y, TileID.Platforms, mute: true, forced: true);
				}

				// 井道照明：每 FireplaceLights.ShaftLightEvery = 2 层平台一盏
				// （平台层距 5 → 纵向 10 格一个光源 ≤ 12；升降井是地宫上下唯一的通路，
				//  上一版井里一盏灯都没有）
				if (ladderPlatforms % FireplaceLights.ShaftLightEvery == 0
					&& !WorldPaint.IsTile(left, y - 1, TileID.Torches)) {
					if (!FireplaceLights.FloorTorch(left, y) && WorldPaint.IsTile(left + 1, y, TileID.Platforms)) {
						WorldPaint.Retile(left + 1, y, TileID.EmeraldGemspark);   // 退路：把平台那格改成微光方块
					}
				}

				ladderPlatforms++;
			}
		}

		// ====================================================================================
		//  内饰：照明 / 书架 / 桌椅 / 藤蔓
		// ====================================================================================

		private static void Decorate()
		{
			FireplaceLayout.VaultRoom[] rooms = FireplaceLayout.VaultRooms;
			int torches = 0;
			int chandeliers = 0;
			int bookcases = 0;
			int vines = 0;

			foreach (FireplaceLayout.VaultRoom room in rooms) {
				bool upper = room.Top == FireplaceLayout.VaultUpperTop;
				int floorY = upper ? FireplaceLayout.VaultSlabTop : FireplaceLayout.VaultFloorY;
				int ceilingY = upper ? FireplaceLayout.VaultCeilingBottom : FireplaceLayout.VaultSlabBottom;

				// 地面火把：贴着地板，每 FireplaceLights.FloorStep = 12 格一盏
				for (int x = room.Left + 3; x <= room.Right - 3; x += FireplaceLights.FloorStep) {
					if (!RoomAir(room, x, floorY - 1)) {
						continue;
					}

					WorldGen.PlaceTile(x, floorY - 1, TileID.Torches, mute: true, forced: true);

					if (WorldPaint.IsTile(x, floorY - 1, TileID.Torches)) {
						torches++;
					}
				}

				// 地面指示灯：翡翠微光**连着铺**（每 2 格一格，玩家要的"连续微光走线"）
				for (int x = room.Left + 2; x <= room.Right - 2; x += FireplaceLights.LineStep) {
					if (RoomAir(room, x, floorY)) {
						continue;
					}

					WorldPaint.Retile(x, floorY, x % 6 == 0
						? TileID.DiamondGemspark
						: TileID.EmeraldGemspark);
				}

				// 天花板走线：钻石微光（比翡翠亮一档）沿顶板铺一条，房间轮廓一眼可见。
				// ⚠️ 两条升降井的竖井穿过这块楼板/顶板（x=2952~2955 与 5200~5203），
				// 在那儿铺方块会把井道堵死，必须让开。
				for (int x = room.Left + 1; x <= room.Right - 1; x += 2) {
					if (InLadderColumn(x)) {
						continue;
					}

					WorldPaint.Retile(x, ceilingY, x % 4 == 0
						? TileID.EmeraldGemspark
						: TileID.DiamondGemspark);
				}

				// 吊灯：从天花板上垂下来，每 FireplaceLights.CeilingStep = **12** 格一盏
				// （本批从 20 再加密：中大厅 1025 格宽，20 格一盏仍然有大段暗区）
				for (int x = room.Left + 8; x <= room.Right - 8; x += FireplaceLights.CeilingStep) {
					if (PlaceHanging(x, ceilingY, TileID.Chandeliers)) {
						chandeliers++;
					}
				}

				// 长明烛台：每 FireplaceLights.FloorStep = 12 格一盏（矮，不挡视线，但把地面提亮）
				for (int x = room.Left + 9; x <= room.Right - 9; x += FireplaceLights.FloorStep) {
					if (RoomAir(room, x, floorY - 1)) {
						WorldGen.PlaceTile(x, floorY - 1, TileID.Candles, mute: true, forced: true);
					}
				}

				// 书架（3×4）：贴墙摆一两组
				if (room.Width >= 60) {
					if (PlaceFurniture(room, room.Left + 12, floorY, TileID.Bookcases, 3, 4)) {
						bookcases++;
					}

					if (PlaceFurniture(room, room.Right - 12, floorY, TileID.Bookcases, 3, 4)) {
						bookcases++;
					}
				}

				// 桌椅：旧时代的驻地感
				PlaceFurniture(room, room.Left + room.Width / 2, floorY, TileID.Tables, 3, 2);

				// 大房间（"中央大厅"有 1025 格宽）多摆几组桌椅：只放一件的话，
				// 玩家一眼看过去还是"一个巨大的空房间"（就是上一批被吐槽的那个观感）。
				int groups = room.Width / 260;

				for (int g = 0; g < groups; g++) {
					int cx = room.Left + (room.Width * (g + 1)) / (groups + 1);

					if (Math.Abs(cx - (room.Left + room.Width / 2)) < 40) {
						continue;       // 别和正中那一组叠在一起
					}

					PlaceFurniture(room, cx, floorY, TileID.Tables, 3, 2);

					if (room.Width >= 260) {
						PlaceFurniture(room, cx + 16, floorY, TileID.Bookcases, 3, 4);
					}
				}

				// 藤蔓：从天花板下沿垂下来（原版藤蔓要附在方块下方，逐格放）
				for (int x = room.Left + 6; x <= room.Right - 6; x += 20) {
					vines += PlaceVines(x, ceilingY + 1, 4 + (x % 5));
				}
			}

			// 主通道（椭球里那一段，也就是通道穿地宫而过的那一截）也补一轮照明：
			// 火把每 12 格、地面连铺微光（这段有 3000 格长，房间之外也得看得见路）
			// ⚠️ 隔墙那一列本来就是实心的，`PlaceTile(forced:true)` 会把墙"顶掉"一格，
			// 所以先判空格子（隔墙与门洞都在这儿让开）。
			for (int x = FireplaceLayout.VaultLeft + 20; x <= FireplaceLayout.VaultRight - 10; x += 12) {
				if (WorldPaint.HasTile(x, FireplaceLayout.VaultFloorY - 1)) {
					continue;
				}

				WorldGen.PlaceTile(x, FireplaceLayout.VaultFloorY - 1, TileID.Torches, mute: true, forced: true);

				if (WorldPaint.IsTile(x, FireplaceLayout.VaultFloorY - 1, TileID.Torches)) {
					torches++;
				}
			}

			for (int x = FireplaceLayout.VaultLeft + 6; x <= FireplaceLayout.VaultRight - 6; x += 2) {
				WorldPaint.Retile(x, FireplaceLayout.VaultFloorY, x % 6 == 0
					? TileID.DiamondGemspark
					: TileID.EmeraldGemspark);
			}

			// 阁楼（二层顶上那圈穹顶空间）里沿壳挂几盏 —— 壳的内表面就是穹顶，
			// 找到每列最下面那一格壳体、从它下面开始挂。
			for (int x = FireplaceLayout.VaultCenterX - 1200; x <= FireplaceLayout.VaultCenterX + 1200; x += 120) {
				int ceiling = AtticCeiling(x);

				if (ceiling > 0) {
					vines += PlaceVines(x, ceiling, 5);
				}
			}

			FireplaceGenLog.Note(string.Format("地宫照明：火把 {0}、吊灯 {1}、书架 {2}、藤蔓 {3} 格",
				torches, chandeliers, bookcases, vines));
		}

		/// <summary>这一列是不是某条升降井的井道（±1 格余量，避免把井口铺死）。</summary>
		private static bool InLadderColumn(int x)
		{
			return (x >= FireplaceLayout.VaultWestLadderX - 1 && x <= FireplaceLayout.VaultWestLadderRight + 1)
				|| (x >= FireplaceLayout.VaultEastLadderX - 1 && x <= FireplaceLayout.VaultEastLadderRight + 1);
		}

		/// <summary>这一格在这间房里、而且现在是空的（家具/火把只能往空处放）。</summary>
		private static bool RoomAir(FireplaceLayout.VaultRoom room, int x, int y)
		{
			return x >= room.Left && x <= room.Right && y >= room.Top && y <= room.Bottom
				&& WorldPaint.InWorld(x, y) && !WorldPaint.HasTile(x, y);
		}

		/// <summary>穹顶在这一列的内表面行号（第一格内空）；这一列被堡垒投影挡着就返回 -1。</summary>
		private static int AtticCeiling(int x)
		{
			if (!WorldPaint.InWorld(x, 0)) {
				return -1;
			}

			for (int y = FireplaceLayout.VaultTop; y <= FireplaceLayout.VaultUpperBottom; y++) {
				if (InFortressBox(x, y)) {
					return -1;
				}

				if (InInnerVault(x, y)) {
					return y;
				}
			}

			return -1;
		}

		/// <summary>
		/// 放一扇原版木门。
		///
		/// <para/>⚠️ 这里的关键不是"把门放上去"，而是**门洞要打穿整堵墙**：
		/// 隔墙有 5~6 格厚，如果只在墙中间放一格门、两侧墙体不动，玩家根本走不过去
		/// （门格被实心墙夹在中间）。所以先按 <paramref name="carveLeft"/>~<paramref name="carveRight"/>
		/// 把整段墙在这 3 行上掏通，再把门放在中间那一列 —— 这一列就成了墙里唯一的通路。
		///
		/// <para/>门本身的"锚点约定"在不同版本里是"底部那一格"或"顶上一格"两种，
		/// 而且放不下时 <c>WorldGen.PlaceObject</c> 只是静默返回 false，
		/// 所以两种锚点都试，并且用"门格有没有真的出现在该在的地方"来判定。
		/// </summary>
		/// <param name="x">门所在列（必须在 <paramref name="carveLeft"/>~<paramref name="carveRight"/> 中间）。</param>
		/// <param name="floorY">门下方那一格实心地板的行号；门应当占 floorY-3 ~ floorY-1。</param>
		/// <param name="carveLeft">这堵墙的左边（含）。</param>
		/// <param name="carveRight">这堵墙的右边（含）。</param>
		private static bool PlaceDoor(int x, int floorY, int carveLeft, int carveRight)
		{
			int bottom = floorY - 1;

			for (int attempt = 0; attempt < 2; attempt++) {
				int anchor = attempt == 0 ? bottom : bottom - 2;

				// 门洞：整堵墙在这 3 行上掏通（门就卡在中间那一列）
				WorldPaint.Carve(carveLeft, bottom - 2, carveRight, bottom);
				WorldGen.PlaceObject(x, anchor, TileID.ClosedDoor, true, 0, 0, -1, -1);

				if (DoorColumn(x, bottom)) {
					return true;
				}

				if (DoorColumn(x, bottom - 2)) {
					return true;
				}
			}

			FireplaceGenLog.Note(string.Format("门没放上：(x={0}, 地板 y={1})", x, floorY));
			return false;
		}

		private static bool DoorColumn(int x, int bottomY)
		{
			for (int i = 0; i < 3; i++) {
				if (!WorldPaint.IsTile(x, bottomY - i, TileID.ClosedDoor)) {
					return false;
				}
			}

			return true;
		}

		/// <summary>
		/// 放一件原版多格家具（桌子 3×2 / 书架 3×4）。锚点约定同样两种都试，
		/// 再用"目标区域里到底有没有这个方块"核对；清空间只清房间内空，不动墙与门。
		/// </summary>
		private static bool PlaceFurniture(FireplaceLayout.VaultRoom room, int centerX, int floorY,
			ushort type, int width, int height)
		{
			int half = width / 2;

			for (int attempt = 0; attempt < 3; attempt++) {
				int anchor = floorY - (attempt * Math.Max(height - 1, 1));

				// 清空间只清"这间房的内空"（不动墙、门、别的房间）
				for (int x = centerX - half; x <= centerX + half; x++) {
					for (int y = anchor - height - 1; y <= anchor + 1; y++) {
						if (x < room.Left || x > room.Right || y < room.Top || y > room.Bottom) {
							continue;
						}

						if (!InInnerVault(x, y) || InTunnelLane(x, y)) {
							continue;
						}

						WorldPaint.ClearTile(x, y);
					}
				}

				WorldGen.PlaceObject(centerX, anchor, type, true, 0, 0, -1, -1);

				if (AnyTileIn(centerX - width, anchor - height - 1, centerX + width, anchor + 2, type)) {
					return true;
				}
			}

			return false;
		}

		/// <summary>放吊灯这类"挂在顶板下面"的 3×3：锚点在顶行，两种情况都试。</summary>
		private static bool PlaceHanging(int centerX, int ceilingBottomY, ushort type)
		{
			for (int attempt = 0; attempt < 2; attempt++) {
				int anchor = ceilingBottomY + 1 + attempt;

				WorldGen.PlaceObject(centerX, anchor, type, true, 0, 0, -1, -1);

				if (AnyTileIn(centerX - 1, anchor - 1, centerX + 1, anchor + 3, type)) {
					return true;
				}
			}

			return false;
		}

		private static bool AnyTileIn(int left, int top, int right, int bottom, ushort type)
		{
			for (int x = left; x <= right; x++) {
				for (int y = top; y <= bottom; y++) {
					if (WorldPaint.IsTile(x, y, type)) {
						return true;
					}
				}
			}

			return false;
		}

		/// <summary>从某一行往下挂一条原版藤蔓（藤蔓要附着在方块下方，逐格放、放不上就停）。</summary>
		private static int PlaceVines(int x, int topY, int length)
		{
			int placed = 0;

			for (int i = 0; i < length; i++) {
				int y = topY + i;

				if (!WorldPaint.InWorld(x, y) || WorldPaint.HasTile(x, y)) {
					break;
				}

				WorldGen.PlaceTile(x, y, TileID.Vines, mute: true, forced: true);

				if (!WorldPaint.IsTile(x, y, TileID.Vines)) {
					break;
				}

				placed++;
			}

			return placed;
		}
	}
}
