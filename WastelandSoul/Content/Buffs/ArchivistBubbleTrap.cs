using Terraria;
using Terraria.ModLoader;

namespace WastelandSoul.Content.Buffs
{
	/// <summary>水泡困住 1.2 秒：不能走、不能跳。</summary>
	public class ArchivistBubbleTrap : ModBuff
	{
		public override void SetStaticDefaults()
		{
			Main.debuff[Type] = true;
			Main.buffNoSave[Type] = true;
			Main.pvpBuff[Type] = false;
		}

		public override void Update(Player player, ref int buffIndex)
		{
			player.velocity *= 0f;
			player.controlJump = false;
			player.controlLeft = false;
			player.controlRight = false;
			player.controlUp = false;
			player.controlDown = false;
			player.controlUseItem = false;
			player.controlUseTile = false;
			player.wingTime = 0f;
		}
	}
}
