# -*- coding: utf-8 -*-
"""Фирменные картинки сайта: обложка для соцсетей и иконки вкладки.

  assets/img/og-cover.jpg      1200×630 — превью ссылки в Telegram, VK, WhatsApp.
                               Формат намеренно jpeg: webp многие сервисы
                               предпросмотра не читают.
  assets/favicon.svg           иконка вкладки, векторная — её берут все
                               современные браузеры
  assets/favicon-32.png        запасная растровая для старых браузеров
  assets/apple-touch-icon.png  180×180 — ярлык сайта на экране iPhone

Запуск из корня проекта:  python3 tools/brand.py
"""

import io
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMGDIR = os.path.join(ROOT, 'assets', 'img')
ASSETS = os.path.join(ROOT, 'assets')

W, H = 1200, 630
SRC = 'int-lounge-green.jpg'      # зона отдыха: тёплый свет и зелёная стена
LOGO = 'logo-light.png'
OUT = 'og-cover.jpg'

BROWN = (67, 48, 31)              # --brown, фон иконки
MINT = (143, 191, 172)            # --mint, буква и акценты
# Jost с сайта в системе нет; Avenir Next — ближайшая по духу гротеска
# с полноценной кириллицей (в Futura её нет, буквы выпадают в квадраты).
FONT = '/System/Library/Fonts/Avenir Next.ttc'
FONT_C = '/System/Library/Fonts/Supplemental/Georgia Italic.ttf'


def cover(im, w, h):
    """Вписать по короткой стороне и обрезать лишнее — как background-size:cover."""
    k = max(float(w) / im.width, float(h) / im.height)
    im = im.resize((int(round(im.width * k)), int(round(im.height * k))), Image.LANCZOS)
    x = (im.width - w) // 2
    y = (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def build_og():
    bg = cover(Image.open(os.path.join(IMGDIR, SRC)).convert('RGB'), W, H)
    bg = ImageEnhance.Brightness(bg).enhance(0.78)
    bg = bg.filter(ImageFilter.GaussianBlur(0.6))

    # Затемнение снизу вверх, чтобы логотип читался на любой части кадра
    shade = Image.new('L', (1, H))
    for y in range(H):
        t = y / float(H - 1)
        shade.putpixel((0, y), int(40 + 150 * t ** 1.6))
    shade = shade.resize((W, H))
    bg = Image.composite(Image.new('RGB', (W, H), (26, 30, 25)), bg, shade)

    # Логотип: в нём уже набраны и «Cuerpo», и «мастерская по телу»
    logo = Image.open(os.path.join(IMGDIR, LOGO)).convert('RGBA')
    lw = 620
    logo = logo.resize((lw, int(round(logo.height * lw / float(logo.width)))), Image.LANCZOS)
    lx, ly = (W - lw) // 2, 168
    bg.paste(logo, (lx, ly), logo)

    d = ImageDraw.Draw(bg)
    y = ly + logo.height + 46
    d.line([(W // 2 - 46, y), (W // 2 + 46, y)], fill=MINT, width=2)

    try:
        f = ImageFont.truetype(FONT, 30)
    except Exception:
        f = ImageFont.load_default()
    line = 'М А С С А Ж   И   S P A   ·   Т О Л Ь Я Т Т И'
    box = d.textbbox((0, 0), line, font=f)
    d.text(((W - (box[2] - box[0])) // 2, y + 34), line, font=f, fill=(238, 234, 226))

    path = os.path.join(IMGDIR, OUT)
    bg.save(path, 'JPEG', quality=88, optimize=True, progressive=True)
    print('  assets/img/%-24s %d×%d, %.0f КБ' % (OUT, W, H, os.path.getsize(path) / 1024.0))


FAVICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <rect width="100" height="100" rx="22" fill="#43301F"/>
  <text x="50" y="72" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif"
        font-size="64" font-style="italic" fill="#8FBFAC">C</text>
</svg>
'''


def icon(size):
    """Растровая иконка: коричневый скруглённый квадрат и мятная «C»."""
    k = 4                                   # рисуем крупнее и уменьшаем — края мягче
    s = size * k
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.22), fill=BROWN + (255,))
    try:
        f = ImageFont.truetype(FONT_C, int(s * 0.64))
    except Exception:
        f = ImageFont.load_default()
    box = d.textbbox((0, 0), 'C', font=f)
    d.text(((s - (box[2] - box[0])) / 2 - box[0], (s - (box[3] - box[1])) / 2 - box[1]),
           'C', font=f, fill=MINT + (255,))
    return im.resize((size, size), Image.LANCZOS)


def build_icons():
    io.open(os.path.join(ASSETS, 'favicon.svg'), 'w', encoding='utf-8').write(FAVICON_SVG)
    print('  assets/favicon.svg')

    icon(32).save(os.path.join(ASSETS, 'favicon-32.png'), 'PNG', optimize=True)
    print('  assets/favicon-32.png            32×32')

    # Ярлык на домашнем экране iOS обрезает прозрачность до квадрата — кладём
    # иконку на сплошной фон, иначе углы становятся чёрными.
    apple = Image.new('RGB', (180, 180), BROWN)
    ic = icon(180)
    apple.paste(ic, (0, 0), ic)
    apple.save(os.path.join(ASSETS, 'apple-touch-icon.png'), 'PNG', optimize=True)
    print('  assets/apple-touch-icon.png      180×180')


def main():
    print('Фирменные картинки:')
    build_og()
    build_icons()


if __name__ == '__main__':
    main()
