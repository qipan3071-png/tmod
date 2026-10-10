using Microsoft.Xna.Framework;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;
using WastelandSoul.Common.ItemBases;
using WastelandSoul.Content.Buffs;
using WastelandSoul.Content.Items.Materials;
using WastelandSoul.Content.Projectiles.Melee;
using WastelandSoul.Content.Projectiles.Rift;

namespace WastelandSoul.Content.Items.Weapons.Rift
{
	/// <summary>
	/// 星隙组。外形各不相同，攻击都走同一套过程：蓄能、撕裂、坍缩、爆发。
	/// </summary>
	public abstract class Riftarm : WastelandClassWeapon
	{
		protected void Register(int bar)
		{
			CreateRecipe()
				.AddIngredient<SalvagedSteelBar>(8)
				.AddIngredient(bar, 12)
				.AddIngredient(ItemID.FallenStar, 8)
				.AddIngredient(ItemID.SoulofLight, 6)
				.AddIngredient(ItemID.SoulofNight, 6)
				.AddTile(WastelandCraftingStations.HardmodeAnvil)
				.Register();
		}
	}

	/// <summary>裂开的弯刃。挥出去留下一道会坍缩的星隙。</summary>
	public class RiftCleaver : Riftarm
	{
		protected override DamageClass Class => DamageClass.Melee;
		protected override int Damage => 108;
		protected override int UseTime => 32;
		protected override float Knockback => 7.5f;
		protected override int Rarity => ItemRarityID.Purple;
		protected override int ShootType => ModContent.ProjectileType<StarRiftSlash>();
		protected override float ShootSpeed => 7f;
		protected override int SellPrice => Item.sellPrice(gold: 8);

		public override void SetDefaults()
		{
			base.SetDefaults();
			WastelandWeaponKit.Melee(Item, WastelandSwingStyle.Smash);
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			Projectile.NewProjectile(source, position, velocity, type, damage, knockback, player.whoAmI, 1f);
			return false;
		}

		public override void AddRecipes()
		{
			Register(ItemID.HallowedBar);
			Register(ItemID.ChlorophyteBar);
		}
	}

	/// <summary>环里封着一颗星。飞出去之后原地坍成裂缝。</summary>
	public class OrbitScepter : Riftarm
	{
		protected override DamageClass Class => DamageClass.Magic;
		protected override int Damage => 84;
		protected override int UseTime => 30;
		protected override float Knockback => 4f;
		protected override int Rarity => ItemRarityID.Purple;
		protected override int ShootType => ModContent.ProjectileType<OrbitMote>();
		protected override float ShootSpeed => 9f;
		protected override int SellPrice => Item.sellPrice(gold: 8);

		public override void SetDefaults()
		{
			base.SetDefaults();
			WastelandWeaponKit.Magic(Item, 16);
		}

		public override void AddRecipes()
		{
			Register(ItemID.HallowedBar);
			Register(ItemID.ChlorophyteBar);
		}
	}

	/// <summary>把一支普通箭转成三支带电矢。手感参考脉冲弓，略作追踪、穿墙、只打一下。</summary>
	public class StarstringBow : Riftarm
	{
		protected override DamageClass Class => DamageClass.Ranged;
		protected override int Damage => 76;
		protected override int UseTime => 24;
		protected override float Knockback => 3.5f;
		protected override int Rarity => ItemRarityID.Purple;
		protected override int ShootType => ModContent.ProjectileType<StarstringShot>();
		protected override float ShootSpeed => 14f;
		protected override int SellPrice => Item.sellPrice(gold: 8);

		public override void SetDefaults()
		{
			base.SetDefaults();
			Item.width = 49;
			Item.height = 52;
			Item.useStyle = ItemUseStyleID.Shoot;
			Item.noMelee = true;
			Item.autoReuse = true;
			Item.useAmmo = AmmoID.Arrow;
			Item.UseSound = SoundID.Item75;
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			float[] spread = { -0.14f, 0f, 0.14f };

			for (int i = 0; i < spread.Length; i++) {
				Projectile.NewProjectile(source, position, velocity.RotatedBy(spread[i]), ShootType, damage, knockback, player.whoAmI);
			}

			return false;
		}

		public override void AddRecipes()
		{
			Register(ItemID.HallowedBar);
			Register(ItemID.ChlorophyteBar);
		}
	}

	/// <summary>缺了一角的环。飞到尽头收成一个小坍缩。</summary>
	public class GapChakram : Riftarm
	{
		protected override DamageClass Class => DamageClass.Throwing;
		protected override int Damage => 64;
		protected override int UseTime => 26;
		protected override float Knockback => 4.5f;
		protected override int Rarity => ItemRarityID.Purple;
		protected override int ShootType => ModContent.ProjectileType<GapChakramProj>();
		protected override float ShootSpeed => 12f;
		protected override int SellPrice => Item.sellPrice(gold: 8);

		public override void SetDefaults()
		{
			base.SetDefaults();
			Item.useStyle = ItemUseStyleID.Swing;
			Item.noMelee = true;
			Item.autoReuse = true;
			Item.UseSound = SoundID.Item1;
		}

		public override void AddRecipes()
		{
			Register(ItemID.HallowedBar);
			Register(ItemID.ChlorophyteBar);
		}
	}

	/// <summary>一颗带着环的虚空种。召出来的灯会自己撕小裂缝。</summary>
	public class VoidSeed : Riftarm
	{
		protected override DamageClass Class => DamageClass.Summon;
		protected override int Damage => 46;
		protected override int UseTime => 30;
		protected override float Knockback => 2.5f;
		protected override int Rarity => ItemRarityID.Purple;
		protected override int ShootType => ModContent.ProjectileType<VoidSeedMinion>();
		protected override int SellPrice => Item.sellPrice(gold: 8);

		public override void SetDefaults()
		{
			base.SetDefaults();
			WastelandWeaponKit.Summon(Item, ModContent.BuffType<VoidSeedBuff>(), 16);
		}

		public override bool Shoot(Player player, EntitySource_ItemUse_WithAmmo source, Vector2 position, Vector2 velocity, int type, int damage, float knockback)
		{
			Projectile.NewProjectile(source, position, velocity, type, damage, knockback, player.whoAmI, 0.45f);
			return false;
		}

		public override void AddRecipes()
		{
			Register(ItemID.HallowedBar);
			Register(ItemID.ChlorophyteBar);
		}
	}
}
