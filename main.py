import os
from   dotenv               import load_dotenv

import discord
from   discord.ext          import commands

import db_utils

from   cogs.HelpCog         import HelpCog
from   cogs.RegisterCog     import RegisterCog
from   cogs.RollCog         import RollCog
from   cogs.ProfileCog      import ProfileCog
from   cogs.GiftSCCog       import GiftSCCog
from   cogs.BoardCog        import BoardCog
from   cogs.CooldownsCog    import CooldownsCog
from   cogs.DailyCog        import DailyCog
from   cogs.ShopCog         import ShopCog
from   cogs.ErrorCog        import ErrorCog
from   cogs.DevCog          import DevCog
from   cogs.LevelCog        import LevelCog
from   cogs.CollectionCog   import CollectionCog
from   cogs.CardCommandsCog import CardCommandsCog

# ----------------------------------------------------------------------------------------------------------

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
RESET = os.getenv('RESET')

intents           = discord.Intents.default()
intents.members   = True
intents.presences = True

bot = commands.Bot(command_prefix=['q', 'Q'], intents=intents, help_command=None, case_insensitive=True)

# ----------------------------------------------------------------------------------------------------------

WASTELAND_ID    = 971676425813901352
TEST_CHANNEL_ID = 971021074638721025
TEST_GUILD_ID   = 967073665252462601
CHANNEL_ID      = TEST_CHANNEL_ID
GUILD_ID        = TEST_GUILD_ID

BOL      = 406986532205887488
HAZE     = 95608676441661440
HOPE     = 414686497371979776
AYAX     = 135827436544851969
NOCT     = 122062302865391616
NEFFY    = 286513574191431682
REVIVE   = 140889208783896576
DEVS     = [BOL, HAZE, HOPE, AYAX, NOCT, NEFFY, REVIVE]

ROLL_PC_COUNT        = 3
ROLL_CLAIM_TIME      = 30  # Seconds
ROLL_COOLDOWN        = 10  # Minutes
ROLL_CLAIM_COOLDOWN  = 3   # Minutes
ROLL_HEADSTART_TIME  = 10  # Seconds

COLLECTION_TIME      = 60  # Seconds
SHOP_TIME            = 60  # Seconds

DAILY_REWARD         = 5   # Starcandies
STREAK_MAX           = 5   # Days in a row before reward
STREAK_REWARD        = 20  # Starcandies

bot.DATA_PATH = 'data/'
bot.TEMP_PATH = 'temp/'

HELP_MSG_FILE = os.path.join(bot.DATA_PATH, 'help.txt')
SHOP_MSG_FILE = os.path.join(bot.DATA_PATH, 'shop.txt')

bot.RARITY      = ['🌿', '🌸', '💎', '👑']
bot.RARITY_NAME = ['Common', 'Rare', 'Epic', 'Legendary']
bot.RARITY_SC   = [1, 5, 50, 500]

# ----------------------------------------------------------------------------------------------------------

@bot.event
async def on_ready():

    print('We have logged in as {0.user}'.format(bot))

    if RESET == '1':
        await db_utils.setup_cards()
        await db_utils.setup_players()
        print('DB resetted')

    bot.CHANNEL   = bot.get_channel(CHANNEL_ID)
    bot.WASTELAND = bot.get_channel(WASTELAND_ID)
    bot.GUILD     = bot.get_guild(GUILD_ID)
    print('Channels fetched')

    help_msg = open(HELP_MSG_FILE, 'r', encoding='utf8').read()
    print('Help message loaded')

    shop_msg = open(SHOP_MSG_FILE, 'r', encoding='utf8').read()
    print('Shop message loaded')

    bot.add_cog(HelpCog(bot,
                        help_msg))
    bot.add_cog(RegisterCog(bot))
    bot.add_cog(RollCog(bot,
                        ROLL_PC_COUNT,
                        ROLL_CLAIM_TIME,
                        ROLL_HEADSTART_TIME,
                        ROLL_COOLDOWN,
                        ROLL_CLAIM_COOLDOWN))
    bot.add_cog(ProfileCog(bot))
    bot.add_cog(GiftSCCog(bot))
    bot.add_cog(BoardCog(bot))
    bot.add_cog(CooldownsCog(bot))
    bot.add_cog(DailyCog(bot,
                         STREAK_MAX,
                         DAILY_REWARD,
                         STREAK_REWARD))
    bot.add_cog(ShopCog(bot,
                        shop_msg,
                        SHOP_TIME))
    bot.add_cog(ErrorCog(bot))
    bot.add_cog(DevCog(bot, DEVS))
    bot.add_cog(LevelCog(bot))
    bot.add_cog(CollectionCog(bot, COLLECTION_TIME))
    bot.add_cog(CardCommandsCog(bot))
    print('Cogs added')

    print('Bot is ready')
    msg = await bot.CHANNEL.send('IUFI started successfully.')
    ctx = await bot.get_context(msg)
    await ctx.invoke(bot.get_command('help'))

# ----------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    bot.run(TOKEN)