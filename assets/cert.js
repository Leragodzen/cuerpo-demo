/* ============================================================
   CUERPO — отрисовка подарочного сертификата
   ------------------------------------------------------------
   Один файл на две страницы: служебный генератор
   (sertifikaty/generator/) рисует им файл для отправки гостю,
   а страница сертификата (sertifikaty/) — предпросмотр, чтобы
   человек видел, что именно получит, ещё до оформления.

   Формат — карточка 1600×1000, пропорции близки к банковской.
   Рисуем крупно и уменьшаем на экране: так файл годится и для
   пересылки в мессенджере, и для печати на A5.

   Композиция намеренно несимметричная: марка и текст прижаты
   влево, справа уходит за край монограмма, поверх всего идут
   дуги. Прошлая версия была центрирована и в рамке — это
   читалось как бланк, а не как подарок.

   Кегли заданы крупно намеренно. Сертификат смотрят с экрана
   телефона и чаще всего в пересланном сообщении, уменьшенным:
   мелкая подпись там просто не читается. Всё, что меньше 26 px
   на этом холсте, на телефоне превращается в серую полоску.
   ============================================================ */
window.CuerpoCert = (function(){
'use strict';

var W = 1600, H = 1000;
var PAPER='#FDFBF7', INK='#1A1613', INK2='#4F463A', INK3='#8B8172',
    GREEN='#4E6A40', DARK='#1F2A19', SAND='#C9B08C';
var PAD = 108;                       /* левое поле, от него живёт весь текст */
var MONTHS = ['января','февраля','марта','апреля','мая','июня',
              'июля','августа','сентября','октября','ноября','декабря'];

function money(n){ return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }

function dateRu(iso){
  if(!iso){ return ''; }
  var p = String(iso).split('-');
  if(p.length !== 3){ return ''; }
  return Number(p[2]) + ' ' + MONTHS[Number(p[1]) - 1] + ' ' + p[0];
}

/* Срок по умолчанию — три месяца от сегодняшнего дня.
   setMonth сам переносит год и подтягивает 31-е число к концу
   короткого месяца, поэтому отдельной проверки не нужно. */
function defaultTill(){
  var d = new Date();
  d.setMonth(d.getMonth() + 3);
  return d.getFullYear() + '-' + ('0'+(d.getMonth()+1)).slice(-2) + '-' + ('0'+d.getDate()).slice(-2);
}

/* Разрядка вручную: ctx.letterSpacing поддерживают не все браузеры,
   а капитель с плотными буквами выглядит дёшево. */
function tracked(ctx, text, x, y, size, weight, color, track){
  ctx.font = weight + ' ' + size + 'px "Jost"';
  ctx.fillStyle = color;
  var ch = text.split(''), i;
  for(i = 0; i < ch.length; i++){
    ctx.fillText(ch[i], x, y);
    x += ctx.measureText(ch[i]).width + track;
  }
  return x - track;
}

/* Название программы бывает длинным («SPA-программа „Двойной Испанский“»).
   Сначала пробуем уменьшить кегль, и только если не помогло — переносим:
   две строки крупно читаются лучше, чем одна мелко. */
function wrap(ctx, text, max, size, weight){
  ctx.font = weight + ' ' + size + 'px "Cormorant Garamond"';
  if(ctx.measureText(text).width <= max){ return {size:size, lines:[text]}; }

  while(size > 76 && ctx.measureText(text).width > max){
    size -= 4;
    ctx.font = weight + ' ' + size + 'px "Cormorant Garamond"';
  }
  if(ctx.measureText(text).width <= max){ return {size:size, lines:[text]}; }

  var words = text.split(' '), lines = [], cur = '';
  words.forEach(function(w){
    var test = cur ? cur + ' ' + w : w;
    if(ctx.measureText(test).width > max && cur){ lines.push(cur); cur = w; }
    else { cur = test; }
  });
  if(cur){ lines.push(cur); }
  return {size:size, lines:lines.slice(0, 2)};
}

/* Монограмма уходит за правый нижний угол. Обрезанная буква выглядит
   как знак на бумаге, а вписанная целиком — как водяной знак на справке.
   Цвет песочный, как и был: по нему сертификат узнаётся. */
function monogram(ctx){
  ctx.save();
  ctx.globalAlpha = 0.58;
  ctx.fillStyle = SAND;
  ctx.textAlign = 'left';
  ctx.font = 'italic 500 900px "Cormorant Garamond"';
  ctx.fillText('C', 960, 1276);
  ctx.restore();
}

/* Дуги. Тонкие светлые линии прошлой версии пропадали при пересылке —
   мессенджер жмёт картинку, и волосяная линия превращается в шум.
   Теперь они тёмные и толстые: это и есть рисунок карточки.
   Держатся правее текстовой колонки, нижняя проходит под текстом. */
function arcs(ctx){
  ctx.save();
  ctx.strokeStyle = DARK;
  ctx.lineCap = 'round';

  ctx.lineWidth = 11;
  ctx.beginPath();
  ctx.moveTo(700, -40);
  ctx.bezierCurveTo(980, 210, 1220, 300, 1660, 286);
  ctx.stroke();

  ctx.lineWidth = 8;
  ctx.beginPath();
  ctx.moveTo(1080, -40);
  ctx.bezierCurveTo(1210, 280, 1400, 540, 1660, 706);
  ctx.stroke();

  ctx.lineWidth = 11;
  ctx.beginPath();
  ctx.moveTo(-40, 1046);
  ctx.bezierCurveTo(520, 1000, 1120, 1020, 1660, 700);
  ctx.stroke();

  ctx.restore();
}

/* data: {mode:'sum'|'svc', sum, svc, num, to, from, till} */
function draw(cv, data){
  var ctx = cv.getContext('2d');
  cv.width = W; cv.height = H;

  ctx.fillStyle = PAPER; ctx.fillRect(0, 0, W, H);
  ctx.textBaseline = 'alphabetic';
  ctx.textAlign = 'left';

  monogram(ctx);
  arcs(ctx);

  /* Марка */
  ctx.fillStyle = DARK;
  ctx.font = 'italic 500 96px "Cormorant Garamond"';
  ctx.fillText('Cuerpo', PAD, 162);
  tracked(ctx, 'МАСТЕРСКАЯ ПО ТЕЛУ', PAD + 6, 212, 19, '400', INK3, 8);

  /* Что это за бумага */
  tracked(ctx, 'ПОДАРОЧНЫЙ СЕРТИФИКАТ', PAD, 344, 26, '500', GREEN, 10);

  /* Главное — номинал или программа */
  var isSum = data.mode !== 'svc';
  var whoY = 676;               /* сдвигается вниз, если название в две строки */
  if(isSum){
    var v = money(String(data.sum || '').replace(/\D/g, '')) || '0';
    ctx.fillStyle = DARK;
    ctx.font = '600 220px "Cormorant Garamond"';
    ctx.fillText(v + ' ₽', PAD, 548);
  } else {
    var r = wrap(ctx, data.svc || '', 960, 116, '600');
    ctx.fillStyle = DARK;
    ctx.font = '600 ' + r.size + 'px "Cormorant Garamond"';
    var ly = r.lines.length > 1 ? 486 : 548;
    r.lines.forEach(function(ln){
      ctx.fillText(ln, PAD, ly);
      ly += r.size + 14;
    });
    whoY = Math.max(whoY, ly - r.size + 56);
  }

  /* Кому и от кого — одной строкой, чтобы не наращивать этажи */
  var who = [];
  if(data.to){ who.push('Для ' + data.to); }
  if(data.from){ who.push('от ' + data.from); }
  if(who.length){
    ctx.fillStyle = INK2;
    ctx.font = '400 38px "Jost"';
    ctx.fillText(who.join('   ·   '), PAD, whoY);
  }

  /* Короткая черта отделяет подарок от служебной части */
  ctx.save();
  ctx.strokeStyle = DARK;
  ctx.lineWidth = 5;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(PAD, 726);
  ctx.lineTo(PAD + 300, 726);
  ctx.stroke();
  ctx.restore();

  /* Что с этим делать */
  ctx.fillStyle = INK2;
  ctx.font = '400 32px "Jost"';
  ctx.fillText('Покажите сертификат администратору — можно прямо с экрана телефона.', PAD, 800);

  ctx.fillStyle = INK3;
  ctx.font = '400 32px "Jost"';
  ctx.fillText('Запись по телефону', PAD, 876);
  var lw = ctx.measureText('Запись по телефону ').width;
  ctx.fillStyle = GREEN;
  ctx.font = '500 46px "Jost"';
  ctx.fillText('+7 (927) 892-30-13', PAD + lw, 880);

  /* Номер и срок — то, что проверяет администратор */
  var meta = [];
  if(data.num){ meta.push('№ ' + data.num); }
  var t = dateRu(data.till);
  if(t){ meta.push('ДЕЙСТВИТЕЛЕН ДО ' + t.toUpperCase()); }
  if(meta.length){ tracked(ctx, meta.join('   ·   '), PAD, 940, 22, '500', INK, 4); }

  ctx.fillStyle = INK3;
  ctx.font = '400 27px "Jost"';
  ctx.fillText('Тольятти, Приморский бульвар, 57', PAD, 980);
}

/* Шрифты грузятся из Google Fonts: без ожидания canvas успевает
   отрисоваться системным шрифтом и так и остаётся. */
function ready(cb){
  if(!document.fonts || !document.fonts.load){ setTimeout(cb, 400); return; }
  Promise.all([
    document.fonts.load('italic 500 96px "Cormorant Garamond"'),
    document.fonts.load('600 220px "Cormorant Garamond"'),
    document.fonts.load('400 32px "Jost"'),
    document.fonts.load('500 46px "Jost"')
  ]).then(cb).catch(cb);
  document.fonts.ready.then(cb);
}

return { draw: draw, ready: ready, money: money, dateRu: dateRu,
         defaultTill: defaultTill, W: W, H: H };
})();
