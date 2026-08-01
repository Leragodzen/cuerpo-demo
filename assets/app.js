/* ============================================================
   CUERPO — скрипты сайта
   ------------------------------------------------------------
   НАСТРОЙКА ПЕРЕД ПУБЛИКАЦИЕЙ — см. блок CONFIG ниже.
   ============================================================ */
(function(){
'use strict';

/* ---------- НАСТРОЙКИ ---------- */
var CONFIG = {
  /* Ссылка на карточку салона на Яндекс Картах (кнопки «Читать все отзывы»).
     Замените на прямую ссылку карточки организации. */
  yandexUrl: 'https://yandex.ru/maps/240/tolyatti/?ll=49.251250%2C53.508350&z=17&text=Cuerpo%20%D0%BC%D0%B0%D1%81%D1%81%D0%B0%D0%B6%20%D0%A2%D0%BE%D0%BB%D1%8C%D1%8F%D1%82%D1%82%D0%B8%20%D0%9F%D1%80%D0%B8%D0%BC%D0%BE%D1%80%D1%81%D0%BA%D0%B8%D0%B9%20%D0%B1%D1%83%D0%BB%D1%8C%D0%B2%D0%B0%D1%80%2C%2057',

  /* Ссылка на карточку салона в 2ГИС (кнопки «Отзывы в 2ГИС»).
     Замените на прямую ссылку карточки организации. */
  gisUrl: 'https://2gis.ru/togliatti/search/Cuerpo%20%D0%BC%D0%B0%D1%81%D1%81%D0%B0%D0%B6',

  /* Уведомления администратору в Telegram.
     1) Создайте бота у @BotFather → получите токен.
     2) Узнайте chat_id администратора (или группы) через @userinfobot.
     3) Впишите значения ниже. Пока поля пустые — заявка открывается
        готовым сообщением в Telegram, сайт работает без сервера. */
  tgBotToken: '',
  tgChatId:   '',

  /* Запасной канал: заявка уходит готовым текстом в Telegram салона */
  tgFallback: 'https://t.me/+79278923013',

  phone: '+7 (927) 892-30-13',
  phoneRaw: '+79278923013'
};

var $  = function(s, c){ return (c||document).querySelector(s); };
var $$ = function(s, c){ return Array.prototype.slice.call((c||document).querySelectorAll(s)); };

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
  else if (/t\.me|vk\.me|vk\.com|max\.ru/.test(href)) goal('messenger');
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

function onScroll(){
  var s = window.scrollY || document.documentElement.scrollTop;
  var mbarVisible = s > 140;
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

/* ---------- Список услуг в форме записи ----------
   Берётся из assets/services.js — файл собирается из tools/data.py вместе со
   страницами, поэтому список одинаков на всех страницах и не разъезжается с
   каталогом. Раньше 24 <option> дублировали каталог руками, и связка держалась
   на точном совпадении строк: одна опечатка молча роняла выбор в «Помогите выбрать».

   value намеренно не задаём — .value должен равняться тексту опции, именно он
   уходит в заявку администратору. */
(function(){
  var sel = $('#f-service');
  if (!sel || !window.CUERPO_SERVICES) return;
  var other = $('#f-service-other');
  var seen = {};
  window.CUERPO_SERVICES.forEach(function(grp){
    var g = document.createElement('optgroup');
    g.label = grp.group;
    grp.items.forEach(function(n){
      if (seen[n]) return;
      seen[n] = 1;
      var o = document.createElement('option');
      o.textContent = n;
      g.appendChild(o);
    });
    if (g.children.length) sel.insertBefore(g, other);
  });
})();

/* ---------- Проверка каталога против микроразметки ----------
   Служебная команда для редактора сайта: открыть консоль браузера и выполнить
   cuerpoCheckServices(). Покажет услуги без оффера в JSON-LD и наоборот.
   На посетителей никак не влияет. */
window.cuerpoCheckServices = function(){
  var cat = {};
  (window.CUERPO_SERVICES || []).forEach(function(g){
    g.items.forEach(function(n){ cat[n] = 1; });
  });
  var ld = {};
  $$('script[type="application/ld+json"]').forEach(function(s){
    var d; try { d = JSON.parse(s.textContent); } catch(e){ return; }
    var list = d.hasOfferCatalog && d.hasOfferCatalog.itemListElement;
    (list || []).forEach(function(o){
      if (o.itemOffered && o.itemOffered.name) ld[o.itemOffered.name] = o.price || '';
    });
  });
  var noOffer = Object.keys(cat).filter(function(n){ return !(n in ld); });
  var noCard  = Object.keys(ld).filter(function(n){ return !(n in cat); });
  console.log('Услуг в каталоге:', Object.keys(cat).length, '· офферов в разметке:', Object.keys(ld).length);
  if (noOffer.length) console.warn('Нет оффера в JSON-LD:', noOffer);
  if (noCard.length)  console.warn('Оффер без карточки в каталоге:', noCard);
  if (!noOffer.length && !noCard.length) console.log('Каталог и микроразметка совпадают.');
};

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

/* ---------- Модальные окна ---------- */
var bookModal = $('#bookModal'), privacyModal = $('#privacyModal');

function openModal(m){
  m.classList.add('is-open');
  document.body.classList.add('is-locked');
  var f = m.querySelector('input:not([type=checkbox]), select');
  if (f) setTimeout(function(){ if (window.innerWidth > 760) f.focus(); }, 260);
}
function closeModal(m){
  m.classList.remove('is-open');
  if (!$('.modal.is-open')) document.body.classList.remove('is-locked');
}
$$('[data-close]').forEach(function(el){
  el.addEventListener('click', function(){ closeModal(el.closest('.modal')); });
});
document.addEventListener('keydown', function(e){
  if (e.key === 'Escape'){ $$('.modal.is-open').forEach(closeModal); if (document.body.classList.contains('menu-open')) closeMenu(); }
});
$$('[data-privacy]').forEach(function(a){
  a.addEventListener('click', function(e){ e.preventDefault(); openModal(privacyModal); });
});

/* Кнопки «Записаться» — с предзаполнением услуги/мастера */
document.addEventListener('click', function(e){
  var btn = e.target.closest('[data-book]');
  if (!btn) return;
  e.preventDefault();
  closeMenu();

  $('#bookFormWrap').hidden = false;
  $('#bookSuccess').hidden = true;

  var svc = btn.dataset.service, master = btn.dataset.master;
  var sel = $('#f-service');
  if (svc){
    var found = Array.prototype.some.call(sel.options, function(o){
      if (o.text === svc){ sel.value = o.value || o.text; return true; }
    });
    if (!found) sel.selectedIndex = 0;
  }
  if (master) $('#f-master').value = master;

  goal('open_form');
  openModal(bookModal);
});

/* ---------- Поле даты и слоты времени ---------- */
(function(){
  var d = $('#f-date');
  var today = new Date();
  var iso = function(dt){ return dt.toISOString().slice(0,10); };
  d.min = iso(today);
  var max = new Date(today.getTime() + 1000*60*60*24*90);
  d.max = iso(max);

  var t = $('#f-time');
  t.innerHTML = '<option value="">Любое удобное</option>';
  for (var h = 9; h <= 20; h++){
    ['00','30'].forEach(function(m){
      if (h === 20 && m === '30') return;
      var v = (h < 10 ? '0' + h : h) + ':' + m;
      var o = document.createElement('option');
      o.textContent = v; t.appendChild(o);
    });
  }
})();

/* ---------- Маска телефона ---------- */
function phoneMask(input){
  if (!input) return;
  input.addEventListener('input', function(){
    var v = input.value.replace(/\D/g, '');
    if (v[0] === '8') v = '7' + v.slice(1);
    if (v[0] !== '7') v = '7' + v;
    v = v.slice(0, 11);
    var out = '+7';
    if (v.length > 1) out += ' (' + v.slice(1, 4);
    if (v.length >= 5) out += ') ' + v.slice(4, 7);
    if (v.length >= 8) out += '-' + v.slice(7, 9);
    if (v.length >= 10) out += '-' + v.slice(9, 11);
    input.value = out;
  });
  input.addEventListener('focus', function(){ if (!input.value) input.value = '+7 ('; });
}
phoneMask($('#f-phone'));
phoneMask($('#c-phone'));

/* ---------- Отправка заявки ---------- */
function buildMessage(d){
  return '🌿 НОВАЯ ЗАЯВКА С САЙТА CUERPO\n\n'
    + '👤 Имя: ' + d.name + '\n'
    + '📞 Телефон: ' + d.phone + '\n'
    + '💆 Услуга: ' + (d.service || 'помочь выбрать') + '\n'
    + '🙌 Мастер: ' + d.master + '\n'
    + '📅 Дата: ' + (d.date || 'не указана') + '\n'
    + '🕐 Время: ' + (d.time || 'любое удобное') + '\n'
    + (d.note ? '💬 Комментарий: ' + d.note + '\n' : '')
    + '\n🌐 Отправлено: ' + new Date().toLocaleString('ru-RU');
}

/* Отправка заявки администратору в Telegram.
   Если токен бота не заполнен — cb(false), и заявку предлагаем отправить вручную. */
function sendToAdmin(text, cb){
  if (CONFIG.tgBotToken && CONFIG.tgChatId){
    fetch('https://api.telegram.org/bot' + CONFIG.tgBotToken + '/sendMessage', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({chat_id: CONFIG.tgChatId, text: text})
    })
    .then(function(r){ return r.json(); })
    .then(function(r){ cb(!!r.ok); })
    .catch(function(){ cb(false); });
  } else {
    setTimeout(function(){ cb(false); }, 400);
  }
}

/* Журнал заявок в браузере (для выгрузки в Excel: window.cuerpoExportCSV()) */
function logBooking(d){
  goal('lead');   /* обе формы проходят здесь — одна точка учёта заявок */
  try{
    var list = JSON.parse(localStorage.getItem('cuerpo_bookings') || '[]');
    d.createdAt = new Date().toISOString();
    list.push(d);
    localStorage.setItem('cuerpo_bookings', JSON.stringify(list));
  }catch(e){}
}
window.cuerpoExportCSV = function(){
  var list = JSON.parse(localStorage.getItem('cuerpo_bookings') || '[]');
  if (!list.length){ alert('Заявок пока нет'); return; }
  var head = ['Дата заявки','Имя','Телефон','Услуга','Мастер','Желаемая дата','Время','Комментарий'];
  var rows = list.map(function(b){
    return [b.createdAt, b.name, b.phone, b.service, b.master, b.date, b.time, b.note]
      .map(function(v){ return '"' + String(v == null ? '' : v).replace(/"/g,'""') + '"'; }).join(';');
  });
  var csv = '﻿' + head.join(';') + '\n' + rows.join('\n');
  var a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], {type:'text/csv;charset=utf-8'}));
  a.download = 'cuerpo-zayavki.csv';
  a.click();
};

var form = $('#bookForm');
form.addEventListener('submit', function(e){
  e.preventDefault();

  var nameF = $('#f-name').closest('.field');
  var phoneF = $('#f-phone').closest('.field');
  var ok = true;

  var name = $('#f-name').value.trim();
  nameF.classList.toggle('is-error', !name);
  if (!name) ok = false;

  var phone = $('#f-phone').value.trim();
  var digits = phone.replace(/\D/g, '');
  var phoneOk = digits.length === 11;
  phoneF.classList.toggle('is-error', !phoneOk);
  if (!phoneOk) ok = false;

  if (!$('#f-agree').checked){
    alert('Пожалуйста, подтвердите согласие на обработку персональных данных.');
    ok = false;
  }
  if (!ok) return;

  var data = {
    name: name,
    phone: phone,
    service: $('#f-service').value,
    master: $('#f-master').value,
    date: $('#f-date').value ? new Date($('#f-date').value).toLocaleDateString('ru-RU') : '',
    time: $('#f-time').value,
    note: $('#f-note').value.trim()
  };
  var text = buildMessage(data);
  logBooking(data);

  var btn = $('#bookSubmit');
  btn.disabled = true;
  btn.textContent = 'Отправляем…';

  function done(sentToAdmin){
    btn.disabled = false;
    btn.textContent = 'Отправить заявку';
    $('#bookFormWrap').hidden = true;
    $('#bookSuccess').hidden = false;

    if (sentToAdmin){
      $('#successText').textContent = 'Спасибо, ' + data.name + '! Заявка у администратора. Мы перезвоним на ' + data.phone + ', чтобы подтвердить время и мастера.';
      $('#successTg').href = CONFIG.tgFallback;
      $('#successTg').textContent = 'Написать в Telegram';
    } else {
      $('#successText').textContent = 'Спасибо, ' + data.name + '! Чтобы мы точно не потеряли вашу заявку, отправьте её нам в Telegram — сообщение уже готово, нужно только нажать «Отправить».';
      $('#successTg').href = CONFIG.tgFallback + '?text=' + encodeURIComponent(text);
      $('#successTg').textContent = 'Отправить заявку в Telegram';
    }
    form.reset();
  }

  sendToAdmin(text, done);
});

/* ---------- Короткая форма «Перезвоните мне» ---------- */
(function(){
  var cf = $('#callForm');
  if (!cf) return;
  cf.addEventListener('submit', function(e){
    e.preventDefault();
    var name = $('#c-name').value.trim(), phone = $('#c-phone').value.trim();
    if (phone.replace(/\D/g, '').length !== 11){
      $('#c-phone').focus();
      $('#c-phone').style.borderColor = '#C0563F';
      return;
    }
    $('#c-phone').style.borderColor = '';

    var data = {
      name: name || 'не указано',
      phone: phone,
      service: 'Подобрать программу (обратный звонок)',
      master: '', date: '', time: '', note: ''
    };
    var text = buildMessage(data);
    logBooking(data);

    var btn = $('#callBtn');
    btn.disabled = true;
    btn.textContent = 'Отправляем…';

    sendToAdmin(text, function(sent){
      btn.disabled = false;
      if (sent){
        btn.textContent = 'Заявка принята ✓';
      } else {
        btn.textContent = 'Открываем Telegram…';
        window.open(CONFIG.tgFallback + '?text=' + encodeURIComponent(text), '_blank');
        setTimeout(function(){ btn.textContent = 'Заявка принята ✓'; }, 900);
      }
      cf.reset();
      setTimeout(function(){ btn.textContent = 'Перезвоните мне'; }, 6000);
    });
  });
})();

/* ---------- Плавная прокрутка с учётом шапки ---------- */
document.addEventListener('click', function(e){
  var a = e.target.closest('a[href^="#"]');
  if (!a) return;
  var id = a.getAttribute('href');
  if (id === '#' || a.hasAttribute('data-privacy') || a.hasAttribute('data-yandex') || a.hasAttribute('data-2gis')) return;
  var t = document.querySelector(id);
  if (!t) return;
  e.preventDefault();
  var offset = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--header-h')) || 68;
  window.scrollTo({ top: t.getBoundingClientRect().top + window.scrollY - offset - 10, behavior:'smooth' });
});

})();
