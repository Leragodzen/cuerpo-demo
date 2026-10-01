# -*- coding: utf-8 -*-
"""Сборщик страниц каталога Cuerpo.

Что делает:
  * uslugi/<направление>/index.html          — страница направления со списком услуг
  * uslugi/<направление>/<услуга>/index.html — страница услуги
  * sertifikaty/index.html                   — подарочные сертификаты
  * 404.html                                 — страница «не найдено»
  * sitemap.xml                              — карта сайта

Общая обвязка (шапка, меню, подвал, мобильная панель, модальные окна) не
дублируется руками: скрипт вырезает её из index.html и правит относительные
пути под глубину страницы. Значит, поправив шапку на главной, достаточно
перезапустить сборку — и она обновится на всех страницах.

Запуск из корня проекта:  python3 tools/build.py
"""

import hashlib
import io
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://cuerpomassage.ru/'

exec(io.open(os.path.join(ROOT, 'tools', 'data.py'), encoding='utf-8').read())

INDEX = io.open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()


# ------------------------------------------------------------------ утилиты

def between(text, start_marker, end_marker, keep_end=True):
    a = text.index(start_marker)
    b = text.index(end_marker, a) + (len(end_marker) if keep_end else 0)
    return text[a:b]


ROOT_DIRS = ('assets/', 'uslugi/', 'sertifikaty/', 'politika/')


def rebase(html, base):
    """Правит относительные ссылки под глубину страницы.

    Обвязка написана для главной, где все пути отсчитываются от корня. На
    вложенной странице к ним нужно добавить нужное число «../» — иначе
    /uslugi/spa-programmy/relax/ будет искать uslugi/ внутри самой себя.
    """
    for d in ROOT_DIRS:
        html = html.replace('src="%s' % d, 'src="%s%s' % (base, d))
        html = html.replace('href="%s' % d, 'href="%s%s' % (base, d))
    # Якоря главной: #services -> ../../#services. Пустой href="#" не трогаем.
    html = re.sub(r'href="#(?!")', 'href="%s#' % base, html)
    return html


LINES = INDEX.split('\n')


def block(start_sub, close_tag='</div>'):
    """Верхнеуровневый блок разметки: от строки со start_sub до закрывающего
    тега в нулевой колонке. Опираться на соседний текст нельзя — он меняется."""
    i = next(k for k, l in enumerate(LINES) if start_sub in l)
    j = next(k for k in range(i + 1, len(LINES)) if LINES[k] == close_tag)
    return '\n'.join(LINES[i:j + 1])


CHROME = {
    'header': block('<header class="header"', '</header>'),
    'menu': block('<div class="mobile-menu"'),
    'footer': block('<footer class="footer">', '</footer>'),
    'mbar': block('<div class="mbar"'),
}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400;1,500&family=Jost:wght@300;400;500;600&display=swap" rel="stylesheet">')

ICONS = '\n'.join(l for l in LINES
                  if l.startswith('<link rel="icon"') or l.startswith('<link rel="apple-touch-icon"'))
METRIKA = between(INDEX, '<!-- ============================================================\n     ЯНДЕКС.МЕТРИКА', '</script>')

# Разрешение на индексацию берём с главной, чтобы значение жило в одном месте:
# поправили <meta name="robots"> в index.html, пересобрали — и оно разошлось по
# всем страницам. Пока это демо, там стоит noindex.
ROBOTS = between(INDEX, '<meta name="robots"', '>')


def esc_attr(s):
    return s.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;')


OG_IMAGE = 'assets/img/og-cover.jpg'


def page(base, url, title, desc, body, extra_ld='', og_image=OG_IMAGE):
    return '''<!DOCTYPE html>
<html lang="ru" class="no-js">
<head>
<script>document.documentElement.className=document.documentElement.className.replace('no-js','js')</script>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#43301F">

<title>%(title)s</title>
<meta name="description" content="%(desc)s">
%(robots)s
<meta name="format-detection" content="telephone=no">
<link rel="canonical" href="%(site)s%(url)s">

<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:site_name" content="Cuerpo — мастерская по телу">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:image" content="%(site)s%(og)s">
<meta property="og:url" content="%(site)s%(url)s">
<meta name="twitter:card" content="summary_large_image">

%(favicon)s
%(fonts)s
<link rel="stylesheet" href="%(base)sassets/style.css">

%(metrika)s
</head>
<body>

%(header)s

%(menu)s

<main id="top">
%(body)s
</main>

%(footer)s

%(mbar)s

%(ld)s
<script src="%(base)sassets/app.js" defer></script>
</body>
</html>
''' % {
        'title': esc_attr(title), 'desc': esc_attr(desc), 'site': SITE, 'url': url,
        'robots': ROBOTS, 'og': og_image, 'base': base,
        'favicon': rebase(ICONS, base), 'fonts': FONTS, 'metrika': METRIKA,
        'header': rebase(CHROME['header'], base), 'menu': rebase(CHROME['menu'], base),
        'footer': rebase(CHROME['footer'], base), 'mbar': rebase(CHROME['mbar'], base),
        'body': body, 'ld': extra_ld,
    }


ARROW = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>'


def crumbs(items):
    """items: [(текст, ссылка|None), ...] — последний без ссылки."""
    out = ['<nav class="crumbs" aria-label="Хлебные крошки">']
    for i, (label, href) in enumerate(items):
        if i:
            out.append('  ' + ARROW)
        if href:
            out.append('  <a href="%s">%s</a>' % (href, label))
        else:
            out.append('  <span aria-current="page">%s</span>' % label)
    out.append('</nav>')
    return '\n'.join(out)


def durations(s, interactive=True):
    """Чипсы длительности.

    Пока у услуги один вариант — он и активен. Как только в tools/data.py
    появится поле durations со списком, чипсы начнут переключать цену.

    В карточках каталога это подписи (span), а не кнопки: нажимать там нечего,
    а неработающий элемент управления только сбивает с толку. Настоящие
    переключатели живут на странице услуги.
    """
    items = s.get('durations') or ([{'label': s['dur'], 'price': s['price_full']}] if s.get('dur') else [])
    if not items:
        return ''
    out = ['<div class="dur" role="group" aria-label="Длительность сеанса">']
    for i, d in enumerate(items):
        cls = 'dur__b' + (' is-active' if i == 0 else '')
        if interactive:
            out.append('  <button type="button" class="%s" data-price="%s">%s</button>'
                       % (cls, esc_attr(d['price']), d['label']))
        else:
            out.append('  <span class="%s">%s</span>' % (cls, d['label']))
    out.append('</div>')
    return '\n'.join(out)


