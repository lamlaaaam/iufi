import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import db_utils
import discord
import photocard_utils
from   discord.ext import commands

class FramesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.thread_pool = ThreadPoolExecutor()
        self.loop        = asyncio.get_running_loop()

    async def card_not_found_error(self, ctx):
        await ctx.send(f"**{ctx.author.mention} this card does not exist.**", delete_after=2)

    async def card_not_owned_error(self, ctx):
        await ctx.send(f"**{ctx.author.mention} you do not own this card.**", delete_after=2)

    async def frame_not_found_error(self, ctx):
        await ctx.send(f"**{ctx.author.mention} this frame does not exist.**", delete_after=2)

    async def frame_not_owned_error(self, ctx):
        await ctx.send(f"**{ctx.author.mention} you do not own this frame.**", delete_after=2)

    async def get_last_card_id(self, user_id):
        user_doc = await db_utils.get_user(user_id)
        cards = user_doc['collection']
        if len(cards) == 0:
            return None
        return cards[-1]

    async def set_card_frame(self, ctx, card_id_tag, frame_id_tag):
        card_doc  = await db_utils.get_card(card_id_tag)
        frame_doc = await db_utils.get_frame(frame_id_tag)
        if card_doc['frame'] != 0:
            await db_utils.update_user_frames(ctx.author.id, card_doc['frame'], 1)
        await db_utils.update_user_frames(ctx.author.id, frame_doc['id'], -1)
        await db_utils.set_card_frame(card_id_tag, frame_id_tag)
        await ctx.send(f"**{ctx.author.mention} you have successfully set a frame.**")

    @commands.command(name = 'setframe', aliases = ['sfr'])
    async def set_frame(self, ctx, card_id_tag, frame_id_tag):
        card_doc  = await db_utils.get_card(card_id_tag)
        frame_doc = await db_utils.get_frame(frame_id_tag)
        user_doc  = await db_utils.get_user(ctx.author.id)
        if card_doc == None:
            await self.card_not_found_error(ctx)
            return
        if card_doc['id'] not in user_doc['collection']:
            await self.card_not_owned_error(ctx)
            return
        if frame_doc == None:
            await self.frame_not_found_error(ctx)
            return
        if str(frame_doc['id']) not in user_doc['frames'] or user_doc['frames'][str(frame_doc['id'])] <= 0:
            await self.frame_not_owned_error(ctx)
            return
        await self.set_card_frame(ctx, card_id_tag, frame_id_tag)

    @commands.command(name = 'removeframe', aliases = ['rfr'])
    async def remove_frame(self, ctx, card_id_tag):
        card_doc = await db_utils.get_card(card_id_tag)
        user_doc = await db_utils.get_user(ctx.author.id)
        if card_doc == None:
            await self.card_not_found_error(ctx)
            return
        if card_doc['id'] not in user_doc['collection']:
            await self.card_not_owned_error(ctx)
            return
        if card_doc['frame'] != 0:
            await db_utils.update_user_frames(ctx.author.id, card_doc['frame'], 1)
        await db_utils.set_card_frame(card_id_tag)
        await ctx.send(f"**{ctx.author.mention} you have successfully removed the frame.**", delete_after=2)

    @commands.command(name = 'setframelast', aliases = ['sfrl'])
    async def set_frame_last(self, ctx, frame_id_tag):
        last_card = await self.get_last_card_id(ctx.author.id)
        frame_doc = await db_utils.get_frame(frame_id_tag)
        user_doc  = await db_utils.get_user(ctx.author.id)
        if last_card == None:
            ctx.send(f'**{ctx.author.mention} you have no photocards.**', delete_after=2)
            return
        if frame_doc == None:
            await self.frame_not_found_error(ctx)
            return
        if str(frame_doc['id']) not in user_doc['frames'] or user_doc['frames'][str(frame_doc['id'])] <= 0:
            await self.frame_not_owned_error(ctx)
            return
        await self.set_card_frame(ctx, last_card, frame_id_tag)

    @commands.command(name = 'frameinfo', aliases = ['fi'])
    async def frame_info(self, ctx, id_tag):
        frame_doc = await db_utils.get_frame(id_tag)
        if frame_doc == None:
            await self.frame_not_found_error(ctx)
            return

        title  = "**ℹ️   Frame Info**"
        id     = f"**🆔   `{frame_doc['id']:03}`**\n"
        tag    = f"**🏷️   `{frame_doc['tag']}`**\n"
        desc   = id + tag + '\n'
        embed = discord.Embed(title=title, description=desc, color=discord.Color.dark_grey())

        frame_img = await (await self.loop.run_in_executor(self.thread_pool, partial(photocard_utils.create_frame, frame_doc)))
        frame_attachment = await (await self.loop.run_in_executor(self.thread_pool, partial(photocard_utils.pillow_to_attachment, frame_img, self.bot.WASTELAND)))
        embed.set_image(url=frame_attachment)

        await ctx.send(embed=embed)