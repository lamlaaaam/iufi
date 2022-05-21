import db_utils
import photocard_utils
import discord
from   discord.ext import commands

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = 'profile', aliases = ['p'])
    async def profile(self, ctx, user: discord.Member=None):
        if user == None:
            id   = ctx.author.id
            user = await self.bot.GUILD.fetch_member(id)
        else:
            if not await db_utils.does_user_exist(user.id):
                await ctx.send(f"**{ctx.author.mention} The user provided is not registered.**")
                return
            id = user.id
        user_doc      = await db_utils.get_user(id)
        user_cards    = user_doc['collection']
        user_main     = user_doc['main']
        user_level    = user_doc['level']
        user_exp      = user_doc['exp']
        user_progress = round((user_exp / (user_level**2+10)) * 100, 1)
        main_card_doc = None

        if user_main in user_cards:
            main_card_doc = await db_utils.get_card(user_main)

        title = f"**👤   {user.display_name}'s Profile**"
        embed = discord.Embed(title=title, color=discord.Color.gold())
        s     = f"📙   Photocards: `{len(user_doc['collection'])}`\n"
        s    += f"⚔️   Level: `{user_doc['level']} ({user_progress}%)`\n\n"
        s    += '🌸 ' * 10
        embed.add_field(name=s, value='\u200b', inline=False)
        embed.set_thumbnail(url=user.avatar_url)

        if main_card_doc:
            img_url         = main_card_doc['url']
            card_img        = await photocard_utils.create_photocard(img_url, border=True, fade=True)
            card_attachment = await photocard_utils.pillow_to_attachment(card_img, self.bot.WASTELAND)
            embed.set_image(url=card_attachment)
        await ctx.send(embed = embed)