def price_rows(s):
    out = ['<div class="prices">']
    if s.get('promo'):
        out.append('  <div class="prices__r prices__r--promo"><b>%s</b><span>первый визит по промокоду «ПЕРВЫЙ»</span></div>' % s['promo'])
        out.append('  <div class="prices__r prices__r--base"><b>%s</b><span>цена без акции</span></div>' % s['price_full'])
    else:
        out.append('  <div class="prices__r"><b>%s</b><span>стоимость сеанса</span></div>' % s['price_full'])
    if s.get('dur'):
        out.append('  <div class="prices__r prices__r--base"><b>%s</b><span>продолжительность</span></div>' % s['dur'])
    out.append('</div>')
    return '\n'.join(out)


CAMERA = ('<svg viewBox="0 0 24 24" aria-hidden="true">'
          '<path d="M3 8.5h3.2l1.4-2.2h8.8l1.4 2.2H21v10H3z"/>'
          '<circle cx="12" cy="13.2" r="3.6"/></svg>')


def shot_stub(s, cls):
    """Заглушка вместо фотографии — с описанием нужного кадра.

    Половина снимков в каталоге была подобрана в интернете и к салону
    отношения не имеет. Ставить их рядом с реальными — обманывать гостя,
    а убрать вовсе — сломать вёрстку. Поэтому здесь стоит осознанная
    заглушка: она держит сетку и заодно служит техзаданием на съёмку.

    Как убрать: положите снимок в assets/img, пропишите его в IMG,
    укажите услуге 'img' и удалите у неё поле 'shot'.
    """
    return ('    <span class="%s shot">\n'
            '      <span class="shot__ic">%s</span>\n'
            '      <span class="shot__lab">Нужна фотография</span>\n'
            '      <span class="shot__txt">%s</span>\n'
            '    </span>' % (cls, CAMERA, s['shot']))


def card(s, href, base, main=False):
    """Карточка услуги для страницы направления и для лент."""
    L = ['<article class="card-s reveal">']
    L.append('  <a class="card-s__open" href="%s">' % href)
    if s.get('shot'):
        L.append(shot_stub(s, 'card-s__pic'))
    else:
        img, w, h = IMG[s['img']]
        L.append('    <span class="card-s__pic">')
        L.append('      <img src="%s%s" width="%d" height="%d" loading="lazy" decoding="async" alt="%s">' % (base, img, w, h, esc_attr(s['alt'])))
        L.append('      <span class="card-s__more">%s</span>' % ARROW)
        L.append('    </span>')
    L.append('  </a>')
    L.append('  <div class="card-s__in">')
    if s.get('promo'):
        L.append('    <span class="card-s__promo">%s</span>' % s['promo'])
        L.append('    <span class="card-s__note">первый визит по промокоду «ПЕРВЫЙ»</span>')
        L.append('    <span class="card-s__old">%s</span>' % s['price_full'])
    else:
        L.append('    <span class="card-s__price">%s</span>' % s['price_html'])
    L.append('    <a class="card-s__ttl" href="%s">%s</a>' % (href, s['title']))
    L.append('    <span class="card-s__txt">%s</span>' % s['txt'])
    tags = ''.join('<span class="card-s__tag">%s</span>' % t for t in s.get('tags', []))
    if tags:
        L.append('    <span class="card-s__tags">%s</span>' % tags)
    d = durations(s, interactive=False)
    if d:
        L.append('    ' + d.replace('class="dur"', 'class="dur dur--card"'))
    L.append('  </div>')
    L.append('  <a class="btn btn--%s btn--sm" data-book data-service="%s">Записаться</a>'
             % ('primary' if main else 'ghost', esc_attr(s['name'])))
    L.append('</article>')
    return '\n'.join(L)


def eff_block(s):
    out = ['<h2 class="h3">Что вас ждёт</h2>', '<ul class="svc-full__eff">']
    for ic, txt in s['eff']:
        out.append('  <li><span class="ic"><svg viewBox="0 0 24 24">%s</svg></span>%s</li>' % (IC[ic], txt))
    out.append('</ul>')
    return '\n'.join(out)


def inc_block(s):
    out = ['<h2 class="h3">Что входит в сеанс</h2>', '<ul class="svc-full__inc">']
    for t in s['inc']:
        out.append('  <li>%s</li>' % t)
    out.append('</ul>')
    return '\n'.join(out)


def long_block(s):
    if not s.get('long'):
        return ''
    out = ['<h2 class="h3">Подробнее об услуге</h2>',
           '<div class="more" id="svcMore">',
           '  <div class="more__body">']
    for head, paras in s['long']:
        out.append('    <h3>%s</h3>' % head)
        for p in paras:
            out.append('    <p>%s</p>' % p)
    out.append('  </div>')
    out.append('  <button type="button" class="btn btn--ghost btn--sm more__btn" data-more>Показать все</button>')
    out.append('</div>')
    return '\n'.join(out)


# ------------------------------------------------------- карта «где чья страница»
HOME = {}          # имя услуги -> (слаг направления, слаг услуги)
for d in DIRS:
    for s in d['services']:
        HOME.setdefault(s['name'], (d['slug'], s['slug']))

ALL = []           # плоский список уникальных услуг
_seen = set()
for d in DIRS:
    for s in d['services']:
        if s['name'] in _seen:
            continue
        _seen.add(s['name'])
        ALL.append((d, s))


def svc_url(name, base):
    ds, ss = HOME[name]
    return '%suslugi/%s/%s/' % (base, ds, ss)


def write(path, html):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    io.open(full, 'w', encoding='utf-8').write(html)
    return path


# ------------------------------------------------------------ страница направления

def build_dir_page(d):
    base = '../../'
    url = 'uslugi/%s/' % d['slug']
    plain = re.sub(r'<[^>]+>', '', d['intro'])

    def href_for(s):
        """Услуга живёт в своём направлении: внутри — рядом, иначе через соседа."""
        ds, ss = HOME[s['name']]
        return '%s/' % ss if ds == d['slug'] else '../%s/%s/' % (ds, ss)

    # Все услуги направления — карточками с фотографией, коротким описанием
    # и кнопкой записи. Прайс-списком строками они были до 14 августа: список
    # компактнее, но заказчик забраковал — «не читается».
    cards = '\n'.join(card(s, href_for(s), base, main=s.get('main', False))
                      for s in d['services'])

    others = '\n'.join(
        '''      <a class="cat" href="../%s/">
        <img class="cat__img" src="%s%s" width="%d" height="%d" loading="lazy" decoding="async" alt="%s">
        <span class="cat__body">
          <span class="cat__ttl">%s</span>
          <span class="cat__meta">%s</span>
        </span>
      </a>''' % (o['slug'], base, IMG[o['img']][0], IMG[o['img']][1], IMG[o['img']][2],
                 esc_attr(o['tile_alt']), o['tile_ttl'], o['tile_meta'])
        for o in DIRS if o['slug'] != d['slug'])

    body = '''<section class="section section--tight subpage">
  <div class="container">
%(crumbs)s

    <header class="pagehead reveal">
      <span class="pagehead__sub">%(sub)s</span>
      <h1>%(title)s</h1>
      <p class="pagehead__lead">%(intro)s</p>
    </header>

    <div class="cards cards--%(ncards)d">
%(cards)s
    </div>
  </div>
</section>

<section class="section section--sand">
  <div class="container">
    <div class="head head--center reveal">
      <p class="eyebrow eyebrow--center">Другие направления</p>
      <h2 class="h2">Посмотрите, что ещё есть<br>в мастерской</h2>
    </div>
    <div class="cats cats--mini reveal">
%(others)s
    </div>
  </div>
</section>
''' % {
        'crumbs': crumbs([('Главная', base), ('Услуги', base + '#services'), (d['title'], None)]),
        'sub': d['sub'], 'title': d['title'], 'intro': d['intro'],
        'cards': cards, 'others': others,
        # Сетка сверстана на 4 колонки. Где услуг меньше, число уезжает
        # в класс: иначе ряд из двух карточек оставляет полэкрана пустым.
        'ncards': min(len(d['services']), 4),
    }

    ld = '''<script type="application/ld+json">
{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
{"@type":"ListItem","position":1,"name":"Главная","item":"%s"},
{"@type":"ListItem","position":2,"name":"%s","item":"%s%s"}]}
</script>''' % (SITE, d['title'], SITE, url)

    title = '%s в Тольятти — цены и запись | Cuerpo' % d['title']
    desc = ('%s в массажном салоне Cuerpo, Тольятти, Приморский бульвар 57. %s Запись по телефону '
            '+7 (927) 892-30-13, ежедневно 09:00–21:00.') % (d['title'], plain[:150])
    return write(url + 'index.html',
                 page(base, url, title, desc, body, ld))


