import db_utils
import photocard_utils
import discord
from   discord.ext import commands

class ProfileCog(commands.Cog):
    def __init__(self, bot, bio_limit):
        self.bot       = bot
        self.bio_limit = bio_limit

    @commands.command(name = 'profile', aliases = ['p'])
    async def profile(self, ctx, user: discord.Member=None):
        if user == None:
            id   = ctx.author.id
            user = await self.bot.GUILD.fetch_member(id)
        else:
            if not await db_utils.does_user_exist(user.id):
                await ctx.send(f"**{ctx.author.mention} the user provided is not registered.**")
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
        bio   = "" if user_doc['bio'] == "" else f"```\n{user_doc['bio']}\n```\n\n"
        embed = discord.Embed(title=title, description=bio, color=discord.Color.gold())
        s     = f"📙   Photocards: `{len(user_doc['collection'])}`\n"
        s    += f"⚔️   Level: `{user_doc['level']} ({user_progress}%)`\n\n"
        #s    += '🌸 ' * 10
        embed.add_field(name=s, value='\u200b', inline=False)
        embed.set_thumbnail(url=user.avatar_url)

        if main_card_doc:
            card_img        = await photocard_utils.create_photocard(main_card_doc)
            card_attachment = await photocard_utils.pillow_to_attachment(card_img, self.bot.WASTELAND)
            embed.set_image(url=card_attachment)
        await ctx.send(embed = embed)

    @commands.command(name = 'setbio', aliases = ['sb'])
    async def set_bio(self, ctx, bio):
        if len(bio) > self.bio_limit:
            await ctx.send(f"**{ctx.author.mention} your bio cannot exceed {self.bio_limit} characters.**")
            return
        await db_utils.set_user_bio(ctx.author.id, bio)
        await ctx.send(f"**{ctx.author.mention} you have successfully set your bio.**")

    @commands.command(name = 'removebio', aliases = ['rb'])
    async def remove_bio(self, ctx):
        await db_utils.remove_user_bio(ctx.author.id)
        await ctx.send(f"**{ctx.author.mention} you have successfully removed your bio.**")
