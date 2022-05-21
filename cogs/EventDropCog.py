import asyncio
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
        title    = "**🎁   Random Card Drop**"
        id       = f"**🆔   `{card_doc['id']:04}`**\n"
        tag      = f"**🏷️   `{card_doc['tag']}`**\n"
        rarity   = f"**{self.bot.RARITY[card_doc['rarity']]}   `{self.bot.RARITY_NAME[card_doc['rarity']]}`**\n\n"
        code_str = self.gen_string(5)
        code     = f"**Enter code to claim: `{code_str}`**"
        desc     = id + tag + rarity + code + '\n\n'
        desc    += "🌸 "*10 + '\n\n'
        embed    = discord.Embed(title=title, description=desc, color=discord.Color.random())

        img_url         = card_doc['url']
        card_img        = await photocard_utils.create_photocard(img_url, border=True, fade=True)
        card_attachment = await photocard_utils.pillow_to_attachment(card_img, self.bot.WASTELAND)
        embed.set_image(url=card_attachment)
        drop_msg = await self.bot.CHANNEL.send(embed=embed)

        def check(m):
            return m.channel == self.bot.CHANNEL and m.content.lower() == code_str and db_utils.sync_does_user_exist(m.author.id)

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=self.valid_time)
            await db_utils.set_card_availability(card_doc['id'], False)
            await db_utils.set_card_owner(card_doc['id'], msg.author.id)
            await db_utils.add_card_to_user(msg.author.id, card_doc['id'])
            await self.bot.CHANNEL.send(f"**{msg.author.mention} has won the random card drop.**")
        except asyncio.TimeoutError:
            pass
        finally:
            code              = f"*This drop has expired*"
            desc              = id + tag + rarity + code + '\n\n'
            desc             += "🌸 "*10 + '\n\n'
            embed.description = desc
            embed.color       = discord.Color.greyple()
            await drop_msg.edit(embed=embed)