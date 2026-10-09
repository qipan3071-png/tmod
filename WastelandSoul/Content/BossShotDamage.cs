namespace WastelandSoul.Content
{
	/// <summary>
	/// Boss 弹幕伤害的**统一换算**（玩家要求：四个 Boss 的所有弹幕"按官方来"）。
	///
	/// <para/>官方机制：**敌对弹幕**的 <c>Projectile.damage</c> 在结算打玩家时会先 **×2**，
	/// 专家模式**再 ×2**（也就是作者在 <c>NewProjectile</c> 里写的数字会被放大到 **4 倍**）。
	/// tModLoader 的官方建议是"作者自己在生成处折半"，于是本项目四个 Boss
	/// （清道夫 / 归档者 / 灰烬之心 / 壁炉守卫）**每一个弹幕生成点**的 damage 参数都过
	/// <see cref="Half"/>：这样 <c>NewProjectile</c> 里写的数字就是"标称伤害"，
	/// 玩家实际吃到的是标称值的 2 倍（普通）/ 4 倍（专家），和原版 Boss 的口径一致。
	///
	/// <para/>⚠️ 只换算**弹幕**：
	/// <list type="bullet">
	/// <item><c>NPC.damage</c>（接触 / 撞击伤害）**一格没动**；</item>
	/// <item>Boss 血量 / 防御也没动；</item>
	/// <item>没有任何一个 Boss 弹幕是用 <c>NPC.damage</c> 赋值的 —— 四个 Boss 的弹幕伤害全部来自
	/// 各自的常量（<c>OrbDamage</c> / <c>BoltDamage</c> / <c>PageDamage</c> …）或字面量，
	/// 所以"NPC.damage 加成"这条路径在我们这儿不存在。</item>
	/// </list>
	///
	/// <para/>⚠️ 两个**手动结算**的弹幕（<c>ArchivistIndexBeam</c> 的索引光束、
	/// <c>AshPulse</c> 的灰烬脉冲）是自己调 <c>player.Hurt(reason, Projectile.damage, …)</c> 的 ——
	/// 那条路**不经过**原版的"敌对弹幕加倍"通道，所以它们要在结算处用
	/// <see cref="ManualHit"/> 把那半份补回来（否则会被这次统一折半白白砍掉一半）。
	/// </summary>
	internal static class BossShotDamage
	{
		/// <summary>
		/// 把"标称伤害"换算成 <c>Projectile.NewProjectile</c> 该传的值（折半，向上取整到至少 1）。
		/// <para/>0 仍然是 0（"归档封印"是纯控制弹幕，不打伤害）。
		/// </summary>
		internal static int Half(int nominal)
		{
			if (nominal <= 0) {
				return 0;
			}

			int half = nominal / 2;

			return half < 1 ? 1 : half;
		}

		/// <summary>
		/// 手动结算（<c>player.Hurt</c>）时的换算：把生成处折半的那一份乘回 2，
		/// 于是"手动结算的弹幕"和"走原版通道的弹幕"最终打出来的伤害口径一致。
		/// </summary>
		internal static int ManualHit(int spawnDamage)
		{
			return spawnDamage <= 0 ? 0 : spawnDamage * 2;
		}
	}
}
