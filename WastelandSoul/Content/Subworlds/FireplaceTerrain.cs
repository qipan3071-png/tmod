using System;
using Terraria;
using Terraria.ID;
using Terraria.IO;
using Terraria.WorldBuilding;

namespace WastelandSoul.Content.Subworlds
{
	/// <summary>
	/// 壁炉**地表**：灰烬原野。
	///
	/// <para/>世界观：为了保住最后的火种，牠们把堡垒外的土地整个烧成了灰。
	/// 于是外面是一片起伏的灰烬荒原，空气被堡垒排出的有害气体污染（减益见
	/// <see cref="Content.Buffs.GasPoison"/>），低洼处积着一点岩浆与污染水。
	///
	/// <para/>生成手法**照原版地表那套**：
	/// <list type="number">
	/// <item>用**分层噪声**（<see cref="WorldPaint.Fractal"/>）算地表高度 ——
	/// 原版地表就是"低频大起伏 + 高频小起伏"叠出来的，这样才有自然的丘陵感，不是正弦波；</item>
	/// <item>往下按深度分层：最表层灰烬草 → 灰烬 → 灰烬夹土 → 岩石层（再混一点黑曜石脉）；</item>
	/// <item>零散特征：灰烬丘（椭圆堆）、黑曜石巨岩、低洼处的岩浆池与污染水塘、
	/// 隧道式矿洞与废弃矿道（没有任何矿石）。</item>
	/// </list>
	///
	/// <para/>=== 这一批：世界从 900×1300 放大到 8400×2400（地表以下约 670 万格） ===
	/// 所有数量按**面积比例**放大（矿洞 150→1400、矿道 6→60 条尝试、水池 21→160、
	/// 灰烬丘 38→320、碎石 70→600、黑曜石巨岩 14→130），同时每一格的**单位成本**必须压下来：
	/// <list type="bullet">
	/// <item>噪声调用从"每格 3 次分形（7 个八度）"压到"每格 3 次单/双八度取值"；</item>
	/// <item><see cref="ReservedHollow"/>：反正会被结构步骤掏掉/重建的地方（通道整条、
	/// 堡垒内腔、祈塔内腔、地宫空腔）**这一步就不铺**，省掉"先铺石头再挖掉"的两遍；</item>
	/// <item><see cref="CaveAir"/>：岩石层里顺手留出天然空洞（约 18%），后面的
	/// <see cref="BuildCaves"/> 也少挖一次 —— 顺便让远离中心的区域真的有东西可探。</item>
	/// </list>
	/// </summary>
	public static class FireplaceTerrain
	{
		/// <summary>噪声种子（写死 = 每次生成的地形完全一致，方便对照与截图）。</summary>
		private const int Seed = 20261008;

		/// <summary>算好的地表高度表（其它生成步骤也会用）。</summary>
		public static readonly int[] Surface = new int[FireplaceLayout.Width];

		public static void Build(GenerationProgress progress, GameConfiguration configuration)
		{
			// 冒烟测试会传 null 进来（不构造 GameConfiguration，免得拉进 Newtonsoft 触发警告）
			progress ??= new GenerationProgress();
			FireplaceGenLog.Start("1/7 灰烬原野");
			progress.Message = "正在吹散壁炉外的灰烬……";

			BuildHeightMap();
			progress.Set(0.12);

			BuildCrust();
			progress.Set(0.45);

			BuildDunes();
			progress.Set(0.55);

			BuildSurfaceGrass();
			progress.Set(0.62);

			BuildPebbles();
			progress.Set(0.68);

			BuildAshTrees();
			progress.Set(0.76);

			BuildPools();
			progress.Set(0.86);

			BuildRocks();
			BuildCaves(progress);
			BuildMineShafts(progress);

			// 矿洞 / 矿道的布光网格（见方法注释：这一遍保证"洞里的可通行点到最近光源 ≤ 12 格"）
			LightCaverns(progress);

			// 最后一道：把结构与矿道周围/上方的沙透镜体换成石头（见方法注释）
			HardenSandNearStructures();
			progress.Set(1.0);
		}

