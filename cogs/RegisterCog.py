import db_utils
from   discord.ext import commands
from   discord import Button, ButtonStyle

class RegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def register(self, ctx):
        id = ctx.author.id
        if await db_utils.register_user(id):
            components = [[Button(emoji='📗', label = 'Beginner Guide',
                url = 'https://docs.google.com/document/d/1VAD20wZQ56S_wDeMJlwIKn_jImIPuxh2lgy1fn17z0c/edit?usp=sharing', style = ButtonStyle.url)]]
            await ctx.reply(content=f'**Welcome to IUFI! Please have a look at the guide or use "qhelp" to begin.**', components=components)
        else:
            await ctx.send(f'**{ctx.author.mention} is already registered.**', delete_after=2)