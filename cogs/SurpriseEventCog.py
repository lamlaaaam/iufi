import asyncio
import db_utils
import discord
from   discord.ext import commands

class SurpriseEventCog(commands.Cog):
    def __init__(self, bot, devs):
        self.bot = bot
        self.answer = None
        self.prize_type = None
        self.prize_arg = None
        self.desc = None
        self.hint1 = None
        self.hint2 = None
        self.hint3 = None
        self.event_msg = None
        self.devs = devs
        self.ch = None

    async def cog_check(self, ctx):
        return ctx.author.id in self.devs

    @commands.command(name = 'eventconfig')
    async def event_config(self, ctx, answer, prize_type, prize_arg, desc, hint1, hint2, hint3):
        self.answer = answer
        self.prize_type = prize_type
        self.prize_arg = prize_arg
        self.desc = desc
        self.hint1 = hint1
        self.hint2 = hint2
        self.hint3 = hint3
        await ctx.send("configured.")

    @commands.command(name = 'eventtrigger')
    async def event_trigger(self, ctx, ch:discord.TextChannel):
        self.ch = ch
        title = "**🎉    Surprise Event!**"
        body  = '```' + self.desc + '```'
        hint1 = '`Hint 1:          hidden          `'
        hint2 = '`Hint 2:          hidden          `'
        hint3 = '`Hint 3:          hidden          `'
        desc  = f"{body}\n{hint1}\n{hint2}\n{hint3}\n"
        embed = discord.Embed(title=title, description=desc, color=discord.Color.purple())
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        self.event_msg = await ch.send(content=f"{self.bot.IUFI_ROLE.mention}", embed=embed)

        def check(m):
            return m.channel in self.bot.CHANNELS and m.content == self.answer and db_utils.does_user_exist_sync(m.author.id)

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=86400)
            await self.handle_win(ctx, msg)
        except asyncio.TimeoutError:
            end   = '` This event has ended. `'
            embed.description = self.event_msg.embeds[0].description + '\n\n' + end
            await self.event_msg.edit(embed=embed)

    @commands.command(name = 'eventpreview')
    async def event_preview(self, ctx, ch:discord.TextChannel):
        title = "**🎉    Surprise Event!**"
        body  = '```' + self.desc + '```'
        hint1 = f'`Hint 1: {self.hint1}`'
        hint2 = f'`Hint 2: {self.hint2}`'
        hint3 = f'`Hint 3: {self.hint3}`'
        desc  = f"{body}\n{hint1}\n{hint2}\n{hint3}\n"
        embed = discord.Embed(title=title, description=desc, color=discord.Color.purple())
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        await ch.send(content=f"", embed=embed)

    async def handle_win(self, ctx, win_msg):
        if self.prize_type == 'card':
            await db_utils.set_card_stars(self.prize_arg, 5)
            await db_utils.set_card_owner(self.prize_arg, win_msg.author.id)
            await db_utils.add_card_to_user(win_msg.author.id, self.prize_arg)
        elif self.prize_type == 'sc':
            await db_utils.update_user_currency(win_msg.author.id, int(self.prize_arg))
        elif self.prize_type == 'frame':
            await db_utils.update_user_frames(win_msg.author.id, self.prize_arg, 1)
        elif self.prize_type == 'roll':
            await db_utils.update_user_roll(win_msg.author.id, self.prize_arg, 1)

        title = "**🎉    Winner!**"
        desc   = f'` {win_msg.author.display_name} has won the event, congratulations! `'
        embed = discord.Embed(title=title, description=desc, color=discord.Color.purple())
        embed.set_thumbnail(url=win_msg.author.avatar_url)
        await self.ch.send(content=f"{self.bot.IUFI_ROLE.mention}", embed=embed)

    @commands.command(name = 'eventhint')
    async def event_hint(self, ctx, num: int):
        title = "**🎉    Surprise Event!**"
        body = '```' + self.desc + '```'
        hint1 = '`Hint 1:          hidden          `'
        hint2 = '`Hint 2:          hidden          `'
        hint3 = '`Hint 3:          hidden          `'
        if num == 1:
            hint1 = f'`Hint 1: {self.hint1}`'
        if num == 2:
            hint1 = f'`Hint 1: {self.hint1}`'
            hint2 = f'`Hint 2: {self.hint2}`'
        if num == 3:
            hint1 = f'`Hint 1: {self.hint1}`'
            hint2 = f'`Hint 2: {self.hint2}`'
            hint3 = f'`Hint 3: {self.hint3}`'
        desc  = f"{body}\n{hint1}\n{hint2}\n{hint3}\n"
        embed = discord.Embed(title=title, description=desc, color=discord.Color.purple())
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        await self.event_msg.edit(content=f"{self.bot.IUFI_ROLE.mention}", embed=embed)
