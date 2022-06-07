from   discord.ext import commands

class ErrorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        cmd = self.bot.get_command(ctx.invoked_with)
        if   isinstance(error, commands.CheckFailure) and cmd not in self.bot.get_cog('RollCog').get_commands():
            await ctx.send(f'**{ctx.author.mention} has no permissions to run this command.**', delete_after=2)
            return
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'**{ctx.author.mention} this command is on cooldown. Try again after {round(error.retry_after)} second(s).**', delete_after=2)
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'**{ctx.author.mention} the command is missing arguments. Check the usage again.**', delete_after=2)
            cmd.reset_cooldown(ctx)
            await ctx.invoke(self.bot.get_command('commandhelp'), ctx.invoked_with)
            return
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f'**{ctx.author.mention} the arguments given are invalid. Check the usage again.**', delete_after=2)
            cmd.reset_cooldown(ctx)
            await ctx.invoke(self.bot.get_command('commandhelp'), ctx.invoked_with)
            return
        else:
            pass
        raise error
