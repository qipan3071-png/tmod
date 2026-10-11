using System.Collections.Generic;
using InnoVault.StateMachines;
using Microsoft.Xna.Framework;
using Terraria;

namespace WastelandSoul.Content.NPCs.Bosses.Archivist
{
	/// <summary>
	/// 归档者上下文。一只 NPC 一份。
	/// ai[0] 阶段（0 火 / 1 植物水），ai[1] 状态机，ai[2] 出招计数，ai[3] 动画（0 待机 / 1 前兆 / 2 攻击）。
	/// </summary>
	public class ArchivistContext : INpcStateContext
	{
		public const int AiSlot = 1;
		public const int BurstWindow = 60;

		private static readonly Dictionary<int, ArchivistContext> Cache = new Dictionary<int, ArchivistContext>();

		public NPC Npc { get; }

		public NpcStateMachine<ArchivistContext> Machine { get; private set; }

		public Player Target { get; set; }

		public int AttackDelay { get; set; }

		public Vector2 ArenaCenter { get; set; }

		public bool ArenaReady { get; set; }

		public int HealCooldown { get; set; }

		public int BurstCursor { get; set; }

		public readonly int[] BurstWindowDamage = new int[BurstWindow];

		private ArchivistContext(NPC npc)
		{
			Npc = npc;
		}

		public static ArchivistContext For(NPC npc)
		{
			if (!Cache.TryGetValue(npc.whoAmI, out ArchivistContext context) || context.Npc != npc) {
				context = new ArchivistContext(npc);
				context.Machine = new NpcStateMachine<ArchivistContext>(context, AiSlot);
				context.Machine.SetInitialState(new ArchivistIdleState());
				PhaseController.For(context.Machine)
					.OnHpBelow(c => (float)c.Npc.life / c.Npc.lifeMax, Archivist.PhaseTwoThreshold, () => new ArchivistPhaseTwoState(), label: "阶段二")
					.Apply();
				Cache[npc.whoAmI] = context;
			}

			return context;
		}

		public static void Release(int whoAmI)
		{
			Cache.Remove(whoAmI);
		}

		public static void Clear()
		{
			Cache.Clear();
		}

		public void TickBurstWindow()
		{
			BurstCursor = (BurstCursor + 1) % BurstWindow;
			BurstWindowDamage[BurstCursor] = 0;

			if (HealCooldown > 0) {
				HealCooldown--;
			}
		}

		public void AddBurstDamage(int damage)
		{
			if (damage > 0) {
				BurstWindowDamage[BurstCursor] += damage;
			}
		}

		public int BurstSum()
		{
			int sum = 0;

			for (int i = 0; i < BurstWindow; i++) {
				sum += BurstWindowDamage[i];
			}

			return sum;
		}
	}
}