# ----------------------------------------------------------------- страница услуги

def build_svc_page(d, s):
    base = '../../../'
    url = 'uslugi/%s/%s/' % (d['slug'], s['slug'])
    img, w, h = IMG[s['img']]

    # «Советуем посетить»: сначала соседи по направлению, потом остальные
    same = [(o, x) for (o, x) in ALL if o['slug'] == d['slug'] and x['name'] != s['name']]
    rest = [(o, x) for (o, x) in ALL if o['slug'] != d['slug']]
    rail = (same + rest)[:6]
    rail_html = '\n'.join(card(x, svc_url(x['name'], base), base) for _, x in rail)

    body = '''<section class="section section--tight subpage">
  <div class="container">
%(crumbs)s

    <div class="svcp">
%(pic)s

      <div class="reveal">
        <h1>%(title)s</h1>
        <p class="pagehead__lead">%(lead)s</p>
%(tags)s
%(prices)s

        <div class="svcp__act">
%(dur)s
          <a class="btn btn--primary btn--full" data-book data-service="%(name)s">Записаться</a>
        </div>

      </div>
    </div>
  </div>
</section>

<section class="section section--sand">
  <div class="container">
    <div class="ba__grid" style="display:grid; gap:clamp(26px,4vw,52px)">
      <div class="reveal">
%(eff)s
      </div>
      <div class="reveal">
%(inc)s
      </div>
%(long)s
    </div>
  </div>
</section>

<section class="section section--tight">
  <div class="container">
    <div class="head reveal">
      <p class="eyebrow">Советуем посетить</p>
      <h2 class="h2">То, что может вам понравиться</h2>
    </div>
    <div class="rail-s reveal">
      <div class="rail-s__track">
%(rail)s
      </div>
    </div>
  </div>
</section>
''' % {
        'crumbs': crumbs([('Главная', base), (d['title'], '../'), (s['name'], None)]),
        'base': base,
        'pic': ('      <figure class="svcp__pic reveal">\n%s\n      </figure>'
                % shot_stub(s, 'svcp__stub').replace('    <span', '        <span')
                ) if s.get('shot') else (
               '      <figure class="svcp__pic reveal">\n'
               '        <img src="%s%s" width="%d" height="%d"\n'
               '             fetchpriority="high" decoding="async" alt="%s">\n'
               '      </figure>' % (base, img, w, h, esc_attr(s['alt']))),
        'title': s['name'], 'lead': s['lead'],
        'tags': ('        <div class="svcp__tags">%s</div>'
                 % ''.join('<span class="card-s__tag">%s</span>' % t for t in s.get('tags', []))) if s.get('tags') else '',
        'prices': '        ' + price_rows(s).replace('\n', '\n        '),
        'dur': '          ' + durations(s).replace('\n', '\n          ') if durations(s) else '',
        'name': esc_attr(s['name']),
        'eff': '        ' + eff_block(s).replace('\n', '\n        '),
        'inc': '        ' + inc_block(s).replace('\n', '\n        '),
        'long': ('      <div class="reveal">\n        %s\n      </div>'
                 % long_block(s).replace('\n', '\n        ')) if s.get('long') else '',
        'rail': rail_html,
    }

    price_ld = ''
    m = re.search(r'(\d[\d\s ]*)\s*₽', s['price_full'])
    if m:
        price_ld = ',"offers":{"@type":"Offer","price":"%s","priceCurrency":"RUB","availability":"https://schema.org/InStock"}' % re.sub(r'\s', '', m.group(1))

    ld = '''<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Service","name":"%(name)s","serviceType":"%(dir)s",
"description":"%(lead)s","image":"%(site)s%(img)s","url":"%(site)s%(url)s","areaServed":"Тольятти",
"provider":{"@type":"HealthAndBeautyBusiness","name":"Cuerpo — мастерская по телу","telephone":"+7 927 892-30-13",
"address":{"@type":"PostalAddress","addressLocality":"Тольятти","streetAddress":"Приморский бульвар, 57"}}%(offer)s}
</script>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
{"@type":"ListItem","position":1,"name":"Главная","item":"%(site)s"},
{"@type":"ListItem","position":2,"name":"%(dir)s","item":"%(site)suslugi/%(ds)s/"},
{"@type":"ListItem","position":3,"name":"%(name)s","item":"%(site)s%(url)s"}]}
</script>''' % {'name': esc_attr(s['name']), 'dir': d['title'], 'lead': esc_attr(s['lead']),
                'site': SITE, 'img': img, 'url': url, 'ds': d['slug'], 'offer': price_ld}

    title = '%s в Тольятти — %s | Cuerpo' % (s['name'], s['price_full'])
    desc = '%s Массажный салон Cuerpo, Тольятти, Приморский бульвар 57. Запись: +7 (927) 892-30-13.' % s['lead']
    return write(url + 'index.html', page(base, url, title, desc[:300], body, ld))


# ------------------------------------------------------------------ сертификаты

# Быстрые подсказки по сумме — не жёсткие номиналы: сумму можно ввести любую.
# Это просто три частых значения, чтобы не набирать руками.
GIFT_HINTS = ['3 000', '5 000', '7 000', '10 000', '15 000']

# Направления, которые не показываем в сертификате. Прогрев отдельной
# услугой в подарок не берут — только внутри SPA-программ.
GIFT_SKIP_DIRS = ('progretsya',)


