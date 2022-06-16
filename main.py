import os
from   dotenv               import load_dotenv

import discord
from   discord.ext          import commands

import db_utils

from   cogs.HelpCog          import HelpCog
from   cogs.RegisterCog      import RegisterCog
from   cogs.RollCog          import RollCog
from   cogs.ProfileCog       import ProfileCog
from   cogs.GiftSCCog        import GiftSCCog
from   cogs.BoardCog         import BoardCog
from   cogs.CooldownsCog     import CooldownsCog
from   cogs.DailyCog         import DailyCog
from   cogs.ShopCog          import ShopCog
from   cogs.ErrorCog         import ErrorCog
from   cogs.DevCog           import DevCog
from   cogs.LevelCog         import LevelCog
from   cogs.CollectionCog    import CollectionCog
from   cogs.CardCommandsCog  import CardCommandsCog
from   cogs.CommandHelpCog   import CommandHelpCog
from   cogs.InventoryCog     import InventoryCog
from   cogs.AuctionCog       import AuctionCog
from   cogs.EventDropCog     import EventDropCog
from   cogs.FavesCog         import FavesCog
from   cogs.FramesCog        import FramesCog
from   cogs.SurpriseEventCog import SurpriseEventCog

# ----------------------------------------------------------------------------------------------------------

load_dotenv()
TOKEN        = os.getenv('DISCORD_TOKEN')
CHANNEL_IDS  = os.getenv('CHANNEL_IDS').split('/')
GUILD_ID     = os.getenv('GUILD_ID')
WASTELAND_ID = os.getenv('WASTELAND_ID')

intents           = discord.Intents.default()
intents.members   = True
intents.presences = True
intents.message_content = True

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
SHOP_TIME            = 120 # Seconds

DAILY_REWARD         = 5   # Starcandies
STREAK_END           = 30  # Days before reset
STREAK_INTERVAL      = 5   # Days before big reward
STREAK_REWARDS       = [
    ("50 🍬",   lambda id: db_utils.update_user_currency(id, 50)),
    ("1 🌸",      lambda id: db_utils.update_user_roll(id, 'rare_rolls', 1)),
    ("100 🍬",  lambda id: db_utils.update_user_currency(id, 100)),
    ("1 💎",      lambda id: db_utils.update_user_roll(id, 'epic_rolls', 1)),
    ("500 🍬",  lambda id: db_utils.update_user_currency(id, 500)),
    ("1 👑", lambda id: db_utils.update_user_roll(id, 'legend_rolls', 1))
]

AUCTION_TIME         = 30  # Seconds
AUCTION_MAX_BID      = 1000000 # SC

EVENT_DROP_INTERVAL  = 1    # Hours
EVENT_DROP_VALID     = 120  # Seconds

BIO_LIMIT            = 100 # Chars

CONVERT_MODES        = ["notag", "common", "rare", "epic", "legend"]

