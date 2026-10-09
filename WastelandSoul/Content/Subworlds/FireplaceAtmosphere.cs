using Microsoft.Xna.Framework;
using SubworldLibrary;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Content.Buffs;

namespace WastelandSoul.Content.Subworlds
{
	/// <summary>
	/// 壁炉世界的**大气与污染水**判定。
	///
	/// <para/>规则（对应设定：堡垒为了保住火种，把外面的土地烧成灰，废气把大气整个污染了）。
	/// 玩家要求：**污染由中心向世界两侧递减** —— 壁炉本身在世界的正中央，它一直在排气，
	/// 所以越靠近中心越呛，越靠近两边的世界边缘越干净（边缘几乎为 0）。
	/// <list type="bullet">
	/// <item><b>污染强度</b> <c>t</c>：见 <see cref="PollutionIntensity"/>。
	/// 它不是"随机的氛围数"而是**唯一的判定输入** —— 减益挂不挂、挂多久、浮尘多密，全都由它推出来；</item>
	/// <item><b>减益分档</b>：<c>t &lt; <see cref="HeavyThreshold"/></c>（0.35）**完全不挂**（清新区）；
	/// 0.35~0.7 轻（<see cref="ApplyServerDebuff"/> 每次只续 45 tick，掉血会一秒一秒地断，平均伤害明显更低）；
	/// &gt; 0.7 重（续满 90 tick，等于一直挂着）；</item>
	/// <item>泡在**污染水**里（原版水 + 壁炉世界）额外挂上既有的 <see cref="Pollution"/>（腐蚀护甲），
	/// 这一条**保持原样**，不受强度影响（水里就是水里）；</item>
	/// <item>再补一点灰绿色浮尘，**密度随强度变化**（中心 6 路、边缘 0.2 路），让"空气有多脏"看得见。</item>
	/// </list>
	///
	/// <para/>=== 联机适配（沿用本轮既有约定，未改动） ===
	/// <list type="number">
	/// <item><b>谁施加</b>：只有 <c>Main.netMode != MultiplayerClient</c>（单机 / 服务端 / 子世界服务端）
	/// 才调 <see cref="Player.AddBuff(int, int)"/>；客户端这一段**完全不碰减益**，
	/// 只保留浮尘这种纯视觉。</item>
	/// <item><b>怎么到客户端</b>：⚠️ 这一条是 Cecil 反编译 <c>Terraria.dll</c> 核过的事实 ——
	/// 原版 <c>Player.AddBuff</c> **只在 <c>Main.netMode == 1</c>（客户端）时**发
	/// <c>MessageID.PlayerBuffs</c>（55 号包），而接收端在 <c>MessageBuffer.GetData</c> 里
	/// 只对 <c>netMode == 1 &amp;&amp; player == myPlayer</c> 调 <c>AddBuff(..., quiet: true)</c>。
	/// 也就是说「服务端自己 AddBuff 就会自动同步给客户端」**并不成立**（全库只有
	/// <c>Player.AddBuff</c> 一处发 55 号包）。所以服务端施加之后必须**自己补发一次**
	/// 55 号包，参数与 <c>Player.AddBuff</c> 内部那一次完全一致（whoAmI / buffType / buffTime）。</item>
	/// <item><b>重挂频率</b>：一次挂 <see cref="DebuffDuration"/>（90 tick = 1.5 秒）为上限，
	/// 只在**剩余时间 ≤ <see cref="RefreshThreshold"/>**（30 tick）时才续挂。
	/// 轻污染区（<c>t &lt; <see cref="HeavyThreshold"/></c>）续得更短（<see cref="LightDebuffDuration"/> = 45 tick），
	/// 于是 buff 会在两次续挂之间**真的掉掉一截**，平均掉血随之下降 —— 这就是"距离决定伤害"的落点。</item>
	/// </list>
	///
	/// <para/>为什么单独开一个 <see cref="ModPlayer"/> 而不是塞进 <c>WastelandPlayer</c>：
	/// 这块逻辑只服务壁炉，分开写以后合并别的分支时冲突面最小。
	/// </summary>
	public class FireplaceAtmospherePlayer : ModPlayer
	{
		/// <summary>
		/// 减益一次挂多久（帧）的上限。**1.5 秒**。
		///
		/// <para/>为什么是这个数：原来污染水那条路就是 90 帧（每帧补，等于一直挂着），
		/// 所以"离开水之后还会留 1.5 秒"的手感与改之前**完全一样**；
		/// 重污染区（中心附近）沿用这个值，等于"一直挂着"。
		/// </summary>
		public const int DebuffDuration = 90;

