using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace WastelandSoul.Content.NPCs.Bosses.AshHeart
{
	/// <summary>
	/// 灰烬残灵：只在阶段二给灰烬之心续燃，不打玩家。阶段三开始后自行散掉。
	/// </summary>
	public class AshWisp : ModNPC
	{
		// 本体血量从 34000 定档到 28000 之后，两条残灵（45 帧一次、每次 80）相对回血变强，
		// 这里同步压到 50 帧 / 70 点：仍然必须清残灵，但不至于把玩家的伤害全吃掉。
		private const int HealInterval = 50;
		private const int HealAmount = 70;

		public override void SetStaticDefaults()
		{
			Main.npcFrameCount[Type] = 4;
			NPCID.Sets.MPAllowedEnemies[Type] = true;
		}

		public override void SetDefaults()
		{
			NPC.width = 30;
			NPC.height = 26;
			NPC.aiStyle = -1;
			NPC.damage = 0;
			NPC.defDamage = 0;
			NPC.defense = 12;
			NPC.lifeMax = 900;
			NPC.noGravity = true;
			NPC.noTileCollide = true;
			NPC.knockBackResist = 0.2f;
			NPC.npcSlots = 0f;
			NPC.HitSound = SoundID.NPCHit3;
			NPC.DeathSound = SoundID.NPCDeath6;
		}

		public override void AI()
		{
			int bossIndex = (int)NPC.ai[0];

			if (bossIndex < 0 || bossIndex >= Main.maxNPCs) {
				NPC.life = 0;
				NPC.active = false;
				return;
			}

			NPC boss = Main.npc[bossIndex];

			if (!boss.active || boss.life <= 0 || (int)boss.ai[0] >= 2) {
				NPC.life = 0;
				NPC.active = false;
				return;
			}

			int slot = (int)NPC.ai[1];
			float orbit = slot * MathHelper.Pi + Main.GameUpdateCount * 0.02f;
			Vector2 hover = boss.Center + orbit.ToRotationVector2() * 150f;
			NPC.velocity = NPC.velocity * 0.88f + (hover - NPC.Center) * 0.07f;

			if (!Main.dedServ) {
				Lighting.AddLight(NPC.Center, 0.8f, 0.3f, 0.05f);
			}

			NPC.localAI[0] += 1f;

			if (NPC.localAI[0] < HealInterval || Main.netMode == NetmodeID.MultiplayerClient) {
				return;
			}

			NPC.localAI[0] = 0f;
			int healed = System.Math.Min(HealAmount, boss.lifeMax - boss.life);

			if (healed > 0) {
				boss.life += healed;
				boss.HealEffect(healed);
				boss.netUpdate = true;
			}
		}

		public override void FindFrame(int frameHeight)
		{
			NPC.frameCounter += 1.0;

			if (NPC.frameCounter >= 6.0) {
				NPC.frameCounter = 0.0;
				NPC.frame.Y += frameHeight;

				if (NPC.frame.Y >= Main.npcFrameCount[Type] * frameHeight) {
					NPC.frame.Y = 0;
				}
			}
		}
	}
}