		/// <summary>
		/// 矿洞 / 矿道的**布光网格**（玩家反馈"亮度还是有点低"，而且矿洞这一块以前一盏灯都没有）。
		///
		/// <para/>做法：把地表线以下的整块地下按 <see cref="FireplaceLights.CaveCell"/> ×
		/// <see cref="FireplaceLights.CaveCell"/>（= 8 × 8）划格；每一格里**从格内开始找第一个
		/// "能站人的空气"**（自己是空气、脚下是实心、头顶是空气），找到就在那一格放一盏火把。
		///
		/// <para/>为什么这样就够了：灯和它服务的可通行点**在同一个 8 × 8 格子里**，
		/// 所以格内任意一点到它的切比雪夫距离 ≤ 7 ≤ <see cref="FireplaceLights.MaxGap"/>（12）。
		/// 结构保护区（堡垒 / 祈塔 / 场地 / 通道 / 地宫）跳过去 —— 那些地方由各自的生成步骤布光，
		/// 而且这一步跑在结构**之前**（那时保护区的格子还是空的，不跳就会把火把放进未来的房间里）。
		/// </summary>
		private static void LightCaverns(GenerationProgress progress)
		{
			progress.Message = "正在给矿洞点上灯……";

			int cell = FireplaceLights.CaveCell;
			int top = Math.Max(FireplaceLayout.SurfaceBase - FireplaceLayout.SurfaceAmplitude, 4);
			int lit = 0;

			for (int cx = 0; cx < FireplaceLayout.Width; cx += cell) {
				for (int cy = top; cy < FireplaceLayout.Height; cy += cell) {
					if (LightCell(cx, cy, cell)) {
						lit++;
					}
				}
			}

			FireplaceGenLog.Note(string.Format("矿洞布光 {0} 盏（{1}×{1} 网格，保护区跳过）", lit, cell));
		}

		/// <summary>给一个 8×8 的格子放一盏灯（格子里没有能站人的空气就返回 false）。</summary>
		private static bool LightCell(int left, int top, int size)
		{
			int right = Math.Min(left + size, FireplaceLayout.Width) - 1;
			int bottom = Math.Min(top + size, FireplaceLayout.Height - 1);

			for (int y = top; y <= bottom; y++) {
				for (int x = left; x <= right; x++) {
					// 结构保护区（堡垒/塔/场地/通道/地宫）由各自步骤布光，这里别插手
					if (y < Surface[x] || InsideStructure(x, y, 2)) {
						continue;
					}

					if (WorldPaint.HasTile(x, y) || WorldPaint.HasTile(x, y - 1) || !WorldPaint.HasTile(x, y + 1)) {
						continue;       // 要"能站人"：自己与头顶空、脚下实心
					}

					WorldGen.PlaceTile(x, y, TileID.Torches, mute: true, forced: true);
					return WorldPaint.IsTile(x, y, TileID.Torches);
				}
			}

			return false;
		}

		/// <summary>
		/// 分层噪声算地表高度。
		/// <para/>波长跟着世界宽度一起放大（大丘陵 ~380 格、碎石 ~70 格），
		/// 否则 8400 格宽的地表会被 90 格一个包的"小土包"糊满。
		/// </summary>
		private static void BuildHeightMap()
		{
			for (int x = 0; x < FireplaceLayout.Width; x++) {
				// 低频：大丘陵
				float broad = WorldPaint.Fractal(Seed, x / 380f, 4, 0.5f);

				// 高频：碎石与灰堆的小起伏，幅度压到 1/4
				float fine = WorldPaint.Fractal(Seed + 1013, x / 70f, 3, 0.5f);

				float offset = ((broad - 0.5f) * 2f * FireplaceLayout.SurfaceAmplitude)
					+ ((fine - 0.5f) * 2f * (FireplaceLayout.SurfaceAmplitude * 0.25f));

				Surface[x] = (int)MathF.Round(FireplaceLayout.SurfaceBase + offset);
			}
		}

		/// <summary>
		/// 岩石层里允许出现**沙 / 泥沙**（受重力）的厚度：只有岩层顶部这一段。
		/// 再往下全是"顺手留的洞"，铺沙会让整张图到处漏沙（见 <see cref="BuildCrust"/>）。
		/// </summary>
		private const int LooseDepth = 140;

