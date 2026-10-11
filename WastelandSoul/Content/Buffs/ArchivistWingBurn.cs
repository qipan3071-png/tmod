using Terraria;
using Terraria.ModLoader;

namespace WastelandSoul.Content.Buffs
{
	/// <summary>切二阶段挂上：翅膀剩余飞行时间上限变成 2/3，打完才掉。没有伤害。</summary>
	public class ArchivistWingBurn : ModBuff
	{
		public override void SetStaticDefaults()
		{
			Main.debuff[Type] = true;
			Main.buffNoSave[Type] = true;
			Main.pvpBuff[Type] = false;
		}

		public override void Update(Player player, ref int buffIndex)
		{
			float cap = player.wingTimeMax * (2f / 3f);

			if (player.wingTime > cap) {
				player.wingTime = cap;
			}
		}
	}
}
