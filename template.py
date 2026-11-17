"""Landing page template. Editorial layout: floating pill nav, blur-in headline, bento grid,
sticky-stack story, dark closing block, accordion FAQ. Fonts: Poppins (display) and Inter (text).
No dollar signs in CSS or JS (string.Template)."""
from string import Template

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">')

MOTION_JS = """(function(){
  var d=document, reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var nav=d.querySelector('.nav'), bar=d.querySelector('.progress i'), call=d.querySelector('.callbar'), hero=d.querySelector('.hero');
  var media=d.querySelector('.media .slot'), cards=[].slice.call(d.querySelectorAll('.scard'));
  var ticking=false;
  function frame(){
    var y=window.scrollY||0, h=Math.max(1,d.body.scrollHeight-window.innerHeight), vh=window.innerHeight;
    if(bar){bar.style.transform='scaleX('+Math.min(1,y/h)+')';}
    if(nav){nav.classList.toggle('scrolled',y>12);}
    if(call&&hero){call.classList.toggle('show',y>hero.offsetHeight*0.6);}
    if(media&&!reduce&&y<1100){media.style.setProperty('--py',(y*0.07).toFixed(1)+'px');}
    cards.forEach(function(c,i){
      if(i===cards.length-1){return;}
      var n=cards[i+1], top=parseFloat(getComputedStyle(n).top)||0, dist=Math.max(0,n.getBoundingClientRect().top-top);
      var p=1-Math.min(1,dist/(c.offsetHeight*0.85));
      c.style.setProperty('--s',(1-0.05*p).toFixed(4));
    });
    ticking=false;
  }
  window.addEventListener('scroll',function(){if(!ticking){ticking=true;requestAnimationFrame(frame);}},{passive:true});
  window.addEventListener('resize',frame);
  frame();

  var counted=false;
  function count(){
    if(counted){return;}counted=true;
    var n=d.getElementById('tabsn'), strip=d.getElementById('tabstrip');
    if(!n||!strip){return;}
    var to=parseInt(n.getAttribute('data-to'),10)||27, i=0;
    if(reduce){n.textContent=to;for(var k=0;k<to;k++){strip.appendChild(d.createElement('i'));}return;}
    var iv=setInterval(function(){i++;n.textContent=i;strip.appendChild(d.createElement('i'));if(i>=to){clearInterval(iv);}},70);
  }
  [].slice.call(d.querySelectorAll('video[autoplay]')).forEach(function(v){var p=v.play();if(p&&p.catch){p.catch(function(){});}});
  var items=[].slice.call(d.querySelectorAll('.reveal,.draw'));
  if(!('IntersectionObserver' in window)||reduce){items.forEach(function(el){el.classList.add('in');});count();}
  else{
    var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){en.target.classList.add('in');if(en.target.id==='pbad'){setTimeout(count,500);}io.unobserve(en.target);}});},{threshold:0.12,rootMargin:'0px 0px -6% 0px'});
    items.forEach(function(el){io.observe(el);});
  }

  d.addEventListener('pointermove',function(e){
    var t=e.target.closest?e.target.closest('.tile'):null;
    if(t){var r=t.getBoundingClientRect();t.style.setProperty('--mx',(e.clientX-r.left)+'px');t.style.setProperty('--my',(e.clientY-r.top)+'px');}
  },{passive:true});

  [].slice.call(d.querySelectorAll('.qa .q')).forEach(function(b){
    b.addEventListener('click',function(){
      var qa=b.parentNode, open=!qa.classList.contains('open');
      [].slice.call(d.querySelectorAll('.qa.open')).forEach(function(o){o.classList.remove('open');o.querySelector('.q').setAttribute('aria-expanded','false');});
      if(open){qa.classList.add('open');b.setAttribute('aria-expanded','true');}
    });
  });
})();"""