COMMAND_MAP = {
    'qleader'      : ('ql', 'qleader', 'Shows the IUFI leaderboard.'),
    'qcooldowns'   : ('qcd', 'qcooldowns', 'Shows all your cooldowns.'),
    'qcommandhelp' : ('qch', 'qcommandhelp command', 'Shows the details for a command, including aliases, usage and description.'),
    'qhelp'        : ('qh', 'qhelp', 'Shows the IUFI help screen.'),
    'qprofile'     : ('qp', 'qprofile @member', 'Shows the profile of a member. If called without a member, shows your own profile.'),
    'qcardinfo'    : ('qi', 'qcardinfo id_or_tag', 'Shows the details of a photocard. Card can be identified by its ID or given tag.'),
    'qcardinfolast': ('qil', 'qcardinfolast', 'Shows the details of your last photocard.'),
    'qconvert'     : ('qc', 'qconvert id_or_tag1 id_or_tag2 ...', 'Converts the photocards into starcandies. Card can be identified by its ID or given tag. The amount of starcandies received is dependent on the card\'s rarity.'),
    'qconvertlast' : ('qcl', 'qconvertlast', 'Converts the last photocard of your collection.'),
    'qgiftpc'      : ('qgpc', 'qgiftpc @member id_or_tag1 id_or_tag2 ...', 'Gifts the member photocards. Card can be identified by its ID or given tag.'),
    'qgiftpclast'  : ('qgpcl', 'qgiftpclast @member', 'Gifts the member your last photocard in your collection.'),
    'qmain'        : ('qm', 'qmain id_or_tag', 'Sets the photocard as your profile display. Card can be identified by its ID or given tag.'),
    'qmainlast'    : ('qml', 'qmainlast', 'Sets the last photocard in your collection as your profile display.'),
    'qremovetag'   : ('qrt', 'qremovetag id_or_tag', 'Removes the photocard\'s tag. Card can be identified by its ID or given tag.'),
    'qsettag'      : ('qst', 'qsettag id_or_tag tag', 'Sets the photocard\'s tag. Card can be identified by its ID or previous tag.'),
    'qsettaglast'  : ('qstl', 'qsettaglast tag', 'Sets the tag of the last photocard in your collection.'),
    'qview'        : ('qv', 'qview', 'View your photocard collection.'),
    'qgiftsc'      : ('qgsc', 'qgsc @member amount', 'Gifts the member the specified amount of starcandies.'),
    'qdaily'       : ('qd', 'qdaily', 'Claims your daily reward.'),
    'qroll'        : ('qr', 'qroll', 'Rolls a set of photocards for claiming.'),
    'qshop'        : ('qs', 'qshop', 'Brings up the IUFI shop'),
    'qregister'    : ('None', 'qregister', 'Registers yourself if you are a new player.'),
    'qreboot'      : ('None', 'qreset', 'Reboots IUFI. Only for those with admin privileges.'),
    'qreset'       : ('None', 'qreset', 'WIPES ALL GAME DATA. Only for those with admin privileges.'),
    'qrareroll'    : ('qrr', 'qrareroll', 'Starts a roll with at least one rare photocard guaranteed.'),
    'qepicroll'    : ('qer', 'qepicroll', 'Starts a roll with at least one epic photocard guaranteed.'),
    'qlegendroll'  : ('qlr', 'qlegendroll', 'Starts a roll with at least one legendary photocard guaranteed.'),
    'qinventory'   : ('qin', 'qinventory', 'Shows the items that you own.'),
    'qauction'     : ('qa', 'qauction id_or_tag min_bid', 'Puts your photocard up for auction with a minimum bid amount. If not specified, minimum bid is 0. Card can be identified by its ID or given tag'),
    'qbid'         : ('qbi', 'qbid amount', 'Places a bid for the ongoing auction.'),
    'qsetfaves'    : ('qsf', 'qsetfaves slot id_or_tag', 'Sets a photocard in the given slot [1 to 6] as your favorite. Card can be identified by its ID or given tag.'),
    'qremovefaves' : ('qrf', 'qremovefaves slot', 'Removes the photocard in the given slot [1 to 6].'),
    'qsetfaveslast': ('qsfl', 'qsetfaveslast slot', 'Sets your last photocard as a favorite in the given slot [1 to 6].'),
    'qfaves'       : ('qf', 'qfaves @member', 'Shows the given member\'s favorite photocards. If not specified, shows your own.'),
    'qsetbio'      : ('qsb', 'qsetbio "bio"', 'Sets your profile bio. Make sure to enclose your bio in double quotes ("")'),
    'qremovebio'   : ('qrb', 'qrb', 'Removes your profile bio.'),
    'qremindon'    : ('qron', 'qremindon', 'Turns reminders on for your cooldowns. Make sure you are not blocking DMs.'),
    'qremindoff'   : ('qroff', 'qremindoff', 'Turns reminders off for your cooldowns.'),
    'qsetframe'    : ('qsfr', 'qsetframe card frame', 'Sets the frame for the photocard. Both card and frame can be identified by id or given tag.'),
    'qsetframelast': ('qsfrl', 'qsetframe frame', 'Sets the frame for the last photocard. Frame can be identified by its id or given tag.'),
    'qremoveframe' : ('qrfr', 'qremoveframe card', 'Removes the frame from the photocard. Card can be identified by its ID or given tag.'),
    'qframeinfo'   : ('qfi', 'qframeinfo id_or_tag', 'Shows the details for the frame. Frame can be identified by its ID or given tag.'),
    'qupgrade'     : ('qu', 'qupgrade id_or_tag', 'Attempts to upgrade star level of the card. Card can be identified by its ID or given tag.'),
    'qconvertall'  : ('None', 'qconvertall', 'Converts ALL your photocards.'),
    'qbuy'         : ('qb', 'qbuy item_id quantity', 'Buys specified amount of the given item.'),
    'qconvertmass' : ('qcm', 'qconvertmass mode', f"Converts photocards that fit the given mode. Allowed modes: {', '.join(CONVERT_MODES)}")
}