def build_gift_page():
    base = '../'
    url = 'sertifikaty/'

    gift_dirs = [d for d in DIRS if d['slug'] not in GIFT_SKIP_DIRS]

    hints = '\n'.join(
        '            <button type="button" class="buy__hint" data-sum="%s">%s ₽</button>'
        % (h.replace(' ', '').replace(' ', ''), h) for h in GIFT_HINTS)

    # Выпадающий список программ: цена едет в data-price, из неё считается итог.
    opts = []
    for d in gift_dirs:
        opts.append('              <optgroup label="%s">' % d['title'])
        for s in d['services']:
            digits = re.sub(r'[^\d]', '', s['price_full'])
            if not digits:
                continue
            opts.append('                <option value="%s" data-price="%s">%s — %s</option>'
                        % (esc_attr(s['name']), digits, s['title'], s['price_full']))
        opts.append('              </optgroup>')
    opts = '\n'.join(opts)

    menu = []
    for d in gift_dirs:
        menu.append('        <div class="gmenu__g">')
        menu.append('          <h3 class="gmenu__h">%s</h3>' % d['title'])
        for s in d['services']:
            menu.append(
                '          <a class="gmenu__r" href="%suslugi/%s/%s/">'
                '<span>%s</span><b>%s</b></a>'
                % (base, d['slug'], s['slug'], s['title'], s['price_full']))
        menu.append('        </div>')
    menu = '\n'.join(menu)

    body = '''<section class="section section--tight subpage">
  <div class="container">
%(crumbs)s

    <div class="svcp">
      <figure class="svcp__pic reveal">
        <img src="%(base)sassets/img/gift-certificate.webp" width="524" height="700"
             fetchpriority="high" decoding="async"
             alt="Подарочный сертификат массажного салона Cuerpo в Тольятти">
      </figure>

      <div class="reveal">
        <h1>Подарочный сертификат</h1>
        <p class="pagehead__lead">Сумма на ваш выбор или конкретная программа.
        Действует 3 месяца.</p>

        <!-- ============================================================
             БЛОК ПОКУПКИ
             Считает итог и собирает заказ. Куда ведёт кнопка «Оформить» —
             задаётся в CONFIG.cert в assets/app.js: пока мессенджер,
             появится онлайн-касса — там же меняется на ссылку оплаты.
             ============================================================ -->
        <form class="buy" id="buy" novalidate>
          <fieldset class="buy__f">
            <legend class="buy__lg">Что дарим</legend>
            <div class="seg" role="group">
              <button type="button" class="seg__b is-on" data-what="sum">Сумму</button>
              <button type="button" class="seg__b" data-what="svc">Программу</button>
            </div>
          </fieldset>

          <div class="buy__f" data-pane="sum">
            <label class="buy__lg" for="buySum">Сумма подарка</label>
            <div class="buy__sum">
              <input class="buy__inp" id="buySum" type="text" inputmode="numeric"
                     autocomplete="off" value="5 000" aria-label="Сумма сертификата в рублях">
              <span class="buy__cur">₽</span>
            </div>
            <div class="buy__hints">
%(hints)s
            </div>
          </div>

          <div class="buy__f" data-pane="svc" hidden>
            <label class="buy__lg" for="buySvc">Программа</label>
            <select class="buy__sel" id="buySvc">
%(opts)s
            </select>
          </div>

          <fieldset class="buy__f">
            <legend class="buy__lg">Сертификат</legend>
            <div class="seg" role="group">
              <button type="button" class="seg__b is-on" data-kind="Электронный">Электронный</button>
              <button type="button" class="seg__b" data-kind="Бумажный">Бумажный</button>
            </div>
            <p class="buy__hintline" id="buyKindNote">Пришлём на почту письмом</p>

            <div class="buy__prev">
              <canvas id="buyCert" class="buy__prevc" width="1600" height="1000"
                      aria-label="Так выглядит электронный подарочный сертификат Cuerpo"></canvas>
              <img class="buy__prevp" id="buyPaper" hidden loading="lazy" decoding="async"
                   src="%(base)sassets/img/gift-certificate.webp" width="524" height="700"
                   alt="Бумажный подарочный сертификат Cuerpo в фирменном конверте">
              <p class="buy__prevnote" id="buyPrevNote">Так выглядит сертификат — сумма и программа подставятся ваши</p>
            </div>
          </fieldset>

          <div class="buy__total">
            <span>Итого</span>
            <b id="buyTotal">5 000 ₽</b>
          </div>

          <button type="button" class="btn btn--primary btn--full buy__go" id="buyGo">Оформить</button>

          <!-- ============================================================
               КУДА ОТПРАВИТЬ ЗАКАЗ
               Появляется по нажатию «Оформить». До этого человек ещё не
               выбрал сумму, и три кнопки внизу только мешают выбирать.
               Текст заказа к этому моменту уже собран и скопирован —
               в мессенджере остаётся вставить его одним нажатием.
               Способы задаются в CONFIG.cert в assets/app.js: чего там
               нет, того нет и на странице.
               ============================================================ -->
          <div class="send" id="buySend" hidden>
            <p class="send__lg">Ваш заказ</p>
            <p class="send__order" id="buyOrder"></p>
            <p class="send__hint">Отправьте его удобным способом — текст уже набран.
            Администратор ответит и пришлёт реквизиты для оплаты.</p>

            <div class="send__ways">
              <a class="send__w" id="sendWA" target="_blank" rel="noopener" hidden>
                <b>Написать в WhatsApp</b><span>текст уже в сообщении</span>
              </a>
              <a class="send__w" id="sendTG" target="_blank" rel="noopener" hidden>
                <b>Написать в Telegram</b><span id="sendTGnote">текст скопирован — вставьте в чат</span>
              </a>
              <a class="send__w" id="sendMAX" target="_blank" rel="noopener" hidden>
                <b>Написать в MAX</b><span>текст скопирован — вставьте в чат</span>
              </a>
              <a class="send__w send__w--tel" id="sendTel">
                <b>Позвонить</b><span>+7 (927) 892-30-13, ежедневно 09:00–21:00</span>
              </a>
            </div>

            <p class="buy__copied" id="buyCopied" hidden></p>
          </div>

          <ol class="buy__steps">
            <li><b>Выбираете подарок.</b> Сумму или программу, электронный или бумажный — справа сразу видно, как он будет выглядеть.</li>
            <li><b>Отправляете заказ.</b> Нажимаете «Оформить» и выбираете, куда написать: текст заказа уже набран, набирать ничего не нужно.</li>
            <li><b>Сертификат у вас.</b> Мы присылаем реквизиты, после оплаты — сертификат письмом на почту и в переписку. Бумажный в конверте забираете в салоне.</li>
          </ol>
          <p class="buy__small">Отвечаем в рабочее время, ежедневно 09:00–21:00</p>
        </form>
      </div>
    </div>
  </div>

  <!-- Общая отрисовка сертификата: тот же файл рисует предпросмотр здесь
       и готовый файл в служебном генераторе. Обычный тег без defer —
       так он выполнится раньше отложенного app.js, которому нужен. -->
  <script src="%(base)sassets/cert.js"></script>
</section>

<section class="section section--sand">
  <div class="container">
    <div class="head reveal">
      <p class="eyebrow">Сертификат на программу</p>
      <h2 class="h2">Что можно подарить</h2>
    </div>

    <div class="gmenu reveal">
%(menu)s
    </div>
  </div>
</section>
''' % {
        'crumbs': crumbs([('Главная', base), ('Подарочный сертификат', None)]),
        'base': base, 'hints': hints, 'opts': opts, 'menu': menu,
    }
    ld = '''<script type="application/ld+json">
{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
{"@type":"ListItem","position":1,"name":"Главная","item":"%s"},
{"@type":"ListItem","position":2,"name":"Подарочный сертификат","item":"%s%s"}]}
</script>''' % (SITE, SITE, url)
    return write(url + 'index.html', page(
        base, url,
        'Подарочный сертификат на массаж в Тольятти | Cuerpo',
        'Подарочный сертификат массажного салона Cuerpo в Тольятти: на любую сумму или на конкретную программу, электронный на почту или бумажный в конверте, срок действия 3 месяца. Приморский бульвар 57, +7 (927) 892-30-13.',
        body, ld))


