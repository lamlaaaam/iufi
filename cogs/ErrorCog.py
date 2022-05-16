from   discord.ext import commands

class ErrorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        cmd = self.bot.get_command(ctx.invoked_with)
        if   isinstance(error, commands.CheckFailure) and cmd not in self.bot.get_cog('RollCog').get_commands():
            await ctx.send(f'**{ctx.author.mention} has no permissions to run this command.**')
            return
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'**{ctx.author.mention} this command is on cooldown. Try again after {round(error.retry_after)} second(s).**')
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'**{ctx.author.mention} the command is missing arguments. Check the usage again.**')
            cmd.reset_cooldown(ctx)
            return
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f'**{ctx.author.mention} the arguments given are invalid. Check the usage again.**')
            cmd.reset_cooldown(ctx)
            return
        else:
            pass
        raise error
