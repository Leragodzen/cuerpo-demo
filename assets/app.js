/* ============================================================
   CUERPO — скрипты сайта
   ------------------------------------------------------------
   НАСТРОЙКА ПЕРЕД ПУБЛИКАЦИЕЙ — см. блок CONFIG ниже.
   ============================================================ */
(function(){
'use strict';

/* ---------- НАСТРОЙКИ ---------- */
var CONFIG = {
  /* ОНЛАЙН-ЗАПИСЬ — единственное место, где живёт ссылка на YClients.
     Все кнопки «Записаться» на сайте берут адрес отсюда: в разметке ссылка
     не продублирована ни разу, поэтому поменять её можно одной правкой. */
  booking: 'https://n908364.yclients.com/company/845911/personal/menu?o=',

  /* Персональные ссылки на конкретные услуги. Пока пусто — все кнопки ведут
     на общий каталог записи выше. Когда появятся прямые ссылки YClients,
     допишите строки сюда, ключ — имя услуги из tools/data.py (data-service):
        'Классический массаж спины': 'https://n908364.yclients.com/company/845911/personal/menu?o=s12345',
     Разметку править не нужно: скрипт подставит адрес сам. */
  bookingByService: {},

  /* То же самое для мастеров (кнопки «Записаться» в блоке команды),
     ключ — имя мастера из data-master. */
  bookingByMaster: {},

  /* Ссылка на карточку салона на Яндекс Картах (кнопки «Читать все отзывы»). */
  yandexUrl: 'https://yandex.ru/maps/org/cuerpo/8688668194/',

  /* Ссылка на карточку салона в 2ГИС (кнопки «Отзывы в 2ГИС»). */
  gisUrl: 'https://2gis.ru/togliatti/firm/3096753025849899',

  phone: '+7 (927) 892-30-13',
  phoneRaw: '+79278923013'
};

var $  = function(s, c){ return (c||document).querySelector(s); };
var $$ = function(s, c){ return Array.prototype.slice.call((c||document).querySelectorAll(s)); };

/* ---------- Онлайн-запись ----------
   Формы с телефоном на сайте нет: заявки принимает YClients, поэтому сайт
   не собирает персональные данные. Кнопкам «Записаться» адрес проставляется
   здесь — из CONFIG.booking и карт CONFIG.bookingByService / bookingByMaster.
   Так ссылка не размазана по разметке: чтобы завести отдельную ссылку на
   услугу или мастера, достаточно дописать строку в CONFIG.

   Блок стоит первым намеренно: запись — главное действие на сайте, и оно не
   должно зависеть от того, что случится ниже по файлу. Ошибка в карусели или
   в лайтбоксе не оставит кнопки «Записаться» без адреса. */
function bookingUrl(el){
  var svc = el.getAttribute('data-service');
  var mst = el.getAttribute('data-master');
  return (svc && CONFIG.bookingByService[svc])
      || (mst && CONFIG.bookingByMaster[mst])
      || CONFIG.booking;
}
$$('[data-book]').forEach(function(el){
  el.setAttribute('href', bookingUrl(el));
  el.setAttribute('target', '_blank');
  el.setAttribute('rel', 'noopener');
});

/* Мобильное меню поверх страницы осталось бы открытым, когда пользователь
   вернётся из YClients назад — закрываем его сразу. Цель Метрики open_yclients
   ставит общий обработчик ссылок выше, дублировать не нужно. */
document.addEventListener('click', function(e){
  if (e.target.closest && e.target.closest('[data-book]')) closeMenu();
});

/* Esc закрывает мобильное меню */
document.addEventListener('keydown', function(e){
  if (e.key === 'Escape' && document.body.classList.contains('menu-open')) closeMenu();
});

/* ---------- Цели Метрики ----------
   Молча ничего не делает, пока номер счётчика не вписан в <head>. */
function goal(name){
  try{
    if (window.CUERPO_METRIKA && typeof window.ym === 'function'){
      window.ym(window.CUERPO_METRIKA, 'reachGoal', name);
    }
  }catch(e){}
}

/* ---------- Год в подвале ---------- */
var y = $('#year'); if (y) y.textContent = new Date().getFullYear();

/* ---------- Звонки, мессенджеры и уход в онлайн-запись ---------- */
document.addEventListener('click', function(e){
  var a = e.target.closest && e.target.closest('a[href]');
  if (!a) return;
  var href = a.getAttribute('href') || '';
  if (href.indexOf('tel:') === 0) goal('call');
  else if (href.indexOf('yclients.com') > -1) goal('open_yclients');
  else if (/t\.me|vk\.me|vk\.com|vk\.ru|max\.ru/.test(href)) goal('messenger');
}, true);

/* ---------- Долистал до услуг ----------
   Следим не за всей секцией, а за лентой под плашками: секция теперь третья
   сверху, её верх видит почти каждый — такая цель ничего не мерила бы.
   Считаем по факту: блок поднялся выше 55 % экрана. */
(function(){
  var sec = $('.rail-s') || $('.cards');
  if (!sec || !('IntersectionObserver' in window)) return;
  var seen = new IntersectionObserver(function(entries){
    if (entries[0].isIntersecting){ goal('view_services'); seen.disconnect(); }
  }, {threshold: 0, rootMargin: '0px 0px -45% 0px'});
  seen.observe(sec);
})();

/* ---------- Ссылки на карты ---------- */
$$('[data-yandex]').forEach(function(a){ a.href = CONFIG.yandexUrl; });
$$('[data-2gis]').forEach(function(a){ a.href = CONFIG.gisUrl; });

/* ---------- Шапка ---------- */
var mbar = $('#mbar');
var heroPic = $('#heroPic');
var heroPins = $('#heroPins');
var heroDim  = $('#heroDim');
var heroStage = $('#heroStage');
var heroLogo  = $('.hero__logo');
/* Анимация появления с fill-mode перебивает inline-стили, поэтому снимаем её,
   как только логотип проявился — дальше им управляет прокрутка. Если
   animationend почему-то не придёт (вкладка была свёрнута/в фоне), подчищаем
   по таймеру — иначе логотип может застыть в промежуточном кадре анимации. */
if (heroLogo){
  var clearLogoAnim = function(){ heroLogo.style.animation = 'none'; };
  heroLogo.addEventListener('animationend', clearLogoAnim);
  setTimeout(clearLogoAnim, 2000);
}
var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* Порог появления нижней панели «Записаться»: на главной — когда первый экран
   уехал вверх примерно на три четверти, на внутренних страницах (там нет hero)
   — сразу после шапки. Высоту первого экрана считаем каждый раз заново:
   на мобильных она меняется, когда браузер сворачивает адресную строку. */
var hero = document.querySelector('.hero');
function mbarThreshold(){
  if (!hero) return 140;
  return Math.max(140, hero.offsetHeight * 0.75);
}

function onScroll(){
  var s = window.scrollY || document.documentElement.scrollTop;
  var mbarVisible = s > mbarThreshold();
  if (mbar) mbar.classList.toggle('is-visible', mbarVisible);
  /* Кнопка «Записаться» в шапке прячется на мобильном ровно тогда, когда
     появляется нижний плавающий бар — иначе на экране одновременно две
     одинаковые по смыслу кнопки. */
  document.body.classList.toggle('cta-in-mbar', mbarVisible);

  /* Снимок медленно уезжает вверх внутри неподвижной рамки, логотип и выноски —
     быстрее и с затуханием. Рамка стоит на месте, поэтому под первым экраном
     не открывается пустая полоса перед блоком с рейтингом. */
  if (heroPic && !reduceMotion){
    /* На самом верху страницы положение всегда нейтральное и не зависит от
       offsetHeight — на мобильных в момент первого рендера (пока адресная
       строка браузера ещё не свернулась) он может быть посчитан неточно,
       что даёт случайный сдвиг сцены/логотипа/выносок на первом кадре. */
    var k = 0;
    if (s > 0){
      var h = heroPic.offsetHeight || 1;
      k = Math.min(s / h, 1);
    }
    if (heroStage) heroStage.style.transform = k ? 'translate3d(0,' + (-k * 45) + 'px,0)' : 'none';
    if (heroDim) heroDim.style.opacity = String(k * 0.3);
    if (heroLogo){
      heroLogo.style.transform = k ? 'translate3d(0,' + (-k * 70) + 'px,0)' : 'none';
      heroLogo.style.opacity   = String(Math.max(0, 1 - k * 2));
    }
    if (heroPins){
      heroPins.style.transform = k ? 'translate3d(0,' + (-k * 130) + 'px,0)' : 'none';
      heroPins.style.opacity   = String(Math.max(0, 1 - k * 2.4));
    }
  }
}
window.addEventListener('scroll', onScroll, {passive:true});
/* Первый вызов откладываем на кадр вперёд — браузер успевает завершить
   первый layout, иначе offsetHeight ещё не окончательный. Высота вьюпорта на
   мобильных дополнительно меняется при сворачивании/разворачивании адресной
   строки — это не событие scroll, поэтому пересчитываем и по resize. */
requestAnimationFrame(onScroll);
window.addEventListener('resize', onScroll, {passive:true});
if (window.visualViewport) window.visualViewport.addEventListener('resize', onScroll, {passive:true});

/* ---------- Мобильное меню ---------- */
var burger = $('#burger');
function closeMenu(){ document.body.classList.remove('menu-open','is-locked'); burger.setAttribute('aria-expanded','false'); }
burger.addEventListener('click', function(){
  var open = document.body.classList.toggle('menu-open');
  document.body.classList.toggle('is-locked', open);
  burger.setAttribute('aria-expanded', open ? 'true' : 'false');
});
$$('#mobileMenu a').forEach(function(a){ a.addEventListener('click', closeMenu); });

/* ---------- Появление секций ---------- */
if ('IntersectionObserver' in window){
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if (e.isIntersecting){ e.target.classList.add('is-in'); io.unobserve(e.target); }
    });
  }, {rootMargin:'0px 0px -8% 0px', threshold:.08});
  $$('.reveal').forEach(function(el){ io.observe(el); });
} else {
  $$('.reveal').forEach(function(el){ el.classList.add('is-in'); });
}

