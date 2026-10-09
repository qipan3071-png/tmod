using System.Collections.Generic;
using SubworldLibrary;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Content.Subworlds;

namespace WastelandSoul.Common.Systems
{
	/// <summary>
	/// **壁炉前期引导**：骷髅王之后的"该去壁炉了"提示，以及"没戴防毒面具进壁炉会被毒气逼回来"。
	///
	/// <para/>=== 为什么单独开一个 <see cref="ModSystem"/> ===
	/// 世界级剧情的权威在 <see cref="WastelandStorySystem"/>（本轮**不许动**），
	/// 而这两件事都是"环境反馈"而不是"剧情推进"：它们不改任何剧情标志位、
	/// 不参与 <c>PacketKindStory</c> 的 15 个 bool 同步，删掉它们主线照样能走完。
	/// 放在这里以后与剧情层的合并冲突面最小。
	///
	/// <para/>=== 三件事（玩家要求逐条对应） ===
	/// <list type="number">
	/// <item><b>骷髅王后的提示</b>：本世界**首次** <c>NPC.downedBoss3</c> 变 true 那一帧，
	/// 公告"壁炉在等你 / 入口在主世界两侧的海洋边"。
	/// 只在**权威侧**（<c>netMode != MultiplayerClient</c>）判定一次 ——
	/// 客户端那侧 <c>NPC.downedBoss3</c> 也会被原版同步，但"公告"这件事广播一次就够了，
	/// 两边都判会有重复播报的风险。判定用 **边沿触发**（<c>lastDownedBoss3 == false &amp;&amp; 现在为 true</c>），
	/// 不是电平触发，所以不会每帧刷屏；世界存档里 <c>downedBoss3</c> 本来就是持久化的，
	/// 重进存档时它一上来就是 true → 边沿不成立 → 不会重复播。</item>
	/// <item><b>没有防毒面具不阻止进门</b>：这一条**不需要写代码** ——
	/// 壁炉门（<c>FireplaceGateSystem</c> / <c>FireplaceTravelNet</c>）从来没有查过面罩，
	/// 本轮也没有给它加任何前置。玩家照样进得去。</item>
	/// <item><b>进去之后被毒气逼回来</b>：<b>权威侧</b>发现"人在壁炉子世界里 + 没戴面具 +
	/// 进门已经过了 <see cref="GraceTicks"/> 的缓冲"就把他送回主世界，并公告原因；
	/// 随后 <see cref="EjectCooldownTicks"/>（30 秒）内不再重复赶 ——
	/// 否则玩家一抬脚进门就被弹出去，只会觉得"门坏了"，而不是"我缺一副面具"。
	/// 送回用的是 **SubworldLibrary 的公开 API <c>SubworldSystem.MovePlayerToMainWorld(whoAmI)</c>**
	/// （与 <c>FireplaceTravelNet.TravelProtocol.MoveToMainWorld</c> 同一支；那边是右键返回门用的），
	/// **只在权威侧调用**：SLL 2.3.0.1 的 IL 开头就有
	/// <c>if (netMode == 1 || (netMode == 2 &amp;&amp; current != null)) return;</c>，
	/// 客户端上这个方法是空操作，所以必须由服务端（子世界服务端进程本身就是 <c>netMode == 2</c>
	/// 且 <c>current != null</c>，是"真有权威"的那一侧）来赶人。
	/// <b>单人同样成立</b>：<c>netMode == 0</c> 时守卫不成立，本机直接执行，
	/// 表现为"进门几秒后被弹回出生点"。</item>
	/// </list>
	///
	/// <para/>=== 联机分工（一句话） ===
	/// 判定与移动**全在权威侧**（单机 / 服务端 / 子世界服务端进程）；
	/// 客户端一格状态都不写，也不发任何请求包（所以本轮**没有新增任何模组包**）。
	/// </summary>
	public class FireplaceWarningSystem : ModSystem
	{
		/// <summary>
		/// 进壁炉之后的**缓冲帧数**（300 tick = 5 秒）。
		///
		/// <para/>为什么要有它：玩家要求的是"让他**亲身体验**到必须戴面具"。
		/// 一进门就被弹回去，体验到的只是"门有问题"；先让他站在灰绿的浮尘里、
		/// 看着自己掉几秒血，再被逼回来并被告知原因，才能真正把"面具"和"壁炉"连起来。
		/// 5 秒也足够他看清污染梯度（靠近中心浮尘明显变浓）。
		/// </summary>
		private const int GraceTicks = 60 * 5;

