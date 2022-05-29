import db_utils
import photocard_utils
import discord
from   discord.ext import commands

class FavesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = 'faves', aliases = ['f'])
    async def faves(self, ctx, user: discord.Member=None):
        if user == None:
            id   = ctx.author.id
            user = await self.bot.GUILD.fetch_member(id)
        else:
            if not await db_utils.does_user_exist(user.id):
                await ctx.send(f"**{ctx.author.mention} The user provided is not registered.**")
                return
            id = user.id

        user_doc   = await db_utils.get_user(id)
        faves      = user_doc['faves']

        if len([f for f in faves if f != None]) == 0:
            await ctx.send(f"**{user.mention} has not set any favorites.**")
            return

        cards_docs   = list(await db_utils.get_cards({'id': {'$in': faves}}))
        faves_dict   = {}
        faves_sorted = [None] * 6
        for doc in cards_docs:
            faves_dict[doc['id']] = doc
        for i in range(len(faves)):
            cid = faves[i]
            if cid == None:
                continue
            faves_sorted[i] = faves_dict[cid]

        desc = ""
        for r, d in enumerate(faves_sorted):
            num = f"{r+1}."
            if d != None:
                cid    = f"🆔 {d['id']:04}"
                tag    = f"🏷️ {d['tag']}"
                f      = f"{d['frame']:03}" if d['frame'] != 0 else '---'
                frame  = f"🖼️ {f}"
                rarity = f"{self.bot.RARITY[d['rarity']]}"
                desc  += f"{cid:<8}{tag:<15}{frame:>5}{rarity:>2}\n"
            else:
                #desc  += f"{num:<5}\n"
                desc  += f" \n"
        desc  = "```\n" + desc + "```\n"
        desc += "🌸 " * 13 + "\n\n"

        img        = await photocard_utils.stitch_gallery(faves_sorted, 2, 3)
        attachment = await photocard_utils.pillow_to_attachment(img, self.bot.WASTELAND)
        title      = f"**❤️   {user.display_name}'s Favorite Photocards**"
        embed      = discord.Embed(title=title, description=desc, color=discord.Color.dark_green())
        embed.set_image(url=attachment)
        await ctx.send(embed=embed)
