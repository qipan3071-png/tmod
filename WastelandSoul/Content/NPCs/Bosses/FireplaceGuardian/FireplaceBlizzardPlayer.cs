using Terraria;
using Terraria.ModLoader;

namespace WastelandSoul.Content.NPCs.Bosses.FireplaceGuardian
{
	/// <summary>
	/// 二阶段在每帧更新末尾把环境标成雪地，并打开原版暴风雪画面。
	/// 守卫不在二阶段时不再改写，下一帧游戏会按方块把生物群系算回去。
	/// </summary>
	public class FireplaceBlizzardPlayer : ModPlayer
	{
		private bool _forced;

		public override void PostUpdate()
		{
			bool on = FireplaceGuardian.BlizzardLiving();

			if (on) {
				_forced = true;
				Player.ZoneSnow = true;

				if (!Main.dedServ) {
					Player.ManageSpecialBiomeVisuals("Blizzard", true, Player.Center);
				}

				return;
			}

			if (!_forced || Main.dedServ) {
				_forced = false;
				return;
			}

			_forced = false;
			Player.ManageSpecialBiomeVisuals("Blizzard", false, Player.Center);
		}
	}
}