SHOP_LIST = [
    ('🃏', 'CLAIM RESET'     , 5,    'Resets your claim cooldown.', lambda id, amt: db_utils.set_user_cooldown(id, 'next_claim')),
    ('🎲', 'ROLL RESET'      , 10,    'Resets your roll cooldown.',  lambda id, amt: db_utils.set_user_cooldown(id, 'next_roll')),
    ('🌸', 'RARE ROLL'       , 20,   'A roll with at least one rare card.', lambda id, amt: db_utils.update_user_roll(id, 'rare_rolls', amt)),
    ('💎', 'EPIC ROLL'       , 150,  'A roll with at least one epic card.', lambda id, amt: db_utils.update_user_roll(id, 'epic_rolls', amt)),
    ('👑', 'LEGENDARY ROLL'  , 800, 'A roll with at least one legendary card.', lambda id, amt: db_utils.update_user_roll(id, 'legend_rolls', amt)),
    ('🔨', 'STAR UPGRADE'    , 40, 'A chance to upgrade a card\'s stars.', lambda id, amt: db_utils.update_user_upgrades(id, amt)),
    ('💕', 'HEARTS FRAME'    , 10,   'Simple hearts and ribbons!', lambda id, amt: db_utils.update_user_frames(id, 2, amt)),
    ('🌟', 'CELEBRITY FRAME' , 20,  'For the Celebrity lovers!', lambda id, amt: db_utils.update_user_frames(id, 7, amt)),
    ('💌', 'UAENA FRAME'     , 30,  'Show off your Uaena love!', lambda id, amt: db_utils.update_user_frames(id, 3, amt)),
    ('🌷', 'DANDELIONS FRAME', 40,  'Dandelion stickers drawn by IU!', lambda id, amt: db_utils.update_user_frames(id, 4, amt)),
    ('✨', 'SHINE FRAME'     , 50,  'Add some shine effect to your photocard!', lambda id, amt: db_utils.update_user_frames(id, 5, amt)),
    ('💠', 'LOVEPOEM FRAME'  , 60,  'For the Love Poem lovers!', lambda id, amt: db_utils.update_user_frames(id, 6, amt)),
    ('🎤', 'CHEER FRAME'     , 70,  'Show your support for concerts!', lambda id, amt: db_utils.update_user_frames(id, 9, amt)),
    ('🍓', 'SMOON FRAME'     , 80,  'Brighten the night with stars and a strawberry moon!', lambda id, amt: db_utils.update_user_frames(id, 8, amt)),
    ('✍️', 'SIGNED FRAME'   , 90, 'IU\'s signature, what else do you need?', lambda id, amt: db_utils.update_user_frames(id, 1, amt)),
]

bot.RARITY      = ['🌿', '🌸', '💎', '👑']
bot.RARITY_NAME = ['Common', 'Rare', 'Epic', 'Legendary']
bot.RARITY_SC   = [1, 5, 50, 300]
bot.RARITY_PROB = [887, 987, 997, 1000] # Out of 1000

bot.STARS_MAX   = 10
bot.STARS_PROB  = [91, 82, 73, 64, 55, 47, 38, 29, 20] # Out of 100; Prob to get to next star

BOL      = 406986532205887488
HAZE     = 95608676441661440
HOPE     = 414686497371979776
AYAX     = 135827436544851969
NOCT     = 122062302865391616
NEFFY    = 286513574191431682
REVIVE   = 140889208783896576
ALY      = 773162600380891156
#DEVS     = [BOL, HAZE, HOPE, AYAX, NOCT, NEFFY, REVIVE, ALY]
DEVS     = [BOL]

# ----------------------------------------------------------------------------------------------------------

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

    bot.CHANNELS  = [await bot.fetch_channel(id) for id in CHANNEL_IDS]
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
    bot.add_cog(ProfileCog(bot, BIO_LIMIT))
    bot.add_cog(GiftSCCog(bot))
    bot.add_cog(BoardCog(bot))
    bot.add_cog(CooldownsCog(bot))
    bot.add_cog(DailyCog(bot,
                         DAILY_REWARD,
                         STREAK_END,
                         STREAK_INTERVAL,
                         STREAK_REWARDS))
    bot.add_cog(ShopCog(bot,
                        SHOP_LIST,
                        SHOP_TIME))
    bot.add_cog(ErrorCog(bot))
    bot.add_cog(DevCog(bot, DEVS))
    bot.add_cog(LevelCog(bot))
    bot.add_cog(CollectionCog(bot, COLLECTION_TIME))
    bot.add_cog(CardCommandsCog(bot, CONVERT_MODES))
    bot.add_cog(CommandHelpCog(bot, COMMAND_MAP))
    bot.add_cog(InventoryCog(bot))
    bot.add_cog(AuctionCog(bot, AUCTION_TIME, AUCTION_MAX_BID))
    bot.add_cog(EventDropCog(bot,
                             EVENT_DROP_INTERVAL,
                             EVENT_DROP_VALID))
    bot.add_cog(FavesCog(bot))
    bot.add_cog(FramesCog(bot))
    bot.add_cog(SurpriseEventCog(bot, DEVS))
    print('Cogs added')

    print('Bot is ready')
    msg = await bot.CHANNELS[0].send('IUFI started successfully.')
    ctx = await bot.get_context(msg)
    await ctx.invoke(bot.get_command('help'))

@bot.event
async def on_message(msg):
    if msg.author.bot:
        return
    ctx    = await bot.get_context(msg)
    is_cmd = ctx.valid
    if is_cmd and msg.channel not in bot.CHANNELS and msg.author.id != BOL:
        await ctx.send(f"**{msg.author.mention} This command is not usable here. Go to one of the IUFI channels.**", delete_after=2)
        return
    if msg.channel in bot.CHANNELS and not await db_utils.does_user_exist(msg.author.id) and ctx.invoked_with != 'register':
        await ctx.send(f"**{msg.author.mention} You are not registered. Use `qregister` to start.**", delete_after=3)
        return
    await bot.process_commands(msg)

@bot.event
async def on_button_click(i, b):
    await i.defer()

@bot.event
async def on_selection_select(i, s):
    await i.defer()

# ----------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    bot.run(TOKEN)