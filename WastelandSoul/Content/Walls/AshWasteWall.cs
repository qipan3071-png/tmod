using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace WastelandSoul.Content.Walls
{
	/// <summary>
	/// 「灰烬荒壁」—— 壁炉子世界里**唯一**的背景墙（玩家要求：整个子世界统一一种墙）。
	///
	/// <para/>贴图 <c>AshWasteWall.png</c> 是**程序化生成**的（<c>tools/gen_ashwaste_wall_art.py</c>），
	/// 尺寸 **360 × 540**，不是随手定的：
	/// <list type="bullet">
	/// <item>原版画一格墙是 <c>new Rectangle(WallFrameX, WallFrameY + Main.wallFrame[type] * 180, 32, 32)</c>
	/// （IL 从 <c>Terraria.GameContent.Drawing.WallDrawing.DrawWalls</c> 核出来的），
	/// 而 <c>WallFrameX/Y</c> 走 **36 像素网格**（<c>Framing.WallFrame</c> 的查表值）、
	/// <c>Main.wallFrame</c> 是 0~2 的变体号；</item>
	/// <item>360 = 36 × 10（覆盖 frameX 0~324），540 = 180 × 3（覆盖 frameY 0~144 加两个变体块）；</item>
	/// <item>贴图内容按 **36 像素一格、每格同一张 32×32 无缝图案** 铺满 —— 于是 36 个变体块 / 每个
	/// frameX 取到的都是同一张图案，相邻两格画出来严丝合缝，不用为变体另画内容。</item>
	/// </list>
	///
	/// <para/>配色：暗底（29,34,38）+ 稀疏的青白点缀（58,96,104 / 104,140,146）——
	/// 和瑜钢合金同一套"青银间色"语言，但整体压暗压闷，**不是亮墙**。
	/// </summary>
	public class AshWasteWall : ModWall
	{
		public override void SetStaticDefaults()
		{
			// 废土墙不算"合规房屋墙"（壁炉是掩体不是城镇；也免得玩家拿它凑 NPC 住房）
			Main.wallHouse[Type] = false;

			DustType = DustID.Stone;
			HitSound = SoundID.Dig;

			AddMapEntry(new Color(34, 42, 46), Language.GetText("Mods.WastelandSoul.Walls.AshWasteWall.MapEntry"));
		}
	}
}
