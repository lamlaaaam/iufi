import asyncio
import db_utils
import discord
from   discord.ext import commands, tasks
from   datetime import datetime

class CooldownsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.prev_roll = {}
        self.prev_daily = {}
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
        embed = discord.Embed(title="🔔 Reminders On Result", description=f"**Reminders have been turned on.**", color=discord.Color.random())
        await ctx.reply(embed=embed)

    @commands.command(name = 'remindoff', aliases = ['roff'])
    async def remind_off(self, ctx):
        await db_utils.set_user_reminders(ctx.author.id, False)
        embed = discord.Embed(title="🔔 Reminders Off Result", description=f"**Reminders have been turned off.**", color=discord.Color.random())
        await ctx.reply(embed=embed)

    @tasks.loop(minutes=1)
    async def cd_check(self):
        now       = datetime.now()
        user_docs = await db_utils.get_users({'reminders':True})
        roll_up   = []
        daily_up  = []
        for doc in user_docs:
            uid = doc['discord_id']
            roll = doc['next_roll']
            daily = doc['next_daily']
            if now >= roll and (uid not in self.prev_roll or self.prev_roll[uid] != roll):
                self.prev_roll[uid] = roll
                roll_up.append(uid)
            if now >= daily and (uid not in self.prev_daily or self.prev_daily[uid] != daily):
                self.prev_daily[uid] = daily
                daily_up.append(uid)
        for id in roll_up:
            await self.send_dm(id, "roll")
        for id in daily_up:
            await self.send_dm(id, "daily")

    @cd_check.before_loop
    async def before_cd_check(self):
        await asyncio.sleep(60)

    async def send_dm(self, id, type):
        try:
            member = await self.bot.GUILD.fetch_member(id)
            if member == None:
                return
            ch = await member.create_dm()
            await ch.send(f"**Your {type} is ready! Visit {', '.join([ch.mention for ch in self.bot.CHANNELS])} to play!**")
        except:
            print("User cannot be reached for reminders.")