		/// <summary>
		/// 被赶回之后的冷却（1800 tick = 30 秒）。这 30 秒内**不再赶他**。
		///
		/// <para/>为什么必须有：没有冷却的话"进门 → 被弹回 → 再进门 → 再被弹回"会变成死循环，
		/// 玩家在门口反复被扔回出生点，连"我想再看看里面长什么样"都做不到。
		/// 30 秒足够他跑回来、戴上面具（或者干脆换个地方待着），又不至于长到忘记被赶过。
		/// </summary>
		private const int EjectCooldownTicks = 60 * 30;

		/// <summary>某个玩家"已经在壁炉里待了多少帧"（键 = 玩家槽位）与"下一次允许被赶在什么时候"。</summary>
		private sealed class VisitorState
		{
			/// <summary>已经在壁炉里连续待了多少帧。</summary>
			public int StayTicks;

			/// <summary>冷却：这个值 &gt; 0 时这一帧不许赶人（每帧递减）。</summary>
			public int Cooldown;
		}

		/// <summary>
		/// 服务端/单机的判定状态。**不参与同步也不存档** —— 它是纯粹的"过程状态"：
		/// 读档 / 重连之后就当"他刚进门"，从头开始计时（最坏结果是多给 5 秒缓冲，无害）。
		/// </summary>
		private static readonly Dictionary<int, VisitorState> visitors = new Dictionary<int, VisitorState>();

		/// <summary>上一帧的 <c>NPC.downedBoss3</c>：只为"首次击败"做边沿触发，见类注释第 1 条。</summary>
		private static bool lastDownedBoss3;

		/// <summary>本存档这一轮（本次进程）已经播过"去壁炉"的提示。</summary>
		private static bool skeletonHintShown;

		public override void OnWorldLoad()
		{
			visitors.Clear();
			lastDownedBoss3 = false;
			skeletonHintShown = false;
		}

		public override void OnWorldUnload()
		{
			visitors.Clear();
			lastDownedBoss3 = false;
			skeletonHintShown = false;
		}

		public override void PostUpdateWorld()
		{
			if (Main.gameMenu) {
				return;
			}

			// 客户端只保留"我在不在壁炉里"这个只读记忆，什么都不做（世界与玩家的改动一律不在客户端发生）
			if (Main.netMode == NetmodeID.MultiplayerClient) {
				lastDownedBoss3 = NPC.downedBoss3;
				return;
			}

			UpdateSkeletonHint();
			UpdateVisitors();
		}

		/// <summary>
		/// 骷髅王后的提示。**边沿触发**：只有"上一帧还没有、这一帧有了"才播一次。
		///
		/// <para/>⚠️ 只在**主世界**判：子世界服务端是另一个进程，它的 <c>NPC.downedBoss3</c>
		/// 不随主世界同步（那是"另一个世界的存档内存"），不挡住的话在壁炉里会白播一次。
		/// </summary>
		private static void UpdateSkeletonHint()
		{
			bool downed = NPC.downedBoss3;

			if (downed && !lastDownedBoss3 && !skeletonHintShown && !SubworldSystem.IsActive<FireplaceSubworld>()) {
				skeletonHintShown = true;

				// 服务端→全体广播 / 单机本地显示，与其它世界事件公告同一条路（AnnounceFormat 内部判 netMode）
				WastelandStorySystem.Announce("Mods.WastelandSoul.Messages.SkeletronFireplaceHint",
					new Microsoft.Xna.Framework.Color(226, 200, 120));
			}

			lastDownedBoss3 = downed;
		}

