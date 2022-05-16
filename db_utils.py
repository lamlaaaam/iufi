import os
import random
import pymongo
from   dotenv import load_dotenv
from   datetime import datetime, timedelta

# ----------------------------------------------------------------------------------------------------------
load_dotenv()
MONGO_STRING = os.getenv('MONGO_STRING')
client       = pymongo.MongoClient(MONGO_STRING)
iufi_db      = client['IUFI_DB']
cards_col    = iufi_db['Cards']
players_col  = iufi_db['Players']

# ----------------------------------------------------------------------------------------------------------

#CARDS_PATH = 'data/test_cards.txt'
DATA_PATH = 'data/'

# ----------------------------------------------------------------------------------------------------------

async def setup_cards():
    if cards_col.count_documents({}) > 0:
        cards_col.drop()
    
    card_docs = []
    id = 1
    for x in range(4):
        for url in open(os.path.join(DATA_PATH, f"{x}.txt"), 'r'):
            doc = {'id'       : id,
                   'tag'      : None,
                   'url'      : url.strip(),
                   'available': True,
                   'owned_by' : None,
                   'rarity'   : x} 
            card_docs.append(doc)
            id += 1
    cards_col.insert_many(card_docs)

async def setup_players():
    if players_col.count_documents({}) > 0:
        players_col.drop()

# ----------------------------------------------------------------------------------------------------------

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
                            'legend_rolls' : 0})
    return True

async def add_card_to_user(user_id, card_id):
    user  = await get_user(user_id)
    cards = user['collection']
    if card_id in cards:
        return
    players_col.update_one({'discord_id': user_id}, {'$push': {'collection': card_id}})

async def remove_card_from_user(user_id, card_id):
    players_col.update_one({'discord_id': user_id}, {'$pull': {'collection': card_id}})

async def get_user(id):
    return players_col.find_one({'discord_id': id})

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
    return players_col.find()

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

# ---------------------------------------------------------------------------------------------------------

async def check_pool_exists(bias):
    if bias > 0:
        available = len(list(cards_col.find({'rarity': bias, 'available': True})))
    else:
        available = len(list(cards_col.find({'available': True})))
    pool_exists = available > 0
    return pool_exists

async def get_random_cards(num, probs, bias):
    cards   = []
    settled = False
    for i in range(num):
        roll = random.randint(1, 1000)
        if not settled and bias > 0:
            settled = True
            rarity  = bias
        else:
            for r, p in enumerate(probs):
                if roll <= p:
                    rarity = r
                    break
        card = list(cards_col.aggregate([{'$match': {'available': True, 'rarity': rarity}}, {'$sample': {'size': 1}}]))[0]
        cards.append(card)
        cards_col.update_one({'id': card['id']}, {'$set': {'available': False}})
    card_ids = [card['id'] for card in cards]
    cards_col.update_many({'id': {'$in': card_ids}}, {'$set': {'available': True}})
    return cards

async def set_card_availability(card_id, val):
    cards_col.update_one({'id': card_id}, {'$set': {'available': val}})

async def get_cards(pred):
    return cards_col.find(pred)

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
        return
    except:
        cards_col.update_one({'tag': str(id_tag)}, {'$set': {'tag': tag}})