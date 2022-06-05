import io
import os
from PIL import Image, ImageDraw, ImageEnhance
import aiohttp

from colorthief import ColorThief

PC_GAP          = 100
PC_BORDER_THICK = 30
PC_BORDER_RAD   = 100
PC_FADE_MAG     = 1.8

GALL_GAP          = 80
GALL_BORDER_THICK = 20
GALL_BORDER_RAD   = 70
GALL_FADE_MAG     = 1.8

SESSION = None

async def image_shiny(im):
    frames = []
    #enhancer = ImageEnhance.Color(im)
    enhancer = ImageEnhance.Brightness(im)
    base_frame = im
    frames.extend([base_frame] * 5)

    for f in range(1, 10, 3):
        factor = 1.0 + 0.1*f
        #factor = f
        bright = enhancer.enhance(factor)
        frames.extend([bright])
    for f in range(9, -1, -3):
        factor = 1.0 + 0.1*f
        #factor = f
        bright = enhancer.enhance(factor)
        frames.extend([bright])
    return frames

async def create_fade(im, fade, col):
    im = im.convert('RGBA')
    width, height = im.size
    gradient_magnitude=fade
    gradient = Image.new('L', (1, height), color=0xFF)
    for y in range(height):
        gradient.putpixel((0, y), int(255 * (1 - (1 - gradient_magnitude * float(y-(height//2))/height))) if y >= height//2 else 0)
    alpha = gradient.resize(im.size)
    color_im = Image.new('RGBA', (width, height), color=col)
    color_im.putalpha(alpha)
    return color_im

async def create_border(im, col, rad, thick):
    width, height = im.size
    blank = Image.new('RGBA', (width+2*thick, height+2*thick), (255,255,255,0))
    ImageDraw.Draw(blank).rounded_rectangle((0,0,width+2*thick-1,height+2*thick-1), outline=col, radius=rad, width=thick)
    return blank

async def assemble_pc_parts(base, border, gradient, thick):
    width, height = base.size
    card_gradient = Image.alpha_composite(base, gradient)
    res = Image.new('RGBA', (width+2*thick, height+2*thick), (255,255,255,0))
    res.paste(card_gradient, (thick, thick))
    res.paste(border, (0,0), border)
    return res

async def create_photocard(img, fade=PC_FADE_MAG, border_rad=PC_BORDER_RAD, border_thick=PC_BORDER_THICK, shiny=False, res=(1080,1920)):
    col = ColorThief(img).get_color(quality=5)
    img_card = Image.open(img).convert('RGBA')
    img_card = img_card.resize(res, resample=Image.BOX)

    border = await create_border(img_card, col, border_rad, border_thick)
    gradient = await create_fade(img_card, fade, col)

    if shiny:
        border_frames = await image_shiny(border)
        gradient_frames = await image_shiny(gradient)
        frames = []
        for i in range(len(border_frames)):
            frame = await assemble_pc_parts(img_card, border_frames[i], gradient_frames[i], border_thick)
            frames.append(frame)
        return frames
    else:
        return await assemble_pc_parts(img_card, border, gradient, border_thick)

async def stitch_images(imgs_url, out, gap=PC_GAP, m=PC_BORDER_THICK, rad=PC_BORDER_RAD, fade=PC_FADE_MAG, shiny=False):
    n = len(imgs_url)

    imgs = [await download_pic(u) for u in imgs_url]
    imgs = [await create_photocard(i, fade, rad, m, shiny) for i in imgs]

    if shiny:
        final_frames = []
        width, height = imgs[0][0].size
        for i in range(len(imgs[0])):
            new_image = Image.new('RGBA', (n * width + (n-1) * gap, height), (255,255,255,0))
            curr_width = 0
            for frames in imgs:
                new_image.paste(frames[i], (curr_width, 0))
                curr_width += width + gap
            scaled = await scale_for_discord(new_image, 0.2)
            final_frames.append(scaled)
        save_transparent_gif(final_frames, 90, out)
        return imgs

    else:
        width, height = imgs[0].size
        new_image = Image.new('RGBA', (n * width + (n-1) * gap, height), (255,255,255,0))
        curr_width = 0
        for i in imgs:
            new_image.paste(i, (curr_width, 0))
            curr_width += width + gap
        scaled = await scale_for_discord(new_image, 0.3)
        scaled.save(out, "PNG")
        return imgs

async def stitch_gallery(imgs_url, out, gap=GALL_GAP, m=GALL_BORDER_THICK, rad=GALL_BORDER_RAD, fade=GALL_FADE_MAG, shiny=False):
    rows = 2
    cols = 3

    imgs = [await download_pic(u) for u in imgs_url]
    imgs = [await create_photocard(i, fade, rad, m, shiny, (540,960)) for i in imgs]

    width, height = imgs[0].size
    new_image = Image.new('RGBA', (cols * width + (cols-1) * gap, rows * height + (rows-1) * gap), (255,255,255,0))
    i = 0
    for r in range(3):
        for c in range(3):
            if i >= len(imgs):
                scaled = await scale_for_discord(new_image, 0.3)
                scaled.save(out, "PNG")
                return
            new_image.paste(imgs[i], ((width + gap) * c, (height + gap) * r))
            i += 1
    scaled = await scale_for_discord(new_image, 0.3)
    scaled.save(out, "PNG")

async def scale_for_discord(img, frac):
    w, h = img.size
    return img.resize((int(w*frac), int(h*frac)))

async def download_pic(url):
    #global SESSION
    #if not SESSION:
    #    SESSION = aiohttp.ClientSession()
    async with aiohttp.ClientSession().get(url) as resp:
        if resp.status != 200:
            print('Cannot get pic')
        data = io.BytesIO(await resp.read())
        return data

def diy_photocard(base_url, border_url, fade_url, out):
    base_img = Image.open(base_url).resize((1080,1920)).convert('RGBA')
    border_img = Image.open(border_url).convert('RGBA')
    fade_img = Image.open(fade_url).convert('RGBA')
    col = ColorThief(base_url).get_color(quality=5)

    fade_img = recolour(fade_img, col)
    border_img = recolour(border_img, col)

    base_img.paste(border_img, border_img)
    base_img.paste(fade_img, fade_img)

    base_img = add_corners(base_img, 90)
    base_img.save(out, 'PNG')

def recolour(img, col):
    data = np.array(img)   # "data" is a height x width x 4 numpy array
    red, green, blue, alpha = data.T # Temporarily unpack the bands for readability
    white_areas = (red > 0) & (blue > 0) & (green > 0)
    data[..., :-1][white_areas.T] = col
    new_img = Image.fromarray(data)
    return new_img

def add_corners(im, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im

#import numpy as np
#diy_photocard('overlays/img2.jpg', 'overlays/border.png', 'overlays/fade.png', 'overlays/out.png')

#d = 'E:\\x\\legendary'
#out = 'E:\\legendary_out'
#i = 1
#for filename in os.listdir(d):
#    f = os.path.join(d, filename)
#    # checking if it is a file
#    if os.path.isfile(f):
#        Image.open(f).convert('RGB').resize((360,640)).save(os.path.join(out, f'{i:05}.jpg'), optimize=True, quality = 85)
#        #print('done', i)
#        i += 1

d = 'E:\\cards\\legendary_out'
i = 6401
for filename in os.listdir(d):
    f = os.path.join(d, filename)
    # checking if it is a file
    if os.path.isfile(f):
        os.rename(f, os.path.join(d, f"{i:05}.jpg"))
        i += 1
