import os
import random
import pymongo
from   dotenv import load_dotenv
from   datetime import datetime, timedelta

# ----------------------------------------------------------------------------------------------------------
load_dotenv()
MONGO_STRING      = os.getenv('MONGO_STRING')
CLOUDFRONT_PREFIX = os.getenv('CLOUDFRONT_PREFIX')
client       = pymongo.MongoClient(MONGO_STRING)
iufi_db      = client['IUFI_DB']
cards_col    = iufi_db['Cards']
players_col  = iufi_db['Players']
frames_col   = iufi_db['Frames']

# ----------------------------------------------------------------------------------------------------------

def fix_stuck_cards():
    cards_col.update_many({'available':False, 'owned_by':None}, {'$set': {'available':True}})

def drop_cards(cluster):
    MONGO_STRING = os.getenv('MONGO_STRING' if cluster == 'SG' else 'MONGO_STRING_US')
    client       = pymongo.MongoClient(MONGO_STRING)
    iufi_db      = client['IUFI_DB']
    cards_col    = iufi_db['Cards']
    if cards_col.count_documents({}) > 0:
        cards_col.drop()

def drop_players(cluster):
    MONGO_STRING = os.getenv('MONGO_STRING' if cluster == 'SG' else 'MONGO_STRING_US')
    client       = pymongo.MongoClient(MONGO_STRING)
    iufi_db      = client['IUFI_DB']
    players_col  = iufi_db['Players']
    if players_col.count_documents({}) > 0:
        players_col.drop()

def drop_frames(cluster):
    MONGO_STRING = os.getenv('MONGO_STRING' if cluster == 'SG' else 'MONGO_STRING_US')
    client       = pymongo.MongoClient(MONGO_STRING)
    iufi_db      = client['IUFI_DB']
    frames_col  = iufi_db['Frames']
    if frames_col.count_documents({}) > 0:
        frames_col.drop()

def setup_cards(ids, cluster):
    MONGO_STRING = os.getenv('MONGO_STRING' if cluster == 'SG' else 'MONGO_STRING_US')
    client       = pymongo.MongoClient(MONGO_STRING)
    iufi_db      = client['IUFI_DB']
    cards_col    = iufi_db['Cards']
    card_docs = []
    for rarity, start_id, end_id in ids:
        for aws_id in range(start_id, end_id+1):
            doc = {'id'       : aws_id,
                   'tag'      : None,
                   'url'      : f"{CLOUDFRONT_PREFIX}/cards/{aws_id:05}.jpg",
                   'available': True,
                   'owned_by' : None,
                   'rarity'   : rarity,
                   'frame'    : 0,
                   'stars'    : 0} 
            card_docs.append(doc)
    cards_col.insert_many(card_docs)

def reset_game(cluster):
    MONGO_STRING = os.getenv('MONGO_STRING' if cluster == 'SG' else 'MONGO_STRING_US')
    client       = pymongo.MongoClient(MONGO_STRING)
    iufi_db      = client['IUFI_DB']
    cards_col    = iufi_db['Cards']
    players_col  = iufi_db['Players']
    cards_col.update_many({}, {'$set': {'available': True, 'tag': None, 'owned_by': None, 'frame': 0, 'stars': 0}})
    players_col.drop()

def setup_frames(id, name, auto_col, cluster):
    MONGO_STRING = os.getenv('MONGO_STRING' if cluster == 'SG' else 'MONGO_STRING_US')
    client       = pymongo.MongoClient(MONGO_STRING)
    iufi_db      = client['IUFI_DB']
    frames_col   = iufi_db['Frames']
    doc = {'id'       : id,
           'tag'      : name,
           'url'      : f"{CLOUDFRONT_PREFIX}/frames/{id:03}-{name}.png",
           'auto'     : auto_col}
    frames_col.insert_one(doc)

async def reset_game_command():
    cards_col.update_many({}, {'$set': {'available': True, 'tag': None, 'owned_by': None, 'frame': 0, 'stars': 0}})
    players_col.drop()

async def purge(cluster, limit):
    MONGO_STRING = os.getenv('MONGO_STRING' if cluster == 'SG' else 'MONGO_STRING_US')
    client       = pymongo.MongoClient(MONGO_STRING)
    iufi_db      = client['IUFI_DB']
    players_col  = iufi_db['Players']
    all_players = list(players_col.find({}))
    for player in all_players:
        if len(player['collection']) > limit:
            ids = player['collection'][limit:]
            await convert_cards(player['discord_id'], ids, 0)

# ----------------------------------------------------------------------------------------------------------
def does_user_exist_sync(q):
    if isinstance(q, int):
        already_exists = players_col.count_documents({'discord_id': q}, limit = 1)
    else:
        already_exists = players_col.count_documents({'discord_id': q.author.id}, limit = 1)
    return already_exists

