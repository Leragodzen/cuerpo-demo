# -*- coding: utf-8 -*-
"""Проверка собранного сайта перед публикацией.

Смотрит то, что легко упустить руками: незакрытые теги, битые пути к файлам,
картинки без alt и без отложенной загрузки, повторяющиеся title и description,
кнопки записи без привязки к YClients, невалидный JSON-LD.

Запуск из корня проекта:  python3 tools/check.py
"""

import io
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {'.git', '_drafts', '_upload', 'tools', '.claude', 'assets'}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}

problems = []


def bad(page, msg):
    problems.append('%s — %s' % (page, msg))


class Balance(HTMLParser):
    """Ищет незакрытые и лишние закрывающие теги."""

    def __init__(self, page):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.page = page
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            bad(self.page, 'лишний </%s> в строке %d' % (tag, self.getpos()[0]))
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
        elif any(t == tag for t, _ in self.stack):
            while self.stack and self.stack[-1][0] != tag:
                t, ln = self.stack.pop()
                bad(self.page, 'не закрыт <%s>, открыт в строке %d' % (t, ln))
            self.stack.pop()
        else:
            bad(self.page, 'лишний </%s> в строке %d' % (tag, self.getpos()[0]))


def pages():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in sorted(files):
            if fn.endswith('.html'):
                yield os.path.relpath(os.path.join(base, fn), ROOT)


def main():
    titles, descs = {}, {}

    for page in sorted(pages()):
        html = io.open(os.path.join(ROOT, page), encoding='utf-8').read()
        folder = os.path.dirname(page)

        b = Balance(page)
        b.feed(html)
        for t, ln in b.stack:
            bad(page, 'не закрыт <%s>, открыт в строке %d' % (t, ln))

        # Пути к файлам
        for m in re.finditer(r'(?:src|href)="([^"]+\.(?:webp|jpg|png|svg|css|js))"', html):
            u = m.group(1)
            if u.startswith(('http', 'data:', '//')):
                continue
            if not os.path.exists(os.path.normpath(os.path.join(ROOT, folder, u))):
                bad(page, 'нет файла %s' % u)

        # Ссылки внутри сайта. Проверка добавлена после того, как удалённая
        # услуга осталась висеть ссылкой в подвале на всех страницах: сборка
        # перезаписывает страницы, но не знает, что раньше вело в никуда.
        for m in re.finditer(r'href="([^"#?][^"]*)"', html):
            u = m.group(1)
            if u.startswith(('http', 'mailto:', 'tel:', 'data:', '//')):
                continue
            target = os.path.normpath(os.path.join(ROOT, folder, u.split('#')[0]))
            if os.path.isdir(target):
                target = os.path.join(target, 'index.html')
            if not os.path.exists(target):
                bad(page, 'ссылка в никуда: %s' % u)

        # Картинки: alt обязателен, отложенная загрузка — всем, кроме первого экрана
        for tag in re.findall(r'<img\b[^>]*>', html):
            if not re.search(r'\balt="[^"]', tag) and 'id="lbImg"' not in tag:
                bad(page, 'картинка без alt: %s' % tag[:90])
            first_screen = 'fetchpriority="high"' in tag or 'hero__logo' in tag
            if 'loading=' not in tag and not first_screen and 'id="lbImg"' not in tag:
                bad(page, 'картинка без loading="lazy": %s' % tag[:90])

        # Уникальные title и description
        t = re.search(r'<title>(.*?)</title>', html, re.S)
        d = re.search(r'<meta name="description" content="([^"]*)"', html)
        if not t:
            bad(page, 'нет <title>')
        else:
            titles.setdefault(t.group(1), []).append(page)
        if not d:
            bad(page, 'нет meta description')
        else:
            descs.setdefault(d.group(1), []).append(page)

        # og-теги. Служебные страницы (noindex, nofollow) их не требуют: они
        # закрыты от поисковиков и не рассчитаны на пересылку ссылкой, а
        # og:image заставил бы придумывать им обложку. Публичные страницы демо
        # стоят как noindex, follow — их проверка по-прежнему касается.
        sluzhebnaya = 'content="noindex, nofollow"' in html
        if not sluzhebnaya:
            for prop in ('og:title', 'og:description', 'og:image', 'og:url'):
                if 'property="%s"' % prop not in html:
                    bad(page, 'нет мета-тега %s' % prop)

        # Кнопки записи: только ссылки, адрес ставит app.js из одной константы
        for tag in re.findall(r'<\w+\b[^>]*\bdata-book\b[^>]*>', html):
            if not tag.startswith('<a'):
                bad(page, 'кнопка записи не ссылка: %s' % tag[:80])
            if 'href=' in tag:
                bad(page, 'адрес записи зашит в разметку: %s' % tag[:80])

        # Формы, собирающие персональные данные, на сайте быть не должно
        if re.search(r'<input[^>]+type="(?:tel|email)"', html):
            bad(page, 'на странице есть поле для телефона или почты')

        # JSON-LD
        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
            try:
                json.loads(m.group(1))
            except Exception as e:
                bad(page, 'JSON-LD не разбирается: %s' % e)

    for t, ps in titles.items():
        if len(ps) > 1:
            bad(', '.join(ps), 'одинаковый title: %s' % t[:60])
    for d, ps in descs.items():
        if len(ps) > 1:
            bad(', '.join(ps), 'одинаковый description')

    if problems:
        print('Замечаний: %d' % len(problems))
        for p in problems:
            print('  ' + p)
        sys.exit(1)
    print('Всё чисто: %d страниц.' % len(list(pages())))


if __name__ == '__main__':
    main()