PAGE = Template("""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>$name | $offer</title>
<meta name="description" content="$sub">
<script>document.documentElement.className+=' js';</script>
$fonts
<style>
:root{--p:$primary;--a:$accent;--ink:#15181d;--mut:#5d6470;--canvas:#f6f4ef;--canvas2:#ece9e1;--card:#fff;--line:rgba(21,24,29,.1);
--night:#0c1018;--night:color-mix(in srgb,var(--p) 76%,#07090d);--ease:cubic-bezier(.2,.7,.2,1);--r:28px;
--fd:Poppins,Inter,system-ui,Segoe UI,Arial,sans-serif;--fb:Inter,system-ui,Segoe UI,Arial,sans-serif}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font:400 17px/1.6 var(--fb);color:var(--ink);background:var(--canvas);-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
.wrap{max-width:1200px;margin:0 auto;padding:0 28px}
a{color:inherit}img,svg{max-width:100%}.ringba-number{white-space:nowrap}
h1,h2,h3,p,button{overflow-wrap:break-word}
h1,h2,h3{font-family:var(--fd);font-weight:500;letter-spacing:-.035em;margin:0}
.eyebrow{font:500 12px/1 var(--fb);letter-spacing:.2em;text-transform:uppercase;color:var(--a);display:inline-flex;align-items:center;gap:12px}
.eyebrow:before{content:"";width:24px;height:1px;background:currentColor}

.progress{position:fixed;left:0;top:0;right:0;height:2px;z-index:80;pointer-events:none}
.progress i{display:block;height:100%;background:var(--a);transform:scaleX(0);transform-origin:0 50%}

.nav-wrap{position:fixed;top:14px;left:0;right:0;z-index:70;padding:0 16px;pointer-events:none}
.nav{pointer-events:auto;max-width:1120px;margin:0 auto;height:60px;border-radius:999px;display:flex;align-items:center;justify-content:space-between;padding:0 8px 0 24px;background:rgba(246,244,239,.62);-webkit-backdrop-filter:saturate(1.5) blur(16px);backdrop-filter:saturate(1.5) blur(16px);border:1px solid var(--line);transition:box-shadow .4s var(--ease),background .4s var(--ease),height .4s var(--ease)}
.nav.scrolled{background:rgba(246,244,239,.86);box-shadow:0 12px 32px rgba(21,24,29,.1);height:54px}
.brand{display:inline-flex;align-items:center;min-height:44px;font:600 19px/1 var(--fd);letter-spacing:-.03em;text-decoration:none;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.tel{flex:none;display:inline-flex;align-items:center;gap:8px;background:var(--ink);color:#fff;text-decoration:none;font:500 14px/1 var(--fb);height:44px;padding:0 20px;border-radius:999px;white-space:nowrap;transition:transform .3s var(--ease),background .3s var(--ease)}
.tel:hover{background:var(--a);transform:translateY(-1px)}

.btn{position:relative;overflow:hidden;display:inline-flex;align-items:center;justify-content:center;gap:12px;background:var(--a);color:#fff;text-decoration:none;font:500 17px/1.2 var(--fd);letter-spacing:-.01em;padding:18px 30px;border-radius:999px;transition:transform .35s var(--ease),box-shadow .35s var(--ease)}
.btn:before{content:"";position:absolute;top:0;bottom:0;left:-60%;width:40%;background:linear-gradient(100deg,transparent,rgba(255,255,255,.35),transparent);transform:skewX(-20deg);transition:left .7s var(--ease)}
.btn:hover{transform:translateY(-3px);box-shadow:0 16px 34px color-mix(in srgb,var(--a) 38%,transparent)}.btn:hover:before{left:130%}
.btn:active{transform:translateY(0) scale(.98)}
.btn svg{width:18px;height:18px;flex:none;transition:transform .35s var(--ease)}.btn:hover svg{transform:translateX(5px)}
.btn.ghost{background:transparent;color:var(--ink);box-shadow:inset 0 0 0 1px var(--line)}.btn.ghost:before{display:none}
.btn.ghost:hover{background:var(--ink);color:#fff;box-shadow:none}

.rise{opacity:0;transform:translateY(18px);animation:rise .9s var(--ease) forwards;animation-delay:calc(var(--i,0) * 110ms + 120ms)}
@keyframes rise{to{opacity:1;transform:none}}
.w{display:inline-block;opacity:0;filter:blur(14px);transform:translateY(.3em);animation:wordin 1s var(--ease) forwards;animation-delay:calc(var(--i) * 70ms + 150ms)}
@keyframes wordin{to{opacity:1;filter:blur(0);transform:none}}

.hero{padding:150px 0 72px;position:relative;overflow:hidden}
.hero:before{content:"";position:absolute;width:640px;height:640px;right:-160px;top:-120px;border-radius:50%;background:radial-gradient(circle,color-mix(in srgb,var(--a) 22%,transparent),transparent 65%);filter:blur(30px);pointer-events:none;animation:drift 14s ease-in-out infinite alternate}
@keyframes drift{to{transform:translate(-60px,40px) scale(1.08)}}
.hero-grid{display:grid;grid-template-columns:1.08fr .92fr;gap:56px;align-items:center;position:relative}
h1{font-size:clamp(40px,6vw,78px);line-height:1.04;margin:22px 0 22px;color:var(--ink)}
.sub{font-size:19px;color:var(--mut);max-width:30em;margin:0 0 34px}
.cta-row{display:flex;flex-wrap:wrap;gap:14px}
.media{position:relative}
.slot{--py:0px;aspect-ratio:4/5;border-radius:var(--r);overflow:hidden;position:relative;transform:translateY(var(--py));background:linear-gradient(155deg,var(--canvas2),color-mix(in srgb,var(--p) 14%,var(--canvas2)));display:grid;place-items:center;text-align:center;padding:28px;color:var(--mut);font-size:14px;border:1px solid var(--line)}
.slot img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}
.i{width:1em;height:1em;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex:none}
.hours{display:flex;align-items:center;gap:10px;margin:22px 0 0;color:var(--mut);font-size:15px}.hours .i{font-size:18px;color:var(--a)}
.slot video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}.slot.has-video{aspect-ratio:4/3.1;border:0;background:var(--night);box-shadow:0 40px 80px rgba(7,23,63,.25)}
.navlink{margin:0 8px 0 auto;padding:0 14px;display:inline-flex;align-items:center;min-height:44px;font:500 14px/1 var(--fb);text-decoration:none;color:var(--mut);transition:color .25s var(--ease)}.navlink:hover{color:var(--a)}
.chip{position:absolute;z-index:2;display:inline-flex;align-items:center;gap:10px;background:rgba(255,255,255,.82);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.7);border-radius:999px;padding:11px 18px 11px 14px;font:500 14px/1 var(--fb);box-shadow:0 14px 30px rgba(21,24,29,.12);animation:float 6s ease-in-out infinite}
.chip i{width:9px;height:9px;border-radius:50%;background:var(--a);box-shadow:0 0 0 0 color-mix(in srgb,var(--a) 50%,transparent);animation:ping 2.4s ease-out infinite}
.chip.c1{left:-22px;bottom:15%}.chip.c2{right:-14px;top:12%;animation-delay:-3s}
@keyframes float{50%{transform:translateY(-9px)}}
@keyframes ping{70%,100%{box-shadow:0 0 0 12px transparent}}

.marquee{overflow:hidden;border-block:1px solid var(--line);background:var(--canvas2)}
.track{display:flex;width:max-content;animation:slide 36s linear infinite}
.marquee:hover .track{animation-play-state:paused}
.track span{display:inline-flex;align-items:center;gap:48px;padding:20px 0 20px 48px;font:500 15px/1 var(--fb);letter-spacing:.02em;white-space:nowrap}
.track span:after{content:"";width:6px;height:6px;border-radius:50%;background:var(--a)}
@keyframes slide{to{transform:translateX(-50%)}}

section{padding:112px 0}
.head{margin:0 0 52px;max-width:760px}.head h2{font-size:clamp(32px,4.4vw,56px);line-height:1.06;margin-top:20px}
.reveal{transition:opacity .9s var(--ease),transform .9s var(--ease);transition-delay:calc(var(--i,0) * 100ms)}
.js .reveal{opacity:0;transform:translateY(26px)}.js .reveal.in{opacity:1;transform:none}

.bento{display:grid;grid-template-columns:repeat(12,1fr);gap:18px}
.tile{--mx:50%;--my:50%;position:relative;isolation:isolate;overflow:hidden;border-radius:var(--r);background:var(--card);border:1px solid var(--line);padding:34px;display:flex;flex-direction:column;transition:transform .5s var(--ease),box-shadow .5s var(--ease),border-color .5s var(--ease)}
.tile:before{content:"";position:absolute;inset:0;z-index:-1;opacity:0;transition:opacity .4s var(--ease);background:radial-gradient(420px circle at var(--mx) var(--my),color-mix(in srgb,var(--a) 15%,transparent),transparent 62%)}
.tile:hover{transform:translateY(-5px);box-shadow:0 28px 56px rgba(21,24,29,.1);border-color:rgba(21,24,29,.2)}.tile:hover:before{opacity:1}
.tile .n{font:500 12px/1 var(--fb);letter-spacing:.2em;color:var(--a);margin-bottom:auto}
.tile h3{font-size:clamp(24px,2.6vw,34px);line-height:1.1;margin:44px 0 12px}.tile p{margin:0;color:var(--mut);max-width:28em}
.t1{grid-column:span 7;grid-row:span 2;min-height:520px}.t2{grid-column:span 5;min-height:250px}.t3{grid-column:span 5;min-height:250px}
.t4{grid-column:span 12;background:var(--night);color:#fff;border-color:transparent;flex-direction:row;align-items:center;justify-content:space-between;gap:28px;min-height:150px;padding:30px 38px}
.t4:before{background:radial-gradient(520px circle at var(--mx) var(--my),color-mix(in srgb,var(--a) 34%,transparent),transparent 62%)}
.t4 .eyebrow{color:#fff;opacity:.7}.t4 .big{font:500 clamp(26px,3.6vw,46px)/1.05 var(--fd);letter-spacing:-.035em;margin-top:10px;display:flex;align-items:center;min-height:48px;text-decoration:none;color:#fff}
.t4 .btn{flex:none}
.bars{display:grid;gap:12px;margin:34px 0 0}.bars i{display:block;height:16px;border-radius:999px;background:var(--canvas2);position:relative;overflow:hidden}
.bars i:after{content:"";position:absolute;inset:0;border-radius:inherit;background:var(--c,var(--a));transform-origin:0 50%;transform:scaleX(var(--w));transition:transform 1.4s var(--ease) calc(var(--d) * 1ms)}
.js .reveal:not(.in) .bars i:after{transform:scaleX(0)}
.ring{width:56px;height:56px;border-radius:50%;background:var(--a);display:grid;place-items:center;position:relative;color:#fff;margin-bottom:auto}
.ring svg{width:24px;height:24px;position:relative;z-index:1}
.ring:before,.ring:after{content:"";position:absolute;inset:0;border-radius:50%;border:1.5px solid var(--a);animation:pulse 2.8s ease-out infinite}.ring:after{animation-delay:1.4s}
@keyframes pulse{0%{transform:scale(1);opacity:.7}100%{transform:scale(2.1);opacity:0}}
.checks{list-style:none;margin:0 0 auto;padding:0;display:grid;gap:12px}
.checks li{display:flex;align-items:center;gap:12px;font:500 15px/1.2 var(--fb)}
.checks svg{width:22px;height:22px;flex:none;color:var(--a)}.checks path{stroke-dasharray:24;stroke-dashoffset:0;transition:stroke-dashoffset .8s var(--ease) calc(var(--i) * 140ms + 300ms)}
.js .reveal:not(.in) .checks path{stroke-dashoffset:24}

.tile.has-img{color:#fff;border:0;background:var(--night)}.tile.has-img p{color:rgba(255,255,255,.78)}.tile.has-img .n{color:#fff}
.tile.has-img img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:-2;opacity:.6;transition:transform 1.4s var(--ease)}.tile.has-img:hover img{transform:scale(1.06)}
.tile.has-img:after{content:"";position:absolute;inset:0;z-index:-1;background:linear-gradient(180deg,rgba(7,23,63,.2),rgba(7,23,63,.9))}
.vs{display:grid;grid-template-columns:1fr auto 1fr;align-items:stretch;position:relative}
.panel{border-radius:var(--r);padding:42px;position:relative;overflow:hidden;transition:transform .5s var(--ease),box-shadow .5s var(--ease)}.panel:hover{transform:translateY(-5px);box-shadow:0 30px 60px rgba(21,24,29,.12)}
.panel.good{background:var(--night);color:#fff}.panel.bad{background:#fff;border:1px solid var(--line)}
.panel h3{font-size:clamp(24px,2.6vw,34px);margin-bottom:26px}.panel ul{list-style:none;margin:0 0 34px;padding:0;display:grid;gap:16px}
.panel li{display:flex;align-items:center;gap:14px;font-size:18px;opacity:0;transform:translateX(-14px);transition:opacity .7s var(--ease) calc(var(--n) * 110ms + 300ms),transform .7s var(--ease) calc(var(--n) * 110ms + 300ms)}
.panel.in li{opacity:1;transform:none}.panel li .i{font-size:24px}.panel.good li .i{color:#7fd1ff}.panel.bad li .i{color:#e5484d}
.stat{display:flex;align-items:baseline;gap:14px;border-top:1px solid rgba(128,138,160,.3);padding-top:26px}.stat b{font:500 clamp(56px,7vw,92px)/.9 var(--fd);letter-spacing:-.05em}.panel.bad .stat b{color:#e5484d}
.stat span{color:var(--mut);font-size:16px}.panel.good .stat span{color:rgba(255,255,255,.7)}
.tabs{display:flex;flex-wrap:wrap;gap:4px;margin-top:18px;min-height:20px}.tabs i{width:26px;height:16px;border-radius:5px 5px 0 0;background:var(--canvas2);border:1px solid var(--line);animation:tabin .35s var(--ease) both}@keyframes tabin{from{opacity:0;transform:translateY(8px) scale(.7)}}
.vsbadge{align-self:center;z-index:2;width:78px;height:78px;margin:0 -39px;border-radius:50%;background:var(--a);color:#fff;display:grid;place-items:center;font:600 22px var(--fd);box-shadow:0 14px 34px color-mix(in srgb,var(--a) 40%,transparent);animation:float 5s ease-in-out infinite}
.pbar{background:var(--night);color:#fff;border-radius:var(--r);padding:48px 52px;display:flex;gap:32px;align-items:center;justify-content:space-between}
.pbar .eyebrow{color:#fff;opacity:.7}.pbar h2{font-size:clamp(26px,3.4vw,42px);margin:14px 0 10px;line-height:1.08}.pbar p{margin:0;color:rgba(255,255,255,.72);max-width:34em}
.btn.light{background:#fff;color:var(--night)}.btn.light:hover{box-shadow:0 16px 34px rgba(255,255,255,.22)}
.how{padding-bottom:40px}
.stack{padding-bottom:10vh}
.scard{--s:1;position:sticky;top:calc(96px + var(--k) * 22px);margin:0 0 26px;border-radius:var(--r);padding:48px 52px;min-height:360px;display:grid;grid-template-columns:auto 1fr auto;gap:52px;align-items:center;border:1px solid var(--line);transform:scale(var(--s));transform-origin:50% 0;will-change:transform;box-shadow:0 -18px 40px rgba(21,24,29,.05)}
.scard.k0{background:var(--card)}.scard.k1{background:var(--canvas2)}.scard.k2{background:var(--night);color:#fff;border-color:transparent}
.scard .num{font:500 clamp(84px,13vw,180px)/.85 var(--fd);letter-spacing:-.06em;color:var(--a)}
.scard h3{font-size:clamp(26px,3.2vw,42px);line-height:1.08;margin:0 0 14px}.scard p{margin:0;font-size:18px;color:var(--mut);max-width:26em}.scard.k2 p{color:rgba(255,255,255,.72)}
.scard .ico{width:92px;height:92px;color:var(--a);flex:none}.scard .ico path,.scard .ico circle,.scard .ico rect{stroke-dasharray:100;stroke-dashoffset:0;transition:stroke-dashoffset 1.5s var(--ease) .2s}
.js .scard .ico:not(.in) path,.js .scard .ico:not(.in) circle,.js .scard .ico:not(.in) rect{stroke-dashoffset:100}

.night{background:var(--night);color:#fff;border-radius:44px;margin:0 14px;position:relative;overflow:hidden;padding:120px 0}
.night:before{content:"";position:absolute;width:760px;height:760px;left:-200px;bottom:-320px;border-radius:50%;background:radial-gradient(circle,color-mix(in srgb,var(--a) 30%,transparent),transparent 65%);filter:blur(24px);pointer-events:none;animation:drift 16s ease-in-out infinite alternate}
.night .wrap{position:relative;display:grid;grid-template-columns:1.1fr .9fr;gap:64px;align-items:center}
.night .eyebrow{color:#fff;opacity:.75}
.night h2{font-size:clamp(34px,5vw,64px);line-height:1.04;margin:22px 0 26px}
.night .lead{color:rgba(255,255,255,.72);font-size:18px;max-width:28em;margin:0 0 34px}
.bigphone{display:inline-block;font:500 clamp(34px,5.4vw,70px)/1 var(--fd);letter-spacing:-.04em;text-decoration:none;color:#fff;background:linear-gradient(currentColor,currentColor) 0 100%/0 2px no-repeat;padding-bottom:8px;transition:background-size .5s var(--ease)}
.bigphone:hover{background-size:100% 2px}
.glass{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);border-radius:var(--r);padding:34px;-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px)}
.glass h3{font-size:24px;margin:0 0 20px}
form input{width:100%;height:54px;padding:0 18px;margin:0 0 12px;border-radius:14px;border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.06);color:#fff;font:400 16px var(--fb);transition:border-color .25s var(--ease),background .25s var(--ease),box-shadow .25s var(--ease)}
form input::placeholder{color:rgba(255,255,255,.55)}
form input:focus{outline:none;border-color:var(--a);background:rgba(255,255,255,.1);box-shadow:0 0 0 4px color-mix(in srgb,var(--a) 28%,transparent)}
form button{width:100%;height:56px;border:0;border-radius:999px;background:var(--a);color:#fff;font:500 17px var(--fd);cursor:pointer;transition:transform .3s var(--ease),box-shadow .3s var(--ease)}
form button:hover{transform:translateY(-2px);box-shadow:0 14px 30px color-mix(in srgb,var(--a) 40%,transparent)}form button:active{transform:scale(.98)}
.thanks{font-size:18px;margin:0}

.faq .wrap{display:grid;grid-template-columns:.8fr 1.2fr;gap:72px}
.faq .head{margin:0;position:sticky;top:110px;align-self:start}
.qa{border-bottom:1px solid var(--line)}.qa:first-child{border-top:1px solid var(--line)}
.q{width:100%;min-height:72px;display:flex;align-items:center;justify-content:space-between;gap:20px;background:none;border:0;padding:0;text-align:left;cursor:pointer;color:var(--ink);font:500 clamp(18px,1.8vw,22px)/1.3 var(--fd);letter-spacing:-.02em;transition:color .25s var(--ease),padding .35s var(--ease)}
.q:hover{color:var(--a);padding-left:8px}
.q i{position:relative;width:22px;height:22px;flex:none}.q i:before,.q i:after{content:"";position:absolute;left:50%;top:50%;width:14px;height:2px;margin:-1px 0 0 -7px;background:currentColor;transition:transform .4s var(--ease)}
.q i:after{transform:rotate(90deg)}.qa.open .q i:after{transform:rotate(0)}
.a{display:grid;grid-template-rows:0fr;transition:grid-template-rows .5s var(--ease)}.qa.open .a{grid-template-rows:1fr}
.a>div{overflow:hidden}.a p{margin:0 0 24px;color:var(--mut);max-width:34em}

footer{padding:72px 0 40px;font-size:14px;color:var(--mut)}
footer .links{display:flex;flex-wrap:wrap;gap:0 26px;margin:0 0 20px}
footer a{display:inline-block;padding:13px 0;color:var(--ink);text-decoration:none;background:linear-gradient(currentColor,currentColor) 0 calc(100% - 10px)/0 1px no-repeat;transition:background-size .35s var(--ease)}
footer a:hover{background-size:100% 1px}footer p{max-width:62em;margin:0}
.callbar{display:none}

@media(max-width:1000px){
  .vs{grid-template-columns:1fr;gap:14px}.vsbadge{margin:-30px auto;width:64px;height:64px}.pbar{flex-direction:column;align-items:flex-start;padding:36px}.navlink{display:none}
  .hero-grid,.night .wrap,.faq .wrap{grid-template-columns:1fr;gap:44px}
  .hero{padding:124px 0 56px}.slot{aspect-ratio:16/11}.chip.c1{left:12px}.chip.c2{right:12px}
  .t1,.t2,.t3{grid-column:span 12;min-height:0}.t1{grid-row:auto;min-height:420px}
  .scard{grid-template-columns:auto 1fr;padding:36px;gap:32px}.scard .ico{display:none}
  .faq .head{position:static}section{padding:84px 0}
}
@media(max-width:640px){
  .panel{padding:28px}.pbar{padding:28px 24px}.pbar .btn{width:100%}
  .wrap{padding:0 20px}.nav{height:56px;padding-left:18px}.nav.scrolled{height:52px}.brand{font-size:17px}.tel{height:42px;padding:0 16px}
  .hero{padding:104px 0 44px}h1{margin:18px 0}.sub{font-size:17px;margin-bottom:26px}
  .cta-row .btn{width:100%}.chip{font-size:13px;padding:9px 14px 9px 12px}
  section{padding:64px 0}.head{margin-bottom:34px}
  .tile{padding:26px}.t1{min-height:380px}.t4{flex-direction:column;align-items:stretch;padding:26px}.t4 .btn{width:100%}
  .scard{grid-template-columns:1fr;gap:6px;padding:28px 26px;min-height:300px;top:calc(76px + var(--k) * 14px);align-content:center}
  .scard .num{font-size:76px}.scard p{font-size:16px}
  .night{margin:0 8px;border-radius:32px;padding:80px 0}.glass{padding:24px}
  .q{min-height:64px}.q:hover{padding-left:0}
  .callbar{display:flex;position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom));z-index:75;transform:translateY(150%);transition:transform .5s var(--ease)}
  .callbar.show{transform:none}.callbar a{width:100%;box-shadow:0 14px 32px rgba(21,24,29,.3)}
  body{padding-bottom:84px}
}
@media(prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}*,*:before,*:after{animation:none!important;transition:none!important}
  .rise,.w,.js .reveal,.panel li{opacity:1!important;transform:none!important;filter:none!important}
  .scard{position:relative;top:auto}
}
</style>
$ringba
$everflow
</head><body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs><symbol id="i-check" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M8 12.5l3 3 5-6"/></symbol><symbol id="i-x" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/></symbol><symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></symbol></defs></svg>
<div class="progress"><i></i></div>
<header class="nav-wrap"><div class="nav"><a class="brand" href="#top">$name</a>$navextra<a class="tel" href="tel:$telhref">Call <span class="ringba-number">$phone</span></a></div></header>
<main id="top">
<section class="hero"><div class="wrap hero-grid"><div>
<span class="eyebrow rise" style="--i:0">$eyebrow</span>
<h1 aria-label="$hero_plain">$hero</h1>
<p class="sub rise" style="--i:5">$sub</p>
<div class="cta-row rise" style="--i:6"><a class="btn" href="tel:$telhref"><span>$cta: <span class="ringba-number">$phone</span></span><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10h12M11 5l5 5-5 5"/></svg></a><a class="btn ghost" href="#how">See how it works</a></div>
$hours_html
</div><div class="media rise" style="--i:3">$photo<span class="chip c1"><i></i>$chip1</span><span class="chip c2"><i></i>$chip2</span></div></div></section>

<div class="marquee" aria-hidden="true"><div class="track">$marquee</div></div>
$compare

<section><div class="wrap"><div class="head"><span class="eyebrow reveal">Why people call</span><h2 class="reveal" style="--i:1">$bento_title</h2></div>
<div class="bento">
<article class="tile t1 reveal"><span class="n">01</span><div class="bars" aria-hidden="true"><i style="--w:.86;--d:200"></i><i style="--w:.64;--d:350;--c:var(--p)"></i><i style="--w:.44;--d:500;--c:var(--p)"></i></div><h3>$b0t</h3><p>$b0b</p></article>
<article class="tile t2 $t2cls reveal" style="--i:1">$t2img<span class="ring" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.2a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/></svg></span><h3>$b1t</h3><p>$b1b</p></article>
<article class="tile t3 reveal" style="--i:2"><ul class="checks">$checks</ul><h3>$b2t</h3><p>$b2b</p></article>
<article class="tile t4 reveal" style="--i:3"><div><span class="eyebrow">Prefer to talk?</span><a class="big" href="tel:$telhref"><span class="ringba-number">$phone</span></a></div><a class="btn" href="tel:$telhref"><span>$cta</span><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10h12M11 5l5 5-5 5"/></svg></a></article>
</div></div></section>

<section class="how" id="how"><div class="wrap"><div class="head"><span class="eyebrow reveal">How it works</span><h2 class="reveal" style="--i:1">$steps_title</h2></div>
<div class="stack">$steps</div></div></section>

<section class="night"><div class="wrap"><div>
<span class="eyebrow">Speak with a person</span>
<h2>$offer_h</h2>
<p class="lead">$lead</p>
<a class="bigphone" href="tel:$telhref"><span class="ringba-number">$phone</span></a>
</div><div class="glass"><h3>Leave your details</h3>
<form id="lead-form"><input name="name" placeholder="Your name" autocomplete="name" required><input name="phone" placeholder="Best phone number" autocomplete="tel" inputmode="tel" required><input name="zip" placeholder="ZIP code" autocomplete="postal-code" inputmode="numeric" required>
<input type="hidden" name="click_id" data-track="_ef_transaction_id"><input type="hidden" name="sub1" data-track="sub1"><input type="hidden" name="affid" data-track="affid">
<button type="submit">$cta</button></form></div></div></section>

$partners
<section class="faq"><div class="wrap"><div class="head"><span class="eyebrow reveal">Questions</span><h2 class="reveal" style="--i:1">Common questions</h2></div><div>$faq</div></div></section>
</main>
<footer><div class="wrap"><div class="links">$links</div><p>&copy; $year $legal. $name is a marketing site that connects consumers with licensed professionals and partners. See our Marketing Partners page for details.$disclaimer</p></div></footer>
<div class="callbar"><a class="btn" href="tel:$telhref"><span>Call <span class="ringba-number">$phone</span></span></a></div>
<script>$tracking</script>
<script>$motion</script>
</body></html>""")

