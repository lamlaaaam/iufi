import db_utils
import discord
from   discord.ext import commands

class DailyCog(commands.Cog):
    def __init__(self,
                 bot,
                 streak_max,
                 daily_reward,
                 streak_reward):
        self.bot           = bot
        self.streak_max    = streak_max
        self.daily_reward  = daily_reward
        self.streak_reward = streak_reward

    @commands.command(name = 'daily', aliases = ['d'])
    async def daily(self, ctx):
        ok, text = await db_utils.check_cooldown(ctx.author.id, 'next_daily')
        if not ok:
            await ctx.send(f'**{ctx.author.mention} you can claim your next daily reward in {text}.**')
            return

        within_streak = await db_utils.check_within_streak(ctx.author.id)
        hit_streak = False
        if within_streak:
            user_doc = await db_utils.get_user(ctx.author.id)
            streak   = user_doc['streak']
            streak  += 1
            if streak >= self.streak_max:
                hit_streak = True
        else:
            streak = 1

        title = "**📅   Daily Reward**"
        desc  = f"Daily reward claimed! +{self.daily_reward} 🍬\n\n"
        desc += f"**Current streak: {streak}/{self.streak_max}**\n"
        desc += f"{'🟩 '*streak}{'⬜ '*(self.streak_max-streak)}\n\n"
        if hit_streak:
            desc += f"You have completed the streak! +{self.streak_reward} 🍬"
        else:
            desc += f"{self.streak_max-streak} days left to get bonus starcandies!"

        embed = discord.Embed(title=title, description=desc, color=discord.Color.magenta())
        await ctx.send(embed=embed)
        
        if hit_streak:
            await db_utils.update_user_currency(ctx.author.id, self.streak_reward)
            await db_utils.set_user_cooldown(ctx.author.id, 'streak_ends')
            streak = 1
        else:
            await db_utils.set_user_cooldown(ctx.author.id, 'streak_ends', d = 2)

        await db_utils.set_user_streak(ctx.author.id, streak)
        await db_utils.set_user_cooldown(ctx.author.id, 'next_daily', d = 1)
        await db_utils.update_user_currency(ctx.author.id, self.daily_reward)