/* ---------- Чипсы длительности на странице услуги ----------
   Пока у услуги один вариант, но разметка и логика рассчитаны на несколько:
   как только в tools/data.py появится поле durations со списком, чипсы начнут
   переключать цену без правок здесь. */
(function(){
  /* Только переключатели на самой странице услуги: в карточках каталога
     длительность выводится подписями и кликов не ждёт. */
  var act = $('.svcp__act');
  if (!act) return;
  var chips = $$('.dur__b', act);
  if (!chips.length) return;
  var out = $('.prices__r b');

  chips.forEach(function(b){
    b.addEventListener('click', function(){
      chips.forEach(function(x){ x.classList.remove('is-active'); });
      b.classList.add('is-active');
      var p = b.getAttribute('data-price');
      /* Цену перебиваем, только когда акции нет: с промо-плашкой первая
         строка — цена по акции, её трогать нельзя. */
      if (out && p && !$('.prices__r--promo')) out.textContent = p;
    });
  });
})();

/* ---------- «Показать все»: разворачивает полотно с описанием ---------- */
(function(){
  var box = $('#svcMore');
  if (!box) return;
  var btn = $('[data-more]', box);
  if (!btn) return;

  /* Если текст и так короче свёрнутой высоты, кнопка не нужна */
  var body = $('.more__body', box);
  if (body.scrollHeight <= body.clientHeight + 4){ btn.hidden = true; box.classList.add('is-open'); return; }

  btn.addEventListener('click', function(){
    var open = box.classList.toggle('is-open');
    btn.textContent = open ? 'Свернуть' : 'Показать все';
    if (open) goal('open_longread');
    if (!open) box.scrollIntoView({behavior:'smooth', block:'start'});
  });
})();

