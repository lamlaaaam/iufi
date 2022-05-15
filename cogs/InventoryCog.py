from locale import currency
import db_utils
import discord
from   discord.ext import commands

class InventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = 'inventory', aliases = ['in'])
    @commands.check(db_utils.does_user_exist)
    async def inventory(self, ctx):
        id               = ctx.author.id
        user             = await self.bot.GUILD.fetch_member(id)
        user_doc = await db_utils.get_user(id)
        currency         = user_doc['currency']
        rare_rolls         = user_doc['rare_rolls']
        epic_rolls         = user_doc['epic_rolls']
        legend_rolls         = user_doc['legend_rolls']
        title            = f"**👜   {user.display_name}'s Inventory**"
        embed            = discord.Embed(title = title, color = discord.Color.dark_green())
        s                = f"🍬  Starcandies: `{currency}`\n"
        s               += f"🌸  Rare rolls : `{rare_rolls}`\n"
        s               += f"💎  Epic rolls : `{epic_rolls}`\n"
        s               += f"👑  Legendary rolls: `{legend_rolls}`"
        embed.add_field(name=s, value='\u200b', inline=False)
        embed.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=embed)