# ------------------------------------------------- блок услуг на главной странице

# Лента «С этого чаще всего начинают» на главной. Порядок здесь = порядок на
# сайте. Список прислан салоном (август 2026) — это то, с чего к ним реально
# приходят впервые, а не наша догадка. Меняем только по слову салона.
# Последним стоит «Двойной Испанский» — самая дорогая программа каталога.
# В списке салона его нет: он добавлен намеренно, чтобы лента заканчивалась
# крупным предложением, а не самой дешёвой строкой прайса.
POPULAR = [
    'Классический массаж спины', 'Авторский массаж спины или ног',
    'SPA-массаж всего тела', 'Испанский массаж всего тела',
    'Массаж лица и головы', 'SPA-программа «Удовольствие»',
    'SPA для двоих «Двойной Испанский»',
]

TILE = '''      <a class="cat" href="uslugi/%(slug)s/">
        <img class="cat__img" src="%(img)s" width="%(w)d" height="%(h)d" loading="lazy" decoding="async"%(pos)s alt="%(alt)s">
        <span class="cat__body">
          <span class="cat__ttl">%(ttl)s</span>
          <span class="cat__sub">%(sub)s</span>
          <span class="cat__meta">%(meta)s</span>
        </span>
      </a>'''

# Направление с 'wide':True занимает всю ширину сетки. Нужно, когда плиток
# нечётное число: седьмая квадратная оставила бы полряда пустым.
WIDE_TILE = TILE.replace('class="cat"', 'class="cat cat--wide"')


# Сертификат стоит последним и занимает всю ширину сетки: это не седьмое
# направление, а отдельное предложение — широкая плашка отделяет его от
# каталога и не оставляет висеть половину ряда пустой.
# Сертификат не плитка каталога, а отдельное предложение, поэтому у него своя
# вёрстка: сплошная тёмно-зелёная заливка вместо фотографии, крупная типографика
# и медленный блик по поверхности. Фотография тут проигрывала — сертификат
# теряется среди снимков массажа, а дарят его часто те, кто сам на массаж
# не собирается и каталог не листает.
GIFT_TILE = '''      <a class="giftban" href="sertifikaty/">
        <span class="giftban__sheen" aria-hidden="true"></span>
        <span class="giftban__in">
          <span class="giftban__eyebrow">Подарок, который ждут</span>
          <span class="giftban__ttl">Подарочный<br>сертификат</span>
          <span class="giftban__sub">На любую услугу мастерской или на свою сумму.<br>В фирменном конверте — или письмом на почту.</span>
          <span class="giftban__row">
            <span class="giftban__btn">Выбрать сертификат %s</span>
            <span class="giftban__meta">любая сумма или программа · действует 3 месяца</span>
          </span>
        </span>
      </a>''' % ARROW

HOME_TPL = '''    <div class="head head--center reveal">
      <p class="eyebrow eyebrow--center">Услуги и цены</p>
      <h2 class="h2">Каталог массажа и SPA<br>в мастерской Cuerpo</h2>
      <p class="lead">Выберите направление — внутри цены, длительность и что входит в сеанс.</p>
    </div>

    <div class="cats reveal">
%(tiles)s
    </div>

    <div class="head reveal" style="margin-top:clamp(34px,5vw,60px)">
      <p class="eyebrow">Популярные услуги</p>
      <h2 class="h2">С этого чаще всего начинают</h2>
    </div>

    <div class="rail-s reveal">
      <div class="rail-s__track">
%(rail)s
      </div>
    </div>
'''


def build_home_section():
    """Содержимое блока услуг на главной — между метками BUILD:services."""
    tiles = []
    for d in DIRS:
        img, w, h = IMG[d['img']]
        tpl = WIDE_TILE if d.get('wide') else TILE
        # tile_pos — какая часть снимка остаётся видна в плашке. Широкая плашка
        # режет фотографию узкой полосой, и центр кадра почти никогда не там,
        # где главное. Не задан — работает значение по умолчанию из стилей.
        pos = ' style="object-position:%s"' % d['tile_pos'] if d.get('tile_pos') else ''
        tiles.append(tpl % {'slug': d['slug'], 'img': img, 'w': w, 'h': h,
                            'alt': esc_attr(d['tile_alt']), 'ttl': d['tile_ttl'],
                            'sub': d['sub'], 'meta': d['tile_meta'], 'pos': pos})
    tiles.append(GIFT_TILE)

    by_name = dict((x['name'], x) for (o, x) in ALL)
    rail = '\n'.join(card(by_name[n], svc_url(n, ''), '')
                     for n in POPULAR if n in by_name)

    return HOME_TPL % {'tiles': '\n'.join(tiles), 'rail': rail}


SOCIALS = [
    'https://vk.ru/cuerpo_massage',
    'https://t.me/cuerpo_massage',
    'https://max.ru/join/cS6n7juwoTfDZ0bwwvBSRJ9FdDHrQW_8NSufPw8zTFs',
    'https://yandex.ru/maps/org/cuerpo/8688668194/',
    'https://n908364.yclients.com/',
]


