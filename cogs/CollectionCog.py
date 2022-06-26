import asyncio
import db_utils
import discord
from   discord.ext import commands
from   discord import Button, ButtonStyle, SelectMenu, SelectOption

class CollectionCog(commands.Cog):
    def __init__(self,
                 bot,
                 collection_time):
        self.bot             = bot
        self.collection_time = collection_time
        self.msg_to_event    = {}

    async def get_nav_buttons(self, num_pages):
        nav_buttons = [Button(label = '⏮',             custom_id = 'nav_first', style = ButtonStyle.blurple),
                       Button(label = '◀',             custom_id = 'nav_left',  style = ButtonStyle.blurple),
                       Button(label = f'1/{num_pages}', custom_id = 'nav_pages', style = ButtonStyle.gray, disabled = True),
                       Button(label = '▶',             custom_id = 'nav_right', style = ButtonStyle.blurple),
                       Button(label = '⏭',             custom_id = 'nav_last',  style = ButtonStyle.blurple)]
        return nav_buttons

    async def page_to_str(self, pages, i, cpp):
        s = ""
        for r, d in enumerate(pages[i]):
            num    = f"{i*cpp+r+1}."
            id     = f"🆔{d['id']:04}"
            tag    = f"🏷️{d['tag'] if d['tag'] else '-'}"
            f      = f"{d['frame']:02}" if d['frame'] != 0 else '-'
            frame  = f"🖼️{f}"
            rarity = f"{self.bot.RARITY[d['rarity']]}"
            stars  = f"⭐{d['stars']}"
            s     += f"{id:<6} {tag:<12} {frame:<4} {stars:<4} {rarity:<1}\n"
        s = "```" + s + "```"
        return s

    @commands.command(name = 'view', aliases = ['v'])
    async def view(self, ctx):
        cards_per_page    = 10
        id                = ctx.author.id
        user              = await self.bot.GUILD.fetch_member(id)
        user_doc          = await db_utils.get_user(id)
        user_collection   = user_doc['collection']
        cards_docs_dict   = {}
        cards_docs        = await db_utils.get_cards({'owned_by': id})
        cards_docs_sorted = [None] * len(cards_docs)
        for doc in cards_docs:
            cards_docs_dict[doc['id']] = doc
        for i in range(len(user_collection)):
            id                   = user_collection[i]
            cards_docs_sorted[i] = cards_docs_dict[id]
        collection_size = len(cards_docs_sorted)
        pages           = [cards_docs_sorted[i:i + cards_per_page] for i in range(0, collection_size, cards_per_page)]
        num_pages       = len(pages)

        if collection_size == 0:
            await ctx.send(f'**{user.mention} you have no photocards.**', delete_after=2)
            return

        title = f"📖   {user.display_name}'s Photocards"
        desc_pre = f"**📙   Collection size: `{collection_size}/{self.bot.INVENTORY_LIMIT}`**\n\n"
        desc = desc_pre + await self.page_to_str(pages, 0, cards_per_page)
        embed = discord.Embed(title = title, description = desc, color = discord.Color.gold())
        embed.set_thumbnail(url=user.avatar_url)
        nav_buttons = await self.get_nav_buttons(num_pages)
        select_menu = [
            SelectMenu(custom_id='select_menu', options=[
               SelectOption(emoji='⌛', label='Sort by oldest card first', value='0'),
               SelectOption(emoji='⌛', label='Sort by latest card first', value='1'),
               SelectOption(emoji='🆔', label='Sort by ascending card ID', value='2'),
               SelectOption(emoji='🆔', label='Sort by descending card ID',value='3'),
               SelectOption(emoji='🏷️', label='Sort by ascending tag name', value='4'),
               SelectOption(emoji='🏷️', label='Sort by descending tag name', value='5'),
               SelectOption(emoji='🖼️', label='Sort by ascending frame ID', value='6'),
               SelectOption(emoji='🖼️', label='Sort by descending frame ID', value='7'),
               SelectOption(emoji='⭐', label='Sort by ascending star level', value='8'),
               SelectOption(emoji='⭐', label='Sort by descending star level', value='9'),
               SelectOption(emoji='👑', label='Sort by ascending rarity', value='10'),
               SelectOption(emoji='👑', label='Sort by descending rarity', value='11')
               ],
            placeholder='Sort collection by ...')
         ]

        page_msg = await ctx.send(embed=embed, components=[nav_buttons, select_menu])
        self.msg_to_event[page_msg.id] = None

        current_page = 0

        async def handle_button_event(user_id, cid):
            nonlocal current_page
            if user_id != ctx.author.id:
                return
            if cid == 'nav_first':
                current_page = 0
            elif cid == 'nav_left':
                current_page = 0 if current_page <= 0 else current_page-1
            elif cid == 'nav_right':
                current_page = num_pages-1 if current_page >= num_pages-1 else current_page+1
            else:
                current_page = num_pages-1
            nav_buttons[2].label = f'{current_page+1}/{num_pages}'

            desc  = desc_pre + await self.page_to_str(pages, current_page, cards_per_page)
            embed.description = desc
            await page_msg.edit(embed=embed, components=[nav_buttons, select_menu])

        async def handle_select_event(user_id, sid):
            nonlocal current_page, pages
            if user_id != ctx.author.id:
                return
            current_page = 0
            nav_buttons[2].label = f'1/{num_pages}'
            new_order = cards_docs_sorted
            if sid == 0:
                new_order = cards_docs_sorted
            if sid == 1:
                new_order = list(reversed(cards_docs_sorted))
            if sid == 2:
                new_order = sorted(cards_docs_sorted, key=lambda d: d['id'])
            if sid == 3:
                new_order = sorted(cards_docs_sorted, key=lambda d: d['id'], reverse=True)
            if sid == 4:
                new_order = sorted(cards_docs_sorted, key=lambda d: d['tag'] if d['tag'] else "")
            if sid == 5:
                new_order = sorted(cards_docs_sorted, key=lambda d: d['tag'] if d['tag'] else "", reverse=True)
            if sid == 6:
                new_order = sorted(cards_docs_sorted, key=lambda d: d['frame'])
            if sid == 7:
                new_order = sorted(cards_docs_sorted, key=lambda d: d['frame'], reverse=True)
            if sid == 8:
                new_order = sorted(cards_docs_sorted, key=lambda d: d['stars'])
            if sid == 9:
                new_order = sorted(cards_docs_sorted, key=lambda d: d['stars'], reverse=True)
            if sid == 10:
                new_order = sorted(cards_docs_sorted, key=lambda d: d['rarity'])
            if sid == 11:
                new_order = sorted(cards_docs_sorted, key=lambda d: d['rarity'], reverse=True)
            pages = [new_order[i:i + cards_per_page] for i in range(0, collection_size, cards_per_page)]
            desc  = desc_pre + await self.page_to_str(pages, 0, cards_per_page)
            embed.description = desc
            await page_msg.edit(embed=embed, components=[nav_buttons, select_menu])
            

        interval = 1
        for _ in range(self.collection_time // interval):
            await asyncio.sleep(interval)
            event = self.msg_to_event[page_msg.id]
            if event:
                user_id, com = event
                if isinstance(com, discord.Button):
                    await handle_button_event(user_id, com.custom_id)
                else:
                    await handle_select_event(user_id, com.values[0])
                self.msg_to_event[page_msg.id] = None

        self.msg_to_event.pop(page_msg.id, None)
        await page_msg.delete()
        
    @commands.Cog.listener()
    async def on_button_click(self, i, b):
        if i.message.id not in self.msg_to_event:
            return
        event = (i.author.id, b)
        self.msg_to_event[i.message.id] = event

    @commands.Cog.listener()
    async def on_selection_select(self, i, s):
        if i.message.id not in self.msg_to_event:
            return
        event = (i.author.id, s)
        self.msg_to_event[i.message.id] = event
        