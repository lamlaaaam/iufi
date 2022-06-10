import discord
from   discord.ext import commands

class CommandHelpCog(commands.Cog):
    def __init__(self, bot, command_map):
        self.bot         = bot
        self.command_map = command_map

    @commands.command(name = 'commandhelp', aliases = ['ch'])
    async def commandhelp(self, ctx, cmd):
        cmd = self.bot.get_command(cmd[1:] if cmd[0] in ['q', 'Q'] else cmd)
        if cmd == None:
            await ctx.send(f"**{ctx.author.mention} The command provided does not exist.**", delete_after=2)
            return

        name               = 'q' + cmd.name
        alias, usage, desc = self.command_map[name]
        name               = f"**{name} [{alias}]**"
        description        = f"Usage: `{usage}`\n"
        description       += f"```{desc}```"
        embed              = discord.Embed(title=name, description=description, color=discord.Color.greyple())
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        await ctx.send(embed=embed)

        