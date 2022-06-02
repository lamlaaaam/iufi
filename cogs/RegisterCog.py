import db_utils
from   discord.ext import commands

class RegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def register(self, ctx):
        id = ctx.author.id
        if await db_utils.register_user(id):
            await ctx.send(f'**{ctx.author.mention} has registered successfully. Welcome to IUFI!**', delete_after=2)
        else:
            await ctx.send(f'**{ctx.author.mention} is already registered.**', delete_after=2)