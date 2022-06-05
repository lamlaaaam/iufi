import db_utils
import discord
from   discord.ext import commands

class InventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = 'inventory', aliases = ['in'])
    async def inventory(self, ctx):
        id               = ctx.author.id
        user             = await self.bot.GUILD.fetch_member(id)
        user_doc         = await db_utils.get_user(id)
        currency         = user_doc['currency']
        rare_rolls       = user_doc['rare_rolls']
        epic_rolls       = user_doc['epic_rolls']
        legend_rolls     = user_doc['legend_rolls']
        upgrades         = user_doc['upgrades']
        frames           = {(await db_utils.get_frame(int(id)))['tag']: count for id, count in user_doc['frames'].items() if count > 0}
        title            = f"**👜   {user.display_name}'s Inventory**"
        s                = f"{'🍬 Starcandies':<20}{'x'+str(currency):<5}\n"
        s               += f"{'🌸 Rare rolls':<20}{'x'+str(rare_rolls):<5}\n"
        s               += f"{'💎 Epic rolls':<20}{'x'+str(epic_rolls):<5}\n"
        s               += f"{'👑 Legend rolls':<20}{'x'+str(legend_rolls):<5}\n"
        s               += f"{'🔨 Upgrades':<20}{'x'+str(upgrades):<5}\n\n"
        s               += f"{'🖼️ Frames':<20}\n"
        if len(frames) == 0:
            s += "You have no frames.\n"
        else:
            i = 1
            for name, count in frames.items():
                s += f"{str(i)+'. '+name.upper():<20} {'x'+str(count):<5}\n"
                i += 1
        s     = '```' + s + '```'
        embed = discord.Embed(title = title, description=s, color = discord.Color.dark_green())

        embed.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=embed)