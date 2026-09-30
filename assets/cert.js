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
   тонкие дуги. Прошлая версия была центрирована и в рамке —
   это читалось как бланк, а не как подарок.
   ============================================================ */
window.CuerpoCert = (function(){
'use strict';

var W = 1600, H = 1000;
var PAPER='#FDFBF7', INK='#241F19', INK2='#6B6153', INK3='#9B9181',
    GREEN='#5F7A50', DARK='#283321', SAND='#C9B08C';
var PAD = 104;                       /* левое поле, от него живёт весь текст */
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

  while(size > 52 && ctx.measureText(text).width > max){
    size -= 3;
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
   как знак на бумаге, а вписанная целиком — как водяной знак на справке. */
function monogram(ctx){
  ctx.save();
  ctx.globalAlpha = 0.62;
  ctx.fillStyle = SAND;
  ctx.textAlign = 'left';
  ctx.font = 'italic 500 620px "Cormorant Garamond"';
  ctx.fillText('C', 1140, 1120);
  ctx.restore();
}

/* Три дуги: две расходятся в правом верхнем углу, одна проходит
   низом под всем текстом. Держатся подальше от левой колонки —
   там живут сумма и подписи. */
function arcs(ctx){
  ctx.save();
  ctx.strokeStyle = SAND;
  ctx.lineWidth = 3;
  ctx.lineCap = 'round';

  ctx.beginPath();
  ctx.moveTo(600, -40);
  ctx.bezierCurveTo(900, 200, 1180, 300, 1660, 300);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(980, -40);
  ctx.bezierCurveTo(1120, 260, 1340, 520, 1660, 690);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(-40, 1030);
  ctx.bezierCurveTo(500, 985, 1100, 1010, 1660, 700);
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
  ctx.font = 'italic 500 66px "Cormorant Garamond"';
  ctx.fillText('Cuerpo', PAD, 158);
  tracked(ctx, 'МАСТЕРСКАЯ ПО ТЕЛУ', PAD + 4, 196, 13, '300', INK3, 5);

  /* Что это за бумага */
  tracked(ctx, 'ПОДАРОЧНЫЙ СЕРТИФИКАТ', PAD, 336, 16, '400', INK, 6);

  /* Главное — номинал или программа */
  var isSum = data.mode !== 'svc';
  if(isSum){
    var v = money(String(data.sum || '').replace(/\D/g, '')) || '0';
    ctx.fillStyle = DARK;
    ctx.font = '500 136px "Cormorant Garamond"';
    ctx.fillText(v + ' ₽', PAD, 486);
  } else {
    var r = wrap(ctx, data.svc || '', 880, 82, '500');
    ctx.fillStyle = DARK;
    ctx.font = '500 ' + r.size + 'px "Cormorant Garamond"';
    var ly = r.lines.length > 1 ? 442 : 486;
    r.lines.forEach(function(ln){
      ctx.fillText(ln, PAD, ly);
      ly += r.size + 12;
    });
  }

  /* Кому и от кого — одной строкой, чтобы не наращивать этажи */
  var who = [];
  if(data.to){ who.push('Для ' + data.to); }
  if(data.from){ who.push('от ' + data.from); }
  if(who.length){
    ctx.fillStyle = INK2;
    ctx.font = '300 27px "Jost"';
    ctx.fillText(who.join('   ·   '), PAD, 570);
  }

  /* Что с этим делать */
  ctx.fillStyle = INK2;
  ctx.font = '300 23px "Jost"';
  ctx.fillText('Покажите сертификат администратору — можно прямо с экрана телефона.', PAD, 706);

  ctx.fillStyle = INK3;
  ctx.font = '300 23px "Jost"';
  ctx.fillText('Запись по телефону', PAD, 782);
  var lw = ctx.measureText('Запись по телефону ').width;
  ctx.fillStyle = GREEN;
  ctx.font = '400 33px "Jost"';
  ctx.fillText('+7 (927) 892-30-13', PAD + lw, 784);

  /* Номер и срок — то, что проверяет администратор */
  var meta = [];
  if(data.num){ meta.push('№ ' + data.num); }
  var t = dateRu(data.till);
  if(t){ meta.push('ДЕЙСТВИТЕЛЕН ДО ' + t.toUpperCase()); }
  if(meta.length){ tracked(ctx, meta.join('   ·   '), PAD, 892, 15, '400', INK, 3); }

  ctx.fillStyle = INK3;
  ctx.font = '300 20px "Jost"';
  ctx.fillText('Тольятти, Приморский бульвар, 57', PAD, 936);
}

/* Шрифты грузятся из Google Fonts: без ожидания canvas успевает
   отрисоваться системным шрифтом и так и остаётся. */
function ready(cb){
  if(!document.fonts || !document.fonts.load){ setTimeout(cb, 400); return; }
  Promise.all([
    document.fonts.load('italic 500 66px "Cormorant Garamond"'),
    document.fonts.load('500 136px "Cormorant Garamond"'),
    document.fonts.load('300 23px "Jost"'),
    document.fonts.load('400 33px "Jost"')
  ]).then(cb).catch(cb);
  document.fonts.ready.then(cb);
}

return { draw: draw, ready: ready, money: money, dateRu: dateRu,
         defaultTill: defaultTill, W: W, H: H };
})();
