import asyncio
import db_utils
import discord
from   async_timeout import timeout
from   discord.ext   import commands
from   discord       import SelectMenu, SelectOption

class ShopCog(commands.Cog):
    def __init__(self,
                 bot,
                 shop_list,
                 shop_time):
        self.bot       = bot
        self.shop_list  = shop_list
        self.shop_time = shop_time

    @commands.command(name = 'shop', aliases = ['s'])
    async def shop(self, ctx):
        id            = ctx.author.id
        user          = await self.bot.GUILD.fetch_member(id)
        user_doc      = await db_utils.get_user(id)
        user_currency = user_doc['currency']
        title         = "**🛒   IUFI Shop**"
        desc          = f"**`Welcome to IUFI Shop! What do you need?`**\n\n"
        desc         += f"**🍬 Starcandies: `{user_currency}`**\n"
        embed         = discord.Embed(title=title, description=desc, color=discord.Color.red())

        embed.set_thumbnail(url=user.avatar_url)

        options    = [SelectOption(emoji=emoji, label=f"{name}  ({price} 🍬)", value=str(i), description=desc) 
                      for i, (emoji, name, price, desc, _) in enumerate(self.shop_list)]
        components = [[SelectMenu(custom_id='shop_menu', options=options, placeholder = 'Pick an item to purchase')]]

        shop_msg = await ctx.send(embed=embed, components=components)

        def check(i: discord.ComponentInteraction, com):
            return i.author == ctx.author and i.message.id == shop_msg.id

        async def buy(i):
            nonlocal shop_msg
            emoji, name, price, _, effect = self.shop_list[i]
            if (await db_utils.get_user(id))['currency'] >= price:
                await db_utils.update_user_currency(id, -price)
                await effect(id)
                await ctx.send(f"**{ctx.author.mention} you have purchased `{emoji} {name}`.**", delete_after=2)
            else:
                await ctx.send(f"**{ctx.author.mention} you do not have enough starcandies.**", delete_after=2)

            desc              = f"**`Welcome to IUFI Shop! What do you need?`**\n\n"
            desc             += f"**🍬 Starcandies: `{(await db_utils.get_user(id))['currency']}`\n**"
            embed.description = desc
            await shop_msg.edit(embed=embed)

        try:
            async with timeout(self.shop_time):
                while True:
                    interaction, select = await self.bot.wait_for('selection_select', check = check)
                    await buy(select.values[0])
        except asyncio.exceptions.TimeoutError:
            pass

        await shop_msg.delete()