		/// <summary>
		/// 这一格会不会在后面的步骤里被掏空 / 由结构自己重新浇出来。
		///
		/// <para/>为什么要在第一步就判：8400×2400 下"先铺满石头、再一步步挖掉"是纯浪费 ——
		/// 通道整条（8400 × 109 格）、堡垒内腔（1000 × 420）、祈塔内腔（100 × 1100）、
		/// 地宫空腔（椭球上半，约 58 万格）加起来，地表以下有 **161 万格**是不必先铺的
		/// （按本目录的生成模型数出来的），既写了一遍 <c>PlaceTile</c>、后面又要
		/// <c>KillTile</c> 一遍。后面那几步自己会把壳 / 压条 / 平台补上，所以直接留空是安全的。
		///
		/// <para/>顺序按"命中率高、判断便宜"排：先判通道那一条横带（两个整数比较），
		/// 再判堡垒 / 祈塔两个矩形，最后才是椭球的浮点判定（只在椭球外框内才算）。
		/// </summary>
		private static bool ReservedHollow(int x, int y)
		{
			// 1) 地下通道整条（含内衬）：通道那一步会自己铺壳、铺压条、铺地面
			if (y >= FireplaceLayout.TunnelTop - FireplaceLayout.TunnelShell
				&& y <= FireplaceLayout.TunnelBottom + FireplaceLayout.TunnelShell) {
				return true;
			}

			// 2) 堡垒体内腔（外壳由堡垒那一步自己浇）
			if (x >= FireplaceLayout.FortLeft - 1 && x <= FireplaceLayout.FortRight + 1
				&& y >= FireplaceLayout.FortTop - 1 && y <= FireplaceLayout.FortBottom + 1) {
				return true;
			}

			// 3) 祈塔体内腔
			if (y >= FireplaceLayout.TowerTop - 1 && y <= FireplaceLayout.TowerBottom
				&& x >= FireplaceLayout.TowerLeft - 1 && x <= FireplaceLayout.TowerRight + 1) {
				return true;
			}

			// 4) 椭球地宫的空腔（平台底面以上那一半）
			if (y <= FireplaceLayout.VaultFloorY + FireplaceLayout.VaultPlatformThickness - 1
				&& x >= FireplaceLayout.VaultLeft && x <= FireplaceLayout.VaultRight) {
				float dx = (x - FireplaceLayout.VaultCenterX)
					/ (float)(FireplaceLayout.VaultRadiusX - FireplaceLayout.VaultShell);
				float dy = (y - FireplaceLayout.VaultCenterY)
					/ (float)(FireplaceLayout.VaultRadiusY - FireplaceLayout.VaultShell);

				if ((dx * dx) + (dy * dy) <= 1f) {
					return true;
				}
			}

			return false;
		}

		/// <summary>
		/// 这一格是不是"结构地基附近"（堡垒 / 地宫的保护区，外扩 40 格）。
		/// <para/>岩石层里的天然空洞要避开这里：地基下面掏空虽然不会塌，
		/// 但看着像悬浮，而且玩家从竖井下来会直接掉进旁边的洞里。
		/// </summary>
		private static bool NearStructures(int x, int y)
		{
			if (y >= FireplaceLayout.VaultTop - 40
				&& x >= FireplaceLayout.VaultLeft - 40 && x <= FireplaceLayout.VaultRight + 40) {
				return true;
			}

			return x >= FireplaceLayout.FortLeft - 40 && x <= FireplaceLayout.FortRight + 40
				&& y >= FireplaceLayout.FortTop - 40 && y <= FireplaceLayout.FortBottom + 40;
		}

		/// <summary>
		/// 岩石层里的**天然空洞**判定（两次独立取值叠加：低频给"洞厅"、高频给"支洞"）。
		/// 命中就这一格不铺 —— 等价于免费挖了一个洞，而且 <see cref="BuildCaves"/>
		/// 后面再挖到同一格时是空操作。阈值 0.66 大约留出 **15% 上下**的空洞率
		/// （生成模型里按 15% 估的），够让远离中心的区域到处有洞可探，又不至于把岩层掏空。
		/// </summary>
		private static bool CaveAir(int x, int y)
		{
			float cave = (WorldPaint.ValueNoise2D(Seed + 4242, x / 62f, y / 20f)
				+ WorldPaint.ValueNoise2D(Seed + 8484, x / 17f, y / 13f)) * 0.5f;

			return cave > 0.66f;
		}