async def does_user_exist(q):
    if isinstance(q, int):
        already_exists = players_col.count_documents({'discord_id': q}, limit = 1)
    else:
        already_exists = players_col.count_documents({'discord_id': q.author.id}, limit = 1)
    return already_exists

async def register_user(id):
    if await does_user_exist(id):
        return False
    players_col.insert_one({'discord_id'   : id,
                            'collection'   : [],
                            'level'        : 1, 
                            'exp'          : 0,
                            'currency'     : 0,
                            'main'         : 0,
                            'next_claim'   : datetime.now(),
                            'next_roll'    : datetime.now(),
                            'next_daily'   : datetime.now(),
                            'streak_ends'  : datetime.now(),
                            'streak'       : 1,
                            'faves'        : [],
                            'rare_rolls'   : 0,
                            'epic_rolls'   : 0,
                            'legend_rolls' : 0,
                            'bio'          : "Your bio is empty.",
                            'reminders'    : False,
                            'frames'       : {},
                            'upgrades'     : 0})
    return True

async def add_card_to_user(user_id, card_id):
    user  = await get_user(user_id)
    cards = user['collection']
    if card_id in cards:
        return
    players_col.update_one({'discord_id': user_id}, {'$push': {'collection': card_id}})

async def remove_card_from_user(user_id, card_id):
    faves     = (await get_user(user_id))['faves']
    new_faves = [f if f != card_id else None for f in faves]
    players_col.update_one({'discord_id': user_id}, {'$pull': {'collection': card_id}, '$set': {'faves': new_faves}})

async def get_user(id):
    return players_col.find_one({'discord_id': id})

async def get_users(pred):
    return list(players_col.find(pred))

async def update_user_currency(id, delta):
    user         = await get_user(id)
    currency     = user['currency']
    new_currency = currency + delta
    if new_currency < 0:
        new_currency = 0
    players_col.update_one({'discord_id': id}, {'$set': {'currency': new_currency}})

async def set_main(user_id, card_id):
    players_col.update_one({'discord_id': user_id}, {'$set': {'main': card_id}})

async def set_user_level_exp(user_id, level, exp):
    players_col.update_one({'discord_id': user_id}, {'$set': {'level': level, 'exp': exp}})

async def get_all_users():
    return list(players_col.find())

async def set_user_cooldown(id, cd_key, d=0, h=0, m=0, s=0):
    now      = datetime.now()
    delta    = timedelta(days=d, hours=h, minutes=m, seconds=s)
    new_time = now + delta
    players_col.update_one({'discord_id': id}, {'$set': {cd_key: new_time}})

async def check_cooldown(user_id, cd_key):
    user_doc = await get_user(user_id)
    end_time = user_doc[cd_key]
    now      = datetime.now()
    if now < end_time:
        delta = end_time - now
        s     = delta.seconds
        h     = s // 3600
        s     = s % 3600
        m     = s // 60
        s     = s % 60
        str   = f'`{h}h {m}m {round(s)}s`'
        return (False, str)
    return (True, '`READY`')

async def check_within_streak(user_id):
    user_doc    = await get_user(user_id)
    streak_ends = user_doc['streak_ends']
    now         = datetime.now()
    return now < streak_ends

async def set_user_streak(id, streak):
    players_col.update_one({'discord_id': id}, {'$set': {'streak': streak}})

async def update_user_roll(id, roll, delta):
    user            = await get_user(id)
    roll_amount     = user[roll]
    new_roll_amount = roll_amount + delta
    if new_roll_amount < 0:
        new_roll_amount = 0
    players_col.update_one({'discord_id': id}, {'$set': {roll: new_roll_amount}})

async def set_user_fave(user_id, card_id, slot):
    players_col.update_one({'discord_id': user_id}, {'$set': {f'faves.{slot}': card_id}})

async def remove_user_fave(user_id, slot):
    players_col.update_one({'discord_id': user_id}, {'$set': {f'faves.{slot}': None}})

async def set_user_bio(user_id, bio):
    players_col.update_one({'discord_id': user_id}, {'$set': {'bio': bio}})

async def remove_user_bio(user_id):
    players_col.update_one({'discord_id': user_id}, {'$set': {'bio': "Your bio is empty."}})

async def set_user_reminders(user_id, state):
    players_col.update_one({'discord_id': user_id}, {'$set': {'reminders': state}})

async def update_user_frames(user_id, frame_id, delta):
    user            = await get_user(user_id)
    frame_count     = user['frames'][str(frame_id)] if str(frame_id) in user['frames'] else 0
    new_frame_count = frame_count + delta
    if new_frame_count < 0:
        new_frame_count = 0
    players_col.update_one({'discord_id': user_id}, {'$set': {f"frames.{frame_id}": new_frame_count}})

async def update_user_upgrades(id, delta):
    user         = await get_user(id)
    upgrades     = user['upgrades']
    new_upgrades = upgrades + delta
    if new_upgrades < 0:
        new_upgrades = 0
    players_col.update_one({'discord_id': id}, {'$set': {'upgrades': new_upgrades}})