/* ---------- Ленты, которые листаются вбок (интерьер и мастера) ---------- */
function setupRail(wrap, rail, prev, next){
  if (!wrap || !rail) return;

  function step(){ return Math.max(220, rail.clientWidth * .62); }
  if (prev) prev.addEventListener('click', function(){ rail.scrollBy({left:-step(), behavior:'smooth'}); });
  if (next) next.addEventListener('click', function(){ rail.scrollBy({left: step(), behavior:'smooth'}); });

  /* Перетаскивание мышью — чтобы лента листалась и без тачскрина */
  var down = false, sx = 0, sl = 0;
  rail.addEventListener('pointerdown', function(e){
    if (e.pointerType === 'touch') return;
    down = true; sx = e.clientX; sl = rail.scrollLeft; rail.classList.add('is-drag');
  });
  rail.addEventListener('pointermove', function(e){
    if (!down) return;
    var d = e.clientX - sx;
    rail.scrollLeft = sl - d;
    if (Math.abs(d) > 4) e.preventDefault();
  });
  ['pointerup','pointerleave','pointercancel'].forEach(function(ev){
    rail.addEventListener(ev, function(){ down = false; rail.classList.remove('is-drag'); });
  });

  function edge(){
    var end = rail.scrollLeft + rail.clientWidth >= rail.scrollWidth - 4;
    wrap.classList.toggle('at-end', end);
    if (prev) prev.disabled = rail.scrollLeft < 4;
    if (next) next.disabled = end;
  }
  rail.addEventListener('scroll', edge, {passive:true});
  window.addEventListener('resize', edge);
  edge();
}

