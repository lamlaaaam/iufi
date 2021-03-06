import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import db_utils
import photocard_utils
import discord
from   discord.ext import commands

class AuctionCog(commands.Cog):
    def __init__(self,
                 bot,
                 auction_time,
                 max_bid):
        self.bot             = bot
        self.auction_time    = auction_time
        self.max_bid         = max_bid
        self.auction_msg     = None
        self.highest_bidder  = None
        self.highest_bid     = 0
        self.auction_starter = None
        self.thread_pool     = ThreadPoolExecutor()
        self.loop            = asyncio.get_running_loop()

    async def card_not_found_error(self, ctx):
        await ctx.send(f"**{ctx.author.mention} this card does not exist.**", delete_after=2)

    async def card_not_owned_error(self, ctx):
        await ctx.send(f"**{ctx.author.mention} you do not own this card.**", delete_after=2)

    @commands.command(name = 'auction', aliases = ['a'])
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def auction(self, ctx, id_tag, min_bid=0):
        if self.auction_msg != None:
            await ctx.send(f"**{ctx.author.mention} there is an ongoing auction. Please wait for it to end.**", delete_after=2)
            self.auction.reset_cooldown(ctx)
            return

        if min_bid < 0:
            await ctx.send(f"**{ctx.author.mention} you cannot set a negative minimum bid.**", delete_after=2)
            self.auction.reset_cooldown(ctx)
            return
        if min_bid > self.max_bid:
            await ctx.send(f"**{ctx.author.mention} you cannot set a minimum bid higher than {self.max_bid}.**", delete_after=2)
            self.auction.reset_cooldown(ctx)
            return

        card_doc  = await db_utils.get_card(id_tag)
        user_doc  = await db_utils.get_user(ctx.author.id)
        if card_doc == None:
            await self.card_not_found_error(ctx)
            self.auction.reset_cooldown(ctx)
            return
        if card_doc['id'] not in user_doc['collection']:
            await self.card_not_owned_error(ctx)
            self.auction.reset_cooldown(ctx)
            return

        frame_doc = await db_utils.get_frame(card_doc['frame'])

        self.highest_bid     = min_bid
        self.auction_starter = ctx.author

        title          = f"**????   {ctx.author.display_name}'s Auction**"
        inst           = "Use `qbid amount` to participate.\n\n"
        id             = f"**????   `{card_doc['id']:04}`**\n"
        tag            = f"**???????   `{card_doc['tag']}`**\n"
        frame          = f"**???????   `{frame_doc['tag']}`**\n"
        rarity         = f"**{self.bot.RARITY[card_doc['rarity']]}   `{self.bot.RARITY_NAME[card_doc['rarity']]}`**\n"
        scount         = card_doc['stars']
        #stars          = '???' * scount + self.bot.BS * (self.bot.STARS_MAX-scount)
        #stars          = '**???   ' + stars + '**\n\n'
        stars          = f"**???   `{scount}`**\n\n"
        highest_bidder = f"**Highest bidder: `None`**\n"
        highest_bid    = f"**Amount to beat: `{min_bid} ????`**\n\n"
        timer          = "**Time:\n**" + '??? ' * 10 + '\n\n'
        desc           = inst + id + tag + frame + rarity + stars + highest_bidder + highest_bid + timer + '\n\n'
        embed          = discord.Embed(title=title, description=desc, color=discord.Color.dark_red())

        if card_doc['stars'] < self.bot.STARS_MAX:
            card_img = await (await self.loop.run_in_executor(self.thread_pool, partial(photocard_utils.create_photocard, card_doc)))
            card_attachment = await (await self.loop.run_in_executor(self.thread_pool, partial(photocard_utils.pillow_to_attachment, card_img, self.bot.WASTELAND)))
        else:
            card_img = await (await self.loop.run_in_executor(self.thread_pool, partial(photocard_utils.create_gif_photocard, card_doc)))
            card_attachment = await (await self.loop.run_in_executor(self.thread_pool, partial(photocard_utils.pillow_to_attachment, card_img, self.bot.WASTELAND, True)))
        embed.set_image(url=card_attachment)
        embed.set_thumbnail(url=ctx.author.avatar_url)

        self.auction_msg     = await ctx.send(embed=embed)
        local_msg            = self.auction_msg
        sleep_interval       = self.auction_time // 10
        for i in range(10):
            await asyncio.sleep(sleep_interval)
            highest_bidder    = f"**Highest bidder: `{self.highest_bidder.display_name if self.highest_bidder else 'None'}`**\n"
            highest_bid       = f"**Amount to beat: `{self.highest_bid} ????`**\n\n"
            timer             = "**Time:\n**" + '???? ' * (i+1) + '??? ' * (10-i-1) + '\n\n'
            desc              = inst + id + tag + frame + rarity + stars + highest_bidder + highest_bid + timer + '\n\n'
            embed.description = desc
            await self.auction_msg.edit(embed=embed)
        self.auction_msg    = None
        embed.color = discord.Color.greyple()
        await local_msg.edit(embed=embed)

        if self.highest_bidder != None:
            user_doc  = await db_utils.get_user(self.highest_bidder.id)
            amount_ok = user_doc['currency'] >= self.highest_bid
            space_ok  = len(user_doc['collection']) < self.bot.INVENTORY_LIMIT
            card_ok   = card_doc['id'] in (await db_utils.get_user(ctx.author.id))['collection']
            if amount_ok and card_ok and space_ok:
                await db_utils.update_user_currency(self.highest_bidder.id, -self.highest_bid)
                await db_utils.update_user_currency(ctx.author.id, self.highest_bid)
                await db_utils.remove_card_from_user(ctx.author.id, card_doc['id'])
                await db_utils.add_card_to_user(self.highest_bidder.id, card_doc['id'])
                await db_utils.set_card_owner(card_doc['id'], self.highest_bidder.id)
                embed = discord.Embed(title="???? Auction", description=f"**???? Card ` {card_doc['id']:04} `\n???? Bid ` {self.highest_bid} `\n???? Winner ` {self.highest_bidder.display_name} `**", color=discord.Color.random())
                await local_msg.reply(embed=embed)
            else:
                await ctx.send(f"**The auction transaction has failed. The card might have become unavailable during the auction, or the winner has no inventory space.**")
        else:
            embed = discord.Embed(title="???? Auction", description=f"**The auction ended with no winner.**", color=discord.Color.random())
            await local_msg.reply(embed=embed)

        self.highest_bidder  = None
        self.highest_bid     = 0
        self.auction_starter = None

    @commands.command(name = 'bid', aliases = ['bi'])
    async def bid(self, ctx, amt: int):
        if self.auction_msg == None:
            await ctx.send(f'**{ctx.author.mention} there is no ongoing auction.**', delete_after=2)
            return
        if ctx.author == self.auction_starter:
            await ctx.send(f'**{ctx.author.mention} you cannot bid for your own auction.**', delete_after=2)
            return
        user_doc = await db_utils.get_user(ctx.author.id)
        currency = user_doc['currency']
        if amt <= 0 or amt > currency:
            await ctx.send(f'**{ctx.author.mention} invalid amount for bidding.**', delete_after=2)
            return
        if amt <= self.highest_bid:
            await ctx.send(f'**{ctx.author.mention} you must bid higher than {self.highest_bid}.**', delete_after=2)
            return
        
        self.highest_bidder = ctx.author
        self.highest_bid    = amt
        await ctx.send(f'**{ctx.author.mention} you have successfully placed a bid.**', delete_after=2)