import db_utils
import discord
from   discord.ext import commands

class LevelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.channel in self.bot.CHANNELS and msg.content.lower().startswith('q') and await db_utils.does_user_exist(msg.author.id):
            user_doc      = await db_utils.get_user(msg.author.id)
            level         = user_doc['level']
            exp           = user_doc['exp']
            new_exp       = exp + 1
            level_up_exp  = level * level + 10
            levels_gained = new_exp // level_up_exp
            leftover_exp  = new_exp % level_up_exp

            if levels_gained > 0:
                level_up_reward = level * 2
                title           = "**📈   Level Up!**"
                desc            = f"```⚔️:  {level}  ->  {level + levels_gained}\n"
                desc           += f"🍬:  {user_doc['currency']}  ->  {user_doc['currency'] + level_up_reward}\n"
                desc           += "You gained some starcandies for leveling up!```"
                embed           = discord.Embed(title=title, description=desc, color=discord.Color.teal())
                embed.set_thumbnail(url=(await self.bot.GUILD.fetch_member(user_doc['discord_id'])).avatar_url)

                await msg.channel.send(embed=embed)
                await db_utils.update_user_currency(msg.author.id, level_up_reward)

            await db_utils.set_user_level_exp(msg.author.id, level + levels_gained, leftover_exp)