import discord
from   discord.ext import commands
from   discord       import Button, ButtonStyle

class HelpCog(commands.Cog):
    def __init__(self,
                 bot,
                 help_msg):
        self.bot      = bot
        self.help_msg = help_msg

    @commands.command(name = 'help', aliases = ['h'])
    async def help(self, ctx):
        title = "**💮   Welcome to IUFI!**"
        desc  = "**To begin your photocard collection journey, `qregister` yourself.**\n"
        desc += "**For more details about a command, use `qcommandhelp command`.**\n\n"
        desc += self.help_msg
        embed = discord.Embed(title=title, description=desc, color=discord.Color.purple())
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        components = [[Button(emoji='🐦', label = 'Twitter', url = 'https://twitter.com/ui8ball', style = ButtonStyle.url),
                       Button(emoji='💻', label = 'Github', url = 'https://github.com/lamlaaaam', style = ButtonStyle.url),
                       Button(emoji='📗', label = 'Beginner Guide', url = 'https://docs.google.com/document/d/1VAD20wZQ56S_wDeMJlwIKn_jImIPuxh2lgy1fn17z0c/edit?usp=sharing', style = ButtonStyle.url)]]
        await ctx.send(embed=embed, components=components)