/* ---------- Атмосфера: мозаичная лента интерьера ---------- */
(function(){
  var atm = $('#atm');
  if (!atm) return;
  var rail = $('.atm__rail', atm);
  var tiles = $$('.atm-t', atm);

  /* Кадры проявляются, когда въезжают в ленту, — и при вертикальной прокрутке
     страницы, и при свайпе вбок. Проверяем положение сами: наблюдатель может
     пропустить кадр при резком свайпе. */
  var pending = tiles.slice(), queued = false;
  function sweep(){
    queued = false;
    if (!pending.length) return;
    var rb = rail.getBoundingClientRect(), vh = window.innerHeight || 0;
    pending = pending.filter(function(t){
      var b = t.getBoundingClientRect();
      var seen = b.right > rb.left + 10 && b.left < rb.right - 10 && b.bottom > 0 && b.top < vh;
      if (seen) t.classList.add('is-in');
      return !seen;
    });
  }
  function ping(){ if (!queued){ queued = true; requestAnimationFrame(sweep); } }
  rail.addEventListener('scroll', ping, {passive:true});
  window.addEventListener('scroll', ping, {passive:true});
  window.addEventListener('resize', ping);
  ping();

  setupRail(atm, rail, $('.atm__prev', atm), $('.atm__next', atm));

  /* Просмотр кадра крупно. Клик после перетаскивания не открывает окно. */
  var lb = $('#lightbox'), lbImg = $('#lbImg'), lbCap = $('#lbCap'), idx = 0;
  if (!lb) return;
  var shots = tiles.map(function(t){
    var i = $('img', t);
    return {src:i.getAttribute('src'), alt:i.getAttribute('alt'), cap:$('b', t).textContent};
  });

  function show(i){
    idx = (i + shots.length) % shots.length;
    lbImg.src = shots[idx].src;
    lbImg.alt = shots[idx].alt;
    lbCap.textContent = shots[idx].cap;
  }
  function open(i){ show(i); lb.classList.add('is-open'); document.body.classList.add('is-locked'); }
  function close(){ lb.classList.remove('is-open'); if (!$('.modal.is-open')) document.body.classList.remove('is-locked'); }

  var downX = 0;
  rail.addEventListener('pointerdown', function(e){ downX = e.clientX; });
  tiles.forEach(function(t, i){
    t.addEventListener('click', function(e){
      if (Math.abs(e.clientX - downX) > 6) return;   /* это было перетаскивание */
      open(i);
    });
  });

  $('.lb__x', lb).addEventListener('click', close);
  $('.lb__prev', lb).addEventListener('click', function(){ show(idx - 1); });
  $('.lb__next', lb).addEventListener('click', function(){ show(idx + 1); });
  lb.addEventListener('click', function(e){ if (e.target === lb || e.target === lbImg) close(); });
  document.addEventListener('keydown', function(e){
    if (!lb.classList.contains('is-open')) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowLeft') show(idx - 1);
    if (e.key === 'ArrowRight') show(idx + 1);
  });

  /* Свайп по открытому фото листает дальше */
  var tx = 0;
  lb.addEventListener('touchstart', function(e){ tx = e.changedTouches[0].clientX; }, {passive:true});
  lb.addEventListener('touchend', function(e){
    var d = e.changedTouches[0].clientX - tx;
    if (Math.abs(d) > 45) show(idx + (d < 0 ? 1 : -1));
  }, {passive:true});
})();

/* ---------- Мастера: лента со свайпом ---------- */
(function(){
  var wrap = $('#mrail');
  if (!wrap) return;
  setupRail(wrap, $('.masters', wrap), $('.mrail__prev', wrap), $('.mrail__next', wrap));
})();

