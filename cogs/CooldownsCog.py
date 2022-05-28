import db_utils
import discord
from   discord.ext import commands, tasks
from   datetime import datetime

class CooldownsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cd_check.start()

    @commands.command(name = 'cooldowns', aliases = ['cd'])
    async def cooldowns(self, ctx):
        id               = ctx.author.id
        user             = await self.bot.GUILD.fetch_member(id)
        user_doc         = await db_utils.get_user(id)
        _, user_roll_cd  = await db_utils.check_cooldown(id,'next_roll')
        _, user_claim_cd = await db_utils.check_cooldown(id,'next_claim')
        _, user_daily_cd = await db_utils.check_cooldown(id,'next_daily')
        title            = f"**⏰   {user.display_name}'s Cooldowns**"
        embed            = discord.Embed(title = title, color = discord.Color.blue())
        s                = f"🎲  ROLL    : {user_roll_cd}\n"
        s               += f"🃏  CLAIM : {user_claim_cd}\n"
        s               += f"📅  DAILY  : {user_daily_cd}\n"
        s               += f"🔔  REMINDERS  : `{'ON' if user_doc['reminders'] else 'OFF'}`"

        embed.add_field(name=s, value='\u200b', inline=False)
        embed.set_thumbnail(url=user.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(name = 'remindon', aliases = ['ron'])
    async def remind_on(self, ctx):
        await db_utils.set_user_reminders(ctx.author.id, True)
        await ctx.send(f"**{ctx.author.mention} you have turned on reminders.**")

    @commands.command(name = 'remindoff', aliases = ['roff'])
    async def remind_off(self, ctx):
        await db_utils.set_user_reminders(ctx.author.id, False)
        await ctx.send(f"**{ctx.author.mention} you have turned off reminders.**")

    @tasks.loop(minutes=1)
    async def cd_check(self):
        now       = datetime.now()
        user_docs = list(await db_utils.get_users({'reminders':True}))
        roll_up   = [doc['discord_id'] for doc in user_docs if now >= doc['next_roll'] and (now-doc['next_roll']).seconds < 90]
        #claim_up  = [doc['discord_id'] for doc in user_docs if now >= doc['next_claim']]
        daily_up  = [doc['discord_id'] for doc in user_docs if now >= doc['next_daily'] and (now-doc['next_daily']).seconds < 90]
        for id in roll_up:
            await self.send_dm(id, "roll")
        #for id in claim_up:
        #    await self.send_dm(id, "claim")
        for id in daily_up:
            await self.send_dm(id, "daily")

    async def send_dm(self, id, type):
        member = await self.bot.GUILD.fetch_member(id)
        if member == None:
            return
        try:
            ch     = await member.create_dm()
            await ch.send(f"**Your {type} is ready! Head over to {self.bot.CHANNEL.mention} to play!**")
        except discord.Forbidden:
            print("User cannot be reached for reminders.")

