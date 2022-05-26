import aws_utils
import asyncio
import aiohttp
import discord
import io
import numpy as np
from   colorthief import ColorThief
from   PIL import Image, ImageDraw
from   async_timeout import timeout

PC_GAP    = 50
GALL_GAP  = 50
CARD_SIZE = (360, 640)

BORDER_URL = 'overlays/border_smol.png'
FADE_URL   = 'overlays/fade_smol.png'
STARS_URL  = 'overlays/stars_smol.png'

CLIENT_SESSION = None

async def stitch_images(imgs_url):
    try:
        async with timeout(30):
            n             = len(imgs_url)
            imgs          = [await create_photocard(i, border=True, fade=True) for i in imgs_url]
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

async def stitch_gallery(imgs_url, rows, cols):
    imgs = [await create_photocard(i, border=True, fade=True) for i in imgs_url]

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

async def create_photocard(base_url, border=False, stars=False, fade=False):
    if base_url == None:
        return None
    img      = await download_url(base_url)
    #rarity, id = base_url.split('-')
    #img      = aws_utils.get_image(rarity, id)
    if img == None:
        return None
    base_img = Image.open(img).resize(CARD_SIZE).convert('RGBA')
    col      = ColorThief(img).get_color(quality=10)
    com      = await complement(col[0], col[1], col[2])

    if fade:
        fade_img = await recolour(Image.open(FADE_URL).convert('RGBA'), col)
        base_img.paste(fade_img, fade_img)
    if stars:
        stars_img = await recolour(Image.open(STARS_URL).convert('RGBA'), col)
        base_img.paste(stars_img, stars_img)
    base_img = await add_corners(base_img, 50)
    if border:
        border_img = await recolour(Image.open(BORDER_URL).convert('RGBA'), col)
        base_img.paste(border_img, border_img)

    return base_img

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

async def pillow_to_attachment(img, channel):
    file       = await pillow_to_file(img)
    attachment = (await channel.send(file = file)).attachments[0].url
    return attachment

async def pillow_to_file(img):
    image_binary = io.BytesIO()
    img.save(image_binary, 'PNG')
    image_binary.seek(0)
    file = discord.File(fp=image_binary, filename='image.png')
    return file

async def download_url(url):
    global CLIENT_SESSION
    if not CLIENT_SESSION:
        CLIENT_SESSION = aiohttp.ClientSession()
    async with CLIENT_SESSION.get(url) as resp:
        if resp.status != 200:
            return None
        data = io.BytesIO(await resp.read())
        return data