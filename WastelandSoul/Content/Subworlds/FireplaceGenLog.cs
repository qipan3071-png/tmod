using System.Diagnostics;
using Terraria;
using Terraria.ModLoader;

namespace WastelandSoul.Content.Subworlds
{
	/// <summary>
	/// 壁炉生成的**步骤日志 + 计时**。玩家反馈"进门只有一片空世界、日志里却什么都没有"，
	/// 所以每一步都留一条痕：开始 / 结束 + 写入了多少格 + **本步耗时**。
	/// 只要有一步抛异常，日志就会停在那一步的"开始"（异常本身由 tML 记录）。
	///
	/// <para/>为什么要带计时：世界从 900×1300 放大到 8400×2400（约 2016 万格）之后，
	/// 生成时间成了必须盯着的指标（目标 &lt; 30 秒，理想 &lt; 15 秒）。这一层用
	/// <see cref="Stopwatch"/> 把每一步、以及**整个生成**的毫秒数打进日志，
	/// 进门一次就能看到真实数字，不用再靠猜。
	/// </summary>
	internal static class FireplaceGenLog
	{
		private static int index;

		/// <summary>整段生成的总计时（<see cref="Reset"/> 时归零）。</summary>
		private static readonly Stopwatch Watch = Stopwatch.StartNew();

		/// <summary>上一条日志的时间点（毫秒），用来算"本步耗时"。</summary>
		private static long lastMs;

		public static void Reset()
		{
			index = 0;
			WorldPaint.Writes = 0;
			lastMs = 0;
			Watch.Restart();
		}

		/// <summary>补一条普通说明（统计数字这类）。</summary>
		public static void Note(string message)
		{
			ModLoader.GetMod("WastelandSoul").Logger.Info("[壁炉生成] " + message);
		}

		public static void Start(string name)
		{
			index++;

			long now = Watch.ElapsedMilliseconds;
			ModLoader.GetMod("WastelandSoul").Logger.Info(string.Format(
				"[壁炉生成] 步骤 {0} {1} 开始：世界 {2}x{3}（布局期望 {4}x{5}）；上一步耗时 {6} ms",
				index, name, Main.maxTilesX, Main.maxTilesY, FireplaceLayout.Width, FireplaceLayout.Height,
				now - lastMs));
			lastMs = now;
		}

		public static void Done(string name)
		{
			long now = Watch.ElapsedMilliseconds;
			ModLoader.GetMod("WastelandSoul").Logger.Info(string.Format(
				"[壁炉生成] 步骤 {0} {1} 完成：本步 {2} ms，累计写入 {3} 格",
				index, name, now - lastMs, WorldPaint.Writes));
			lastMs = now;
		}

		/// <summary>最后一步收尾时打一条总账（本步 + 全部生成耗时）。</summary>
		public static void Total(string name)
		{
			long now = Watch.ElapsedMilliseconds;
			ModLoader.GetMod("WastelandSoul").Logger.Info(string.Format(
				"[壁炉生成] 步骤 {0} {1} 完成：本步 {2} ms；**整个世界生成共 {3} ms**，累计写入 {4} 格",
				index, name, now - lastMs, now, WorldPaint.Writes));
			lastMs = now;
		}
	}
}
