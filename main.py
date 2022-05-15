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
from   cogs.CommandHelpCog  import CommandHelpCog
from   cogs.InventoryCog    import InventoryCog

# ----------------------------------------------------------------------------------------------------------

load_dotenv()
TOKEN        = os.getenv('DISCORD_TOKEN')
RESET        = os.getenv('RESET')
CHANNEL_ID   = os.getenv('CHANNEL_ID')
GUILD_ID     = os.getenv('GUILD_ID')
WASTELAND_ID = os.getenv('WASTELAND_ID')

intents           = discord.Intents.default()
intents.members   = True
intents.presences = True

bot = commands.Bot(command_prefix=['q', 'Q'], intents=intents, help_command=None, case_insensitive=True)

bot.DATA_PATH = 'data/'
bot.TEMP_PATH = 'temp/'

# ----------------------------------------------------------------------------------------------------------

ROLL_PC_COUNT        = 3
ROLL_CLAIM_TIME      = 30  # Seconds
ROLL_COOLDOWN        = 10  # Minutes
ROLL_CLAIM_COOLDOWN  = 3   # Minutes
ROLL_HEADSTART_TIME  = 10  # Seconds
ROLL_COMMON_COOLDOWN = 3   # Seconds

COLLECTION_TIME      = 60  # Seconds
SHOP_TIME            = 60  # Seconds

DAILY_REWARD         = 5   # Starcandies
STREAK_MAX           = 5   # Days in a row before reward
STREAK_REWARD        = 20  # Starcandies

COMMAND_MAP = {
    'qboard'      : ('qb', 'qboard', 'Shows the IUFI leaderboard.'),
    'qcooldowns'  : ('qcd', 'qcooldowns', 'Shows all your cooldowns.'),
    'qcommandhelp': ('qch', 'qcommandhelp command', 'Shows the details for a command, including aliases, usage and description.'),
    'qhelp'       : ('qh', 'qhelp', 'Shows the IUFI help screen.'),
    'qprofile'    : ('qp', 'qprofile @member', 'Shows the profile of a member. If called without a member, shows your own profile.'),
    'qcardinfo'   : ('qi', 'qcardinfo id_or_tag', 'Shows the details of a photocard. Card can be identified by its ID or given tag.'),
    'qconvert'    : ('qc', 'qconvert id_or_tag', 'Converts the photocard into starcandies. Card can be identified by its ID or given tag. The amount of starcandies received is dependent on the card\'s rarity.'),
    'qconvertlast': ('qcl', 'qconvertlast', 'Converts the last photocard of your collection.'),
    'qgiftpc'     : ('qgpc', 'qgiftpc id_or_tag @member', 'Gifts the member a photocard. Card can be identified by its ID or given tag.'),
    'qgiftpclast' : ('qgpcl', 'qgiftpclast @member', 'Gifts the member your last photocard in your collection.'),
    'qmain'       : ('qm', 'qmain id_or_tag', 'Sets the photocard as your profile display. Card can be identified by its ID or given tag.'),
    'qmainlast'   : ('qml', 'qmainlast', 'Sets the last photocard in your collection as your profile display.'),
    'qremovetag'  : ('qrt', 'qremovetag id_or_tag', 'Removes the photocard\'s tag. Card can be identified by its ID or given tag.'),
    'qsettag'     : ('qst', 'qsettag id_or_tag tag', 'Sets the photocard\'s tag. Card can be identified by its ID or previous tag.'),
    'qsettaglast' : ('qstl', 'qsettaglast tag', 'Sets the tag of the last photocard in your collection.'),
    'qview'       : ('qv', 'qview', 'View your photocard collection.'),
    'qgiftsc'     : ('qgsc', 'qgsc amount @member', 'Gifts the member the specified amount of starcandies.'),
    'qdaily'      : ('qd', 'qdaily', 'Claims your daily reward.'),
    'qroll'       : ('qr', 'qroll', 'Rolls a set of photocards for claiming.'),
    'qshop'       : ('qs', 'qshop', 'Brings up the IUFI shop'),
    'qregister'   : ('None', 'qregister', 'Registers yourself if you are a new player.'),
    'qreset'      : ('None', 'qreset', 'Resets IUFI. Only for those with admin privileges.'),
    'qrareroll'   : ('qrr', 'qrareroll', 'Starts a roll with at least one rare photocard guaranteed.'),
    'qepicroll'   : ('qer', 'qepicroll', 'Starts a roll with at least one epic photocard guaranteed.'),
    'qlegendroll' : ('qlr', 'qlegendroll', 'Starts a roll with at least one legendary photocard guaranteed.'),
    'qinventory'  : ('qin', 'qinventory', 'Shows the items that you own.')
}

