import db_utils
import discord
from   discord.ext import commands

class LevelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def level_up_check(ctx):
        user_doc      = await db_utils.get_user(ctx.author.id)
        level         = user_doc['level']
        exp           = user_doc['exp']
        new_exp       = exp + 1
        level_up_exp  = level * level + 10
        levels_gained = new_exp // level_up_exp
        leftover_exp  = new_exp % level_up_exp

        if levels_gained > 0:
            level_up_reward = level * 2
            title           = "**📈   Level Up!**"
            desc            = f"```⚔️:  {level}  ->  {level + levels_gained}\n"
            desc           += f"🍬:  {user_doc['currency']}  ->  {user_doc['currency'] + level_up_reward}\n"
            desc           += "You gained some starcandies for leveling up!```"
            embed           = discord.Embed(title=title, description=desc, color=discord.Color.teal())
            embed.set_thumbnail(url=ctx.author.avatar_url)

            await ctx.send(embed=embed)
            await db_utils.update_user_currency(ctx.author.id, level_up_reward)

        await db_utils.set_user_level_exp(ctx.author.id, level + levels_gained, leftover_exp)