# ---------------------------------------------------------------------------------------------------------

async def check_pool_exists(bias):
    if bias > 0:
        available = len(list(cards_col.find({'rarity': bias, 'available': True})))
    else:
        available = len(list(cards_col.find({'available': True})))
    pool_exists = available > 0
    return pool_exists

def roll_rarity(probs):
    roll = random.randint(1, 1000)
    for r, p in enumerate(probs):
        if roll <= p:
            return r
    return 0

async def get_random_cards(num, probs, bias):
    rarity_rolls = [roll_rarity(probs) for _ in range(num)]
    if bias > 0:
        rarity_rolls[0] = bias
    rarities = [0, 0, 0, 0]
    for rare in rarity_rolls:
        rarities[rare] += 1
    cards  = []
    pool   = [list(cards_col.find({'available': True, 'rarity': rarity})) for rarity in range(4)]
    for rarity, amt in enumerate(rarities):
        if amt > len(pool[rarity]):
            return None
        cards.extend(random.sample(pool[rarity], amt))
    await set_cards_availability([doc['id'] for doc in cards], False)
    return cards

async def set_card_availability(card_id, val):
    cards_col.update_one({'id': card_id}, {'$set': {'available': val}})

async def set_cards_availability(card_ids, val):
    cards_col.update_many({'id': {'$in': card_ids}}, {'$set': {'available': val}})

async def get_cards(pred):
    return list(cards_col.find(pred))

async def get_card(id_tag):
    try:
        card_by_id = cards_col.find_one({'id': int(id_tag)})
        if card_by_id != None:
            return card_by_id
    except:
        card_by_tag = cards_col.find_one({'tag': str(id_tag)})
        return card_by_tag

async def set_card_owner(card_id, user_id):
    cards_col.update_one({'id': card_id}, {'$set': {'owned_by': user_id}})

async def set_card_tag(id_tag, tag):
    try:
        cards_col.update_one({'id': int(id_tag)}, {'$set': {'tag': tag}})
    except:
        cards_col.update_one({'tag': str(id_tag)}, {'$set': {'tag': tag}})

async def set_card_frame(card_id_tag, frame_id_tag=0):
    frame_doc = await get_frame(frame_id_tag)
    try:
        cards_col.update_one({'id': int(card_id_tag)}, {'$set': {'frame': frame_doc['id']}})
    except:
        cards_col.update_one({'tag': str(card_id_tag)}, {'$set': {'frame': frame_doc['id']}})

async def set_card_stars(id, stars):
    cards_col.update_one({'id': id}, {'$set': {'stars': stars}})

async def update_card_stars(id, delta, max):
    card         = await get_card(id)
    stars        = card['stars']
    new_stars    = stars + delta
    if new_stars < 0:
        new_stars = 0
    if new_stars > max:
        new_stars = max
    cards_col.update_one({'id': id}, {'$set': {'stars': new_stars}})

# ---------------------------------------------------------------------------------------------------------

async def get_frame(id_tag):
    try:
        frame_by_id =  frames_col.find_one({'id': int(id_tag)})
        if frame_by_id != None:
            return frame_by_id
    except:
        frame_by_tag = frames_col.find_one({'tag': str(id_tag).lower()})
        return frame_by_tag

# ---------------------------------------------------------------------------------------------------------

async def convert_cards(user_id, card_ids, reward):
    user_doc  = await get_user(user_id)
    card_docs = await get_cards({'id': {'$in': card_ids}})
    faves     = user_doc['faves']
    new_faves = [f if f not in card_ids else None for f in faves]
    frames = user_doc['frames']
    for card_doc in card_docs:
        frame_id = card_doc['frame']
        if frame_id == 0:
            continue
        if frame_id not in frames:
            frames[str(frame_id)] = 0
        frames[str(frame_id)] += 1

    players_col.update_one({'discord_id': user_id}, {'$pull': {'collection': {'$in': card_ids}},
        '$set': {'faves': new_faves, 'frames': frames}})
    cards_col.update_many({'id': {'$in': card_ids}}, {'$set': {'available': True, 'tag': None, 'owned_by': None, 'frame': 0, 'stars': 0}})
    await update_user_currency(user_id, reward)

async def gift_cards(giver_id, rec_id, card_ids):
    faves     = (await get_user(giver_id))['faves']
    new_faves = [f if f not in card_ids else None for f in faves]
    players_col.update_one({'discord_id': giver_id}, {'$pull': {'collection': {'$in': card_ids}}, '$set': {'faves': new_faves}})
    players_col.update_one({'discord_id': rec_id}, {'$push': {'collection': {'$each': card_ids}}})
    cards_col.update_many({'id': {'$in': card_ids}}, {'$set': {'owned_by': rec_id}})