/* ---------- Слайдер «до / после» ---------- */
(function(){
  var slider = $('#baSlider'), after = $('#baAfter'), handle = $('#baHandle');
  if (!slider) return;
  var dragging = false;

  function setPos(clientX){
    var r = slider.getBoundingClientRect();
    var p = Math.min(Math.max((clientX - r.left) / r.width, 0), 1) * 100;
    after.style.clipPath = 'inset(0 0 0 ' + p + '%)';
    handle.style.left = p + '%';
  }
  function down(e){ dragging = true; setPos(e.touches ? e.touches[0].clientX : e.clientX); }
  function move(e){ if (!dragging) return; setPos(e.touches ? e.touches[0].clientX : e.clientX); }
  function up(){ dragging = false; }

  slider.addEventListener('mousedown', down);
  slider.addEventListener('touchstart', down, {passive:true});
  window.addEventListener('mousemove', move);
  window.addEventListener('touchmove', move, {passive:true});
  window.addEventListener('mouseup', up);
  window.addEventListener('touchend', up);
  slider.addEventListener('click', function(e){ setPos(e.clientX); });

  /* Когда слайдер впервые появляется на экране, ползунок сам проходит короткий
     путь и возвращается — без подсказки словами человек понимает, что его
     можно тянуть. Один раз за визит; при первом же касании проход прерывается. */
  var swept = false;
  function setPercent(p){
    after.style.clipPath = 'inset(0 0 0 ' + p + '%)';
    handle.style.left = p + '%';
  }
  function sweep(){
    if (swept) return;
    swept = true;
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var t0 = null, dur = 1500, from = 50, to = 72;
    function step(ts){
      if (dragging) { setPercent(from); return; }
      if (t0 === null) t0 = ts;
      var t = Math.min((ts - t0) / dur, 1);
      /* туда и обратно, с мягким замедлением на краях */
      var e = t < .5 ? t * 2 : (1 - t) * 2;
      e = e * e * (3 - 2 * e);
      setPercent(from + (to - from) * e);
      if (t < 1) requestAnimationFrame(step); else setPercent(from);
    }
    requestAnimationFrame(step);
  }
  if ('IntersectionObserver' in window){
    var io = new IntersectionObserver(function(entries){
      if (entries[0].isIntersecting){ io.disconnect(); setTimeout(sweep, 450); }
    }, {threshold:.55});
    io.observe(slider);
  }
})();

/* ---------- Карусель отзывов ---------- */
(function(){
  var box = $('#revScroll'); if (!box) return;
  function step(){ var c = box.querySelector('.rev'); return c ? c.offsetWidth + 16 : 320; }
  $('#revNext').addEventListener('click', function(){ box.scrollBy({left: step(), behavior:'smooth'}); });
  $('#revPrev').addEventListener('click', function(){ box.scrollBy({left:-step(), behavior:'smooth'}); });
})();

/* ---------- Всплывающая плашка с предложением ----------
   Показывается один раз в сутки и только после того, как человек ушёл ниже
   первого экрана: до этого он ещё не понял, куда попал, и закроет её не читая.
   Отказ помним в localStorage — навязываться на каждой странице нельзя.
   Плашка есть не на всех страницах, поэтому сначала проверяем, что она в вёрстке. */
(function(){
  var pop = $('#pop');
  if (!pop) return;

  var KEY = 'cuerpo_pop_closed';
  var DAY = 24 * 60 * 60 * 1000;

  /* localStorage может быть недоступен — приватный режим, отключённые куки.
     Тогда просто показываем плашку как обычно, но молча: падать нельзя. */
  function closedRecently(){
    try {
      var t = window.localStorage.getItem(KEY);
      return t && (Date.now() - parseInt(t, 10)) < DAY;
    } catch (e) { return false; }
  }
  function remember(){
    try { window.localStorage.setItem(KEY, String(Date.now())); } catch (e) {}
  }

  if (closedRecently()) return;

  var shown = false;
  function maybeShow(){
    if (shown || window.scrollY < window.innerHeight * 0.8) return;
    shown = true;
    window.removeEventListener('scroll', maybeShow);
    pop.classList.add('is-in');
  }

  function hide(){
    pop.classList.remove('is-in');
    remember();
  }

  $('[data-pop-close]', pop).addEventListener('click', hide);
  /* Ушёл по ссылке — значит плашка сработала, второй раз показывать незачем */
  var link = $('a', pop);
  if (link) link.addEventListener('click', remember);
  document.addEventListener('keydown', function(e){
    if (e.key === 'Escape' && pop.classList.contains('is-in')) hide();
  });

  window.addEventListener('scroll', maybeShow, { passive: true });
  maybeShow();
})();

/* ---------- Плавная прокрутка с учётом шапки ---------- */
document.addEventListener('click', function(e){
  var a = e.target.closest('a[href^="#"]');
  if (!a) return;
  var id = a.getAttribute('href');
  if (id === '#' || a.hasAttribute('data-yandex') || a.hasAttribute('data-2gis')) return;
  var t = document.querySelector(id);
  if (!t) return;
  e.preventDefault();
  var offset = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--header-h')) || 68;
  window.scrollTo({ top: t.getBoundingClientRect().top + window.scrollY - offset - 10, behavior:'smooth' });
});

})();
