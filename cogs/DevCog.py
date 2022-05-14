import sys
from   discord.ext import commands

class DevCog(commands.Cog):
    def __init__(self, bot, devs):
        self.bot  = bot
        self.devs = devs

    async def cog_check(self, ctx):
        return ctx.author.id in self.devs

    @commands.command(name = 'reset')
    async def reset(self, ctx):
        sys.exit()