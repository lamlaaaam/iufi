import db_utils
import discord
from   discord.ext import commands

class GiftSCCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = 'giftsc', aliases = ['gsc'])
    async def giftsc(self, ctx, rec: discord.Member=None, amt: int=0):
        if rec == None:
            await ctx.send(f'**{ctx.author.mention} pick a recipient for your gift.**', delete_after=2)
            return
        if rec.id == ctx.author.id:
            await ctx.send(f'**{ctx.author.mention} you cannot gift yourself.**', delete_after=2)
            return
        if not await db_utils.does_user_exist(rec.id):
            await ctx.send(f'**{ctx.author.mention} the recipient is not registered.**', delete_after=2)
            return

        user_doc = await db_utils.get_user(ctx.author.id)
        currency = user_doc['currency']

        if amt <= 0 or amt > currency:
            await ctx.send(f'**{ctx.author.mention} invalid amount for gifting.**', delete_after=2)
            return

        await db_utils.update_user_currency(ctx.author.id, -amt)
        await db_utils.update_user_currency(rec.id, amt)
        await ctx.send(f'**{ctx.author.mention} has gifted {rec.mention} {amt} starcandies.**', delete_after=2)
