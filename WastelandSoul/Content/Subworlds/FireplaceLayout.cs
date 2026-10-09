namespace WastelandSoul.Content.Subworlds
{
	/// <summary>
	/// 「壁炉」子世界的**布局常量**：生成器、剧情触发点、门/终端位置全部从这里取，
	/// 避免同一个坐标写死在几个文件里（改尺寸时只改这一处）。
	///
	/// <para/>世界尺寸 **8400 × 2400**（= 原版大世界）。竖直方向的分层
	/// （把 900×1300 的那一套按 ~1.85 倍放大、并把结构整体居中到 x=4200）：
	/// <code>
	///   y=0     ~ 100   太空
	///   y=100   ~ 520   塔顶 Boss 场地（整块都在太空线 worldSurface×0.35=560 以上）
	///   y=520   ~ 540   塔顶接驳颈
	///   y=540   ~ 1680  塔身（19 层，青银相间的瑜钢合金壳）
	///   y=1552  ~ 1648 灰烬地表（基准 1600，起伏 ±48）
	///   y=1680  ~ 2100  堡垒（**全埋**在灰烬下：屋顶 1680 在地表以下）
	///   y=2130  ~ 2230  地下通道（横贯整张图：x=8 ~ 8388，两端封死）
	///   y=1940  ~ 2340  椭球地宫（堡垒下方的合金空腔，见 FireplaceVault）
	///   y=2390  ~ 2400  世界底部的实心岩层
	/// </code>
	///
	/// <para/>椭球地宫的几何全部由 <see cref="FireplaceVault"/> 消费，房间清单写在
	/// <see cref="VaultRooms"/> 里；<c>tools/check_fireplace_layout.py</c> 会把下面这些
	/// 数字读出来核对（房间必须在椭球内、不能压到堡垒与地下通道、每间都要有门）。
	/// </summary>
	public static class FireplaceLayout
	{
		// ---------------- 世界 ----------------
		public const int Width = 8400;
		public const int Height = 2400;

		/// <summary>灰烬地表的基准高度（堡垒只剩塔身从灰烬里钻出来）。</summary>
		public const int SurfaceBase = 1600;

		/// <summary>地表起伏幅度（格）。</summary>
		public const int SurfaceAmplitude = 48;

		/// <summary>灰烬 / 土层厚度，之下转岩石。</summary>
		public const int CrustDepth = 220;

		/// <summary>岩石层起始高度（对应 <c>Main.rockLayer</c>）。</summary>
		public const int RockTop = SurfaceBase + CrustDepth;

		// ---------------- 堡垒（整体居中在 x=4200） ----------------
		public const int FortLeft = 3700;
		public const int FortRight = 4700;
		public const int FortTop = 1680;
		public const int FortBottom = 2100;

		/// <summary>门厅（室内可站立空间）。</summary>
		public const int HallLeft = 3760;
		public const int HallRight = 4640;
		public const int HallTop = 1740;
		public const int HallBottom = 2040;

		/// <summary>壁炉火塘的左右边界（门厅正中，也是整张图的中线 4200）。</summary>
		public const int HearthLeft = 4120;
		public const int HearthRight = 4280;

		/// <summary>数据终端所在的 y。</summary>
		public const int TerminalY = 1980;

		/// <summary>数据终端中心 x。</summary>
		public const int TerminalX = 4400;

		/// <summary>返回门（主世界出口）中心 x。</summary>
		public const int ExitX = 3860;

		/// <summary>堡垒外壳厚度。</summary>
		public const int FortShell = 5;

		/// <summary>
		/// 堡垒通往下方的**竖井**左右边（门厅地板 → 地下通道 → 地宫主通道）。
		///
		/// <para/>⚠️ 新尺寸下通道是**横贯整张图**的，所以竖井不再是"通道的西口"，
		/// 必须显式给坐标：放在火塘（4120~4280）东侧、门厅（3760~4640）内部，
		/// 正好落在「一层·中央大厅」里。地宫那一步会把整段竖井重新打通（见
		/// <see cref="FireplaceVault"/> 的 <c>OpenFortressShaft</c>）。
		/// </summary>
		public const int FortShaftLeft = 4020;
		public const int FortShaftRight = 4040;

		// ---------------- 祈塔 ----------------
		public const int TowerLeft = 4150;
		public const int TowerRight = 4250;
		public const int TowerTop = 540;
		public const int TowerBottom = FortTop;

		/// <summary>
		/// 塔身层高（每层一块合金楼板）。
		/// <para/>必须能整除塔身高度（1680-540=1140）：1140/60 = **19 层**。
		/// 这个不变量由 <c>tools/check_fireplace_layout.py</c> 盯着。
		/// </summary>
		public const int TowerFloorHeight = 60;

		/// <summary>塔壁厚度。</summary>
		public const int TowerShell = 2;

		// ---------------- 塔顶 Boss 场地 ----------------
		/// <summary>场地整块落在太空线 560 以上（ArenaBottom=520，留 40 格余量）。</summary>
		public const int ArenaLeft = 3750;
		public const int ArenaRight = 4650;
		public const int ArenaTop = 100;
		public const int ArenaBottom = 520;

		/// <summary>场地与塔身之间的接驳颈（空心合金）。</summary>
		public const int ArenaNeckLeft = TowerLeft + 2;
		public const int ArenaNeckRight = TowerRight - 2;

		// ---------------- 地下通道（横贯整张图，两端封死） ----------------
		public const int TunnelLeft = 8;
		public const int TunnelRight = Width - 12;
		public const int TunnelTop = 2130;
		public const int TunnelBottom = 2230;

		/// <summary>通道内衬厚度。</summary>
		public const int TunnelShell = 4;

		// ---------------- 椭球地宫 ----------------
		/// <summary>椭球中心（整张图的横向中线）。</summary>
		public const int VaultCenterX = 4200;
		public const int VaultCenterY = 2140;

		/// <summary>
		/// 椭球半径：**3000 × 400** 的外框（900×1300 时代是 744×264 —— 横向放大到 4 倍、
		/// 纵向按新世界高度放到 1.5 倍）。横向必须给这么大：里面要塞下"1025 格宽的中央大厅 +
		/// 另外 11 间房 + 4~6 格隔墙"，而且中间那 1000 格是堡垒投影（地宫一格都不写）。
		/// 横向 x=2700~5700（离世界两边各留 2700 格），纵向 y=1940~2340（离世界底留 59 格），
		/// 上缘 1940 仍在岩石层（RockTop=1820）以下。
		/// </summary>
		public const int VaultRadiusX = 1500;
		public const int VaultRadiusY = 200;

		/// <summary>隔绝墙（合金壳）厚度：玩家要求 4~6 格厚。</summary>
		public const int VaultShell = 5;

		/// <summary>内表面墙裙（压条）的行距：玩家要求 12~16 行一条。</summary>
		public const int VaultTrimStep = 14;

		public const int VaultLeft = VaultCenterX - VaultRadiusX;
		public const int VaultRight = VaultCenterX + VaultRadiusX;
		public const int VaultTop = VaultCenterY - VaultRadiusY;
		public const int VaultBottom = VaultCenterY + VaultRadiusY;

		/// <summary>
		/// 主平台（地宫一层地面）的**顶面行**。
		/// <para/>刻意对齐地下通道的走道面（通道地板压条在 <c>TunnelBottom - 1</c>），
		/// 这样从竖井下来、走出通道都是一路平的（检查器会核对这条等式）。
		/// </summary>
		public const int VaultFloorY = TunnelBottom - 1;

		/// <summary>主平台厚度（顶面那一行算在内）。</summary>
		public const int VaultPlatformThickness = 6;

		// ---- 一层（主层，也是通道那一层）----
		/// <summary>一层房间内空的顶行（天花板下沿）。</summary>
		public const int VaultStoryTop = 2140;

		/// <summary>一层天花板 / 二层楼板：这一整段填实心合金（房间的墙就靠它"抠"出来）。</summary>
		public const int VaultSlabTop = 2111;
		public const int VaultSlabBottom = 2139;

		/// <summary>楼板的横向范围 = 整个椭球（铺满，左右端不再留观景口）。</summary>
		public const int VaultSlabLeft = VaultLeft;
		public const int VaultSlabRight = VaultRight;

		// ---- 二层（两翼）----
		/// <summary>二层房间内空的上下界。</summary>
		public const int VaultUpperTop = 2041;
		public const int VaultUpperBottom = 2110;

		/// <summary>二层房间的顶板。</summary>
		public const int VaultCeilingTop = 2038;
		public const int VaultCeilingBottom = 2040;

		/// <summary>
		/// 二层两翼的**外墙范围**（一翼三间，外墙 6 格厚）。
		/// <para/>中间那 1000 格是堡垒投影（3700~4700），地宫在这一块**一格都不写**，
		/// 所以二层只能做成两翼；两翼的左右边界必须落在椭球内空里（检查器核对房间四角）。
		/// </summary>
		public const int VaultWestWingLeft = 2960;
		public const int VaultWestWingRight = 3698;
		public const int VaultEastWingLeft = 4702;
		public const int VaultEastWingRight = 5440;

		/// <summary>东侧升降井（一层东头房间里开洞，直通二层右翼的房间）。</summary>
		public const int VaultEastLadderX = 5200;
		public const int VaultEastLadderRight = 5203;

		/// <summary>西侧升降井（一层西头房间里开洞，直通二层阁楼）。</summary>
		public const int VaultWestLadderX = 2952;
		public const int VaultWestLadderRight = 2955;

		// ---- 一层分隔墙 ----
		// 房间之间不留缝：分隔墙的范围就是「左房右界+1 ~ 右房左界-1」，
		// 门开在墙中间那一列。
		public const int VaultDoorFloor = VaultFloorY - 1;

		/// <summary>椭球地宫里的一个房间（记录的是**内空**范围）。</summary>
		public readonly struct VaultRoom
		{
			/// <summary>房间名（只用于日志与检查器）。</summary>
			public readonly string Name;

			/// <summary>内空左边界。</summary>
			public readonly int Left;

			/// <summary>内空顶行。</summary>
			public readonly int Top;

			/// <summary>内空右边界。</summary>
			public readonly int Right;

			/// <summary>内空底行。</summary>
			public readonly int Bottom;

			public VaultRoom(string name, int left, int top, int right, int bottom)
			{
				Name = name;
				Left = left;
				Top = top;
				Right = right;
				Bottom = bottom;
			}

			/// <summary>房间内空高度。</summary>
			public int Height => Bottom - Top + 1;

			/// <summary>房间内空宽度。</summary>
			public int Width => Right - Left + 1;
		}

		/// <summary>
		/// 椭球地宫的**房间清单**（**12 间**：一层 6 间连成一条链，二层两翼各 3 间）。
		///
		/// <para/>一层（y=2140~2228）就是通道那一层：主通道从西边一路穿过椭球到东边，
		/// 6 间房依次串在这条主通道上（相邻两间之间是 5 格厚隔墙 + 一扇门），
		/// 玩家从堡垒竖井（x=4020~4040）落进「中央大厅」，往西走是 3 间、往东走是 3 间，
		/// 两端的房间直接连着通往世界东西边缘的通道臂。
		///
		/// <para/>二层（y=2041~2110）落在堡垒投影两侧的两翼里（中间 1000 格是堡垒，
		/// 地宫不写），每翼 3 间，靠外墙那侧的门外是穹顶阁楼，两条升降井分别把
		/// 一层西头房间与二层右翼房间接上（升降井本身也要落在房间里，检查器会核对）。
		///
		/// <para/>尺寸刻意做大中小混排（125 ~ 1025 格宽），隔墙一律 **5 格**。
		/// 改这些数字要同时跑 <c>tools/check_fireplace_layout.py</c> 与
		/// <c>tools/check_fireplace_vault_connectivity.py</c>。
		/// </summary>
		public static readonly VaultRoom[] VaultRooms = new VaultRoom[]
		{
			// ---- 一层：主通道上串起来的 6 间（自西向东）----
			new VaultRoom("一层·废料仓", 2950, 2140, 3170, 2228),      // 221 宽（中）
			new VaultRoom("一层·修械间", 3176, 2140, 3300, 2228),      // 125 宽（小），隔墙 3171~3175
			new VaultRoom("一层·中央大厅", 3306, 2140, 4330, 2228),    // 1025 宽（大），隔墙 3301~3305；竖井落在里面
			new VaultRoom("一层·观测台", 4336, 2140, 4700, 2228),      // 365 宽（中），隔墙 4331~4335
			new VaultRoom("一层·寝区", 4706, 2140, 5150, 2228),        // 445 宽（中），隔墙 4701~4705
			new VaultRoom("一层·配电间", 5156, 2140, 5450, 2228),      // 295 宽（中），隔墙 5151~5155；东升降井落在里面

			// ---- 二层西翼：三间（自西向东，外墙 2960~2965 / 3693~3698）----
			new VaultRoom("二层·档案库", 2966, 2041, 3140, 2110),      // 175 宽
			new VaultRoom("二层·寝舱", 3146, 2041, 3320, 2110),        // 175 宽，隔墙 3141~3145
			new VaultRoom("二层·观测室", 3326, 2041, 3692, 2110),      // 367 宽，隔墙 3321~3325

			// ---- 二层东翼：三间（自西向东，外墙 4702~4707 / 5435~5440）----
			new VaultRoom("二层·配电间", 4708, 2041, 4882, 2110),      // 175 宽
			new VaultRoom("二层·机房", 4888, 2041, 5062, 2110),        // 175 宽，隔墙 4883~4887
			new VaultRoom("二层·穹顶库", 5068, 2041, 5434, 2110),      // 367 宽，隔墙 5063~5067；东升降井落在里面
		};

		// ---------------- 出生点 ----------------
		/// <summary>玩家进入壁炉时的落点（门厅地面，火塘西侧）。</summary>
		public const int SpawnX = 3900;
		public const int SpawnY = HallBottom;
	}
}
