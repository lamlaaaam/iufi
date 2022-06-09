import asyncio
from functools import partial
import random
import discord
import db_utils
import photocard_utils
import concurrent.futures
from   discord.ext   import commands
from   discord       import Button, ButtonStyle
from   async_timeout import timeout

class RollCog(commands.Cog):
    def __init__(self, 
                 bot,
                 roll_pc_count,
                 roll_claim_time,
                 roll_headstart_time,
                 roll_cooldown,
                 roll_claim_cooldown,
                 roll_common_cooldown):
        self.bot                 = bot
        self.roll_pc_count       = roll_pc_count
        self.roll_claim_time     = roll_claim_time
        self.roll_headstart_time = roll_headstart_time
        self.roll_cooldown       = roll_cooldown
        self.roll_claim_cooldown = roll_claim_cooldown
        self.loop                = asyncio.get_running_loop()
        self.thread_pool         = concurrent.futures.ThreadPoolExecutor()
        self.msg_to_event        = {}
        self._cd = commands.CooldownMapping.from_cooldown(1, roll_common_cooldown, commands.BucketType.channel)

    async def cog_check(self, ctx):
        bucket = self._cd.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            await ctx.send(f"**{ctx.author.mention} you rolled a little too close to someone else, try again in {round(retry_after)} second(s).**", delete_after=2)
            return False
        return True

    @commands.command(name = 'roll', aliases = ['r'])
    async def roll(self, ctx):
        ok, text = await db_utils.check_cooldown(ctx.author.id, 'next_roll')
        if not ok:
            await ctx.send(f'**{ctx.author.mention} your next roll is in {text}.**', delete_after=2)
            return

        await db_utils.set_user_cooldown(ctx.author.id, 'next_roll', m = self.roll_cooldown)
        await db_utils.set_user_cooldown(ctx.author.id, 'next_claim')

        success = await self.start_roll(ctx, 0)
        if not success:
            await ctx.send(f'**{ctx.author.mention} the roll has failed. Your roll has not been consumed.**', delete_after=2)
            await db_utils.set_user_cooldown(ctx.author.id, 'next_roll')

    @commands.command(name = 'rareroll', aliases = ['rr'])
    async def rareroll(self, ctx):
        user_doc = await db_utils.get_user(ctx.author.id)
        roll_amount = user_doc['rare_rolls']
        if roll_amount <= 0:
            await ctx.send(f"**{ctx.author.mention} you do not have any rare rolls to use.**", delete_after=2)
            return

        await db_utils.set_user_cooldown(ctx.author.id, 'next_claim')
        await db_utils.update_user_roll(ctx.author.id, 'rare_rolls', -1)

        success = await self.start_roll(ctx, 1)
        if not success:
            await ctx.send(f'**{ctx.author.mention} the roll has failed. Your roll has not been consumed.**', delete_after=2)
            await db_utils.update_user_roll(ctx.author.id, 'rare_rolls', 1)

    @commands.command(name = 'epicroll', aliases = ['er'])
    async def epicroll(self, ctx):
        user_doc = await db_utils.get_user(ctx.author.id)
        roll_amount = user_doc['epic_rolls']
        if roll_amount <= 0:
            await ctx.send(f"**{ctx.author.mention} you do not have any epic rolls to use.**", delete_after=2)
            return

        await db_utils.set_user_cooldown(ctx.author.id, 'next_claim')
        await db_utils.update_user_roll(ctx.author.id, 'epic_rolls', -1)

        success = await self.start_roll(ctx, 2)
        if not success:
            await ctx.send(f'**{ctx.author.mention} the roll has failed. Your roll has not been consumed.**', delete_after=2)
            await db_utils.update_user_roll(ctx.author.id, 'epic_rolls', 1)

    @commands.command(name = 'legendroll', aliases = ['lr'])
    async def legendroll(self, ctx):
        user_doc = await db_utils.get_user(ctx.author.id)
        roll_amount = user_doc['legend_rolls']
        if roll_amount <= 0:
            await ctx.send(f"**{ctx.author.mention} you do not have any legendary rolls to use.**", delete_after=2)
            return

        await db_utils.set_user_cooldown(ctx.author.id, 'next_claim')
        await db_utils.update_user_roll(ctx.author.id, 'legend_rolls', -1)

        success = await self.start_roll(ctx, 3)
        if not success:
            await ctx.send(f'**{ctx.author.mention} the roll has failed. Your roll has not been consumed.**', delete_after=2)
            await db_utils.update_user_roll(ctx.author.id, 'legend_rolls', 1)

    async def start_roll(self, ctx, rarity_bias):
        async def expire_msg():
            content    = "*⏳ This roll has expired.*"
            for i in range(self.roll_pc_count):
                components[0][i].style    = ButtonStyle.gray
                components[0][i].disabled = True
            await roll_msg.edit(content=content, components=components)

        async def button_check(id):
            if not await db_utils.does_user_exist(id):
                return False
            if id in already_claimed:
                return False
            ok, text = await db_utils.check_cooldown(id, 'next_claim')
            if not ok:
                return False
            if roll_headstart_id != None and id != roll_headstart_id:
                return False
            return True

        def check(i: discord.ComponentInteraction, com):
            return i.message.id == roll_msg.id

        async def handle_claim(uid, card_index):
            nonlocal taken
            if card_index in index_taken:
                return
            components[0][card_index].disabled = True
            doc    = roll_pc_docs[card_index]
            no     = card_index + 1
            id     = doc['id']
            rarity = self.bot.RARITY[doc['rarity']]
            await roll_msg.edit(components=components)
            already_claimed.append(uid)
            taken += 1
            index_taken.append(card_index)
            stars = random.randint(1, self.bot.STARS_MAX // 2)
            await db_utils.set_card_stars(roll_pc_ids[card_index], stars)
            await db_utils.set_card_owner(roll_pc_ids[card_index], uid)
            await db_utils.add_card_to_user(uid, roll_pc_ids[card_index])
            await db_utils.set_user_cooldown(uid, 'next_claim', m = self.roll_claim_cooldown)
            await roll_msg.channel.send(f'**{self.bot.get_user(uid).mention} has claimed ` {no} | 🆔 {id:04} | {rarity} | ⭐ {stars} `**')

        async def handle_event(event):
            id, btn_index = event
            if await button_check(id):
                await handle_claim(id, btn_index)

        roll_pc_docs = await db_utils.get_random_cards(self.roll_pc_count, self.bot.RARITY_PROB, rarity_bias)
        if roll_pc_docs == None:
            return False
        roll_pc_ids  = [doc['id'] for doc in roll_pc_docs]
        print('Rolled', roll_pc_docs)

        if len(roll_pc_docs) == 0:
            await ctx.send('**The pool is empty!**', delete_after=2)
            return
        stitched_img = await (await self.loop.run_in_executor(self.thread_pool, partial(photocard_utils.stitch_images, roll_pc_docs)))
        if stitched_img == None:
            await ctx.send("**The roll could not load due to server error. And no don't ping 8 bol he can't do shit it's the image hosting site giving up. Try again later.**", delete_after=2)
            return False
        stitched_img = await (await self.loop.run_in_executor(self.thread_pool, partial(photocard_utils.pillow_to_file, stitched_img)))

        roll_headstart_id = ctx.author.id

        content = f'**{ctx.author.mention} has initiated a roll\n**'
        components = [[Button(emoji=self.bot.RARITY[doc['rarity']], label = str(i+1), custom_id = f'claim {i+1}', style = ButtonStyle.green)
                      for i, doc in enumerate(roll_pc_docs)]]
        roll_msg = await ctx.send(
            file=stitched_img,
            content=content,
            components=components
        )
        self.msg_to_event[roll_msg.id] = []

        index_taken = []
        taken = 0
        already_claimed = []

        interval = 2
        for _ in range(self.roll_headstart_time // interval):
            await asyncio.sleep(interval)
            if taken >= 1:
                break
            i = 0
            for event in self.msg_to_event[roll_msg.id]:
                await handle_event(event)
                i += 1
            self.msg_to_event[roll_msg.id] = self.msg_to_event[roll_msg.id][i:]

        roll_headstart_id = None

        for button in components[0]:
            button.style = ButtonStyle.blurple
        await roll_msg.edit(components=components)

        for _ in range(self.roll_claim_time // interval):
            await asyncio.sleep(interval)
            if taken >= len(roll_pc_docs):
                break
            i = 0
            for event in self.msg_to_event[roll_msg.id]:
                await handle_event(event)
                i += 1
            self.msg_to_event[roll_msg.id] = self.msg_to_event[roll_msg.id][i:]

        await expire_msg()
        self.msg_to_event.pop(roll_msg.id, None)
        not_taken_ids = [roll_pc_ids[i] for i in range(self.roll_pc_count) if i not in index_taken]
        await db_utils.set_cards_availability(not_taken_ids, True)
        return True

    @commands.Cog.listener()
    async def on_button_click(self, i, b):
        if i.channel not in self.bot.CHANNELS or i.message.id not in self.msg_to_event:
            return
        event = (i.author.id, int(b.custom_id.split()[1])-1)
        self.msg_to_event[i.message.id].append(event)