		/// <summary>
		/// **轻污染区**的续挂时长（帧）。45 tick = 0.75 秒，比 <see cref="RefreshThreshold"/> 只长一点点。
		///
		/// <para/>为什么：<see cref="Content.Buffs.GasPoison"/> 的伤害是 <c>lifeRegen -= 18</c>（约 9 HP/秒）
		/// 这种**固定值**，只跟"buff 在不在身上"有关、跟剩余时间无关。所以想让"离中心越远越轻"
		/// 真的体现在伤害上，唯一能让玩家尝到差别的做法就是**让 buff 在两次续挂之间断掉**：
		/// 45 - 30 = 15 tick 的空档（0.25 秒）→ 每 45 tick 里有 30 tick 在掉血，
		/// 平均伤害约为重污染区的 66%。重污染区续满 90 tick，中间没有空档（100%）。
		/// </summary>
		public const int LightDebuffDuration = 45;

		/// <summary>
		/// 剩余时间**少于**这个值才续挂（帧）。0.5 秒 —— 也就是每个玩家大约**每秒重挂一次**，
		/// 既不会掉 buff，也不会像"每帧调 AddBuff"那样把同步包刷成每帧一个。
		/// </summary>
		public const int RefreshThreshold = 30;

		/// <summary>
		/// 污染强度低于这个值时**完全不挂**有害气体。见 <see cref="PollutionIntensity"/> 的分段。
		///
		/// <para/>0.35 对应「离世界中心约 84% 半宽」的位置：也就是世界两侧各约 16% 宽的一条边带
		/// （世界宽 8400 时每侧约 670 格）是**可以自由呼吸**的 —— 玩家在那里能歇脚、能建前哨，
		/// 但离中心越近就越难受。
		/// </summary>
		public const float WeakThreshold = 0.35f;

		/// <summary>污染强度高于这个值算**重污染**（续满 <see cref="DebuffDuration"/>）。</summary>
		public const float HeavyThreshold = 0.7f;

		/// <summary>低于 <see cref="WeakThreshold"/> 的强度折算成"还剩下多少"。见 <see cref="PollutionIntensity"/>。</summary>
		private const float WeakScale = 0.3f;

		/// <summary>本帧是否戴着防毒面具（饰品在 <c>UpdateAccessory</c> 里置位）。</summary>
		public bool gasMaskEquipped;

		/// <summary>
		/// 本帧戴的是不是「防毒面具系」的任一件（面具 / 强化滤芯面罩 / 灰烬之心净界面罩）。
		///
		/// <para/>为什么单独记一个：<see cref="gasMaskEquipped"/> 是"本帧某一帧的饰品效果"，
		/// 而 <see cref="Content.NPCs.Town.MechanicalCompanion"/> 判断"她还要不要教你怎么做面具"
		/// 时读的是**上一帧结算完**的结果（NPC 对话发生在玩家更新之后）。
		/// 这里在 <see cref="PostUpdateEquips"/> 末尾做一次快照，把时序问题挡在外面。
		/// </summary>
		public bool anyFilterMaskEquipped;

		/// <summary>本帧算出来的污染强度（0~1）。给对话 / 调试用，权威侧与客户端都会算。</summary>
		public float pollutionStrength;

		public override void ResetEffects()
		{
			gasMaskEquipped = false;
		}

