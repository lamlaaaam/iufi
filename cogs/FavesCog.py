import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import db_utils
import photocard_utils
import discord
from   discord.ext import commands

class FavesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.thread_pool = ThreadPoolExecutor()
        self.loop        = asyncio.get_running_loop()

    @commands.command(name = 'faves', aliases = ['f'])
    async def faves(self, ctx, user: discord.Member=None):
        if user == None:
            id   = ctx.author.id
            user = await self.bot.GUILD.fetch_member(id)
        else:
            if not await db_utils.does_user_exist(user.id):
                await ctx.send(f"**{ctx.author.mention} The user provided is not registered.**", delete_after=2)
                return
            id = user.id

        user_doc   = await db_utils.get_user(id)
        faves      = user_doc['faves']

        if len([f for f in faves if f != None]) == 0:
            await ctx.send(f"**{user.mention} has not set any favorites.**", delete_after=2)
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
                id     = f"🆔{d['id']:04}"
                tag    = f"🏷️{d['tag'] if d['tag'] else '-'}"
                f      = f"{d['frame']:02}" if d['frame'] != 0 else '-'
                frame  = f"🖼️{f}"
                rarity = f"{self.bot.RARITY[d['rarity']]}"
                stars  = f"✨{d['stars']}"
                desc  += f"{id:<6}|{tag:<12}|{frame:<4}|{stars:<4}|{rarity:<1}\n"
            else:
                desc  += f" \n"
        desc  = "```\n" + desc + "```\n"

        img = await (await self.loop.run_in_executor(self.thread_pool, partial(photocard_utils.stitch_gallery, faves_sorted, 2, 3)))
        attachment = await (await self.loop.run_in_executor(self.thread_pool, partial(photocard_utils.pillow_to_attachment, img, self.bot.WASTELAND)))
        title      = f"**❤️   {user.display_name}'s Favorite Photocards**"
        embed      = discord.Embed(title=title, description=desc, color=discord.Color.dark_green())
        embed.set_image(url=attachment)
        await ctx.send(embed=embed)
