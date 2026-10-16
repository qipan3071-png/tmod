using InnoVault.StateMachines;
using Microsoft.Xna.Framework;
using Terraria.Audio;
using Terraria.ID;
using WastelandSoul.Common.Effects;

namespace WastelandSoul.Content.NPCs.Bosses.FireplaceGuardian
{
	[VaultState(0, typeof(FireplaceGuardianContext))]
	public class FireplaceGuardianIdleState : VaultState<FireplaceGuardianContext>
	{
		public override string StateName => "炉心待机";

		public override void OnEnter(VaultStateMachine<FireplaceGuardianContext> machine, FireplaceGuardianContext ctx)
		{
			base.OnEnter(machine, ctx);
			ctx.AttackDelay = FireplaceGuardian.RollAttackDelay(ctx);
			ctx.Npc.localAI[0] = 0f;
			ctx.Npc.damage = FireplaceGuardian.ContactDamage;
			ctx.Npc.defDamage = FireplaceGuardian.ContactDamage;
		}

		public override IVaultState<FireplaceGuardianContext> OnUpdate(VaultStateMachine<FireplaceGuardianContext> machine, FireplaceGuardianContext ctx)
		{
			base.OnUpdate(machine, ctx);
			FireplaceGuardian.Hover(ctx, FireplaceGuardian.HoverDefault);
			return Timer >= ctx.AttackDelay ? FireplaceGuardian.ChooseNextState(ctx) : null;
		}
	}

	[VaultState(1, typeof(FireplaceGuardianContext))]
	public class FireplaceGuardianPhaseTwoState : VaultState<FireplaceGuardianContext>
	{
		public override string StateName => "阶段二·暴风雪";

		public override void OnEnter(VaultStateMachine<FireplaceGuardianContext> machine, FireplaceGuardianContext ctx)
		{
			base.OnEnter(machine, ctx);
			FireplaceGuardian.OnPhaseStart(ctx.Npc, 1);
		}

		public override IVaultState<FireplaceGuardianContext> OnUpdate(VaultStateMachine<FireplaceGuardianContext> machine, FireplaceGuardianContext ctx)
		{
			base.OnUpdate(machine, ctx);
			ctx.Npc.velocity *= 0.92f;
			return Timer >= 44 ? new FireplaceGuardianIdleState() : null;
		}
	}

	[VaultState(2, typeof(FireplaceGuardianContext))]
	public class FireplaceGuardianSweepState : VaultState<FireplaceGuardianContext>
	{
		private bool _fired;

		public override string StateName => "横扫";

		public override void OnEnter(VaultStateMachine<FireplaceGuardianContext> machine, FireplaceGuardianContext ctx)
		{
			_fired = false;
			base.OnEnter(machine, ctx);
			ctx.Npc.localAI[0] = 0f;

			if (!Terraria.Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item1, ctx.Npc.Center);
			}
		}

		public override IVaultState<FireplaceGuardianContext> OnUpdate(VaultStateMachine<FireplaceGuardianContext> machine, FireplaceGuardianContext ctx)
		{
			base.OnUpdate(machine, ctx);
			FireplaceGuardian.Hover(ctx, FireplaceGuardian.HoverDefault);

			if (!_fired && Timer >= FireplaceGuardian.SweepWindup) {
				_fired = true;
				FireplaceGuardian.SpawnSweep(ctx);
			}

			return Timer >= FireplaceGuardian.SweepWindup + 50 ? new FireplaceGuardianIdleState() : null;
		}
	}

	[VaultState(3, typeof(FireplaceGuardianContext))]
	public class FireplaceGuardianSwordQiState : VaultState<FireplaceGuardianContext>
	{
		private bool _fired;

		public override string StateName => "竖直剑气";

		public override void OnEnter(VaultStateMachine<FireplaceGuardianContext> machine, FireplaceGuardianContext ctx)
		{
			_fired = false;
			base.OnEnter(machine, ctx);
			ctx.Npc.localAI[0] = 0f;

			if (!Terraria.Main.dedServ) {
				SoundEngine.PlaySound(SoundID.Item28, ctx.Npc.Center);
			}
		}

		public override IVaultState<FireplaceGuardianContext> OnUpdate(VaultStateMachine<FireplaceGuardianContext> machine, FireplaceGuardianContext ctx)
		{
			base.OnUpdate(machine, ctx);
			FireplaceGuardian.Hover(ctx, FireplaceGuardian.HoverHigh);

			if (!_fired && Timer >= FireplaceGuardian.SwordQiWindup) {
				_fired = true;
				FireplaceGuardian.SpawnSwordQi(ctx);
			}

			return Timer >= FireplaceGuardian.SwordQiWindup + 40 ? new FireplaceGuardianIdleState() : null;
		}
	}

	[VaultState(4, typeof(FireplaceGuardianContext))]
	public class FireplaceGuardianDashState : VaultState<FireplaceGuardianContext>
	{
		private bool _fired;

		public override string StateName => "暴雪冲刺";

		public override void OnEnter(VaultStateMachine<FireplaceGuardianContext> machine, FireplaceGuardianContext ctx)
		{
			_fired = false;
			base.OnEnter(machine, ctx);
			ctx.Npc.localAI[0] = 0f;
			ctx.Npc.velocity *= 0.2f;
		}

		public override IVaultState<FireplaceGuardianContext> OnUpdate(VaultStateMachine<FireplaceGuardianContext> machine, FireplaceGuardianContext ctx)
		{
			base.OnUpdate(machine, ctx);

			if (Timer < FireplaceGuardian.DashWindup) {
				ctx.Npc.velocity *= 0.8f;
				return null;
			}

			if (!_fired && Timer >= FireplaceGuardian.DashWindup) {
				_fired = true;
				ctx.Npc.localAI[0] = 1f;
				ctx.Npc.damage = FireplaceGuardian.DashDamage;
				ctx.Npc.defDamage = FireplaceGuardian.DashDamage;
				FireplaceGuardian.DashTowards(ctx);

				if (!Terraria.Main.dedServ) {
					SoundEngine.PlaySound(SoundID.Item14, ctx.Npc.Center);
					WastelandFxSystem.Impact(ctx.Npc.Center, new Color(176, 220, 255), 1.15f);
				}
			}

			if (Timer % 5 == 0) {
				FireplaceGuardian.StrikeDash(ctx.Npc);
			}

			return Timer >= FireplaceGuardian.DashWindup + FireplaceGuardian.DashTicks
				? new FireplaceGuardianIdleState()
				: null;
		}
	}
}
