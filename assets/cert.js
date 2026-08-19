/* ============================================================
   CUERPO — отрисовка подарочного сертификата
   ------------------------------------------------------------
   Один файл на две страницы: служебный генератор
   (sertifikaty/generator/) рисует им файл для отправки гостю,
   а страница сертификата (sertifikaty/) — предпросмотр, чтобы
   человек видел, что именно получит, ещё до оформления.

   Формат — карточка 1600×1000, пропорции близки к банковской.
   Рисуем крупно и уменьшаем на экране: так файл годится и для
   пересылки в мессенджере, и для печати.
   ============================================================ */
window.CuerpoCert = (function(){
'use strict';

var W = 1600, H = 1000;
var BG='#F7F2E9', INK='#241F19', INK2='#6B6153', INK3='#948A7A',
    GREEN='#5F7A50', DARK='#283321', SAND='#D3B99A';
var MONTHS = ['января','февраля','марта','апреля','мая','июня',
              'июля','августа','сентября','октября','ноября','декабря'];

function money(n){ return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }

function dateRu(iso){
  if(!iso){ return ''; }
  var p = String(iso).split('-');
  if(p.length !== 3){ return ''; }
  return Number(p[2]) + ' ' + MONTHS[Number(p[1]) - 1] + ' ' + p[0];
}

/* Срок по умолчанию — полгода от сегодняшнего дня */
function defaultTill(){
  var d = new Date();
  d.setMonth(d.getMonth() + 6);
  return d.getFullYear() + '-' + ('0'+(d.getMonth()+1)).slice(-2) + '-' + ('0'+d.getDate()).slice(-2);
}

/* Разрядка вручную: ctx.letterSpacing поддерживают не все браузеры,
   а капитель с плотными буквами выглядит дёшево. */
function spaced(ctx, text, cx, y, size, font, weight, color, track){
  ctx.font = weight + ' ' + size + 'px "' + font + '"';
  ctx.fillStyle = color;
  var ch = text.split(''), w = 0, i;
  for(i = 0; i < ch.length; i++){ w += ctx.measureText(ch[i]).width + track; }
  w -= track;
  var x = cx - w / 2;
  for(i = 0; i < ch.length; i++){
    ctx.fillText(ch[i], x, y);
    x += ctx.measureText(ch[i]).width + track;
  }
}

function fit(ctx, text, max, size, font, weight){
  ctx.font = weight + ' ' + size + 'px "' + font + '"';
  while(size > 26 && ctx.measureText(text).width > max){
    size -= 2;
    ctx.font = weight + ' ' + size + 'px "' + font + '"';
  }
  return size;
}

/* Уголковые засечки на рамке: сплошная двойная рамка выглядит как бланк,
   а разомкнутые уголки — как приглашение. */
function corners(ctx, x, y, w, h, len){
  ctx.strokeStyle = SAND;
  ctx.lineWidth = 2;
  var pts = [[x, y, 1, 1], [x + w, y, -1, 1], [x, y + h, 1, -1], [x + w, y + h, -1, -1]];
  pts.forEach(function(p){
    ctx.beginPath();
    ctx.moveTo(p[0] + p[2] * len, p[1]);
    ctx.lineTo(p[0], p[1]);
    ctx.lineTo(p[0], p[1] + p[3] * len);
    ctx.stroke();
  });
}

/* data: {mode:'sum'|'svc', sum, svc, num, to, from, till} */
function draw(cv, data){
  var ctx = cv.getContext('2d');
  cv.width = W; cv.height = H;

  ctx.fillStyle = BG; ctx.fillRect(0, 0, W, H);
  ctx.textBaseline = 'alphabetic';

  ctx.lineWidth = 1;
  ctx.strokeStyle = 'rgba(211,185,154,.5)';
  ctx.strokeRect(46, 46, W - 92, H - 92);
  corners(ctx, 32, 32, W - 64, H - 64, 46);

  /* Монограмма фоном: еле различимая, держит центр композиции */
  ctx.save();
  ctx.globalAlpha = 0.045;
  ctx.textAlign = 'center';
  ctx.fillStyle = GREEN;
  ctx.font = '500 520px "Cormorant Garamond"';
  ctx.fillText('C', W / 2, 700);
  ctx.restore();

  ctx.textAlign = 'center';
  spaced(ctx, 'CUERPO', W / 2, 152, 58, 'Cormorant Garamond', '400', DARK, 10);
  spaced(ctx, 'МАСТЕРСКАЯ ПО ТЕЛУ', W / 2, 190, 14, 'Jost', '300', INK3, 5);

  ctx.strokeStyle = SAND; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(W/2 - 70, 232); ctx.lineTo(W/2 + 70, 232); ctx.stroke();

  ctx.fillStyle = INK;
  ctx.font = '400 42px "Cormorant Garamond"';
  ctx.fillText('Подарочный сертификат', W / 2, 302);

  var isSum = data.mode !== 'svc';
  spaced(ctx, isSum ? 'НА СУММУ' : 'НА ПРОГРАММУ', W / 2, 356, 13, 'Jost', '300', INK3, 5);

  if(isSum){
    var v = money(String(data.sum || '').replace(/\D/g, '')) || '0';
    ctx.fillStyle = GREEN;
    ctx.font = '500 104px "Cormorant Garamond"';
    ctx.fillText(v + ' ₽', W / 2, 470);
  } else {
    var name = data.svc || '';
    var sz = fit(ctx, name, 1240, 64, 'Cormorant Garamond', '500');
    ctx.fillStyle = GREEN;
    ctx.font = '500 ' + sz + 'px "Cormorant Garamond"';
    ctx.fillText(name, W / 2, 462);
  }

  var y = 546;
  if(data.to){ ctx.fillStyle = INK2; ctx.font = '300 25px "Jost"'; ctx.fillText('Для ' + data.to, W/2, y); y += 38; }
  if(data.from){ ctx.fillStyle = INK2; ctx.font = '300 25px "Jost"'; ctx.fillText('от ' + data.from, W/2, y); }

  ctx.strokeStyle = SAND; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(W/2 - 70, 652); ctx.lineTo(W/2 + 70, 652); ctx.stroke();

  ctx.fillStyle = INK2; ctx.font = '300 23px "Jost"';
  ctx.fillText('Запись на программу по телефону', W / 2, 708);
  ctx.fillStyle = GREEN; ctx.font = '400 34px "Jost"';
  ctx.fillText('+7 (927) 892-30-13', W / 2, 752);

  ctx.fillStyle = INK3; ctx.font = '300 20px "Jost"';
  ctx.fillText('Покажите сертификат администратору в салоне — можно прямо', W / 2, 806);
  ctx.fillText('с экрана телефона, до или после сеанса.', W / 2, 836);

  var line = [];
  if(data.num){ line.push('СЕРТИФИКАТ № ' + data.num); }
  var t = dateRu(data.till);
  if(t){ line.push('ДЕЙСТВИТЕЛЕН ДО ' + t.toUpperCase()); }
  if(line.length){ spaced(ctx, line.join('   ·   '), W/2, 900, 15, 'Jost', '400', INK, 3); }

  ctx.fillStyle = INK3; ctx.font = '300 19px "Jost"';
  ctx.fillText('Тольятти, Приморский бульвар, 57', W / 2, 936);
}

/* Шрифты грузятся из Google Fonts: без ожидания canvas успевает
   отрисоваться системным шрифтом и так и остаётся. */
function ready(cb){
  if(!document.fonts || !document.fonts.load){ setTimeout(cb, 400); return; }
  Promise.all([
    document.fonts.load('400 58px "Cormorant Garamond"'),
    document.fonts.load('500 104px "Cormorant Garamond"'),
    document.fonts.load('300 25px "Jost"'),
    document.fonts.load('400 34px "Jost"')
  ]).then(cb).catch(cb);
  document.fonts.ready.then(cb);
}

return { draw: draw, ready: ready, money: money, dateRu: dateRu,
         defaultTill: defaultTill, W: W, H: H };
})();