		/// <summary>
		/// 按深度铺地表层与地下岩层。
		///
		/// <para/>⚠️ 这是整个生成里最贵的一步（670 万格），噪声调用与写入次数都卡得很紧：
		/// 岩石层只用 3 次噪声取值（旧写法是 3 次分形、共 7 个八度），
		/// 而且"反正要掏空"的格子直接跳过（<see cref="ReservedHollow"/>）。
		/// </summary>
		private static void BuildCrust()
		{
			int crust = FireplaceLayout.CrustDepth;
			int height = FireplaceLayout.Height;

			for (int x = 0; x < FireplaceLayout.Width; x++) {
				int top = Surface[x];

				for (int y = top; y < height; y++) {
					int depth = y - top;

					// 最上面 4 行（灰烬草 + 灰烬）永远照铺，保证地表是连续的
					if (depth > 3 && ReservedHollow(x, y)) {
						continue;
					}

					ushort type;

					if (depth == 0) {
						type = TileID.AshGrass;                 // 表层：灰烬草（原版 1.4.4 自带）
					}
					else if (depth <= 3) {
						type = TileID.Ash;
					}
					else if (depth < crust) {
						// 灰烬与土交错：用二维噪声决定，看起来像被烧透的旧土壤
						float mix = WorldPaint.Fractal2D(Seed + 77, x / 26f, y / 22f, 2);
						type = mix < 0.42f ? TileID.Dirt : TileID.Ash;
					}
					else {
						// 岩石层里顺手留洞（结构地基附近除外）
						if (!NearStructures(x, y) && CaveAir(x, y)) {
							continue;
						}

						// 岩石层：**石 / 沙 / 土 / 泥沙**四样按噪声交错（玩家要求：资源枯竭，不放任何矿石）。
						// 两次不同尺度的取值叠出"有层理、有透镜体"的观感，而不是一片纯石头。
						float vein = (WorldPaint.ValueNoise2D(Seed + 313, x / 52f, y / 34f)
							+ WorldPaint.ValueNoise2D(Seed + 733, x / 15f, y / 11f)) * 0.5f;
						float lens = WorldPaint.ValueNoise2D(Seed + 907, x / 26f, y / 90f);

						// ⚠️ 沙 / 泥沙受重力：只让它们出现在岩石层**顶部 140 行**里。
						// 再往下全是洞（CaveAir 留了约 18%），铺满沙的话玩家一路走过去
						// 会看到整张图到处在漏沙 —— 原版世界也没有"深层沙层"。
						// 深层的沙/泥沙一律退回石头（顺手也呼应"资源枯竭"的设定）。
						bool loose = depth - crust < LooseDepth;

						if (loose && vein > 0.72f) {
							type = TileID.Sand;                 // 沙透镜体
						}
						else if (loose && vein > 0.60f) {
							type = TileID.Silt;                 // 泥沙
						}
						else if (lens > 0.62f) {
							type = TileID.Dirt;                 // 土夹层
						}
						else if (vein < 0.26f) {
							type = TileID.Ash;                  // 灰烬（烧透的旧土）
						}
						else {
							type = TileID.Stone;
						}

						// 极少数位置给一点黑曜石脉，作为瑜钢合金的观感伏笔
						if (vein > 0.70f && lens > 0.90f) {
							type = TileID.Obsidian;
						}
					}

					WorldPaint.Retile(x, y, type);
				}
			}
		}

		/// <summary>灰烬丘：在地表堆一批椭圆灰堆，让轮廓不那么"平"。原版做沙丘/雪堆也是这个手法。</summary>
		private static void BuildDunes()
		{
			// 按面积比例：900 宽时 38 个 → 8400 宽时 320 个（大约每 26 格一座）
			const int count = 320;

			for (int i = 0; i < count; i++) {
				int x = 30 + (int)(i * (FireplaceLayout.Width - 60) / (float)count);
				int jitter = (int)(WorldPaint.ValueNoise(Seed + 9001, i * 3.7f) * 70f);
				x = Math.Clamp(x + jitter - 35, 12, FireplaceLayout.Width - 13);

				float radiusX = 7f + WorldPaint.ValueNoise(Seed + 500, i * 1.3f) * 17f;
				float radiusY = 3f + WorldPaint.ValueNoise(Seed + 600, i * 1.7f) * 6f;
				int y = Surface[x] + (int)(radiusY * 0.6f);

				WorldPaint.Ellipse(x, y, radiusX, radiusY, TileID.Ash);

				// 丘顶再压一层碎石，别的列也顺便带一点
				if (WorldPaint.ValueNoise(Seed + 700, i * 2.1f) > 0.55f) {
					WorldPaint.Ellipse(x + 3, y - (int)radiusY, radiusX * 0.35f, radiusY * 0.4f, TileID.Stone);
				}
			}
		}