LEGAL_PAGE = Template("""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>$title | $name</title>
$fonts
<style>
:root{--p:$primary;--a:$accent;--ink:#15181d;--mut:#5d6470;--canvas:#f6f4ef;--line:rgba(21,24,29,.1);--ease:cubic-bezier(.2,.7,.2,1)}
*{box-sizing:border-box}body{margin:0;background:var(--canvas);color:var(--ink);font:400 17px/1.7 Inter,system-ui,Segoe UI,Arial,sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:760px;margin:0 auto;padding:28px 24px 96px}
.back{display:inline-flex;align-items:center;min-height:44px;margin-bottom:28px;font:500 14px Inter,sans-serif;color:var(--mut);text-decoration:none;transition:color .25s var(--ease),transform .25s var(--ease)}.back:hover{color:var(--a);transform:translateX(-3px)}
h1{font:500 clamp(34px,6vw,54px)/1.05 Poppins,Inter,sans-serif;letter-spacing:-.035em;margin:0 0 8px;overflow-wrap:break-word}
h2{font:500 22px/1.25 Poppins,Inter,sans-serif;letter-spacing:-.02em;margin:40px 0 8px}
p{margin:0 0 14px;color:#2a2f37}.upd{color:var(--mut);font-size:14px;margin-bottom:34px}
.draft{background:#fff3d6;border:1px solid #e6c46a;padding:12px 16px;border-radius:14px;font-size:14px;margin:0 0 28px}
a{color:var(--a)}
</style></head><body><div class="wrap">
<a class="back" href="index.html">&larr; $name</a>$banner<h1>$title</h1><p class="upd">Last updated $date</p>$body</div></body></html>""")
