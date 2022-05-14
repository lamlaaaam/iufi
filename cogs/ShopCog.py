import asyncio
import db_utils
import discord
from   async_timeout import timeout
from   discord.ext   import commands
from   discord       import SelectMenu, SelectOption

class ShopCog(commands.Cog):
    def __init__(self,
                 bot,
                 shop_msg,
                 shop_time):
        self.bot       = bot
        self.shop_msg  = shop_msg
        self.shop_time = shop_time

    @commands.command(name = 'shop', aliases = ['s'])
    @commands.check(db_utils.does_user_exist)
    async def shop(self, ctx):
        id            = ctx.author.id
        user          = await self.bot.GUILD.fetch_member(id)
        user_doc      = await db_utils.get_user(id)
        user_currency = user_doc['currency']
        title         = "**🛒   IUFI Shop**"
        desc          = f"**🍬 Starcandies: `{user_currency}`\n**"
        desc         += self.shop_msg
        embed         = discord.Embed(title=title, description=desc, color=discord.Color.red())

        embed.set_thumbnail(url=user.avatar_url)

        components = [[
            SelectMenu(custom_id = 'shop_menu', options = [
                SelectOption(emoji = '🃏', label='CLAIM',          value='0', description='Resets your claim cooldown.'),
                SelectOption(emoji = '🎲', label='ROLL',           value='1', description='Resets your roll cooldown.'),
                SelectOption(emoji = '🌸', label='RARE ROLL',      value='2', description='A roll with at least one rare card.'),
                SelectOption(emoji = '💎', label='EPIC ROLL',      value='3', description='A roll with at least one epic card.'),
                SelectOption(emoji = '👑', label='LEGENDARY ROLL', value='4', description='A roll with at least one legendary card.')],
                placeholder = 'Pick an item to purchase')]]

        shop_msg = await ctx.send(embed=embed, components=components)

        def check(i: discord.ComponentInteraction, com):
            return i.author == ctx.author and i.message.id == shop_msg.id

        async def buy(i):
            nonlocal shop_msg
            if   i == 0 and user_currency >= 2:
                await db_utils.update_user_currency(id, -2)
                await db_utils.set_user_cooldown(id, 'next_claim')
                await ctx.send(f"**{ctx.author.mention} you have purchased a CLAIM reset.**", delete_after=3)
            elif i == 1 and user_currency >= 5:
                await db_utils.update_user_currency(id, -5)
                await db_utils.set_user_cooldown(id, 'next_roll')
                await ctx.send(f"**{ctx.author.mention} you have purchased a ROLL reset.**", delete_after=3)
            elif i == 2 and user_currency >= 10:
                await ctx.send(f"**{ctx.author.mention} this item is not available yet.**", delete_after=3)
            elif i == 3 and user_currency >= 100:
                await ctx.send(f"**{ctx.author.mention} this item is not available yet.**", delete_after=3)
            elif i == 4 and user_currency >= 1000:
                await ctx.send(f"**{ctx.author.mention} this item is not available yet.**", delete_after=3)
            else:
                await ctx.send(f"**{ctx.author.mention} you do not have enough starcandies.**", delete_after=3)

            desc              = f"**🍬 Starcandies: `{(await db_utils.get_user(id))['currency']}`\n**"
            desc             += self.shop_msg
            embed.description = desc
            await shop_msg.edit(embed=embed)

        try:
            async with timeout(self.shop_time):
                while True:
                    interaction, select = await self.bot.wait_for('selection_select', check = check)
                    await interaction.defer()
                    await buy(select.values[0])
        except asyncio.exceptions.TimeoutError:
            pass

        await shop_msg.delete()