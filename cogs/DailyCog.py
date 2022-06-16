import db_utils
import discord
from   discord.ext import commands

class DailyCog(commands.Cog):
    def __init__(self,
                 bot,
                 daily_reward,
                 streak_end,
                 streak_interval,
                 streak_rewards):
        self.bot             = bot
        self.daily_reward    = daily_reward
        self.streak_end      = streak_end
        self.streak_interval = streak_interval
        self.streak_rewards  = streak_rewards

    @commands.command(name = 'daily', aliases = ['d'])
    async def daily(self, ctx):
        ok, text = await db_utils.check_cooldown(ctx.author.id, 'next_daily')
        if not ok:
            await ctx.send(f'**{ctx.author.mention} you can claim your next daily reward in {text}.**', delete_after=2)
            return

        user          = await self.bot.GUILD.fetch_member(ctx.author.id)
        within_streak = await db_utils.check_within_streak(ctx.author.id)
        hit_streak    = False
        reward_index  = None
        if within_streak:
            user_doc = await db_utils.get_user(ctx.author.id)
            streak   = user_doc['streak']
            streak  += 1
            if streak % self.streak_interval == 0:
                hit_streak   = True
                reward_index = streak // self.streak_interval - 1
        else:
            streak = 1

        title = "**📅   Daily Reward**"
        desc  = f"Daily reward claimed! +{self.daily_reward} 🍬\n\n"
        desc += f"**Streak Rewards\n**"
        total = streak
        cols  = ['🟥','🟧','🟨','🟩','🟦','🟪']
        desc += "```\n"
        for r in range(self.streak_end // self.streak_interval):
            if total >= self.streak_interval:
                squares = self.streak_interval
            else:
                squares = total
            total -= self.streak_interval
            if total < 0:
                total = 0
            desc += f"{(cols[r]+'')*squares+'⬜'*(self.streak_interval-squares):<5} {self.streak_rewards[r][0] + ' ' + ('✅' if squares == self.streak_interval else '⬛'):>8}\n"
        desc += "```"

        embed = discord.Embed(title=title, description=desc, color=discord.Color.magenta())
        embed.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=embed)
        
        if hit_streak:
            await self.streak_rewards[reward_index][1](user.id)
            await db_utils.set_user_cooldown(ctx.author.id, 'streak_ends', h = 46)
            if streak >= self.streak_end:
                await db_utils.set_user_cooldown(ctx.author.id, 'streak_ends')
                streak = 1
        else:
            await db_utils.set_user_cooldown(ctx.author.id, 'streak_ends', h = 46)

        await db_utils.set_user_streak(ctx.author.id, streak)
        await db_utils.set_user_cooldown(ctx.author.id, 'next_daily', h = 23)
        await db_utils.update_user_currency(ctx.author.id, self.daily_reward)