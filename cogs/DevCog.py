import os
import sys
import db_utils
from   discord.ext import commands

class DevCog(commands.Cog):
    def __init__(self, bot, devs):
        self.bot  = bot
        self.devs = devs
        self.pizza_master_id = 982571914516131892

    async def cog_check(self, ctx):
        return self.pizza_master_id in [r.id for r in ctx.author.roles]

    @commands.command(name = 'reboot')
    async def reboot(self, ctx):
        await ctx.send("**IUFI is rebooting...**")
        os.execl(sys.executable, sys.executable, *sys.argv)
        #sys.exit()

    @commands.command(name = 'reset')
    async def reset(self, ctx):
        await db_utils.reset_game_command()
        await ctx.send("**All game data has been wiped.**")