		public override void PostUpdateEquips()
		{
			bool inFireplace = !Player.dead && SubworldSystem.IsActive<FireplaceSubworld>();

			// 每一帧都重算：不在壁炉里就是 0（离开子世界后对话 / 调试读到的也是 0，不会留着旧值）
			pollutionStrength = inFireplace ? PollutionIntensity(Player.Center.X) : 0f;

			if (!inFireplace) {
				anyFilterMaskEquipped = false;
				return;
			}

			// 1) 减益：**服务端权威**。单人时这一支就是本地施加（与改之前的表现一致）；
			//    联机时服务端施加 + 显式广播，客户端只负责显示与结算原版 buff 效果。
			if (Main.netMode != NetmodeID.MultiplayerClient) {
				if (!gasMaskEquipped && pollutionStrength >= WeakThreshold) {
					// 强度越高续得越久：重污染区（> 0.7）等于常驻，轻污染区会一秒一秒地断。
					int duration = pollutionStrength > HeavyThreshold ? DebuffDuration : LightDebuffDuration;

					ApplyServerDebuff(Player, ModContent.BuffType<GasPoison>(), duration);
				}

				// 污染水：泡在水里额外挂污染（岩浆/蜂蜜不算）。与原实现完全一致 —— 水里就是水里，
				// 不受大气强度影响。
				if (Player.wet && !Player.lavaWet && !Player.honeyWet) {
					ApplyServerDebuff(Player, ModContent.BuffType<Pollution>(), DebuffDuration);
				}
			}

			// 2) 大气视觉：玩家附近飘灰绿色浮尘（纯视觉，客户端本地；服务端不产生 dust）。
			//    **密度随强度变化**：中心 6 路/帧、边缘 0.2 路/帧，见 VisualDustDensity。
			if (!Main.dedServ) {
				SpawnVisualDust(pollutionStrength);
			}

			// 3) 快照（放在最后：本帧所有饰品的 UpdateAccessory 都跑完了）
			anyFilterMaskEquipped = gasMaskEquipped;
		}

		/// <summary>
		/// **污染强度**：中心 = 1（最强），世界左右边缘 = <see cref="WeakScale"/>（几乎为 0）。
		///
		/// <para/>===== 公式 =====
		/// <code>
		/// offset = |x - (Main.maxTilesX / 2))|            // 离世界中心的水平距离（格）
		/// d      = offset / (Main.maxTilesX / 2)          // 归一化到 0（正中）~ 1（世界边缘）
		/// t0     = 1 - d                                  // 线性梯度：中心 1 → 边缘 0
		/// t      = WeakScale + (1 - WeakScale) * t0       // 映射到 0.3 ~ 1.0
		/// t      = t * t                                  // 平方：让"靠近中心"的压迫感集中在中段
		/// </code>
		///
		/// <para/>=== 为什么映射到 0.3 而不是 0，又为什么要平方 ===
		/// <list type="number">
		/// <item>映射到 0.3：世界边缘也不是"绝对干净"，而是"几乎不呛"（需求原话）；
		/// 强度永远不会掉到 0，将来想加"边缘也有一点点灰"的效果不用改公式；</item>
		/// <item>平方：线性梯度下"一半路程"就已经只剩一半强度，玩家会觉得"刚出门就好多了"；
		/// 平方之后 <c>d = 0.25</c>（走完四分之一）才掉到 0.7 以下，重污染区被拉成
		/// 「中心 ± 约 28% 半宽」的一块，中段（轻污染）变宽、边缘（干净）变窄 ——
		/// 也就是"越往外走变化越明显"。</item>
		/// </list>
		///
		/// <para/>分档（阈值都是常量，方便后续调）：
		/// <list type="bullet">
		/// <item><c>t &lt; 0.35</c>：**不挂**有害气体（干净带，约在 |d| &gt; 0.84，即世界两侧各约 16% 宽）；</item>
		/// <item><c>0.35 ≤ t ≤ 0.7</c>：轻（续挂 45 tick，两挂之间会断 15 tick）；</item>
		/// <item><c>t &gt; 0.7</c>：重（续挂 90 tick，常驻）。</item>
		/// </list>
		/// </summary>
		public static float PollutionIntensity(float worldX)
		{
			float halfWidth = Main.maxTilesX / 2f;

			if (halfWidth <= 0f) {
				return 1f;
			}

			float normalized = System.Math.Abs(worldX - halfWidth) / halfWidth;   // 0（正中）~ 1（边缘）

			if (normalized > 1f) {
				normalized = 1f;   // 防越界（理论上到不了）
			}

			float raw = WeakScale + (1f - WeakScale) * (1f - normalized);

			return raw * raw;
		}

