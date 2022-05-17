import re
import db_utils
import photocard_utils
import discord
from   discord.ext import commands

class CardCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot       = bot
        self.tag_limit = 10

    async def card_not_found_error(self, ctx):
        await ctx.send(f"**{ctx.author.mention} this card does not exist.**")

    async def card_not_owned_error(self, ctx):
        await ctx.send(f"**{ctx.author.mention} you do not own this card.**")

    @commands.command(name = 'cardinfo', aliases = ['i'])
    @commands.check(db_utils.does_user_exist)
    async def cardinfo(self, ctx, id_tag):
        card_doc = await db_utils.get_card(id_tag)
        if card_doc == None:
            await self.card_not_found_error(ctx)
            return

        title  = "**ℹ️   Card Info**"
        id     = f"**🆔   `{card_doc['id']:04}`**\n"
        tag    = f"**🏷️   `{card_doc['tag']}`**\n"
        rarity = f"**{self.bot.RARITY[card_doc['rarity']]}   `{self.bot.RARITY_NAME[card_doc['rarity']]}`**\n\n"
        try:
            owner  = await self.bot.GUILD.fetch_member(card_doc['owned_by'])
            owned  = f"**Owned by:   `{owner.display_name}`**"
        except:
            owned  = "**Owned by:   nobody**"
        desc   = id + tag + rarity + owned + '\n\n'
        desc  += "🌸 "*10 + '\n\n'
        embed = discord.Embed(title=title, description=desc, color=discord.Color.dark_grey())

        img_url         = card_doc['url']
        card_img        = await photocard_utils.create_photocard(img_url, border=True, fade=True)
        card_attachment = await photocard_utils.pillow_to_attachment(card_img, self.bot.WASTELAND)
        embed.set_image(url=card_attachment)

        try:
            embed.set_thumbnail(url=owner.avatar_url)
        except:
            pass

        await ctx.send(embed=embed)

    @commands.command(name = 'settag', aliases = ['st'])
    @commands.check(db_utils.does_user_exist)
    async def settag(self, ctx, id_tag, tag):
        card_doc = await db_utils.get_card(id_tag)
        user_doc = await db_utils.get_user(ctx.author.id)
        if card_doc == None:
            await self.card_not_found_error(ctx)
            return
        if card_doc['id'] not in user_doc['collection']:
            await self.card_not_owned_error(ctx)
            return
        if not re.match("^[A-Za-z0-9]*$", tag):
            await ctx.send(f"**{ctx.author.mention} the tag name must be alphanumeric.**")
            return
        if len(tag) > self.tag_limit:
            await ctx.send(f"**{ctx.author.mention} the tag name cannot be longer than {self.tag_limit} characters.**")
            return
        if tag.isdigit():
            await ctx.send(f"**{ctx.author.mention} the tag name cannot be fully numbers.**")
            return
        if await db_utils.get_card(tag) != None:
            await ctx.send(f"**{ctx.author.mention} there is already a card with this tag.**")
            return

        await db_utils.set_card_tag(id_tag, tag)
        await ctx.send(f"**{ctx.author.mention} you have set the tag successfully.**")
        
    @commands.command(name = 'settaglast', aliases = ['stl'])
    @commands.check(db_utils.does_user_exist)
    async def settaglast(self, ctx, tag):
        if len(tag) > self.tag_limit:
            await ctx.send(f"**{ctx.author.mention} the tag name cannot be longer than {self.tag_limit} characters.**")
            return
        if tag.isdigit():
            await ctx.send(f"**{ctx.author.mention} the tag name cannot be fully numbers.**")
            return
        if await db_utils.get_card(tag) != None:
            await ctx.send(f"**{ctx.author.mention} there is already a card with this tag.**")
            return

        last_card = await self.get_last_card_id(ctx.author.id)
        if last_card == None:
            ctx.send(f'**{ctx.author.mention} you have no photocards.**')
            return

        await db_utils.set_card_tag(last_card, tag)
        await ctx.send(f"**{ctx.author.mention} you have set the tag successfully.**")

    @commands.command(name = 'removetag', aliases = ['rt'])
    @commands.check(db_utils.does_user_exist)
    async def removetag(self, ctx, id_tag):
        card_doc = await db_utils.get_card(id_tag)
        user_doc = await db_utils.get_user(ctx.author.id)
        if card_doc == None:
            await self.card_not_found_error(ctx)
            return
        if card_doc['id'] not in user_doc['collection']:
            await self.card_not_owned_error(ctx)
            return

        await db_utils.set_card_tag(id_tag, None)
        await ctx.send(f"**{ctx.author.mention} you have removed the tag successfully.**")

    async def get_last_card_id(self, user_id):
        user_doc = await db_utils.get_user(user_id)
        cards = user_doc['collection']
        if len(cards) == 0:
            return None
        return cards[-1]

    async def convert_card(self, user_id, card_id, rarity):
        reward = self.bot.RARITY_SC[rarity]
        await db_utils.remove_card_from_user(user_id, card_id)
        await db_utils.set_card_availability(card_id, True)
        await db_utils.set_card_tag(card_id, None)
        await db_utils.set_card_owner(card_id, None)
        await db_utils.update_user_currency(user_id, reward)
        return reward

    @commands.command(name = 'convert', aliases = ['c'])
    @commands.check(db_utils.does_user_exist)
    async def convert(self, ctx, *id_tags):
        success = 0
        fail    = 0
        total   = 0
        for id_tag in id_tags:
            card_doc = await db_utils.get_card(id_tag)
            user_doc = await db_utils.get_user(ctx.author.id)
            if card_doc == None or card_doc['id'] not in user_doc['collection']:
                fail += 1
                continue
            reward = await self.convert_card(ctx.author.id, card_doc['id'], card_doc['rarity'])
            success += 1
            total   += reward
        await ctx.send(f"**{ctx.author.mention} you requested to convert {len(id_tags)} photocard(s). {success} succeeded and {fail} failed. You gained {total} starcandies.**")

    @commands.command(name = 'convertlast', aliases = ['cl'])
    @commands.check(db_utils.does_user_exist)
    async def convert_last(self, ctx):
        last_card = await self.get_last_card_id(ctx.author.id)
        if last_card == None:
            ctx.send(f'**{ctx.author.mention} you have no photocards.**')
            return
        reward = await self.convert_card(ctx.author.id, last_card, (await db_utils.get_card(last_card))['rarity'])
        await ctx.send(f'**{ctx.author.mention} you converted your last photocard and gained {reward} starcandies.**')

    async def main_card(self, user_id, card_id):
        await db_utils.set_main(user_id, card_id)

    @commands.command(name = 'main', aliases = ['m'])
    @commands.check(db_utils.does_user_exist)
    async def main(self, ctx, id_tag):
        card_doc = await db_utils.get_card(id_tag)
        user_doc = await db_utils.get_user(ctx.author.id)
        if card_doc == None:
            await self.card_not_found_error(ctx)
            return
        if card_doc['id'] not in user_doc['collection']:
            await self.card_not_owned_error(ctx)
            return
        await self.main_card(ctx.author.id, card_doc['id'])
        await ctx.send(f'**{ctx.author.mention} you have successfully set a main photocard.**')

    @commands.command(name = 'mainlast', aliases = ['ml'])
    @commands.check(db_utils.does_user_exist)
    async def mainlast(self, ctx):
        last_card = await self.get_last_card_id(ctx.author.id)
        if last_card == None:
            ctx.send(f'**{ctx.author.mention} you have no photocards.**')
            return
        await self.main_card(ctx.author.id, last_card)
        await ctx.send(f'**{ctx.author.mention} you have successfully set your last photocard as your main.**')

    async def gift_card(self, giver, rec, card_id):
        await db_utils.remove_card_from_user(giver.id, card_id)
        await db_utils.add_card_to_user(rec.id, card_id)
        await db_utils.set_card_owner(card_id, rec.id)

    @commands.command(name = 'giftpc', aliases = ['gpc'])
    @commands.check(db_utils.does_user_exist)
    async def giftpc(self, ctx, rec: discord.Member, *id_tags):
        if rec.id == ctx.author.id:
            await ctx.send(f'**{ctx.author.mention} you cannot gift yourself.**')
            return
        if not await db_utils.does_user_exist(rec.id):
            await ctx.send(f'**{ctx.author.mention} the recipient is not registered.**')
            return

        success = 0
        fail    = 0
        for id_tag in id_tags:
            card_doc = await db_utils.get_card(id_tag)
            user_doc = await db_utils.get_user(ctx.author.id)
            if card_doc == None or card_doc['id'] not in user_doc['collection']:
                fail += 1
                continue
            await self.gift_card(ctx.author, rec, card_doc['id'])
            success += 1

        await ctx.send(f'**{ctx.author.mention} you requested to gift {len(id_tags)} photocard(s). {success} succeeded and {fail} failed.**')
        if success > 0:
            await ctx.send(f'**{rec.mention} you have received {success} photocard(s) from {ctx.author.mention}!**')

    @commands.command(name = 'giftpclast', aliases = ['gpcl'])
    @commands.check(db_utils.does_user_exist)
    async def giftpclast(self, ctx, rec: discord.Member=None):
        if rec == None:
            await ctx.send(f'**{ctx.author.mention} pick a recipient for your gifts.**')
            return
        if rec.id == ctx.author.id:
            await ctx.send(f'**{ctx.author.mention} you cannot gift yourself.**')
            return
        if not await db_utils.does_user_exist(rec.id):
            await ctx.send(f'**{ctx.author.mention} the recipient is not registered.**')
            return

        last_card = await self.get_last_card_id(ctx.author.id)
        if last_card == None:
            ctx.send(f'**{ctx.author.mention} you have no photocards.**')
            return

        await self.gift_card(ctx.author, rec, last_card)
        await ctx.send(f'**{ctx.author.mention} you have successfully gifted your last photocard.**')
        await ctx.send(f'**{rec.mention} you have received a photocard gift from {ctx.author.mention}!**')