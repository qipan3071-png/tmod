using Terraria;
using Terraria.GameContent.ItemDropRules;
using Terraria.ModLoader;
using WastelandSoul.Content.NPCs.Bosses.Scavenger;

namespace WastelandSoul.Content.Items.Weapons.Boss1Scavenger.ScavengerDrops
{
	/// <summary>
	/// 清道夫掉落接线：把四把 B 线武器（掉落专属、**没有配方**）塞进清道夫的掉落表。
	/// <para/>纪律（照 <c>Content\Items\Weapons\Rust\RustPackLoot.cs</c> 的既有写法）：
	/// <list type="bullet">
	/// <item>用 <see cref="GlobalNPC"/> **只追加**规则，不动 <c>Scavenger.cs</c> 里已有的
	/// 「掉落袋 + 10% 奖杯」规则，也不碰别人正在改的朝向 / 背景墙代码；</item>
	/// <item>四把各 25% 独立判定 —— 一次正常击败大约能摸到 1 把，
	/// 掉落袋里的 A 线（可合成）武器不受影响。</item>
	/// </list>
	/// </summary>
	public class ScavengerDropLootNPC : GlobalNPC
	{
		public override void ModifyNPCLoot(NPC npc, NPCLoot npcLoot)
		{
			if (npc.type != ModContent.NPCType<Scavenger>()) {
				return;
			}

			// 1/4 = 25%，四把各自独立判定
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<ScavengerGreatblade>(), 4));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<SteelDischarger>(), 4));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<PollutionCannon>(), 4));
			npcLoot.Add(ItemDropRule.Common(ModContent.ItemType<SteelBow>(), 4));
		}
	}
}