		/// <summary>
		/// 浮尘的**每帧路数**：中心 6 路、边缘 0.2 路。
		///
		/// <para/>为什么不做成"每路一个 <c>Main.rand.NextBool(p)</c>"：<c>NextBool</c> 的概率是
		/// <c>1/p</c> 这种整数倒数，表达不了 0.2 这种小数。所以这里由**调用方**取一次
		/// <c>[0,1)</c> 随机数，再按这条曲线决定本帧喷几路 —— 期望路数正比于强度，
		/// 两端分别是 6 与 0.2，符合"中心浓、边缘几乎看不见"。
		/// </summary>
		private static float VisualDustDensity(float intensity)
		{
			// 视觉上不要真的归零：边缘那一条干净带也留 0.2 路，偶尔一颗浮尘才不像"世界没做完"
			const float minDensity = 0.2f;
			const float maxDensity = 6f;

			if (intensity <= 0f) {
				return minDensity;
			}

			if (intensity >= 1f) {
				return maxDensity;
			}

			return minDensity + (maxDensity - minDensity) * intensity;
		}

		/// <summary>
		/// 按强度喷灰绿浮尘。纯客户端视觉（调用方已经判过 <c>Main.dedServ</c>）。
		/// <para/>实例方法（不是 static）：浮尘要围着**本玩家** <c>Player.Center</c> 生成。
		/// </summary>
		private void SpawnVisualDust(float intensity)
		{
			float density = VisualDustDensity(intensity);

			// 整数部分一定喷，小数部分按概率再喷一路 —— 这样密度可以是小数（0.2 这种也能表达）
			int guaranteed = (int)density;

			if (Main.rand.NextFloat() < density - guaranteed) {
				guaranteed++;
			}

			for (int i = 0; i < guaranteed; i++) {
				Vector2 position = Player.Center + Main.rand.NextVector2Circular(320f, 240f);

				if (WorldPaint.HasTile((int)(position.X / 16f), (int)(position.Y / 16f))) {
					continue;
				}

				Dust dust = Dust.NewDustDirect(position, 2, 2, DustID.Smoke);
				dust.velocity = Main.rand.NextVector2Circular(0.4f, 0.4f);
				dust.noGravity = true;
				dust.scale = 1.1f;
				dust.color = new Color(148, 168, 124);
				dust.alpha = 60;
			}
		}

		/// <summary>
		/// 服务端（含单机）施加 / 续挂一个减益，并在联机时把它显式同步给该玩家的客户端。
		///
		/// <para/>续挂判定用**剩余时间**而不是"有没有"：<c>Player.AddBuff</c> 一旦发现这个 buff
		/// 已经存在就会走 <c>AddBuff_TryUpdatingExistingBuffTime</c> 直接 return（IL 已核），
		/// 所以每帧调用既不会延长时间也不会发包，但也没有意义 —— 这里按 <see cref="RefreshThreshold"/>
		/// 把它压成"每秒一次"。
		///
		/// <para/>⚠️ 续挂时长按强度分两档（<see cref="DebuffDuration"/> / <see cref="LightDebuffDuration"/>），
		/// 但**续挂判定本身**仍然是同一个 <see cref="RefreshThreshold"/>：
		/// 这样"轻污染区掉血是断断续续的"这件事，完全由"挂的时间比阈值长不了多少"自然产生，
		/// 不需要第二套计时器。
		/// </summary>
		private static void ApplyServerDebuff(Player player, int buffType, int duration)
		{
			if (buffType <= 0) {
				return;
			}

			int index = player.FindBuffIndex(buffType);

			if (index >= 0 && player.buffTime[index] > RefreshThreshold) {
				return;   // 还够久，不重挂（这是"不刷包"的关键）
			}

			player.AddBuff(buffType, duration);

			// 服务端自己加 buff 不会自动广播（见类注释第 2 条），这里补一次原版的 buff 同步包：
			// 参数顺序与 Player.AddBuff 内部那次 SendData(55, ...) 完全一致。
			if (Main.netMode == NetmodeID.Server) {
				NetMessage.SendData(MessageID.PlayerBuffs, -1, -1, null, player.whoAmI, buffType, duration);
			}
		}
	}
}
