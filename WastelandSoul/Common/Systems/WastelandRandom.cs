using System;

namespace WastelandSoul.Common.Systems
{
	/// <summary>
	/// **联机安全的掷骰**：同一份"世界状态"在服务端与每个客户端都会算出**同一个数**。
	///
	/// <para/>=== 为什么必须有它（玩家 2026-10-09 指出的联机问题）===
	/// tModLoader 会自动同步原版字段（NPC 的位置/速度/生命/目标、<c>NPC.ai[0..3]</c>、
	/// 弹幕的基础字段、玩家原版属性…），**但不会同步"我们自己的随机结果"**。
	/// <c>Main.rand</c> 是一台**每台机器各自推进**的随机数发生器，而 <c>NPC.AI()</c> 在
	/// 服务端和每个客户端上都会跑一遍 —— 于是同一句
	/// <c>interval + Main.rand.Next(-12, 13)</c> 在两边掷出**不同的数字**：
	/// </summary>
	/// <code>
	/// // ❌ 服务端：下一次出招 150-7 = 143 帧后      客户端B：150+4 = 154 帧后
	/// ctx.AttackDelay = Archivist.RollAttackDelay(ctx);
	/// </code>
	/// <para/>后果是"看起来只有几帧"的不同步：**攻击时机、弹幕落点、Boss 走位都会慢慢错开**
	/// （玩家看到的是"Boss 的动作和伤害对不上""弹幕瞬移"）。单机永远复现不出来。
	///
	/// <para/>=== 用法 ===
	/// <code>
	/// // ✅ 三方同值：种子只取自**已经同步过的**数据（whoAmI / ai[] / 阶段序号）
	/// ctx.AttackDelay = Archivist.AttackIntervalPhaseOne
	///     + WastelandRandom.Roll(Npc.whoAmI, (int)Npc.ai[2], 0, -20, 21);
	/// </code>
	///
	/// <para/>⚠️ 三条使用规矩：
	/// <list type="number">
	/// <item>种子**只能用同步过的量**（<c>whoAmI</c>、<c>ai[]</c>、<c>life</c>、世界时间…）；
	/// 用别的"各自算出来的值"当种子等于没修；</item>
	/// <item>**每次调用都要给不同的 salt**，否则同一轮里两处掷骰会拿到同一个数；</item>
	/// <item>它**不是**用来替代 <c>SendExtraAI</c> 的：真要传"结果"（比如选中的目标玩家）时，
	/// 还是得用 <c>SendExtraAI/ReceiveExtraAI</c>，这里只解决"随机数本身不同步"。</item>
	/// </list>
	/// </summary>
	public static class WastelandRandom
	{
		/// <summary>
		/// 掷一个 <c>[minValue, maxValue)</c> 的整数，**任意机器上结果相同**。
		/// <para/>实现是 splitmix64 风格的两轮混淆（只用乘法与异或，不需要 <c>BitConverter</c>，
		/// 也不会因为平台/版本差异改变结果）。
		/// </summary>
		public static int Roll(int seedA, int seedB, int seedC, int minValue, int maxValue)
		{
			if (maxValue <= minValue) {
				return minValue;
			}

			ulong mixed = Mix((ulong)(uint)seedA * 0x9E3779B97F4A7C15UL
				^ (ulong)(uint)seedB * 0xC2B2AE3D27D4EB4FUL
				^ (ulong)(uint)seedC * 0x165667B19E3779F9UL);

			return minValue + (int)(mixed % (ulong)(maxValue - minValue));
		}

		/// <summary>两参数版本（大多数场合只需要 "谁 + 第几轮"）。</summary>
		public static int Roll(int seedA, int seedB, int minValue, int maxValue)
		{
			return Roll(seedA, seedB, 0, minValue, maxValue);
		}

		/// <summary>开区间浮点版本（<c>[0, 1)</c>），同样任意机器同值。</summary>
		public static float RollFloat(int seedA, int seedB, int seedC)
		{
			ulong mixed = Mix((ulong)(uint)seedA * 0x9E3779B97F4A7C15UL
				^ (ulong)(uint)seedB * 0xC2B2AE3D27D4EB4FUL
				^ (ulong)(uint)seedC * 0x165667B19E3779F9UL);

			return (float)(mixed >> 40) / (1 << 24);
		}

		private static ulong Mix(ulong value)
		{
			value ^= value >> 33;
			value *= 0xFF51AFD7ED558CCDUL;
			value ^= value >> 33;
			value *= 0xC4CEB9FE1A85EC53UL;
			return value ^ (value >> 33);
		}
	}
}