		/// <summary>
		/// 地表整理：把每一列**最高的那格地表**（灰烬 / 土）换成灰烬草。
		/// <para/>为什么需要：<see cref="BuildCrust"/> 只给基准高度那一行铺草，
		/// 之后 <see cref="BuildDunes"/> 堆出来的灰烬丘顶面是裸灰烬。
		/// 这一步让整个荒原都有灰烬草的起伏（玩家要的"地表稍微微像样一些"）。
		/// </summary>
		private static void BuildSurfaceGrass()
		{
			int grassed = 0;

			for (int x = 2; x < FireplaceLayout.Width - 2; x++) {
				if (InsideStructure(x, Surface[x], 4)) {
					continue;
				}

				int from = Math.Max(Surface[x] - 40, 0);

				for (int y = from; y < FireplaceLayout.Height; y++) {
					if (!WorldPaint.HasTile(x, y)) {
						continue;
					}

					// 只认地表层的灰烬 / 土：石头、黑曜石、合金一律不动
					ushort type = Main.tile[x, y].TileType;

					if (type == TileID.Ash || type == TileID.Dirt) {
						WorldPaint.Retile(x, y, TileID.AshGrass);
						grassed++;
					}

					break;
				}
			}

			FireplaceGenLog.Note(string.Format("灰烬草地表 {0} 列", grassed));
		}

		/// <summary>地表碎石：小块石头 / 黑曜石，让荒原看着不那么"铺平过"。</summary>
		private static void BuildPebbles()
		{
			// 按面积比例：70 → 600 处
			int placed = 0;

			for (int i = 0; i < 1400 && placed < 600; i++) {
				int x = 10 + (int)(WorldPaint.ValueNoise(Seed + 8200, i * 1.7f) * (FireplaceLayout.Width - 20));

				if (InsideStructure(x, Surface[x], 4)) {
					continue;
				}

				float radius = 1.1f + WorldPaint.ValueNoise(Seed + 8300, i * 2.3f) * 2.4f;
				int y = Surface[x] - (int)(radius * 0.3f);
				ushort type = WorldPaint.ValueNoise(Seed + 8400, i * 3.1f) > 0.62f
					? TileID.Obsidian
					: TileID.Stone;

				WorldPaint.Ellipse(x, y, radius, radius * 0.7f, type);
				placed++;
			}

			FireplaceGenLog.Note(string.Format("地表碎石 {0} 处", placed));
		}

		/// <summary>
		/// 灰烬树（地狱风格的枯树）：只长在灰烬草上，散在世界里。
		///
		/// <para/>用原版 <see cref="WorldGen.GrowTree"/>：1.4.4 里它自己认得灰烬草
		/// （内部走 <c>WorldGen.AshTreeGroundTest</c> / <c>IsTileTypeFitForTree</c>），
		/// 不用手搭树干 —— 手搭要自己算 <c>TileID.Trees</c> 的 frameX/frameY，很容易歪。
		/// <para/>⚠️ 它的第二个参数是**地面那一格**（不是地面上一格）：IL 里先拿它当
		/// "起点格"跳过树苗，再对同一格做 <c>IsTileTypeFitForTree</c> 与坡度检查。
		/// 所以这里传 <c>Surface[x]</c>，并用返回值 + "树干到底在不在"双保险。
		///
		/// <para/>（900×1300 时代的日志里这一步一直是"灰烬树 0 棵" —— 原版这套判定
		/// 在灰烬草上就是不成立。这里保留这一步并按面积把尝试次数放大到 80 棵的量，
		/// 长不出来也不会影响其它任何东西。）
		/// </summary>
		private static void BuildAshTrees()
		{
			int placed = 0;

			for (int i = 0; i < 1600 && placed < 80; i++) {
				int x = 14 + (int)(WorldPaint.ValueNoise(Seed + 9100, i * 1.31f) * (FireplaceLayout.Width - 28));
				int ground = Surface[x];

				if (!WorldPaint.InWorld(x, ground) || InsideStructure(x, ground, 6)) {
					continue;
				}

				if (!WorldPaint.IsTile(x, ground, TileID.AshGrass)) {
					continue;
				}

				if (WorldPaint.HasTile(x, ground - 1) || WorldPaint.HasTile(x, ground - 2)
					|| WorldPaint.HasTile(x, ground - 3)) {
					continue;
				}

				WorldGen.GrowTree(x, ground);

				// 树干是 TileID.Trees：长出来了才算一棵（GrowTree 空间不够时会返回 false 且什么都不做）
				for (int y = ground - 1; y >= ground - 6 && y > 0; y--) {
					if (WorldPaint.IsTile(x, y, TileID.Trees)) {
						placed++;
						break;
					}
				}
			}

			FireplaceGenLog.Note(string.Format("灰烬树 {0} 棵", placed));
		}

