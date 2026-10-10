using Terraria;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Items.Materials;
using WastelandSoul.Content.Projectiles.Whips;

namespace WastelandSoul.Content.Items.Weapons.Whips
{
	/// <summary>
	/// 打完对应 Boss 后可合成的四把鞭。手感对齐原版鞭：
	/// 召唤伤害、不自动挥舞、命中锁定仆从目标、穿透衰减、4 秒标记。
	/// </summary>
	public abstract class WastelandWhip : ModItem
	{
		protected abstract int WhipProjectile { get; }

		protected abstract int Damage { get; }

		protected abstract float Knockback { get; }

		protected abstract float ShootSpeed { get; }

		protected abstract int Animation { get; }

		protected abstract int Rarity { get; }

		protected abstract int SellCopper { get; }

		public override void SetDefaults()
		{
			Item.DefaultToWhip(WhipProjectile, Damage, Knockback, ShootSpeed, Animation);
			Item.width = 40;
			Item.height = 40;
			Item.rare = Rarity;
			Item.value = SellCopper;
			Item.autoReuse = false;
			Item.channel = false;
		}

		public override bool MeleePrefix()
		{
			return true;
		}
	}

	/// <summary>清道夫后。对标脊柱骨鞭 / 荆鞭：27 伤、标记 6、中毒。</summary>
	public class SteelLash : WastelandWhip
	{
		protected override int WhipProjectile => ModContent.ProjectileType<SteelLashProj>();
		protected override int Damage => 27;
		protected override float Knockback => 2f;
		protected override float ShootSpeed => 8f;
		protected override int Animation => 30;
		protected override int Rarity => WastelandRarityTiers.Early;
		protected override int SellCopper => Item.sellPrice(gold: 1, silver: 50);

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient<SalvagedSteelBar>(8)
				.AddIngredient<SalvagedSteelChunk>(12)
				.AddIngredient(ItemID.Leather, 6)
				.AddTile(WastelandCraftingStations.EarlyAnvil)
				.Register();
		}
	}

	/// <summary>归档者后。对标迪朗达尔：52 伤、标记 9、挥得更快。</summary>
	public class IndexLash : WastelandWhip
	{
		protected override int WhipProjectile => ModContent.ProjectileType<IndexLashProj>();
		protected override int Damage => 52;
		protected override float Knockback => 2f;
		protected override float ShootSpeed => 12f;
		protected override int Animation => 28;
		protected override int Rarity => WastelandRarityTiers.EarlyLate;
		protected override int SellCopper => Item.sellPrice(gold: 4, silver: 60);

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient<ArchivistFragment>(12)
				.AddIngredient(ItemID.Bone, 20)
				.AddIngredient(ItemID.SoulofLight, 6)
				.AddTile(WastelandCraftingStations.EarlyAnvil)
				.Register();
		}
	}

	/// <summary>灰烬之心后。对标暗黑收割前一档：95 伤、标记 12、点燃。</summary>
	public class CinderLash : WastelandWhip
	{
		protected override int WhipProjectile => ModContent.ProjectileType<CinderLashProj>();
		protected override int Damage => 95;
		protected override float Knockback => 3f;
		protected override float ShootSpeed => 8f;
		protected override int Animation => 30;
		protected override int Rarity => WastelandRarityTiers.MidLate;
		protected override int SellCopper => Item.sellPrice(gold: 6);

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient<AshHeartAlloyBar>(10)
				.AddIngredient(ItemID.ChlorophyteBar, 8)
				.AddIngredient(ItemID.Ectoplasm, 6)
				.AddTile(WastelandCraftingStations.HardmodeAnvil)
				.Register();
		}
	}

	/// <summary>壁炉守卫后。对标晨星 / 电鳗前一档：145 伤、标记 16、10% 仆从暴击。</summary>
	public class HearthLash : WastelandWhip
	{
		protected override int WhipProjectile => ModContent.ProjectileType<HearthLashProj>();
		protected override int Damage => 145;
		protected override float Knockback => 4f;
		protected override float ShootSpeed => 8f;
		protected override int Animation => 32;
		protected override int Rarity => WastelandRarityTiers.Late;
		protected override int SellCopper => Item.sellPrice(gold: 8);

		public override void AddRecipes()
		{
			CreateRecipe()
				.AddIngredient<FireplaceAlloyBar>(12)
				.AddIngredient(ItemID.ChlorophyteBar, 10)
				.AddIngredient(ItemID.HallowedBar, 8)
				.AddTile(WastelandCraftingStations.HardmodeAnvil)
				.Register();
		}
	}
}
