using InnoVault.StateMachines;
using Terraria;

namespace WastelandSoul.Content.NPCs.Bosses.Archivist
{
	/// <summary>待机：坐在杖上漂。倒计时结束后按阶段出招。</summary>
	[VaultState(0, typeof(ArchivistContext))]
	public class ArchivistIdleState : VaultState<ArchivistContext>
	{
		public override string StateName => "待机";

		public override void OnEnter(VaultStateMachine<ArchivistContext> machine, ArchivistContext ctx)
		{
			base.OnEnter(machine, ctx);
			ctx.AttackDelay = Archivist.RollAttackDelay(ctx);
			Archivist.SetAnim(ctx.Npc, Archivist.AnimIdle);
		}

		public override IVaultState<ArchivistContext> OnUpdate(VaultStateMachine<ArchivistContext> machine, ArchivistContext ctx)
		{
			base.OnUpdate(machine, ctx);
			Archivist.Hover(ctx, Archivist.HoverDefault);
			return Timer >= ctx.AttackDelay ? Archivist.ChooseNextState(ctx) : null;
		}
	}

	/// <summary>50% 切二阶段：挂翅膀灼烧，然后回待机。</summary>
	[VaultState(1, typeof(ArchivistContext))]
	public class ArchivistPhaseTwoState : VaultState<ArchivistContext>
	{
		public override string StateName => "二阶段";

		public override void OnEnter(VaultStateMachine<ArchivistContext> machine, ArchivistContext ctx)
		{
			base.OnEnter(machine, ctx);
			Archivist.OnPhaseStart(ctx.Npc, 1);
			Archivist.ApplyWingBurn();
		}

		public override IVaultState<ArchivistContext> OnUpdate(VaultStateMachine<ArchivistContext> machine, ArchivistContext ctx)
		{
			base.OnUpdate(machine, ctx);
			ctx.Npc.velocity *= 0.9f;
			Archivist.SetAnim(ctx.Npc, Archivist.AnimTelegraph);
			return Timer >= 50 ? new ArchivistIdleState() : null;
		}
	}

	/// <summary>大火球：眼罩红光前兆后朝玩家当时方向飞出。</summary>
	[VaultState(2, typeof(ArchivistContext))]
	public class ArchivistFireballState : VaultState<ArchivistContext>
	{
		private bool fired;

		public override string StateName => "大火球";

		public override void OnEnter(VaultStateMachine<ArchivistContext> machine, ArchivistContext ctx)
		{
			fired = false;
			base.OnEnter(machine, ctx);
			Archivist.PlayCastSound(ctx.Npc);
			Archivist.SetAnim(ctx.Npc, Archivist.AnimTelegraph);
			ctx.Npc.velocity *= 0.4f;
		}

		public override IVaultState<ArchivistContext> OnUpdate(VaultStateMachine<ArchivistContext> machine, ArchivistContext ctx)
		{
			base.OnUpdate(machine, ctx);
			Archivist.Hover(ctx, Archivist.HoverDefault);

			if (Timer < Archivist.TelegraphTicks) {
				Archivist.SetAnim(ctx.Npc, Archivist.AnimTelegraph);
				return null;
			}

			Archivist.SetAnim(ctx.Npc, Archivist.AnimAttack);

			if (!fired && Timer >= Archivist.TelegraphTicks) {
				fired = true;
				Archivist.SpawnFireball(ctx);
			}

			return Timer >= Archivist.TelegraphTicks + 24 ? new ArchivistIdleState() : null;
		}
	}

	/// <summary>火墙：高 256 格，同时最多两道。</summary>
	[VaultState(3, typeof(ArchivistContext))]
	public class ArchivistFirePillarState : VaultState<ArchivistContext>
	{
		private bool fired;

		public override string StateName => "火柱";