		/// <summary>
		/// 低洼处的液体：岩浆 + 污染水（按面积比例放大到 70 / 90 处）。
		/// 污染水用原版水（液体类型 0）表现：视觉上是水，进游戏后湿地会挂上污染减益。
		/// </summary>
		private static void BuildPools()
		{
			// 按面积比例：900 宽时 9 岩浆 + 12 水 → 8400 宽时 70 + 90
			const int lavaTarget = 70;
			const int waterTarget = 90;

			int lavaPlaced = 0;
			int waterPlaced = 0;

			for (int x = 24; x < FireplaceLayout.Width - 24
				&& (lavaPlaced < lavaTarget || waterPlaced < waterTarget); x += 7) {
				// 只在"局部最低点"放液体，水才会待在坑里
				if (Surface[x] < Surface[x - 4] || Surface[x] < Surface[x + 4]) {
					continue;
				}

				bool lava = lavaPlaced <= waterPlaced && lavaPlaced < lavaTarget;

				if (lava && lavaPlaced >= lavaTarget) {
					continue;
				}

				if (!lava && waterPlaced >= waterTarget) {
					continue;
				}

				float chance = WorldPaint.ValueNoise(Seed + 4242, x * 0.31f);

				if (chance < 0.45f) {
					continue;
				}

				int width = 4 + (int)(WorldPaint.ValueNoise(Seed + 777, x * 0.13f) * 5f);
				int depth = lava ? 3 : 2;
				int top = Surface[x];

				// 挖出一个小盆（比液面低 depth + 1 格，液体才不会溢出去）
				WorldPaint.EllipseCarve(x, top + depth, (width * 0.5f) + 1f, depth + 1.5f);

				// 灌液体：岩浆是 1、水是 0；只灌满盆底那一层（空格子才生效）
				byte liquid = lava ? (byte)1 : (byte)0;
				int half = width / 2;

				for (int dx = -half; dx <= half; dx++) {
					for (int dy = top + depth; dy <= top + depth + 1; dy++) {
						WorldPaint.SetLiquid(x + dx, dy, 255, liquid);
					}
				}

				if (lava) {
					lavaPlaced++;
				}
				else {
					waterPlaced++;
				}
			}

			FireplaceGenLog.Note(string.Format("岩浆池 {0} 处、污染水池 {1} 处", lavaPlaced, waterPlaced));
		}


		// ==================== 自然洞穴与矿道 ====================
		//
		// 玩家要求："随机生成一些不干扰原本建筑的矿道和自然矿洞，只不过因为资源枯竭没有矿石。"
		// 所以：**只挖洞、不放任何矿石**；每一处都先做"是否撞到结构"的判定。

		/// <summary>
		/// 某个坐标是否落在塔 / 堡垒 / 地下通道 / **椭球地宫**的保护区里（这些地方不许挖洞、
		/// 也不许留沙）。
		///
		/// <para/>⚠️ 椭球地宫：椭球横向 x=2700~5700、纵向 y=1940~2340，整块都在保护区里；
		/// 判据直接用椭球外框（比逐格算椭圆便宜，多保护一点没有副作用）。
		/// 通道是横贯整张图的，它那一条横带把全世界都保护掉 —— 这正是我们要的
		/// （通道里不能长洞，也不能有矿道横穿）。
		/// </summary>
		internal static bool InsideStructure(int x, int y, int margin = 12)
		{
			return Rect(x, y, FireplaceLayout.FortLeft, FireplaceLayout.FortTop, FireplaceLayout.FortRight, FireplaceLayout.FortBottom, margin)
				|| Rect(x, y, FireplaceLayout.TowerLeft, FireplaceLayout.TowerTop, FireplaceLayout.TowerRight, FireplaceLayout.TowerBottom, margin)
				|| Rect(x, y, FireplaceLayout.ArenaLeft, FireplaceLayout.ArenaTop, FireplaceLayout.ArenaRight, FireplaceLayout.ArenaBottom, margin)
				|| Rect(x, y, FireplaceLayout.TunnelLeft - 6, FireplaceLayout.TunnelTop - 6,
					FireplaceLayout.TunnelRight + 8, FireplaceLayout.TunnelBottom + 6, margin)
				|| Rect(x, y, FireplaceLayout.VaultLeft, FireplaceLayout.VaultTop,
					FireplaceLayout.VaultRight, FireplaceLayout.VaultBottom, margin);
		}

