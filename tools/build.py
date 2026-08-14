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

import io
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://leragodzen.github.io/cuerpo-demo/'

exec(io.open(os.path.join(ROOT, 'tools', 'data.py'), encoding='utf-8').read())

INDEX = io.open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()


# ------------------------------------------------------------------ утилиты

def between(text, start_marker, end_marker, keep_end=True):
    a = text.index(start_marker)
    b = text.index(end_marker, a) + (len(end_marker) if keep_end else 0)
    return text[a:b]


ROOT_DIRS = ('assets/', 'uslugi/', 'sertifikaty/')


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


def card(s, href, base, main=False):
    """Карточка услуги для страницы направления и для лент."""
    img, w, h = IMG[s['img']]
    L = ['<article class="card-s reveal">']
    L.append('  <a class="card-s__open" href="%s">' % href)
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

    <div class="cards">
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
      <figure class="svcp__pic reveal">
        <img src="%(base)s%(img)s" width="%(w)d" height="%(h)d"
             fetchpriority="high" decoding="async" alt="%(alt)s">
      </figure>

      <div class="reveal">
        <h1>%(title)s</h1>
        <p class="pagehead__lead">%(lead)s</p>
%(tags)s
%(prices)s

        <div class="svcp__act">
%(dur)s
          <a class="btn btn--primary btn--full" data-book data-service="%(name)s">Записаться</a>
        </div>

        <p class="svcp__note">
          <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>
          Точную стоимость и свободное время подскажет администратор. Звоните
          <a href="tel:+79278923013">+7 (927) 892-30-13</a> — ежедневно с 09:00 до 21:00.
        </p>
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
        'base': base, 'img': img, 'w': w, 'h': h, 'alt': esc_attr(s['alt']),
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

def build_gift_page():
    base = '../'
    url = 'sertifikaty/'
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
        <p class="pagehead__lead">Самый простой способ подарить близкому человеку время на себя.
        Сертификат оформляется на конкретную программу или на сумму — получатель сам выберет,
        что ему нужнее, и придёт тогда, когда будет удобно.</p>

        <div class="prices">
          <div class="prices__r"><b>от 1 200 ₽</b><span>на любую услугу из каталога</span></div>
          <div class="prices__r prices__r--base"><b>6 месяцев</b><span>срок действия</span></div>
        </div>

        <div class="svcp__act">
          <a class="btn btn--primary btn--full" data-book data-service="Подарочный сертификат">Заказать сертификат</a>
        </div>

        <p class="svcp__note">
          <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>
          Оформляем в салоне или по телефону <a href="tel:+79278923013">+7 (927) 892-30-13</a>.
          Выдаём в подарочном конверте — забрать можно в день обращения.
        </p>
      </div>
    </div>
  </div>
</section>

<section class="section section--sand">
  <div class="container">
    <div class="ba__grid" style="display:grid; gap:clamp(26px,4vw,52px)">
      <div class="reveal">
        <h2 class="h3">Что вас ждёт</h2>
        <ul class="svc-full__eff">
          <li><span class="ic"><svg viewBox="0 0 24 24">%(heart)s</svg></span>Подарок, который точно пригодится</li>
          <li><span class="ic"><svg viewBox="0 0 24 24">%(star)s</svg></span>Получатель сам выбирает программу и время</li>
          <li><span class="ic"><svg viewBox="0 0 24 24">%(clock)s</svg></span>Полгода на то, чтобы воспользоваться</li>
        </ul>
      </div>
      <div class="reveal">
        <h2 class="h3">Как оформить</h2>
        <ul class="svc-full__inc">
          <li>Позвоните или напишите — подскажем, что выбрать под повод и бюджет</li>
          <li>Назовите номинал или конкретную программу</li>
          <li>Заберите сертификат в салоне на Приморском бульваре, 57</li>
          <li>Вручите — активировать заранее не нужно</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="section section--tight">
  <div class="container">
    <div class="head reveal">
      <p class="eyebrow">Что подарить</p>
      <h2 class="h2">Программы, которые чаще всего<br>берут в подарок</h2>
    </div>
    <div class="rail-s reveal">
      <div class="rail-s__track">
%(rail)s
      </div>
    </div>
  </div>
</section>
''' % {
        'crumbs': crumbs([('Главная', base), ('Подарочный сертификат', None)]),
        'base': base, 'heart': IC['heart'], 'star': IC['star'], 'clock': IC['clock'],
        'rail': '\n'.join(card(x, svc_url(x['name'], base), base)
                          for _, x in ALL if x['name'] in (
                              'SPA-программа «Десерт для души»', 'SPA-программа для двоих',
                              'SPA-программа «Relax»', 'SPA-программа «Удовольствие»',
                              'Кедровая бочка', 'Массаж горячими камнями')),
    }
    ld = '''<script type="application/ld+json">
{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
{"@type":"ListItem","position":1,"name":"Главная","item":"%s"},
{"@type":"ListItem","position":2,"name":"Подарочный сертификат","item":"%s%s"}]}
</script>''' % (SITE, SITE, url)
    return write(url + 'index.html', page(
        base, url,
        'Подарочный сертификат на массаж в Тольятти | Cuerpo',
        'Подарочный сертификат массажного салона Cuerpo в Тольятти: на любую услугу от 1 200 ₽, срок действия 6 месяцев, подарочный конверт. Приморский бульвар 57, +7 (927) 892-30-13.',
        body, ld))


# ------------------------------------------------- блок услуг на главной странице

POPULAR = [
    'Классический массаж спины', 'Французская талия', 'Буккальный массаж лица',
    'SPA-программа «Десерт для души»', 'SPA-программа для двоих', 'Кедровая бочка',
    'SPA-программа «Relax»', 'Массаж для беременных',
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
GIFT_TILE = '''      <a class="cat cat--wide" href="sertifikaty/">
        <img class="cat__img" src="assets/img/gift-certificate.webp" width="524" height="700" loading="lazy" decoding="async"
             alt="Подарочный сертификат массажного салона Cuerpo в Тольятти">
        <span class="cat__body">
          <span class="cat__ttl">Подарочный сертификат</span>
          <span class="cat__sub">на любую услугу или сумму · в подарочном конверте</span>
          <span class="cat__meta">от 1 200 ₽ · оформить онлайн или в салоне</span>
        </span>
      </a>'''

HOME_TPL = '''    <div class="head head--center reveal">
      <p class="eyebrow eyebrow--center">Услуги и цены</p>
      <h2 class="h2">Каталог массажа и SPA<br>в мастерской Cuerpo</h2>
      <p class="lead">Выберите направление — внутри цены, длительность и запись в один клик.</p>
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
    'https://t.me/+79278923013',
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
    "reviewCount": "150"
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


# ----------------------------------------------------------------------- сборка

def main():
    made = []
    for d in DIRS:
        made.append(build_dir_page(d))
    for d, s in ALL:
        made.append(build_svc_page(d, s))
    made.append(build_gift_page())
    made.append(build_404())
    made.append(patch_index())
    made.append(fix_links_everywhere())

    urls = [''] + ['uslugi/%s/' % d['slug'] for d in DIRS] \
                + ['uslugi/%s/%s/' % (HOME[s['name']][0], s['slug']) for _, s in ALL] \
                + ['sertifikaty/']
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
