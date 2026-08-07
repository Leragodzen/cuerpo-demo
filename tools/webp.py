# -*- coding: utf-8 -*-
"""Перевод фотографий сайта в webp.

Зачем: webp весит в 2–3 раза меньше jpeg при том же качестве, а поддерживают
его все актуальные браузеры (Safari — с 14-й версии, 2020 год).

Запуск из корня проекта:
    python3 tools/webp.py           — пересобрать webp из исходных jpg/png
    python3 tools/webp.py --clean   — то же плюс удалить исходники

Файл assets/img/og-cover.jpg НЕ трогаем: картинку для превью в мессенджерах
многие сервисы читают только в jpeg.
"""

import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMGDIR = os.path.join(ROOT, 'assets', 'img')
KEEP = {'og-cover.jpg'}
QUALITY = 82


def main():
    clean = '--clean' in sys.argv
    saved_before = saved_after = 0
    made = []

    for fn in sorted(os.listdir(IMGDIR)):
        if fn in KEEP or not fn.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        src = os.path.join(IMGDIR, fn)
        dst = os.path.splitext(src)[0] + '.webp'

        im = Image.open(src)
        # Логотип на первом экране лежит поверх фотографии — прозрачность нужна
        im = im.convert('RGBA' if im.mode in ('RGBA', 'LA', 'P') else 'RGB')
        im.save(dst, 'WEBP', quality=QUALITY, method=6)

        saved_before += os.path.getsize(src)
        saved_after += os.path.getsize(dst)
        made.append((fn, os.path.getsize(src), os.path.getsize(dst)))
        if clean:
            os.remove(src)

    for fn, a, b in made:
        print('  %-28s %6.0f КБ -> %6.0f КБ' % (fn, a / 1024.0, b / 1024.0))
    print('Всего: %d файлов, %.1f МБ -> %.1f МБ' %
          (len(made), saved_before / 1048576.0, saved_after / 1048576.0))
    if not clean:
        print('Исходники оставлены. Удалить: python3 tools/webp.py --clean')


if __name__ == '__main__':
    main()
