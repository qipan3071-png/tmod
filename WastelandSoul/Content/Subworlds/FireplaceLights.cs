using Terraria;
using Terraria.ID;

namespace WastelandSoul.Content.Subworlds
{
	/// <summary>
	/// 壁炉子世界的**布光密度**规则（玩家反馈："亮度还是有点低"）。
	///
	/// <para/>不变量（由 <c>tools/check_fireplace_layout.py</c> 第 12 节抽样校验）：
	/// **每个可通行点到最近光源的距离 ≤ <see cref="MaxGap"/> 格**（按切比雪夫距离算，
	/// 也就是 |dx|、|dy| 都不超过 12）。
	///
	/// 手段是三条**结构性**保证，而不是到处随手加灯：
	/// <list type="number">
	/// <item><b>可通行地面行全部铺连续微光走线</b>（<see cref="WalkwayLine"/>，步长
	/// <see cref="LineStep"/> = 2）—— 这一条最强：任何站在地板上的点离走线只有 1~2 格；</item>
	/// <item><b>地面火把 / 天花吊灯按 <see cref="FloorStep"/> / <see cref="CeilingStep"/>（都是 12）铺</b>
	/// —— 让"看得见"和"数值达标"同时成立（塔层高 60，一层只挂一盏是不够的）；</item>
	/// <item><b>攀登竖井 / 矿洞 / 升降井按更密的网格补灯</b>：竖井平台每
	/// <see cref="ShaftStep"/> 行一层、每 <see cref="ShaftLightEvery"/> 层一盏；
	/// 矿洞按 <see cref="CaveCell"/> × <see cref="CaveCell"/> 的网格，每格只要有能站的地方就放一盏
	/// （8 格的格子 → 格内任意点到该灯 ≤ 7 格，留出余量）。</item>
	/// </list>
	///
	/// <para/>这里只放常量与三个放灯原语，具体的范围（哪儿要躲开火塘 / 井口）由调用方决定。
	/// 常量被 Python 检查器用正则读出来核对（都 ≤ <see cref="MaxGap"/>），所以**别在别处写死步长**。
	/// </summary>
	internal static class FireplaceLights
	{
		/// <summary>不变量：可通行点 → 最近光源的距离上限（格）。</summary>
		internal const int MaxGap = 12;

		/// <summary>可通行地面行的微光走线步长（连着铺，2 格一盏）。</summary>
		internal const int LineStep = 2;

		/// <summary>地面火把步长。</summary>
		internal const int FloorStep = 12;

		/// <summary>天花吊灯步长（塔层高 60 → 每层一排，别再"一层一盏"）。</summary>
		internal const int CeilingStep = 12;

		/// <summary>攀登竖井 / 升降井里平台的层距（和平台本身的步长一致）。</summary>
		internal const int ShaftStep = 5;

		/// <summary>竖井里每隔几层平台放一盏灯（5 × 2 = 10 格 ≤ 12）。</summary>
		internal const int ShaftLightEvery = 2;

		/// <summary>矿洞布光的网格边长：每格只要有可站立的空气就放一盏（格内最远 7 格）。</summary>
		internal const int CaveCell = 8;

		/// <summary>墙面竖向指示灯带的步长。</summary>
		internal const int WallBandStep = 2;

		/// <summary>
		/// 在一条可通行地面行上铺**连续微光走线**（翡翠 / 钻石交替，都是自带光的方块）。
		/// <para/>⚠️ 这会把该行变成实心：调用方给的行必须是"地板面"那一行（人站在它上面），
		/// 不是人站的那一行。
		/// </summary>
		internal static void WalkwayLine(int left, int right, int y)
		{
			for (int x = left; x <= right; x += LineStep) {
				WorldPaint.Retile(x, y, x % 6 == 0 ? TileID.DiamondGemspark : TileID.EmeraldGemspark);
			}
		}

		/// <summary>
		/// 地板上放一盏火把（放在 <paramref name="floorY"/> 的上一格）。
		/// <para/>先确认那一格是空气：<c>WorldGen.PlaceTile(forced: true)</c> 会把已有方块直接顶掉，
		/// 落在立柱 / 压条上就会在结构上啃出一个洞。
		/// </summary>
		internal static bool FloorTorch(int x, int floorY)
		{
			int y = floorY - 1;

			if (!WorldPaint.InWorld(x, y) || Main.tile[x, y].HasTile) {
				return false;
			}

			WorldGen.PlaceTile(x, y, TileID.Torches, mute: true, forced: true);
			return WorldPaint.IsTile(x, y, TileID.Torches);
		}

		/// <summary>
		/// 从"天花板那一行"往下挂一盏吊灯（吊灯占 <paramref name="ceilingY"/> + 1 起的 3 行）。
		/// <para/>同样先确认那一格是空气；放不下时 <c>WorldGen.PlaceObject</c> 只是静默返回 false。
		/// </summary>
		internal static bool Chandelier(int x, int ceilingY)
		{
			int y = ceilingY + 1;

			if (!WorldPaint.InWorld(x, y) || Main.tile[x, y].HasTile) {
				return false;
			}

			return WorldGen.PlaceObject(x, y, TileID.Chandeliers, true, 0, 0, -1, -1);
		}
	}
}
