using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ModLoader;

namespace WastelandSoul.Content.Projectiles.Fireplace
{
	/// <summary>
	/// 壁炉大剑右键不走 UseItem，避免 C.I.V.E 的 StormySlash 把右键吃成连击斩。
	/// </summary>
	public sealed class FireplaceGreatbladeChargePlayer : ModPlayer
	{
		public override void SetControls()
		{
			FireplaceGreatbladeCharge.EatRightClick(Player);
		}

		public override bool PreItemCheck()
		{
			FireplaceGreatbladeCharge.EatRightClick(Player);
			FireplaceGreatbladeCharge.TryStart(Player);
			return true;
		}
	}

	/// <summary>蓄力时把逐渐变大的大剑画在手持层，不走 C.I.V.E 刀光画布。</summary>
	public sealed class FireplaceGreatbladeChargeLayer : PlayerDrawLayer
	{
		public override Position GetDefaultPosition()
		{
			return new AfterParent(PlayerDrawLayers.HeldItem);
		}

		public override bool GetDefaultVisibility(PlayerDrawSet drawInfo)
		{
			return FireplaceGreatbladeCharge.IsCharging(drawInfo.drawPlayer);
		}

		protected override void Draw(ref PlayerDrawSet drawInfo)
		{
			if (drawInfo.shadow != 0f) {
				return;
			}

			Player player = drawInfo.drawPlayer;
			int type = ModContent.ProjectileType<FireplaceCrescentCharge>();
			for (int i = 0; i < Main.maxProjectiles; i++) {
				Projectile projectile = Main.projectile[i];
				if (!projectile.active || projectile.owner != player.whoAmI || projectile.type != type) {
					continue;
				}

				float flash = projectile.localAI[1] / FireplaceGreatbladeCharge.FlashTicks;
				Color light = Lighting.GetColor(player.Center.ToTileCoordinates());
				FireplaceCrescentCharge.DrawHeldBlade(player, projectile.scale, light, flash, drawInfo.DrawDataCache);
				return;
			}
		}
	}
}