def build_home_ld():
    """Микроразметка организации для главной.

    Каталог услуг собирается из tools/data.py, поэтому цены в разметке не
    расходятся с ценами на страницах. Адрес и часы работы намеренно не
    выводятся: подтверждённых данных от салона пока нет.
    """
    offers = []
    for _, x in ALL:
        m = re.search(r'(\d[\d\s\u00a0]*)\s*\u20bd', x['price_full'])
        price = (',"price":"%s","priceCurrency":"RUB"' % re.sub(r'\s|\u00a0', '', m.group(1))) if m else ''
        offers.append('      {"@type":"Offer","itemOffered":{"@type":"Service","name":"%s"}%s}'
                      % (esc_attr(x['name']), price))

    return '''<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": ["LocalBusiness", "HealthAndBeautyBusiness", "DaySpa"],
  "name": "Cuerpo — мастерская по телу",
  "alternateName": "Массажный салон Cuerpo Тольятти",
  "description": "Массажный салон и мастерская по телу Cuerpo в Тольятти: авторский оздоровительный массаж, коррекция фигуры, массаж лица, SPA-программы для двоих, кедровая бочка и сауна с гималайской солью.",
  "slogan": "Станем скульпторами твоего тела",
  "url": "%(site)s",
  "image": "%(site)sassets/img/og-cover.jpg",
  "telephone": "+7-927-892-30-13",
  "priceRange": "900–6500 ₽",
  "currenciesAccepted": "RUB",
  "areaServed": "Тольятти",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "5.0",
    "bestRating": "5",
    "ratingCount": "180",
    "reviewCount": "159"
  },
  "sameAs": [
%(social)s
  ],
  "hasOfferCatalog": {
    "@type": "OfferCatalog",
    "name": "Услуги массажного салона Cuerpo",
    "itemListElement": [
%(offers)s
    ]
  }
}
</script>''' % {
        'site': SITE,
        'social': ',\n'.join('    "%s"' % u for u in SOCIALS),
        'offers': ',\n'.join(offers),
    }


# ------------------------------------------------------------------ страница 404


