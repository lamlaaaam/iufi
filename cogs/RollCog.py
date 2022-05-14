import asyncio
import discord
import db_utils
import photocard_utils
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
                 roll_claim_cooldown):
        self.bot                 = bot
        self.roll_pc_count       = roll_pc_count
        self.roll_claim_time     = roll_claim_time
        self.roll_headstart_time = roll_headstart_time
        self.roll_cooldown       = roll_cooldown
        self.roll_claim_cooldown = roll_claim_cooldown

    @commands.command(name = 'roll', aliases = ['r'])
    @commands.check(db_utils.does_user_exist)
    @commands.cooldown(1, 1, commands.BucketType.channel)
    async def roll(self, ctx):
        await self.start_roll(ctx)

    async def start_roll(self, ctx):
        async def expire_msg():
            content    = "*⏳ This roll has expired.*"
            components = [[Button(label = str(i+1), custom_id = f'claim {i+1}', style = ButtonStyle.gray, disabled = True)
                          for i in range(self.roll_pc_count)]]
            await roll_msg.edit(content=content, components=components)

        async def button_check(i: discord.ComponentInteraction, com):
            if not await db_utils.does_user_exist(i.author.id):
                await i.channel.send(f'**{i.author.mention} you have not registered.**',
                                     delete_after = 3)
                return False
            if i.author.id in already_claimed:
                await i.channel.send(f'**{i.author.mention} you have already claimed from this roll.**',
                                     delete_after = 3)
                return False
            ok, text = await db_utils.check_cooldown(i.author.id, 'next_claim')
            if not ok:
                await i.channel.send(f'**{i.author.mention} you can claim another photocard in {text}.**', 
                                     delete_after = 3)
                return False
            if roll_headstart_id != None and i.author.id != roll_headstart_id:
                await i.channel.send(f'**{i.author.mention} the first {self.roll_headstart_time} seconds are exclusive to the roll starter!**',
                                     delete_after = 3)
                return False
            return True

        def check(i: discord.ComponentInteraction, com):
            return i.message.id == roll_msg.id

        async def handle_claim(i, button, card_index):
            nonlocal taken
            components[0][card_index].disabled = True
            taken += 1
            already_claimed.append(i.author.id)
            await i.message.edit(components=components)
            await i.channel.send(f'**{i.author.mention} has claimed photocard {card_index + 1}!**')
            await db_utils.set_card_availability(roll_pc_ids[card_index], False)
            await db_utils.set_card_owner(roll_pc_ids[card_index], i.author.id)
            await db_utils.add_card_to_user(i.author.id, roll_pc_ids[card_index])
            await db_utils.set_user_cooldown(i.author.id, 'next_claim', m = self.roll_claim_cooldown)

        ok, text = await db_utils.check_cooldown(ctx.author.id, 'next_roll')
        if not ok:
            await ctx.send(f'**{ctx.author.mention} your next roll is in {text}.**')
            return

        await db_utils.set_user_cooldown(ctx.author.id, 'next_roll', m = self.roll_cooldown)
        await db_utils.set_user_cooldown(ctx.author.id, 'next_claim')

        loading_msg = await ctx.send('**Loading...**')

        roll_pc_docs = [doc for doc in await db_utils.get_random_cards(self.roll_pc_count)]
        print('Rolled', roll_pc_docs)

        if len(roll_pc_docs) == 0:
            await ctx.send('**The pool is empty!**')
            await loading_msg.delete()
            return

        roll_pc_ids = [doc['id'] for doc in roll_pc_docs]
        stitched_img = await photocard_utils.stitch_images([doc['url'] for doc in roll_pc_docs])
        stitched_img = await photocard_utils.pillow_to_file(stitched_img)

        await loading_msg.delete()

        roll_headstart_id = ctx.author.id

        content = f'**{ctx.author.mention} has initiated a roll 🎲\n**'
        components = [[Button(label = str(i+1), custom_id = f'claim {i+1}', style = ButtonStyle.green)
                      for i in range(self.roll_pc_count)]]
        roll_msg = await ctx.send(
            file=stitched_img,
            content=content,
            components=components
        )

        taken = 0
        already_claimed = []

        try:
            async with timeout(self.roll_headstart_time):
                while taken < 1:
                    interaction, button = await self.bot.wait_for('button_click', check = check)
                    await interaction.defer()
                    if await button_check(interaction, button):
                        card_index = int(button.custom_id.split()[1]) - 1
                        await handle_claim(interaction, button, card_index)
                        break
        except asyncio.exceptions.TimeoutError:
            pass

        roll_headstart_id = None

        for button in components[0]:
            button.style = ButtonStyle.blurple
        await roll_msg.edit(components=components)

        try:
            async with timeout(self.roll_claim_time):
                while taken < self.roll_pc_count:
                    interaction, button = await self.bot.wait_for('button_click', check = check)
                    await interaction.defer()
                    if await button_check(interaction, button):
                        card_index = int(button.custom_id.split()[1]) - 1
                        await handle_claim(interaction, button, card_index)
        except asyncio.exceptions.TimeoutError:
            pass

        await expire_msg()
