import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import random
import re
import db_utils
import photocard_utils
import discord
from   discord.ext import commands

class CardCommandsCog(commands.Cog):
    def __init__(self, bot, modes):
        self.bot       = bot
        self.tag_limit = 10
        self.modes     = modes
        self.thread_pool = ThreadPoolExecutor()
        self.loop        = asyncio.get_running_loop()

    async def card_not_found_error(self, ctx):
        await ctx.send(f"**{ctx.author.mention} this card does not exist.**", delete_after=2)

    async def card_not_owned_error(self, ctx):
        await ctx.send(f"**{ctx.author.mention} you do not own this card.**", delete_after=2)

    async def show_card_info(self, ctx, id):
        card_doc  = await db_utils.get_card(id)
        frame_doc = await db_utils.get_frame(card_doc['frame'])

        title  = "**ℹ️   Card Info**"
        id     = f"**🆔   `{card_doc['id']:04}`**\n"
        tag    = f"**🏷️   `{card_doc['tag']}`**\n"
        frame  = f"**🖼️   `{frame_doc['tag']}`**\n"
        rarity = f"**{self.bot.RARITY[card_doc['rarity']]}   `{self.bot.RARITY_NAME[card_doc['rarity']]}`**\n"
        if card_doc['owned_by'] != None:
            scount = card_doc['stars']
            #stars  = '⭐' * scount + self.bot.BS * (self.bot.STARS_MAX-scount)
            #stars  = '**✨   ' + stars + '**\n\n'
            stars  = f"**⭐   `{scount}`**\n\n"
        else:
            stars = '\n'
        try:
            owner  = await self.bot.GUILD.fetch_member(card_doc['owned_by'])
            owned  = f"**Owned by:   `{owner.display_name}`**"
        except:
            owned  = "**Owned by:   nobody**"
        desc   = id + tag + frame + rarity + stars + owned + '\n\n'
        embed = discord.Embed(title=title, description=desc, color=discord.Color.dark_grey())

        if card_doc['stars'] < self.bot.STARS_MAX:
            card_img = await (await self.loop.run_in_executor(self.thread_pool, partial(photocard_utils.create_photocard, card_doc)))
            card_attachment = await (await self.loop.run_in_executor(self.thread_pool, partial(photocard_utils.pillow_to_attachment, card_img, self.bot.WASTELAND)))
        else:
            card_img = await (await self.loop.run_in_executor(self.thread_pool, partial(photocard_utils.create_gif_photocard, card_doc)))
            card_attachment = await (await self.loop.run_in_executor(self.thread_pool, partial(photocard_utils.pillow_to_attachment, card_img, self.bot.WASTELAND, True)))
        embed.set_image(url=card_attachment)

        try:
            embed.set_thumbnail(url=owner.avatar_url)
        except:
            pass
        await ctx.send(embed=embed)

    @commands.command(name = 'cardinfo', aliases = ['i'])
    async def card_info(self, ctx, id_tag):
        card_doc = await db_utils.get_card(id_tag)
        if card_doc == None:
            await self.card_not_found_error(ctx)
            return
        await self.show_card_info(ctx, card_doc['id'])

    @commands.command(name = 'cardinfolast', aliases = ['il'])
    async def card_info_last(self, ctx):
        last_card = await self.get_last_card_id(ctx.author.id)
        if last_card == None:
            await ctx.send(f'**{ctx.author.mention} you have no photocards.**', delete_after=2)
            return
        await self.show_card_info(ctx, last_card)


    @commands.command(name = 'settag', aliases = ['st'])
    async def set_tag(self, ctx, id_tag, tag):
        card_doc = await db_utils.get_card(id_tag)
        user_doc = await db_utils.get_user(ctx.author.id)
        if card_doc == None:
            await self.card_not_found_error(ctx)
            return
        if card_doc['id'] not in user_doc['collection']:
            await self.card_not_owned_error(ctx)
            return
        if not re.match("^[A-Za-z0-9]*$", tag):
            await ctx.send(f"**{ctx.author.mention} the tag name must be alphanumeric.**", delete_after=2)
            return
        if len(tag) > self.tag_limit:
            await ctx.send(f"**{ctx.author.mention} the tag name cannot be longer than {self.tag_limit} characters.**", delete_after=2)
            return
        if tag.isdigit():
            await ctx.send(f"**{ctx.author.mention} the tag name cannot be fully numbers.**", delete_after=2)
            return
        if await db_utils.get_card(tag) != None:
            await ctx.send(f"**{ctx.author.mention} there is already a card with this tag.**", delete_after=2)
            return
        await db_utils.set_card_tag(id_tag, tag)
        await ctx.send(f"**{ctx.author.mention} you have set the tag.**", delete_after=2)
        
    @commands.command(name = 'settaglast', aliases = ['stl'])
    async def set_tag_last(self, ctx, tag):
        if not re.match("^[A-Za-z0-9]*$", tag):
            await ctx.send(f"**{ctx.author.mention} the tag name must be alphanumeric.**", delete_after=2)
            return
        if len(tag) > self.tag_limit:
            await ctx.send(f"**{ctx.author.mention} the tag name cannot be longer than {self.tag_limit} characters.**", delete_after=2)
            return
        if tag.isdigit():
            await ctx.send(f"**{ctx.author.mention} the tag name cannot be fully numbers.**", delete_after=2)
            return
        if await db_utils.get_card(tag) != None:
            await ctx.send(f"**{ctx.author.mention} there is already a card with this tag.**", delete_after=2)
            return

        last_card = await self.get_last_card_id(ctx.author.id)
        if last_card == None:
            await ctx.send(f'**{ctx.author.mention} you have no photocards.**', delete_after=2)
            return

        await db_utils.set_card_tag(last_card, tag)
        await ctx.send(f"**{ctx.author.mention} you have set the tag.**", delete_after=2)

    @commands.command(name = 'removetag', aliases = ['rt'])
    async def remove_tag(self, ctx, id_tag):
        card_doc = await db_utils.get_card(id_tag)
        user_doc = await db_utils.get_user(ctx.author.id)
        if card_doc == None:
            await self.card_not_found_error(ctx)
            return
        if card_doc['id'] not in user_doc['collection']:
            await self.card_not_owned_error(ctx)
            return

        await db_utils.set_card_tag(id_tag, None)
        await ctx.send(f"**{ctx.author.mention} you have removed the tag.**", delete_after=2)

    async def get_last_card_id(self, user_id):
        user_doc = await db_utils.get_user(user_id)
        cards = user_doc['collection']
        if len(cards) == 0:
            return None
        return cards[-1]

    @commands.command(name = 'convert', aliases = ['c'])
    async def convert(self, ctx, *id_tags):
        id_tags    = [int(it) if it.isnumeric() else it for it in id_tags]
        valid_docs = await db_utils.get_cards({'owned_by': ctx.author.id, '$or': [{'id': {'$in': id_tags}}, {'tag': {'$in': id_tags}}]})
        success    = len(valid_docs)
        reward     = sum([self.bot.RARITY_SC[doc['rarity']] for doc in valid_docs])
        card_ids   = [doc['id'] for doc in valid_docs]
        await db_utils.convert_cards(ctx.author.id, card_ids, reward)
        await ctx.send(f"**{ctx.author.mention} you converted {success} photocards into {reward} starcandies.**", delete_after=2)

    @commands.command(name = 'convertall')
    async def convert_all(self, ctx):
        valid_docs = await db_utils.get_cards({'owned_by': ctx.author.id})
        success    = len(valid_docs)
        reward     = sum([self.bot.RARITY_SC[doc['rarity']] for doc in valid_docs])
        card_ids   = [doc['id'] for doc in valid_docs]
        await db_utils.convert_cards(ctx.author.id, card_ids, reward)
        await ctx.send(f"**{ctx.author.mention} you converted all {success} photocards into {reward} starcandies.**", delete_after=2)

    @commands.command(name = 'convertmass', aliases=['cm'])
    async def convert_mass(self, ctx, mode):
        mode = mode.lower()
        if mode not in self.modes:
            raise commands.BadArgument
        if mode == 'notag':
            valid_docs = await db_utils.get_cards({'owned_by': ctx.author.id, 'tag': None})
        if mode == 'common':
            valid_docs = await db_utils.get_cards({'owned_by': ctx.author.id, 'rarity': 0})
        if mode == 'rare':
            valid_docs = await db_utils.get_cards({'owned_by': ctx.author.id, 'rarity': 1})
        if mode == 'epic':
            valid_docs = await db_utils.get_cards({'owned_by': ctx.author.id, 'rarity': 2})
        if mode == 'legend':
            valid_docs = await db_utils.get_cards({'owned_by': ctx.author.id, 'rarity': 3})
        success    = len(valid_docs)
        reward     = sum([self.bot.RARITY_SC[doc['rarity']] for doc in valid_docs])
        card_ids   = [doc['id'] for doc in valid_docs]
        await db_utils.convert_cards(ctx.author.id, card_ids, reward)
        await ctx.send(f"**{ctx.author.mention} you converted {success} {mode} photocards into {reward} starcandies.**", delete_after=2)

    @commands.command(name = 'convertlast', aliases = ['cl'])
    async def convert_last(self, ctx):
        last_card = await self.get_last_card_id(ctx.author.id)
        if last_card == None:
            await ctx.send(f'**{ctx.author.mention} you have no photocards.**', delete_after=2)
            return
        reward = self.bot.RARITY_SC[(await db_utils.get_card(last_card))['rarity']]
        await db_utils.convert_cards(ctx.author.id, [last_card], reward)
        await ctx.send(f'**{ctx.author.mention} you converted your last photocard into {reward} starcandies.**', delete_after=2)

    async def main_card(self, user_id, card_id):
        await db_utils.set_main(user_id, card_id)

    @commands.command(name = 'main', aliases = ['m'])
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
        await ctx.send(f'**{ctx.author.mention} you have set a main photocard.**', delete_after=2)

    @commands.command(name = 'mainlast', aliases = ['ml'])
    async def main_last(self, ctx):
        last_card = await self.get_last_card_id(ctx.author.id)
        if last_card == None:
            await ctx.send(f'**{ctx.author.mention} you have no photocards.**', delete_after=2)
            return
        await self.main_card(ctx.author.id, last_card)
        await ctx.send(f'**{ctx.author.mention} you have set your last photocard as your main.**', delete_after=2)

    @commands.command(name = 'giftpc', aliases = ['gpc'])
    async def gift_pc(self, ctx, rec: discord.Member, *id_tags):
        if rec.id == ctx.author.id:
            await ctx.send(f'**{ctx.author.mention} you cannot gift yourself.**', delete_after=2)
            return
        if not await db_utils.does_user_exist(rec.id):
            await ctx.send(f'**{ctx.author.mention} the recipient is not registered.**', delete_after=2)
            return

        id_tags    = [int(it) if it.isnumeric() else it for it in id_tags]
        valid_docs = await db_utils.get_cards({'owned_by': ctx.author.id, '$or': [{'id': {'$in': id_tags}}, {'tag': {'$in': id_tags}}]})
        success    = len(valid_docs)
        card_ids   = [doc['id'] for doc in valid_docs]
        await db_utils.gift_cards(ctx.author.id, rec.id, card_ids)
        await ctx.send(f'**{ctx.author.mention} you gifted {success} photocards.**', delete_after=2)
        if success > 0:
            try:
                ch = await rec.create_dm()
                ids = ', '.join([f"{i:04}" for i in card_ids])
                if len(valid_docs) == 1:
                    doc    = valid_docs[0]
                    id     = doc['id']
                    rarity = self.bot.RARITY[doc['rarity']]
                    stars  = doc['stars']
                    await ch.send(f'**you have received ` 🆔 {id:04} | {rarity} | ⭐ {stars} ` from {ctx.author.display_name}**')
                else:
                    await ch.send(f'**you have received ` 🆔 {ids} ` from {ctx.author.display_name}**')
            except discord.Forbidden:
                pass

    @commands.command(name = 'giftpclast', aliases = ['gpcl'])
    async def gift_pc_last(self, ctx, rec: discord.Member=None):
        if rec == None:
            await ctx.send(f'**{ctx.author.mention} pick a recipient for your gifts.**', delete_after=2)
            return
        if rec.id == ctx.author.id:
            await ctx.send(f'**{ctx.author.mention} you cannot gift yourself.**', delete_after=2)
            return
        if not await db_utils.does_user_exist(rec.id):
            await ctx.send(f'**{ctx.author.mention} the recipient is not registered.**', delete_after=2)
            return

        last_card = await self.get_last_card_id(ctx.author.id)
        if last_card == None:
            await ctx.send(f'**{ctx.author.mention} you have no photocards.**', delete_after=2)
            return

        await db_utils.gift_cards(ctx.author.id, rec.id, [last_card])
        await ctx.send(f'**{ctx.author.mention} you have gifted your last photocard.**', delete_after=2)
        try:
            ch     = await rec.create_dm()
            doc    = await db_utils.get_card(last_card)
            id     = doc['id']
            rarity = self.bot.RARITY[doc['rarity']]
            stars  = doc['stars']
            await ch.send(f'**you have received ` 🆔 {id:04} | {rarity} | ⭐ {stars} ` from {ctx.author.display_name}**')
        except discord.Forbidden:
            pass

    async def set_fave(self, user_id, card_id, slot):
        await db_utils.set_user_fave(user_id, card_id, slot-1)

    @commands.command(name = 'removefaves', aliases = ['rf'])
    async def remove_faves(self, ctx, slot: int):
        if slot <= 0 or slot > 6:
            await ctx.send(f"**{ctx.author.mention} you have selected an invalid slot.**", delete_after=2)
            return
        await db_utils.remove_user_fave(ctx.author.id, slot-1)
        await ctx.send(f'**{ctx.author.mention} you have removed the favorite photocard in slot {slot}.**', delete_after=2)

    @commands.command(name = 'setfaves', aliases = ['sf'])
    async def set_faves(self, ctx, slot: int, id_tag):
        if slot <= 0 or slot > 6:
            await ctx.send(f"**{ctx.author.mention} you have selected an invalid slot.**", delete_after=2)
            return
        card_doc = await db_utils.get_card(id_tag)
        user_doc = await db_utils.get_user(ctx.author.id)
        if card_doc == None:
            await self.card_not_found_error(ctx)
            return
        if card_doc['id'] not in user_doc['collection']:
            await self.card_not_owned_error(ctx)
            return
        if card_doc['id'] in user_doc['faves']:
            await db_utils.remove_user_fave(ctx.author.id, user_doc['faves'].index(card_doc['id']))
        await self.set_fave(ctx.author.id, card_doc['id'], slot)
        await ctx.send(f'**{ctx.author.mention} you have set a favorite photocard in slot {slot}.**', delete_after=2)

    @commands.command(name = 'setfaveslast', aliases = ['sfl'])
    async def set_faves_last(self, ctx, slot: int):
        if slot <= 0 or slot > 6:
            await ctx.send(f"**{ctx.author.mention} you have selected an invalid slot.**", delete_after=2)
            return
        last_card = await self.get_last_card_id(ctx.author.id)
        user_doc = await db_utils.get_user(ctx.author.id)
        if last_card == None:
            ctx.send(f'**{ctx.author.mention} you have no photocards.**', delete_after=2)
            return
        if last_card in user_doc['faves']:
            await db_utils.remove_user_fave(ctx.author.id, user_doc['faves'].index(last_card))
        await self.set_fave(ctx.author.id, last_card, slot)
        await ctx.send(f'**{ctx.author.mention} you have set your last photocard as a favorite in slot {slot}.**', delete_after=2)

    @commands.command(name = 'upgrade', aliases = ['u'])
    async def upgrade(self, ctx, id_tag):
        user_doc   = await db_utils.get_user(ctx.author.id)
        card_doc   = await db_utils.get_card(id_tag)
        if card_doc == None:
            await self.card_not_found_error(ctx)
            return
        if card_doc['id'] not in user_doc['collection']:
            await self.card_not_owned_error(ctx)
            return
        if user_doc['upgrades'] <= 0:
            await ctx.send(f"**{ctx.author.mention} you have no upgrades.**", delete_after=2)
            return
        if card_doc['stars'] >= self.bot.STARS_MAX:
            await ctx.send(f"**{ctx.author.mention} the card is already at max stars.**", delete_after=2)
            return
        await db_utils.update_user_upgrades(ctx.author.id, -1)
        success = random.randint(1,100) <= self.bot.STARS_PROB[card_doc['stars']-1]
        if success:
            await db_utils.update_card_stars(card_doc['id'], 1, self.bot.STARS_MAX)
            await ctx.send(f"**{ctx.author.mention} the upgrade was successful.**", delete_after=2)
        else:
            await ctx.send(f"**{ctx.author.mention} the upgrade failed.**", delete_after=2)