		public override void OnEnter(VaultStateMachine<ArchivistContext> machine, ArchivistContext ctx)
		{
			fired = false;
			base.OnEnter(machine, ctx);
			Archivist.PlayCastSound(ctx.Npc);
			Archivist.SetAnim(ctx.Npc, Archivist.AnimTelegraph);
			ctx.Npc.velocity *= 0.4f;
		}

		public override IVaultState<ArchivistContext> OnUpdate(VaultStateMachine<ArchivistContext> machine, ArchivistContext ctx)
		{
			base.OnUpdate(machine, ctx);
			Archivist.Hover(ctx, Archivist.HoverDefault);

			if (Timer < Archivist.TelegraphTicks) {
				Archivist.SetAnim(ctx.Npc, Archivist.AnimTelegraph);
				return null;
			}

			Archivist.SetAnim(ctx.Npc, Archivist.AnimAttack);

			if (!fired && Timer >= Archivist.TelegraphTicks) {
				fired = true;
				Archivist.SpawnFirePillars(ctx);
			}

			return Timer >= Archivist.TelegraphTicks + 20 ? new ArchivistIdleState() : null;
		}
	}

	/// <summary>毒液弹：自身一圈打出，跟踪 3 秒。</summary>
	[VaultState(4, typeof(ArchivistContext))]
	public class ArchivistVenomState : VaultState<ArchivistContext>
	{
		private bool fired;

		public override string StateName => "毒液弹";

		public override void OnEnter(VaultStateMachine<ArchivistContext> machine, ArchivistContext ctx)
		{
			fired = false;
			base.OnEnter(machine, ctx);
			Archivist.PlayCastSound(ctx.Npc);
			Archivist.SetAnim(ctx.Npc, Archivist.AnimTelegraph);
			ctx.Npc.velocity *= 0.45f;
		}

		public override IVaultState<ArchivistContext> OnUpdate(VaultStateMachine<ArchivistContext> machine, ArchivistContext ctx)
		{
			base.OnUpdate(machine, ctx);
			Archivist.Hover(ctx, Archivist.HoverDefault);

			if (Timer < Archivist.TelegraphTicks) {
				Archivist.SetAnim(ctx.Npc, Archivist.AnimTelegraph);
				return null;
			}

			Archivist.SetAnim(ctx.Npc, Archivist.AnimAttack);

			if (!fired && Timer >= Archivist.TelegraphTicks) {
				fired = true;
				Archivist.SpawnVenomRing(ctx);
			}

			return Timer >= Archivist.TelegraphTicks + 18 ? new ArchivistIdleState() : null;
		}
	}

	/// <summary>开始 25 秒冒泡，然后立刻回待机，期间还能出别的招。</summary>
	[VaultState(5, typeof(ArchivistContext))]
	public class ArchivistBubbleStormState : VaultState<ArchivistContext>
	{
		private bool fired;

		public override string StateName => "水泡";

		public override void OnEnter(VaultStateMachine<ArchivistContext> machine, ArchivistContext ctx)
		{
			fired = false;
			base.OnEnter(machine, ctx);
			Archivist.PlayCastSound(ctx.Npc);
			Archivist.SetAnim(ctx.Npc, Archivist.AnimTelegraph);
			ctx.Npc.velocity *= 0.45f;
		}

		public override IVaultState<ArchivistContext> OnUpdate(VaultStateMachine<ArchivistContext> machine, ArchivistContext ctx)
		{
			base.OnUpdate(machine, ctx);
			Archivist.Hover(ctx, Archivist.HoverDefault);

			if (Timer < Archivist.TelegraphTicks) {
				Archivist.SetAnim(ctx.Npc, Archivist.AnimTelegraph);
				return null;
			}

			Archivist.SetAnim(ctx.Npc, Archivist.AnimAttack);

			if (!fired && Timer >= Archivist.TelegraphTicks) {
				fired = true;
				Archivist.StartBubbleStorm(ctx);
			}

			return Timer >= Archivist.TelegraphTicks + 12 ? new ArchivistIdleState() : null;
		}
	}
}