SHOP_LIST = [
    ('🃏', 'CLAIM RESET'   , 2,    'Resets your claim cooldown.', lambda id: db_utils.set_user_cooldown(id, 'next_claim')),
    ('🎲', 'ROLL RESET'    , 5,    'Resets your roll cooldown.',  lambda id: db_utils.set_user_cooldown(id, 'next_roll')),
    ('🌸', 'RARE ROLL'     , 10,   'A roll with at least one rare card.', lambda id: db_utils.update_user_roll(id, 'rare_rolls', 1)),
    ('💎', 'EPIC ROLL'     , 100,  'A roll with at least one epic card.', lambda id: db_utils.update_user_roll(id, 'epic_rolls', 1)),
    ('👑', 'LEGENDARY ROLL', 1000, 'A roll with at least one legendary card.', lambda id: db_utils.update_user_roll(id, 'legend_rolls', 1))
]

bot.RARITY      = ['🌿', '🌸', '💎', '👑']
bot.RARITY_NAME = ['Common', 'Rare', 'Epic', 'Legendary']
bot.RARITY_SC   = [1, 5, 50, 500]
bot.RARITY_PROB = [957, 987, 997, 1000] # Out of 1000

BOL      = 406986532205887488
HAZE     = 95608676441661440
HOPE     = 414686497371979776
AYAX     = 135827436544851969
NOCT     = 122062302865391616
NEFFY    = 286513574191431682
REVIVE   = 140889208783896576
DEVS     = [BOL, HAZE, HOPE, AYAX, NOCT, NEFFY, REVIVE]

# ----------------------------------------------------------------------------------------------------------

@bot.event
async def on_ready():

    print('We have logged in as {0.user}'.format(bot))

    if RESET == '1':
        await db_utils.setup_cards()
        await db_utils.setup_players()
        print('DB resetted')

    bot.CHANNEL   = await bot.fetch_channel(CHANNEL_ID)
    bot.WASTELAND = await bot.fetch_channel(WASTELAND_ID)
    bot.GUILD     = await bot.fetch_guild(GUILD_ID)
    print('Channels fetched')

    help_msg_file = os.path.join(bot.DATA_PATH, 'help.txt')
    help_msg = open(help_msg_file, 'r', encoding='utf8').read()
    print('Help message loaded')

    bot.add_cog(HelpCog(bot,
                        help_msg))
    bot.add_cog(RegisterCog(bot))
    bot.add_cog(RollCog(bot,
                        ROLL_PC_COUNT,
                        ROLL_CLAIM_TIME,
                        ROLL_HEADSTART_TIME,
                        ROLL_COOLDOWN,
                        ROLL_CLAIM_COOLDOWN,
                        ROLL_COMMON_COOLDOWN))
    bot.add_cog(ProfileCog(bot))
    bot.add_cog(GiftSCCog(bot))
    bot.add_cog(BoardCog(bot))
    bot.add_cog(CooldownsCog(bot))
    bot.add_cog(DailyCog(bot,
                         STREAK_MAX,
                         DAILY_REWARD,
                         STREAK_REWARD))
    bot.add_cog(ShopCog(bot,
                        SHOP_LIST,
                        SHOP_TIME))
    bot.add_cog(ErrorCog(bot))
    bot.add_cog(DevCog(bot, DEVS))
    bot.add_cog(LevelCog(bot))
    bot.add_cog(CollectionCog(bot, COLLECTION_TIME))
    bot.add_cog(CardCommandsCog(bot))
    bot.add_cog(CommandHelpCog(bot, COMMAND_MAP))
    bot.add_cog(InventoryCog(bot))
    print('Cogs added')

    print('Bot is ready')
    msg = await bot.CHANNEL.send('IUFI started successfully.')
    ctx = await bot.get_context(msg)
    await ctx.invoke(bot.get_command('help'))

@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return
    if msg.content[0] in ['q', 'Q'] and msg.channel != bot.CHANNEL:
        await msg.reply(f"**This game is not playable in this channel. Go to {bot.CHANNEL.mention}**")
        return
    await bot.process_commands(msg)

# ----------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    bot.run(TOKEN)