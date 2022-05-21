import db_utils
import photocard_utils
import discord
from   discord.ext import commands

class FavesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = 'faves', aliases = ['f'])
    async def faves(self, ctx):
        user       = await self.bot.GUILD.fetch_member(ctx.author.id)
        user_doc   = await db_utils.get_user(ctx.author.id)
        faves      = user_doc['faves']

        if len([f for f in faves if f != None]) == 0:
            await ctx.send(f"**{ctx.author.mention} you have not set any favorites.**")
            return

        cards_docs   = list(await db_utils.get_cards({'id': {'$in': faves}}))
        faves_dict   = {}
        faves_sorted = [None] * 6
        for doc in cards_docs:
            faves_dict[doc['id']] = doc
        for i in range(len(faves)):
            id = faves[i]
            if id == None:
                continue
            faves_sorted[i] = faves_dict[id]

        desc = ""
        for r, d in enumerate(faves_sorted):
            num = f"{r+1}."
            if d != None:
                id     = f"🆔 {d['id']:04}"
                tag    = f"🏷️ {d['tag']}"
                rarity = f"{self.bot.RARITY[d['rarity']]}"
                desc  += f"{num:<5}{id:<10}{tag:<15}{rarity:>1}\n"
            else:
                desc  += f"{num:<5}\n"
        desc  = "```\n" + desc + "```\n"
        desc += "🌸 " * 13 + "\n\n"

        faves_urls = [doc['url'] if doc != None else None for doc in faves_sorted]
        img        = await photocard_utils.stitch_gallery(faves_urls, 2, 3)
        attachment = await photocard_utils.pillow_to_attachment(img, self.bot.WASTELAND)
        title      = f"**❤️   {user.display_name}'s Favorite Photocards**"
        embed      = discord.Embed(title=title, description=desc, color=discord.Color.dark_green())
        embed.set_image(url=attachment)
        await ctx.send(embed=embed)
