import asyncio
import db_utils
import discord
from   discord.ext import commands
from   discord import Button, ButtonStyle
from   async_timeout import timeout

class CollectionCog(commands.Cog):
    def __init__(self,
                 bot,
                 collection_time):
        self.bot             = bot
        self.collection_time = collection_time

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
            stars  = f"✨{d['stars']}"
            s     += f"{id:<5}|{tag:<11}|{frame:<3}|{stars:<3}|{rarity:<1}\n"
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
        cards_docs        = list(await db_utils.get_cards({'owned_by': id}))
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
        desc_pre = f"**📙   Collection size: `{collection_size}`**\n\n"
        desc = desc_pre + await self.page_to_str(pages, 0, cards_per_page)
        embed = discord.Embed(title = title, description = desc, color = discord.Color.gold())
        embed.set_thumbnail(url=user.avatar_url)
        nav_buttons = [await self.get_nav_buttons(num_pages)]

        page_msg = await ctx.send(embed=embed, components=nav_buttons)

        def check(i: discord.ComponentInteraction, b):
            return i.member == ctx.author and i.message.id == page_msg.id

        current_page = 0

        try:
            async with timeout(self.collection_time):
                while True:
                    interaction, button = await self.bot.wait_for('button_click', check = check)
                    cid = button.custom_id
                    if cid == 'nav_first':
                        current_page = 0
                    elif cid == 'nav_left':
                        current_page = 0 if current_page <= 0 else current_page-1
                    elif cid == 'nav_right':
                        current_page = num_pages-1 if current_page >= num_pages-1 else current_page+1
                    else:
                        current_page = num_pages-1
                    nav_buttons[0][2].label = f'{current_page+1}/{num_pages}'

                    desc  = desc_pre + await self.page_to_str(pages, current_page, cards_per_page)
                    embed = discord.Embed(title = title, description = desc, color = discord.Color.gold())
                    embed.set_thumbnail(url=user.avatar_url)
                    await interaction.message.edit(embed=embed, components=nav_buttons)

        except asyncio.exceptions.TimeoutError:
            pass

        await page_msg.delete()
        