def build_policy_page():
    """Политика обработки персональных данных.

    Нужна, потому что на сайте работает Яндекс.Метрика: форм с телефоном на
    сайте нет, но cookie, IP и идентификаторы устройства российская практика
    относит к персональным данным, а часть 2 статьи 18.1 закона 152-ФЗ
    обязывает оператора опубликовать политику в свободном доступе.

    Текст намеренно написан сухим юридическим языком и по той же структуре,
    которую ждёт Роскомнадзор при проверке: оператор, состав данных, цели,
    основания, порядок и сроки, передача, права субъекта, безопасность.
    Объяснялку «по-человечески» отсюда убрали — она ослабляла документ.
    """
    body = '''<section class="section section--tight subpage">
  <div class="container container--narrow">
    <p class="eyebrow">Документ</p>
    <h1>Политика обработки персональных данных</h1>

    <div class="legal">
      <h2>1. Общие положения</h2>
      <p>1.1. Настоящая Политика обработки персональных данных (далее — Политика)
      разработана во исполнение требований пункта 2 части 1 статьи 18.1
      Федерального закона от 27.07.2006 № 152-ФЗ «О персональных данных»
      (далее — Закон № 152-ФЗ) и определяет порядок обработки персональных данных
      и меры по обеспечению их безопасности, реализуемые Оператором.</p>
      <p>1.2. Политика распространяется на все персональные данные субъектов,
      обрабатываемые Оператором в связи с функционированием сайта
      <a href="https://cuerpomassage.ru/">cuerpomassage.ru</a> (далее — Сайт),
      с использованием средств автоматизации и без использования таких средств.</p>
      <p>1.3. Политика является общедоступным документом и подлежит размещению
      в сети «Интернет» по адресу <a href="https://cuerpomassage.ru/politika/">cuerpomassage.ru/politika/</a>.</p>
      <p>1.4. Термины, используемые в Политике, применяются в значениях,
      определённых статьёй 3 Закона № 152-ФЗ.</p>

      <h2>2. Сведения об Операторе</h2>
      <p>2.1. Оператором персональных данных является индивидуальный предприниматель
      Фролова Марина Сергеевна, ОГРНИП 324632700128861, ИНН 632147346695,
      адрес осуществления деятельности: Самарская область, г. Тольятти,
      Приморский бульвар, д. 57 (далее — Оператор).</p>
      <p>2.2. Контактные данные для направления обращений, предусмотренных
      разделом 8 Политики: телефон <a href="tel:+79278923013">+7 (927) 892-30-13</a>,
      почтовый адрес — указанный в пункте 2.1 настоящей Политики.</p>

      <h2>3. Категории субъектов и состав обрабатываемых персональных данных</h2>
      <p>3.1. Оператор обрабатывает персональные данные пользователей Сайта —
      физических лиц, осуществляющих доступ к Сайту.</p>
      <p>3.2. Сайт не содержит форм сбора персональных данных: ввод фамилии, имени,
      номера телефона, адреса электронной почты и иных сведений на Сайте
      не предусмотрен.</p>
      <p>3.3. В связи с использованием на Сайте сервиса статистики «Яндекс Метрика»
      обработке подлежат следующие данные, получаемые автоматически:</p>
      <ul>
        <li>IP-адрес устройства пользователя;</li>
        <li>данные файлов cookie;</li>
        <li>сведения о браузере, операционной системе и типе устройства;</li>
        <li>сведения о страницах Сайта, к которым осуществлялся доступ, времени
        доступа и совершённых на страницах действиях (переходы, нажатия, прокрутка);</li>
        <li>адрес страницы-источника перехода на Сайт (реферер).</li>
      </ul>
      <p>3.4. Специальные категории персональных данных и биометрические
      персональные данные Оператором не обрабатываются.</p>

      <h2>4. Цели обработки персональных данных</h2>
      <p>4.1. Обработка данных, указанных в пункте 3.3 Политики, осуществляется
      исключительно в целях сбора обезличенной статистики посещаемости Сайта,
      анализа пользовательской активности и улучшения структуры и содержания
      Сайта.</p>
      <p>4.2. Обработка персональных данных в целях продвижения товаров, работ и
      услуг на рынке путём осуществления прямых контактов с пользователем
      Сайта не производится. Принятие решений, порождающих юридические
      последствия, исключительно на основании автоматизированной обработки
      персональных данных не осуществляется.</p>

      <h2>5. Правовые основания обработки персональных данных</h2>
      <p>5.1. Правовым основанием обработки является согласие субъекта
      персональных данных на обработку его персональных данных (пункт 1 части 1
      статьи 6 Закона № 152-ФЗ), а также осуществление Оператором прав и законных
      интересов, не нарушающее права и свободы субъекта персональных данных
      (пункт 7 части 1 статьи 6 Закона № 152-ФЗ).</p>
      <p>5.2. Согласие на обработку данных, получаемых при помощи файлов cookie и
      сервиса статистики, предоставляется субъектом путём совершения конклюдентных
      действий — продолжения использования Сайта после ознакомления с
      уведомлением, размещённым в нижней части каждой страницы Сайта, содержащим
      ссылку на настоящую Политику.</p>
      <p>5.3. Субъект персональных данных вправе не предоставлять такое согласие
      либо отозвать его в порядке, предусмотренном разделом 9 Политики.
      Функциональность Сайта при этом не ограничивается.</p>

      <h2>6. Порядок и условия обработки персональных данных</h2>
      <p>6.1. Обработка персональных данных включает сбор, запись, систематизацию,
      накопление, хранение, уточнение (обновление, изменение), извлечение,
      использование, обезличивание, блокирование, удаление и уничтожение.</p>
      <p>6.2. Обработка осуществляется с использованием средств автоматизации.
      Сбор, запись, систематизация, накопление, хранение, уточнение и извлечение
      персональных данных граждан Российской Федерации осуществляются
      с использованием баз данных, находящихся на территории Российской Федерации,
      в соответствии с частью 5 статьи 18 Закона № 152-ФЗ.</p>
      <p>6.3. Оператор не осуществляет трансграничную передачу персональных данных.</p>

      <h2>7. Передача персональных данных третьим лицам</h2>
      <p>7.1. Обработка данных, указанных в пункте 3.3 Политики, осуществляется
      ООО «ЯНДЕКС» (ОГРН 1027700229193, 119021, г. Москва, ул. Льва Толстого, д. 16)
      по поручению Оператора на условиях Пользовательского соглашения сервиса
      «Яндекс Метрика». Указанное лицо обязано соблюдать принципы и правила
      обработки персональных данных, предусмотренные Законом № 152-ФЗ.</p>
      <p>7.2. Иным третьим лицам персональные данные пользователей Сайта
      не передаются, за исключением случаев, предусмотренных законодательством
      Российской Федерации.</p>
      <p>7.3. Персональные данные пользователей Сайта не подлежат распространению
      и не используются в целях, не предусмотренных разделом 4 Политики.</p>
      <p>7.4. Сайт содержит ссылки на сторонние ресурсы: систему онлайн-записи
      YCLIENTS, мессенджеры, картографические сервисы, социальные сети. Обработка
      персональных данных при переходе по таким ссылкам осуществляется владельцами
      соответствующих ресурсов и регулируется их политиками. Оператор не несёт
      ответственности за обработку персональных данных третьими лицами.</p>

      <h2>8. Сроки обработки и хранения персональных данных</h2>
      <p>8.1. Персональные данные обрабатываются в течение срока, необходимого для
      достижения целей, указанных в разделе 4 Политики, но не дольше срока
      хранения данных в сервисе «Яндекс Метрика», установленного его правилами.</p>
      <p>8.2. Файлы cookie хранятся на устройстве пользователя в течение
      установленного для них срока либо до момента их удаления пользователем.</p>
      <p>8.3. По достижении целей обработки, а также в случае отзыва согласия
      персональные данные подлежат уничтожению или обезличиванию в сроки,
      установленные статьёй 21 Закона № 152-ФЗ.</p>

      <h2>9. Права субъекта персональных данных</h2>
      <p>9.1. Субъект персональных данных имеет право на получение сведений,
      предусмотренных частью 7 статьи 14 Закона № 152-ФЗ, в том числе на получение
      информации о наличии у Оператора персональных данных, относящихся к
      соответствующему субъекту.</p>
      <p>9.2. Субъект персональных данных вправе требовать уточнения своих
      персональных данных, их блокирования или уничтожения в случае, если
      персональные данные являются неполными, устаревшими, неточными, незаконно
      полученными или не являются необходимыми для заявленной цели обработки,
      а также принимать предусмотренные законом меры по защите своих прав.</p>
      <p>9.3. Запрос направляется Оператору по контактным данным, указанным в
      пункте 2.2 Политики, и должен содержать сведения, предусмотренные частью 3
      статьи 14 Закона № 152-ФЗ. Ответ предоставляется в срок, не превышающий
      десяти рабочих дней с даты получения запроса.</p>
      <p>9.4. Согласие на обработку персональных данных может быть отозвано
      субъектом персональных данных. Отзыв согласия осуществляется одним из
      следующих способов:</p>
      <ul>
        <li>отключение файлов cookie в настройках браузера либо использование
        режима просмотра, не сохраняющего данные;</li>
        <li>установка официального дополнения для браузера «Блокировщик Яндекс
        Метрики»;</li>
        <li>направление Оператору обращения по контактным данным, указанным
        в пункте 2.2 Политики.</li>
      </ul>
      <p>9.5. Субъект персональных данных вправе обжаловать действия или
      бездействие Оператора в уполномоченный орган по защите прав субъектов
      персональных данных (Роскомнадзор) или в судебном порядке.</p>

      <h2>10. Меры по обеспечению безопасности персональных данных</h2>
      <p>10.1. Оператор принимает необходимые правовые, организационные и
      технические меры для защиты персональных данных от неправомерного или
      случайного доступа, уничтожения, изменения, блокирования, копирования,
      предоставления и распространения, а также от иных неправомерных действий,
      в том числе: назначает лицо, ответственное за организацию обработки
      персональных данных; осуществляет внутренний контроль соответствия обработки
      требованиям Закона № 152-ФЗ; ограничивает доступ к данным статистики
      средствами аутентификации.</p>
      <p>10.2. Собственных информационных систем персональных данных Оператор
      в связи с функционированием Сайта не ведёт: статистические данные
      обрабатываются на стороне лица, указанного в пункте 7.1 Политики.</p>

      <h2>11. Заключительные положения</h2>
      <p>11.1. Политика вступает в силу с момента её размещения на Сайте и
      действует бессрочно до замены её новой редакцией.</p>
      <p>11.2. Оператор вправе вносить изменения в Политику. Действующая редакция
      размещается по адресу, указанному в пункте 1.3 Политики.</p>
      <p>11.3. Вопросы, не урегулированные Политикой, разрешаются в соответствии
      с законодательством Российской Федерации.</p>

      <p class="legal__date">Редакция от 30 сентября 2026 года.</p>
    </div>
  </div>
</section>
'''

    return write('politika/index.html',
                 page('../', 'politika/',
                      'Политика обработки персональных данных — Cuerpo, Тольятти',
                      'Политика обработки персональных данных массажного салона Cuerpo в Тольятти: оператор, состав и цели обработки данных пользователей сайта, правовые основания, сроки, права субъекта персональных данных.',
                      body))


