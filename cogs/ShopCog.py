import db_utils
import discord
from   discord.ext   import commands

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
        #desc          = f"**`Welcome to IUFI Shop! What do you need?`**\n"
        desc          = f"```Buy using qbuy item_id quantity\n"
        desc         += f"WARNING: DO NOT BUY MULTIPLE RESETS```\n"
        #desc         += f"**🍬 Starcandies: `{user_currency}`**\n"
        shop_list     = '\n'.join([f"🆔 {i:<2} {emoji} {name:<16} {price:>4} 🍬" for i, (emoji, name, price, _, _) in enumerate(self.shop_list)])
        desc         += '```' + shop_list + '```'
        embed         = discord.Embed(title=title, description=desc, color=discord.Color.red())

        embed.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=embed)
    
    @commands.command(name = 'buy', aliases = ['b'])
    async def buy(self, ctx, item_id: int, amt: int=1):
        if not 0 <= item_id < len(self.shop_list):
            await ctx.send(f"**{ctx.author.mention} the item ID is invalid.**", delete_after=2)
            return
        if amt <= 0:
            await ctx.send(f"**{ctx.author.mention} the amount is invalid.**", delete_after=2)
            return
        emoji, name, price, _, effect = self.shop_list[item_id]
        if (await db_utils.get_user(ctx.author.id))['currency'] >= price * amt:
            await db_utils.update_user_currency(ctx.author.id, -(price * amt))
            await effect(ctx.author.id, amt)
            embed = discord.Embed(title="🛒 Shop Purchase Result", description=f"**{emoji} {name} ` {amt} `**", color=discord.Color.random())
            await ctx.reply(embed=embed)
        else:
            await ctx.send(f"**{ctx.author.mention} you do not have enough starcandies.**", delete_after=2)
