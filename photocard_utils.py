import asyncio
import aiohttp
import discord
import io
import numpy as np
import db_utils
from   colorthief import ColorThief
from   PIL import Image, ImageDraw
from   async_timeout import timeout
from   async_lru import alru_cache

PC_GAP    = 50
GALL_GAP  = 50
CARD_SIZE = (360, 640)

CLIENT_SESSION = None

async def stitch_images(card_docs):
    try:
        async with timeout(30):
            n    = len(card_docs)
            imgs = []
            for doc in card_docs:
                img = await create_photocard(doc)
                imgs.append(img)
            none_check     = None in imgs
            if none_check:
                return None
            width, height = imgs[0].size
            new_image     = Image.new('RGBA', (n * width + (n-1) * PC_GAP, height), (255,255,255,0))
            curr_width    = 0

            for i in imgs:
                new_image.paste(i, (curr_width, 0))
                curr_width += width + PC_GAP
            return new_image
    except asyncio.exceptions.TimeoutError:
        return None

async def stitch_gallery(card_docs, rows, cols):
    imgs = []
    for doc in card_docs:
        img = await create_photocard(doc)
        imgs.append(img)

    width, height = [img for img in imgs if img != None][0].size
    new_image     = Image.new('RGBA', (cols * width + (cols-1) * GALL_GAP, rows * height + (rows-1) * GALL_GAP), (255,255,255,0))

    i = 0
    for r in range(rows):
        for c in range(cols):
            if i >= len(imgs):
                return new_image
            if imgs[i] != None:
                new_image.paste(imgs[i], ((width + GALL_GAP) * c, (height + GALL_GAP) * r))
            i += 1
    return new_image

async def create_frame(frame_doc):
    if frame_doc == None:
        return
    frame_img = await download_url(frame_doc['url'])
    frame_img = Image.open(frame_img).resize(CARD_SIZE)
    return frame_img

from PIL import ImageEnhance
import gif_utils as gu
async def image_shiny(im):
    frames = []
    #enhancer = ImageEnhance.Color(im)
    enhancer = ImageEnhance.Brightness(im)
    base_frame = im
    frames.extend([base_frame] * 10)

    for f in range(1, 5, 2):
        factor = 1.0 + 0.1*f
        #factor = f
        bright = enhancer.enhance(factor)
        frames.extend([bright])
    for f in range(5, -1, -1):
        factor = 1.0 + 0.1*f
        #factor = f
        bright = enhancer.enhance(factor)
        frames.extend([bright])
    return frames

async def create_gif_photocard(card_doc):
    if card_doc == None:
        return
    card_img  = await download_url(card_doc['url'])
    frame     = await db_utils.get_frame(card_doc['frame'])
    frame_img = await download_url(frame['url'])

    col      = ColorThief(card_img).get_color(quality=10)

    card_img = Image.open(card_img).convert('RGBA')
    frame_img = Image.open(frame_img)

    if frame['auto']:
        frame_img = await recolour(frame_img, col)

    card_img.paste(frame_img, frame_img)
    card_img = await add_corners(card_img, 45)

    frames = await image_shiny(card_img)
    return frames

async def create_photocard(card_doc):
    if card_doc == None:
        return
    card_img  = await download_url(card_doc['url'])
    frame     = await db_utils.get_frame(card_doc['frame'])
    frame_img = await download_url(frame['url'])

    col      = ColorThief(card_img).get_color(quality=10)

    card_img = Image.open(card_img).convert('RGBA')
    frame_img = Image.open(frame_img)

    if frame['auto']:
        frame_img = await recolour(frame_img, col)

    card_img.paste(frame_img, frame_img)
    card_img = await add_corners(card_img, 45)

    return card_img

async def recolour(img, col):
    data                          = np.array(img)
    red, green, blue, alpha       = data.T
    white_areas                   = (red > 0) & (blue > 0) & (green > 0)
    data[..., :-1][white_areas.T] = col
    new_img                       = Image.fromarray(data)
    return new_img

async def add_corners(im, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw   = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha  = Image.new('L', im.size, 255)
    w, h   = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im

async def hilo(a, b, c):
    if c < b: b, c = c, b
    if b < a: a, b = b, a
    if c < b: b, c = c, b
    return a + c

async def complement(r, g, b):
    k = await hilo(r, g, b)
    return tuple(k - u for u in (r, g, b))

async def pillow_to_attachment(img, channel, gif=False):
    file       = await pillow_to_file(img, gif)
    attachment = (await channel.send(file = file)).attachments[0].url
    return attachment

async def pillow_to_file(img, gif=False):
    image_binary = io.BytesIO()
    if gif:
        gu.save_transparent_gif(img, 80, image_binary)
        image_binary.seek(0)
        file = discord.File(fp=image_binary, filename=f"image.gif")
    else:
        img.save(image_binary, 'PNG')
        image_binary.seek(0)
        file = discord.File(fp=image_binary, filename=f"image.png")
    return file

@alru_cache(maxsize=64)
async def download_url(url):
    global CLIENT_SESSION
    if not CLIENT_SESSION:
        CLIENT_SESSION = aiohttp.ClientSession()
    async with CLIENT_SESSION.get(url) as resp:
        if resp.status != 200:
            return None
        data = io.BytesIO(await resp.read())
        return data