def build_404():
    body = '''<section class="section section--tight subpage">
  <div class="container">
    <div class="e404">
      <p class="eyebrow eyebrow--center">Ошибка 404</p>
      <h1>Такой страницы нет</h1>
      <p class="pagehead__lead">Возможно, услугу переименовали или в адресе опечатка.
      Загляните в каталог — там все программы мастерской с ценами и длительностью,
      или вернитесь на главную.</p>
      <div class="e404__act">
        <a class="btn btn--primary" href="%(site)s">На главную</a>
        <a class="btn btn--ghost" href="%(site)s#services">Каталог услуг</a>
      </div>
      <p class="svcp__note e404__note">
        <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>
        Не нашли, что искали — подскажем по телефону
        <a href="tel:+79278923013">+7 (927) 892-30-13</a>.
      </p>
    </div>
  </div>
</section>

<section class="section section--sand">
  <div class="container">
    <div class="head head--center reveal">
      <p class="eyebrow eyebrow--center">Направления</p>
      <h2 class="h2">Начните отсюда</h2>
    </div>
    <div class="cats cats--mini reveal">
%(cats)s
    </div>
  </div>
</section>
''' % {'site': SITE, 'cats': '\n'.join(
        '''      <a class="cat" href="%suslugi/%s/">
        <img class="cat__img" src="%s%s" width="%d" height="%d" loading="lazy" decoding="async" alt="%s">
        <span class="cat__body">
          <span class="cat__ttl">%s</span>
          <span class="cat__meta">%s</span>
        </span>
      </a>''' % (SITE, d['slug'], SITE, IMG[d['img']][0], IMG[d['img']][1], IMG[d['img']][2],
                 esc_attr(d['tile_alt']), d['tile_ttl'], d['tile_meta'])
        for d in DIRS)}

    # Сервер отдаёт эту страницу по ЛЮБОМУ несуществующему адресу, в том числе
    # /uslugi/opechatka/. Относительные пути там указывали бы в никуда, поэтому
    # обвязка собирается с абсолютной базой.
    html = page(SITE, '404.html',
                'Страница не найдена — Cuerpo, массажный салон в Тольятти',
                'Такой страницы на сайте массажного салона Cuerpo нет. Вернитесь на главную или откройте каталог услуг: массаж, SPA-программы, коррекция фигуры.',
                body)
    # Страницу ошибки поисковикам индексировать не нужно — независимо от того,
    # что стоит в robots на главной. Заменяем тег целиком, а не конкретную
    # строку: иначе, открыв индексацию сайта, эту страницу тоже открыли бы.
    html = re.sub(r'<meta name="robots"[^>]*>',
                  '<meta name="robots" content="noindex, follow">', html, count=1)
    return write('404.html', html)


def patch_index():
    path = os.path.join(ROOT, 'index.html')
    html = io.open(path, encoding='utf-8').read()
    a = html.index('<!-- BUILD:services -->') + len('<!-- BUILD:services -->')
    b = html.index('<!-- /BUILD:services -->')
    html = html[:a] + '\n' + build_home_section() + '    ' + html[b:]

    a = html.index('<!-- BUILD:ld -->') + len('<!-- BUILD:ld -->')
    b = html.index('<!-- /BUILD:ld -->')
    html = html[:a] + '\n' + build_home_ld() + '\n' + html[b:]

    io.open(path, 'w', encoding='utf-8').write(html)
    return 'index.html (блок услуг и микроразметка)'


# --------------------------------------------------- ссылки, работающие без сервера

# Ссылка на папку (uslugi/massazh-lica/) раскрывается в index.html только там,
# где есть веб-сервер. Если открыть сайт двойным кликом по файлу — протокол
# file:// подставлять index.html не умеет, и переход просто не происходит.
# Поэтому в <a> дописываем index.html явно: так работает и локально, и на
# GitHub Pages. Адреса в canonical, og:url и sitemap.xml при этом остаются
# короткими — их правило не трогает, потому что они не в теге <a>.
# Ловим и «uslugi/spa-programmy/», и «../../#reviews» — второе с подстраниц
# ведёт на якорь главной и без index.html тоже никуда не открывается.
LINK_RE = re.compile(r'(<a\b[^>]*?\shref=")([^":]*?/)(#[^"]*)?(")')


def explicit_index(html):
    def repl(m):
        return m.group(1) + m.group(2) + 'index.html' + (m.group(3) or '') + m.group(4)
    return LINK_RE.sub(repl, html)


def fix_links_everywhere():
    """Дописывает index.html в ссылках на всех собранных страницах."""
    touched = 0
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in ('.git', '_drafts', '_upload', 'tools', '.claude')]
        for fn in files:
            if not fn.endswith('.html'):
                continue
            p = os.path.join(base, fn)
            html = io.open(p, encoding='utf-8').read()
            fixed = explicit_index(html)
            if fixed != html:
                io.open(p, 'w', encoding='utf-8').write(fixed)
                touched += 1
    return 'ссылки → index.html (%d файлов)' % touched


# ------------------------------------------------- отметка версии у стилей и скриптов

# Браузер держит style.css и app.js в кэше и после выкладки какое-то время
# показывает старые. Человек открывает сайт и не видит правку — а она уже
# там. Поэтому к адресу каждого файла дописываем отпечаток его содержимого:
# поменялся файл — поменялся адрес — браузер обязан скачать заново.
# Не поменялся — адрес прежний, и кэш работает как работал.
ASSETS_RE = re.compile(r'(assets/(?:style\.css|app\.js|cert\.js))(\?v=[0-9a-f]+)?')


def stamp_assets():
    """Дописывает ?v=отпечаток к стилям и скриптам на всех страницах."""
    marks = {}
    for name in ('assets/style.css', 'assets/app.js', 'assets/cert.js'):
        data = io.open(os.path.join(ROOT, name), 'rb').read()
        marks[name] = hashlib.md5(data).hexdigest()[:8]

    def repl(m):
        return m.group(1) + '?v=' + marks[m.group(1)]

    touched = 0
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in ('.git', '_drafts', '_upload', 'tools', '.claude')]
        for fn in files:
            if not fn.endswith('.html'):
                continue
            path = os.path.join(base, fn)
            html = io.open(path, encoding='utf-8').read()
            fixed = ASSETS_RE.sub(repl, html)
            if fixed != html:
                io.open(path, 'w', encoding='utf-8').write(fixed)
                touched += 1
    return 'отметка версии у стилей и скриптов (%d файлов)' % touched


# ----------------------------------------------------------------------- сборка

def main():
    made = []
    for d in DIRS:
        made.append(build_dir_page(d))
    for d, s in ALL:
        made.append(build_svc_page(d, s))
    made.append(build_gift_page())
    made.append(build_policy_page())
    made.append(build_404())
    made.append(patch_index())
    made.append(fix_links_everywhere())
    made.append(stamp_assets())

    urls = [''] + ['uslugi/%s/' % d['slug'] for d in DIRS] \
                + ['uslugi/%s/%s/' % (HOME[s['name']][0], s['slug']) for _, s in ALL] \
                + ['sertifikaty/', 'politika/']
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemap.org/schemas/sitemap/0.9">'.replace('sitemap.org', 'sitemaps.org')]
    for u in urls:
        pri = '1.0' if u == '' else ('0.8' if u.count('/') <= 2 else '0.6')
        sm.append('  <url><loc>%s%s</loc><priority>%s</priority></url>' % (SITE, u, pri))
    sm.append('</urlset>')
    made.append(write('sitemap.xml', '\n'.join(sm) + '\n'))

    print('Собрано страниц: %d' % len(made))
    for p in made:
        print('  ' + p)


if __name__ == '__main__':
    main()