		/// <summary>
		/// 结构保护区（外扩 <see cref="SandGuardMargin"/> 格）里的 **沙 / 泥沙** 全部换成石头。
		///
		/// <para/>为什么需要：<c>TileID.Sand</c> / <c>TileID.Silt</c> 受重力。掏空之后
		/// （地宫空腔、矿道、竖井），上面的沙柱会一路往下漏 —— 原版机制是
		/// <c>WorldGen.SpawnFallingBlockProjectile</c>：它只把**沙自己**那一格
		/// <c>ClearTile()</c> 掉、再生成一个落沙弹幕（落地的 <c>Projectile.Kill</c> 只调
		/// <c>PlaceTile</c>）—— 所以沙**不会破坏**瑜钢合金，但会灌进房间、把地板与家具埋掉，
		/// 玩家看到的就是"结构里出现异样"。
		///
		/// <para/>做法：保护区外扩 24 格（覆盖结构正上方那一段岩层）之内，只要是沙/泥沙一律
		/// 换 <c>TileID.Stone</c>。岩石层里"顺手留洞"留下的空洞不属于保护区，不受影响。
		/// </summary>
		private const int SandGuardMargin = 24;

		private static void HardenSandNearStructures()
		{
			int changed = 0;

			for (int x = 0; x < FireplaceLayout.Width; x++) {
				// 只扫岩石层以下（地表那几层是灰烬/土，没有沙；宝箱区也不在这儿）
				for (int y = FireplaceLayout.RockTop - 40; y < FireplaceLayout.Height; y++) {
					// 先判"在不在保护区"（几次整数比较），再读格子 —— 5 百万格扫下来，
					// 顺序反过来的话就是一千多万次多余的读盘。
					if (!InsideStructure(x, y, SandGuardMargin)) {
						continue;
					}

					if (!WorldPaint.IsTile(x, y, TileID.Sand) && !WorldPaint.IsTile(x, y, TileID.Silt)) {
						continue;
					}

					WorldPaint.Retile(x, y, TileID.Stone);
					changed++;
				}
			}

			FireplaceGenLog.Note(string.Format("结构附近沙透镜体换成石头 {0} 格（外扩 {1} 格）",
				changed, SandGuardMargin));
		}

		private static bool Rect(int x, int y, int left, int top, int right, int bottom, int margin)
		{
			return x >= left - margin && x <= right + margin && y >= top - margin && y <= bottom + margin;
		}

		/// <summary>
		/// 自然矿洞：在岩石层里挖一批大小不一的洞，彼此可能相连（原版洞穴就是这个做法）。
		/// <para/>按面积比例：150 → **1400 处**（900 宽 ~6 格一处 → 8400 宽同样密度）。
		/// 岩石层里那些"顺手留出的空洞"（<see cref="CaveAir"/>）已经贡献了一部分，
		/// 这里再挖一遍时如果已经是空的，<c>ClearTile</c> 会直接跳过。
		/// </summary>
		private static void BuildCaves(GenerationProgress progress)
		{
			progress.Message = "正在蚀出旧时代的空洞……";

			int carved = 0;

			for (int i = 0; i < 4000 && carved < 1400; i++) {
				int x = 20 + (int)(WorldPaint.ValueNoise(Seed + 6100, i * 1.7f) * (FireplaceLayout.Width - 40));
				int y = FireplaceLayout.RockTop + 30
					+ (int)(WorldPaint.ValueNoise(Seed + 6200, i * 2.3f) * (FireplaceLayout.Height - FireplaceLayout.RockTop - 60));

				if (InsideStructure(x, y, 14)) {
					continue;
				}

				float radiusX = 5f + (WorldPaint.ValueNoise(Seed + 6300, i * 1.1f) * 16f);
				float radiusY = 4f + (WorldPaint.ValueNoise(Seed + 6400, i * 1.3f) * 9f);

				WorldPaint.EllipseCarve(x, y, radiusX, radiusY);

				// 一半的洞再连一条细通道出去，制造"洞系"的感觉
				if (WorldPaint.ValueNoise(Seed + 6500, i * 0.9f) > 0.5f) {
					int steps = 8 + (int)(WorldPaint.ValueNoise(Seed + 6600, i * 2.1f) * 26f);
					float angle = WorldPaint.ValueNoise(Seed + 6700, i * 3.1f) * 6.28f;
					int cx = x;
					int cy = y;

					for (int s = 0; s < steps; s++) {
						cx += (int)MathF.Round(MathF.Cos(angle) * 3f);
						cy += (int)MathF.Round(MathF.Sin(angle) * 2f);

						if (InsideStructure(cx, cy, 10) || cy <= FireplaceLayout.RockTop) {
							break;
						}

						WorldPaint.EllipseCarve(cx, cy, 3.4f, 2.6f);
					}
				}

				carved++;
			}

			FireplaceGenLog.Note(string.Format("自然矿洞 {0} 处", carved));
		}

