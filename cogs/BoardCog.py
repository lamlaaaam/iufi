import db_utils
import discord
from   discord.ext import commands

class BoardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = 'board', aliases = ['b'])
    @commands.check(db_utils.does_user_exist)
    async def board(self, ctx):
        top_user_docs = await db_utils.get_all_users()
        top_user_docs = sorted(top_user_docs, key=lambda doc: doc['level'], reverse=True)
        trophy        = '🏆'
        title         = f"{trophy}\u200b   IUFI Leaderboard"
        emojis        = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        names         = []
        levels        = []
        currencies    = []
        strs          = []
        champ         = None
        count         = 0

        for doc in top_user_docs:
            try:
                user = await self.bot.GUILD.fetch_member(doc['discord_id'])
            except:
                continue

            if not champ:
                champ = user

            name = user.display_name.encode('ascii', 'ignore')
            name = name.decode()[:10]
            if len(name) == 0:
                u    = await self.bot.fetch_user(id)
                name = u.display_name[:10]

            level    = doc['level']
            currency = doc['currency']
            names.append(name)
            levels.append(level)
            currencies.append(currency)
            count += 1
            if count >= 10:
                break

        for i in range(len(names)):
            left   = f'{emojis[i]} {names[i]}'
            right  = f'{levels[i]} ⚔️'
            row    = f"{left:<20}{right:>5}"
            strs.append(row)

        if len(strs) == 0:
            embed = discord.Embed(title=title, description='The leaderboard is empty.', color=discord.Color.green())
            await ctx.send(embed=embed)
            return

        str         = '\n'.join(strs)
        description = '```\n' + str + '\n```'
        embed       = discord.Embed(title = title, description = description, color = discord.Color.green())
        embed.set_thumbnail(url=champ.avatar_url)

        await ctx.send(embed=embed)