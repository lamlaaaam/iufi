import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import random
import string
import db_utils
import discord
import photocard_utils
from   discord.ext import commands, tasks

class EventDropCog(commands.Cog):
    def __init__(self, bot, interval, valid_time):
        self.bot        = bot
        self.interval   = interval
        self.valid_time = valid_time
        self.event_drop.change_interval(hours=interval)
        self.event_drop.start()
        self.thread_pool = ThreadPoolExecutor()
        self.loop        = asyncio.get_running_loop()

    def gen_string(self, l):
        s = ''.join(random.choices(string.ascii_lowercase + string.digits, k=l))
        return s

    @tasks.loop()
    async def event_drop(self):
        await self.random_drop()

    @event_drop.before_loop
    async def before_event_drop(self):
        await asyncio.sleep(self.interval * 3600)

    async def random_drop(self):
        card_doc = (await db_utils.get_random_cards(1, self.bot.RARITY_PROB, 0))[0]
        stars     = random.randint(1, self.bot.STARS_MAX // 2)
        await db_utils.set_card_stars(card_doc['id'], stars)
        title     = "**🎁   Random Card Drop**"
        id        = f"**🆔   `{card_doc['id']:04}`**\n"
        tag       = f"**🏷️   `{card_doc['tag']}`**\n"
        rarity    = f"**{self.bot.RARITY[card_doc['rarity']]}   `{self.bot.RARITY_NAME[card_doc['rarity']]}`**\n"
        #stars_str = '⭐' * stars + self.bot.BS * (self.bot.STARS_MAX-stars)
        #stars_str = '**✨   ' + stars_str + '**\n\n'
        stars_str = f"**⭐   `{stars}`**\n\n"
        code_str  = self.gen_string(5)
        code      = f"**Enter code to claim: `{code_str}`**"
        desc      = id + tag + rarity + stars_str + code + '\n\n'
        embed     = discord.Embed(title=title, description=desc, color=discord.Color.random())

        card_img = await (await self.loop.run_in_executor(self.thread_pool, partial(photocard_utils.create_photocard, card_doc)))
        card_attachment = await (await self.loop.run_in_executor(self.thread_pool, partial(photocard_utils.pillow_to_attachment, card_img, self.bot.WASTELAND)))
        embed.set_image(url=card_attachment)
        event_channel   = random.choice(self.bot.CHANNELS)
        drop_msg = await event_channel.send(embed=embed)

        def check(m):
            return m.channel == event_channel and m.content.lower() == code_str and db_utils.does_user_exist_sync(m.author.id)

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=self.valid_time)
            user_doc  = await db_utils.get_user(msg.author.id)
            space_ok  = len(user_doc['collection']) < self.bot.INVENTORY_LIMIT
            if space_ok:
                await db_utils.set_card_owner(card_doc['id'], msg.author.id)
                await db_utils.add_card_to_user(msg.author.id, card_doc['id'])
                embed_win = discord.Embed(title="🎊 Random Drop", description=f"**{msg.author.display_name} has won the random drop!**", color=discord.Color.random())
                await drop_msg.reply(embed=embed_win)
            else:
                embed_win = discord.Embed(title="🎊 Random Drop", description=f"**{msg.author.display_name} has won the random drop, but has no inventory space...**", color=discord.Color.random())
                await drop_msg.reply(embed=embed_win)
        except asyncio.TimeoutError:
            await db_utils.set_card_availability(card_doc['id'], True)
        finally:
            code              = f"*This drop has expired*"
            desc              = id + tag + rarity + stars_str + code + '\n\n'
            embed.description = desc
            embed.color       = discord.Color.greyple()
            await drop_msg.edit(embed=embed)