		/// <summary>
		/// 矿道：几条横向主巷 + 竖井，配原版木平台当支撑（没有任何矿石）。
		/// <para/>按面积比例：6 → **60 条尝试**。通道横贯整张图之后，
		/// 落在通道那一条横带、或者压在堡垒/地宫上的矿道会被整条放弃（<c>blocked</c>），
		/// 所以实际建成的条数会明显少于尝试次数 —— 日志里会打出来。
		/// </summary>
		private static void BuildMineShafts(GenerationProgress progress)
		{
			progress.Message = "正在凿出废弃的矿道……";

			int built = 0;

			for (int i = 0; i < 120; i++) {
				int y = FireplaceLayout.RockTop + 60
					+ (int)(WorldPaint.ValueNoise(Seed + 7100, i * 2.7f) * (FireplaceLayout.Height - FireplaceLayout.RockTop - 120));

				int left = 30 + (int)(WorldPaint.ValueNoise(Seed + 7200, i * 1.9f) * (FireplaceLayout.Width - 200));
				int right = left + 90 + (int)(WorldPaint.ValueNoise(Seed + 7300, i * 2.3f) * 130f);

				// 撞到结构就整条不要，保证"不干扰原本建筑"
				bool blocked = false;

				for (int x = left; x <= right; x += 6) {
					if (InsideStructure(x, y, 16)) {
						blocked = true;
						break;
					}
				}

				if (blocked) {
					continue;
				}

				for (int x = left; x <= right; x++) {
					WorldPaint.Carve(x, y, x, y + 3);           // 主巷：4 格高
				}

				// 支撑：每隔 14 格一对木梁 + 顶板
				for (int x = left + 4; x <= right - 4; x += 14) {
					WorldPaint.Retile(x, y - 1, TileID.WoodenBeam);
					WorldPaint.Retile(x + 1, y - 1, TileID.WoodenBeam);
					WorldPaint.HLine(x - 1, x + 2, y - 1, TileID.WoodBlock);
				}

				// 竖井：从主巷往上打一条，接到上层
				int shaftX = left + 30 + (int)(WorldPaint.ValueNoise(Seed + 7400, i * 1.3f) * (right - left - 60));
				int shaftTop = y - 40 - (int)(WorldPaint.ValueNoise(Seed + 7500, i * 2.9f) * 50f);

				for (int sy = Math.Max(shaftTop, FireplaceLayout.RockTop + 8); sy <= y; sy++) {
					if (InsideStructure(shaftX, sy, 10)) {
						continue;
					}

					WorldPaint.Carve(shaftX, sy, shaftX + 2, sy);

					if ((y - sy) % 6 == 0) {
						WorldPaint.Retile(shaftX, sy, TileID.Platforms);   // 当梯子用
					}
				}

				built++;
			}

			FireplaceGenLog.Note(string.Format("矿道 {0} 条（尝试 {1} 条）", built, 120));
		}

		/// <summary>
		/// 地表散落的黑曜石巨岩 —— 让"灰烬 + 黑曜石"的观感提前立住。
		/// <para/>按面积比例：14 → 130 处。
		/// </summary>
		private static void BuildRocks()
		{
			for (int i = 0; i < 130; i++) {
				int x = 30 + (int)(WorldPaint.ValueNoise(Seed + 3131, i * 2.9f) * (FireplaceLayout.Width - 60));
				float radius = 3f + WorldPaint.ValueNoise(Seed + 555, i * 1.1f) * 5f;
				int y = Surface[x] - (int)(radius * 0.4f);

				WorldPaint.Ellipse(x, y, radius, radius * 0.7f, TileID.Obsidian);
			}
		}
	}
}