		/// <summary>
		/// 逐个玩家：在壁炉里 + 没戴面具 + 熬过缓冲 → 送回主世界（带冷却）。
		///
		/// <para/>"有没有面具"读的是 <see cref="FireplaceAtmospherePlayer.gasMaskEquipped"/> ——
		/// 也就是**全库唯一那条通路**（<c>GasMask</c> 与两件升级面罩的
		/// <c>UpdateWastelandAccessory</c> 都置它，防毒面具系的判定不许再有第二套）。
		/// 饰品槽本身是原版 <c>MessageID.SyncEquipment</c> 同步的，所以服务端的镜像槽位是准的，
		/// 服务端这一侧同样能读到这个字段。
		/// </summary>
		private static void UpdateVisitors()
		{
			bool inFireplace = SubworldSystem.IsActive<FireplaceSubworld>();

			for (int i = 0; i < Main.maxPlayers; i++) {
				Player player = Main.player[i];

				if (player == null || !player.active || player.dead) {
					visitors.Remove(i);
					continue;
				}

				if (!inFireplace) {
					// 回了主世界：清掉"待了多久"，但**冷却按真实时间继续走**（否则卡在门口反复横跳就没有冷却了）
					if (visitors.TryGetValue(i, out VisitorState outside)) {
						outside.StayTicks = 0;

						if (outside.Cooldown > 0) {
							outside.Cooldown--;
						}

						// 冷却走完、人又不在壁炉里 → 这条记录没有意义了，清掉（别让它一直挂着）
						if (outside.Cooldown <= 0) {
							visitors.Remove(i);
						}
					}

					continue;
				}

				if (!visitors.TryGetValue(i, out VisitorState state)) {
					// 刚发现他在壁炉里（进门 / 重连 / 读档）：重新开始计时
					state = new VisitorState { StayTicks = 0, Cooldown = 0 };
					visitors[i] = state;
				}

				if (state.Cooldown > 0) {
					state.Cooldown--;
					continue;
				}

				bool masked = player.GetModPlayer<FireplaceAtmospherePlayer>().gasMaskEquipped;

				if (masked) {
					state.StayTicks = 0;   // 戴上面具就重新计时，摘下来之后又是完整 5 秒
					continue;
				}

				state.StayTicks++;

				if (state.StayTicks < GraceTicks) {
					continue;
				}

				EjectToMainWorld(player);
				state.StayTicks = 0;
				state.Cooldown = EjectCooldownTicks;
			}
		}

		/// <summary>
		/// 把一个玩家从壁炉送回主世界，并公告原因。
		///
		/// <para/>⚠️ <c>SubworldSystem.MovePlayerToMainWorld(whoAmI)</c> 是本仓库已核过的 SLL 2.3.0.1
		/// 公开签名（见 <c>FireplaceTravelNet</c> 类注释里的签名清单），与"右键返回门"走的是同一个方法。
		/// 包一层 try/catch 只是为了让 SLL 的意外状态只丢一条日志、不影响其它玩家。
		/// </summary>
		private static void EjectToMainWorld(Player player)
		{
			try {
				SubworldSystem.MovePlayerToMainWorld(player.whoAmI);
			}
			catch (System.Exception exception) {
				ModLoader.GetMod("WastelandSoul")?.Logger?.Warn(
					"FireplaceWarningSystem: MovePlayerToMainWorld 失败（玩家 " + player.whoAmI + "）："
					+ exception.GetType().Name + ": " + exception.Message);
				return;
			}

			WastelandStorySystem.Announce("Mods.WastelandSoul.Messages.GasMaskForcedBack",
				new Microsoft.Xna.Framework.Color(200, 226, 140));
		}
	}
}
