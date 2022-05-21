import db_utils
import discord
from   discord.ext import commands

class CooldownsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = 'cooldowns', aliases = ['cd'])
    async def cooldowns(self, ctx):
        id               = ctx.author.id
        user             = await self.bot.GUILD.fetch_member(id)
        _, user_roll_cd  = await db_utils.check_cooldown(id,'next_roll')
        _, user_claim_cd = await db_utils.check_cooldown(id,'next_claim')
        _, user_daily_cd = await db_utils.check_cooldown(id,'next_daily')
        title            = f"**⏰   {user.display_name}'s Cooldowns**"
        embed            = discord.Embed(title = title, color = discord.Color.blue())
        s                = f"🎲  ROLL    : {user_roll_cd}\n"
        s               += f"🃏  CLAIM : {user_claim_cd}\n"
        s               += f"📅  DAILY  : {user_daily_cd}"

        embed.add_field(name=s, value='\u200b', inline=False)
        embed.set_thumbnail(url=user.avatar_url)

        await ctx.send(embed=embed)