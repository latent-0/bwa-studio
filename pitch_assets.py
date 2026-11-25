CSS = r""":root{--a:#0b5ed7;--p:#0a2a6b;--hot:#ff8a00;--ink:#101828;--mut:#5b6678;--canvas:#f5f7fb;--canvas2:#e8edf6;--card:#fff;--line:rgba(16,24,40,.1);
--night:#07173f;--ease:cubic-bezier(.2,.7,.2,1);--r:28px;--fd:Poppins,Inter,system-ui,Segoe UI,Arial,sans-serif;--fb:Inter,system-ui,Segoe UI,Arial,sans-serif}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font:400 17px/1.6 var(--fb);color:var(--ink);background:var(--canvas);-webkit-font-smoothing:antialiased}
.wrap{max-width:1200px;margin:0 auto;padding:0 28px}a{color:inherit}img,svg,video{max-width:100%}.ringba-number{white-space:nowrap}
h1,h2,h3,p,button,li{overflow-wrap:break-word}h1,h2,h3{font-family:var(--fd);font-weight:500;letter-spacing:-.035em;margin:0}
.i{width:1em;height:1em;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex:none}
.eyebrow{font:500 12px/1 var(--fb);letter-spacing:.2em;text-transform:uppercase;color:var(--a);display:inline-flex;align-items:center;gap:12px}.eyebrow:before{content:"";width:24px;height:1px;background:currentColor}

.progress{position:fixed;left:0;top:0;right:0;height:2px;z-index:90;pointer-events:none}.progress i{display:block;height:100%;background:var(--hot);transform:scaleX(0);transform-origin:0 50%}
.nav-wrap{position:fixed;top:14px;left:0;right:0;z-index:80;padding:0 16px;pointer-events:none}
.nav{pointer-events:auto;max-width:1120px;margin:0 auto;height:60px;border-radius:999px;display:flex;align-items:center;justify-content:space-between;padding:0 8px 0 20px;background:rgba(245,247,251,.64);-webkit-backdrop-filter:saturate(1.5) blur(16px);backdrop-filter:saturate(1.5) blur(16px);border:1px solid var(--line);transition:box-shadow .4s var(--ease),background .4s var(--ease),height .4s var(--ease)}
.nav.scrolled{background:rgba(245,247,251,.88);box-shadow:0 12px 32px rgba(16,24,40,.1);height:54px}
.brand{display:inline-flex;align-items:center;gap:10px;min-height:44px;font:600 19px/1 var(--fd);letter-spacing:-.03em;text-decoration:none;white-space:nowrap;min-width:0}
.brand .logo{width:32px;height:32px;border-radius:10px;background:var(--a);color:#fff;display:grid;place-items:center;font-size:18px;transition:transform .5s var(--ease)}.brand:hover .logo{transform:rotate(-12deg) scale(1.08)}
.tel{flex:none;display:inline-flex;align-items:center;gap:8px;background:var(--a);color:#fff;text-decoration:none;font:500 14px/1 var(--fb);height:44px;padding:0 20px;border-radius:999px;white-space:nowrap;transition:transform .3s var(--ease),background .3s var(--ease)}.tel:hover{background:var(--p);transform:translateY(-1px)}

.btn{position:relative;overflow:hidden;display:inline-flex;align-items:center;justify-content:center;gap:12px;background:var(--a);color:#fff;text-decoration:none;font:500 17px/1.2 var(--fd);letter-spacing:-.01em;padding:18px 30px;border-radius:999px;border:0;cursor:pointer;transition:transform .35s var(--ease),box-shadow .35s var(--ease)}
.btn:before{content:"";position:absolute;top:0;bottom:0;left:-60%;width:40%;background:linear-gradient(100deg,transparent,rgba(255,255,255,.38),transparent);transform:skewX(-20deg);transition:left .7s var(--ease)}
.btn:hover{transform:translateY(-3px);box-shadow:0 16px 34px rgba(11,94,215,.38)}.btn:hover:before{left:130%}.btn:active{transform:scale(.98)}
.btn .i{font-size:20px}.btn .arr{transition:transform .35s var(--ease)}.btn:hover .arr{transform:translateX(5px)}
.btn.ghost{background:transparent;color:var(--ink);box-shadow:inset 0 0 0 1px var(--line)}.btn.ghost:before{display:none}.btn.ghost:hover{background:var(--ink);color:#fff;box-shadow:none}
.btn.light{background:#fff;color:var(--p)}.btn.light:hover{box-shadow:0 16px 34px rgba(255,255,255,.25)}

.rise{opacity:0;transform:translateY(18px);animation:rise .9s var(--ease) forwards;animation-delay:calc(var(--i,0) * 110ms + 120ms)}@keyframes rise{to{opacity:1;transform:none}}
.w{display:inline-block;opacity:0;filter:blur(14px);transform:translateY(.3em);animation:wordin 1s var(--ease) forwards;animation-delay:calc(var(--i) * 80ms + 150ms)}@keyframes wordin{to{opacity:1;filter:blur(0);transform:none}}
.reveal{transition:opacity .9s var(--ease),transform .9s var(--ease);transition-delay:calc(var(--i,0) * 100ms)}.js .reveal{opacity:0;transform:translateY(26px)}.js .reveal.in{opacity:1;transform:none}

.hero{padding:150px 0 76px;position:relative;overflow:hidden}
.hero:before{content:"";position:absolute;width:700px;height:700px;right:-200px;top:-160px;border-radius:50%;background:radial-gradient(circle,rgba(11,94,215,.22),transparent 65%);filter:blur(30px);pointer-events:none;animation:drift 14s ease-in-out infinite alternate}
@keyframes drift{to{transform:translate(-60px,40px) scale(1.08)}}
.hero-grid{display:grid;grid-template-columns:1.05fr .95fr;gap:56px;align-items:center;position:relative}
h1{font-size:clamp(42px,6.4vw,84px);line-height:1.02;margin:22px 0 18px}h1 em{font-style:normal;color:var(--a)}
.kicker{font:500 clamp(18px,2vw,24px)/1.3 var(--fd);letter-spacing:-.02em;margin:0 0 26px}
.points{list-style:none;margin:0 0 34px;padding:0;display:grid;gap:14px}
.points li{display:flex;gap:14px;align-items:flex-start;font-size:18px}.points b{font-weight:600}.points .i{font-size:26px;color:var(--a);margin-top:1px}
.points li span{color:var(--mut)}
.cta-row{display:flex;flex-wrap:wrap;gap:14px}
.media{position:relative}.hero-grid.solo{grid-template-columns:1fr;max-width:880px}.hero-grid.solo h1{max-width:14em}
.vid{--py:0px;position:relative;aspect-ratio:4/3.1;border-radius:var(--r);overflow:hidden;background:linear-gradient(150deg,#12327a,#0a2a6b 55%,#0b5ed7);transform:translateY(var(--py));box-shadow:0 40px 80px rgba(7,23,63,.28)}
.vid video,.vid .fallback{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}
.fallback{display:grid;place-items:center;color:rgba(255,255,255,.55);font-size:14px;text-align:center;padding:30px}.fallback .i{font-size:96px;opacity:.35;display:block;margin:0 auto 12px}
.play{position:absolute;left:50%;top:50%;width:92px;height:92px;margin:-46px 0 0 -46px;border:0;border-radius:50%;background:rgba(255,255,255,.94);color:var(--a);display:grid;place-items:center;cursor:pointer;transition:transform .4s var(--ease),background .3s;z-index:3}
.play:hover{transform:scale(1.1)}.play svg{width:34px;height:34px;margin-left:5px;fill:currentColor}
.play:before,.play:after{content:"";position:absolute;inset:0;border-radius:50%;border:2px solid rgba(255,255,255,.7);animation:pulse 2.8s ease-out infinite}.play:after{animation-delay:1.4s}
@keyframes pulse{0%{transform:scale(1);opacity:.8}100%{transform:scale(1.9);opacity:0}}
.vid.playing .play{opacity:0;pointer-events:none}
.chip{position:absolute;z-index:4;display:inline-flex;align-items:center;gap:10px;background:rgba(255,255,255,.88);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.7);border-radius:999px;padding:11px 18px 11px 14px;font:500 14px/1 var(--fb);box-shadow:0 14px 30px rgba(16,24,40,.14);animation:float 6s ease-in-out infinite}
.chip .i{color:var(--a);font-size:18px}.chip.c1{left:-22px;bottom:14%}.chip.c2{right:-14px;top:10%;animation-delay:-3s}@keyframes float{50%{transform:translateY(-9px)}}

.marquee{overflow:hidden;border-block:1px solid var(--line);background:var(--canvas2)}.track{display:flex;width:max-content;animation:slide 34s linear infinite}.marquee:hover .track{animation-play-state:paused}
.track span{display:inline-flex;align-items:center;gap:48px;padding:20px 0 20px 48px;font:500 14px/1 var(--fb);letter-spacing:.12em;text-transform:uppercase;white-space:nowrap}.track span:after{content:"";width:6px;height:6px;border-radius:50%;background:var(--hot)}@keyframes slide{to{transform:translateX(-50%)}}

section{padding:112px 0}.head{margin:0 0 52px;max-width:780px}.head h2{font-size:clamp(32px,4.6vw,58px);line-height:1.05;margin-top:20px}.head p{color:var(--mut);margin:18px 0 0;font-size:18px}

.vs{display:grid;grid-template-columns:1fr auto 1fr;gap:0;align-items:stretch;position:relative}
.panel{border-radius:var(--r);padding:42px;position:relative;overflow:hidden;transition:transform .5s var(--ease),box-shadow .5s var(--ease)}.panel:hover{transform:translateY(-5px);box-shadow:0 30px 60px rgba(16,24,40,.12)}
.panel.good{background:var(--night);color:#fff}.panel.bad{background:#fff;border:1px solid var(--line)}
.panel h3{font-size:clamp(24px,2.6vw,34px);margin-bottom:26px}.panel.good h3{color:#fff}
.panel ul{list-style:none;margin:0 0 34px;padding:0;display:grid;gap:16px}
.panel li{display:flex;align-items:center;gap:14px;font-size:18px;opacity:0;transform:translateX(-14px);transition:opacity .7s var(--ease) calc(var(--n) * 110ms + 300ms),transform .7s var(--ease) calc(var(--n) * 110ms + 300ms)}
.panel.in li{opacity:1;transform:none}.no-js .panel li,.panel li{}
.panel li .i{font-size:24px}.panel.good li .i{color:#5cc8ff}.panel.bad li .i{color:#e5484d}
.stat{display:flex;align-items:baseline;gap:14px;border-top:1px solid rgba(128,138,160,.3);padding-top:26px}.stat b{font:500 clamp(56px,7vw,92px)/.9 var(--fd);letter-spacing:-.05em}.panel.good .stat b{color:#fff}.panel.bad .stat b{color:#e5484d}
.stat span{color:var(--mut);font-size:16px}.panel.good .stat span{color:rgba(255,255,255,.7)}
.tabs{display:flex;flex-wrap:wrap;gap:4px;margin-top:18px;min-height:20px}.tabs i{width:26px;height:16px;border-radius:5px 5px 0 0;background:var(--canvas2);border:1px solid var(--line);animation:tabin .35s var(--ease) both}@keyframes tabin{from{opacity:0;transform:translateY(8px) scale(.7)}}
.vsbadge{align-self:center;z-index:2;width:78px;height:78px;margin:0 -39px;border-radius:50%;background:var(--hot);color:#fff;display:grid;place-items:center;font:600 22px var(--fd);box-shadow:0 14px 34px rgba(255,138,0,.4);animation:float 5s ease-in-out infinite}

.bento{display:grid;grid-template-columns:repeat(12,1fr);gap:18px}
.tile{--mx:50%;--my:50%;position:relative;isolation:isolate;overflow:hidden;border-radius:var(--r);background:var(--card);border:1px solid var(--line);padding:32px;display:flex;flex-direction:column;justify-content:flex-end;min-height:240px;transition:transform .5s var(--ease),box-shadow .5s var(--ease),border-color .5s var(--ease)}
.tile:before{content:"";position:absolute;inset:0;z-index:-1;opacity:0;transition:opacity .4s var(--ease);background:radial-gradient(420px circle at var(--mx) var(--my),rgba(11,94,215,.16),transparent 62%)}
.tile:hover{transform:translateY(-5px);box-shadow:0 28px 56px rgba(16,24,40,.12);border-color:rgba(16,24,40,.2)}.tile:hover:before{opacity:1}
.tile .ic{width:56px;height:56px;border-radius:18px;background:rgba(11,94,215,.1);color:var(--a);display:grid;place-items:center;font-size:28px;margin-bottom:auto;transition:transform .5s var(--ease),background .4s,color .4s}
.tile:hover .ic{transform:rotate(-8deg) scale(1.1);background:var(--a);color:#fff}
.tile h3{font-size:clamp(22px,2.3vw,30px);line-height:1.1;margin:30px 0 8px}.tile p{margin:0;color:var(--mut);max-width:26em}
.t1{grid-column:span 5;grid-row:span 2;min-height:500px}.t2{grid-column:span 7;color:#fff;border:0;background:var(--night)}.t3{grid-column:span 4}.t4{grid-column:span 3}.t5,.t6,.t7{grid-column:span 4}
.t7{background:var(--a);color:#fff;border:0}.t7 p{color:rgba(255,255,255,.8)}.t7 .ic{background:rgba(255,255,255,.18);color:#fff}
.t2 p{color:rgba(255,255,255,.75)}.t2 .ic{background:rgba(255,255,255,.14);color:#fff}
.t2 img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:-2;opacity:.55;transition:transform 1.4s var(--ease)}.t2:hover img{transform:scale(1.06)}.t2:after{content:"";position:absolute;inset:0;z-index:-1;background:linear-gradient(180deg,rgba(7,23,63,.25),rgba(7,23,63,.92))}
.t1 .big{position:absolute;right:-30px;top:30px;font-size:260px;color:rgba(11,94,215,.08);transition:transform .8s var(--ease)}.t1:hover .big{transform:rotate(-6deg) scale(1.06)}
.ring{position:relative;width:64px;height:64px;border-radius:50%;background:var(--a);color:#fff;display:grid;place-items:center;font-size:30px;margin-bottom:auto}.ring:before,.ring:after{content:"";position:absolute;inset:0;border-radius:50%;border:1.5px solid var(--a);animation:pulse 2.8s ease-out infinite}.ring:after{animation-delay:1.4s}

.stack{padding-bottom:10vh}
.scard{--s:1;position:sticky;top:calc(96px + var(--k) * 22px);margin:0 0 24px;border-radius:var(--r);padding:44px 52px;min-height:300px;display:grid;grid-template-columns:auto 1fr auto;gap:48px;align-items:center;border:1px solid var(--line);transform:scale(var(--s));transform-origin:50% 0;will-change:transform;box-shadow:0 -18px 40px rgba(16,24,40,.05);background:var(--card)}
.scard:nth-child(even){background:var(--canvas2)}.scard.last{background:var(--a);color:#fff;border-color:transparent}
.scard .num{font:500 clamp(80px,12vw,160px)/.85 var(--fd);letter-spacing:-.06em;color:var(--a)}.scard.last .num{color:#fff}
.scard h3{font-size:clamp(26px,3.2vw,42px);line-height:1.08;margin:0 0 12px}.scard p{margin:0;font-size:18px;color:var(--mut);max-width:26em}.scard.last p{color:rgba(255,255,255,.85)}
.scard .ico{font-size:84px;color:var(--a)}.scard.last .ico{color:#fff}.scard .ico .i{stroke-width:1.2;stroke-dasharray:140;stroke-dashoffset:0;transition:stroke-dashoffset 1.6s var(--ease) .2s}
.js .scard:not(.in) .ico .i{stroke-dashoffset:140}

.free{background:var(--night);color:#fff;border-radius:44px;margin:0 14px;position:relative;overflow:hidden;padding:120px 0}
.free:before{content:"";position:absolute;width:760px;height:760px;left:-200px;bottom:-320px;border-radius:50%;background:radial-gradient(circle,rgba(11,94,215,.5),transparent 65%);filter:blur(24px);pointer-events:none;animation:drift 16s ease-in-out infinite alternate}
.free .wrap{position:relative;display:grid;grid-template-columns:1.05fr .95fr;gap:64px;align-items:center}.free .eyebrow{color:#fff;opacity:.75}
.free h2{font-size:clamp(34px,5vw,64px);line-height:1.04;margin:22px 0 22px}.free .lead{color:rgba(255,255,255,.75);font-size:19px;max-width:30em;margin:0 0 34px}.free .lead b{color:#fff;font-weight:600}
.nos{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.no{display:flex;align-items:center;gap:14px;padding:22px;border-radius:22px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);font:500 17px/1.2 var(--fd);letter-spacing:-.02em;transition:transform .4s var(--ease),background .4s}
.no:hover{transform:translateY(-4px);background:rgba(255,255,255,.12)}.no .i{font-size:30px;color:#5cc8ff}

.close .box{border-radius:44px;background:linear-gradient(135deg,var(--a),var(--p));color:#fff;padding:72px;display:grid;grid-template-columns:1.1fr .9fr;gap:56px;align-items:center;position:relative;overflow:hidden}
.close h2{font-size:clamp(34px,5vw,62px);line-height:1.04;margin:0 0 18px}.close p{margin:0 0 30px;color:rgba(255,255,255,.82);font-size:19px}.close h2 em{font-style:normal;color:#ffd08a}
.bigphone{display:inline-block;font:500 clamp(34px,5vw,64px)/1 var(--fd);letter-spacing:-.04em;text-decoration:none;color:#fff;background:linear-gradient(currentColor,currentColor) 0 100%/0 2px no-repeat;padding-bottom:8px;transition:background-size .5s var(--ease)}.bigphone:hover{background-size:100% 2px}
.glass{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:var(--r);padding:30px;-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px)}.glass h3{font-size:22px;margin:0 0 18px}
form input{width:100%;height:54px;padding:0 18px;margin:0 0 12px;border-radius:14px;border:1px solid rgba(255,255,255,.25);background:rgba(255,255,255,.08);color:#fff;font:400 16px var(--fb);transition:border-color .25s,background .25s,box-shadow .25s}
form input::placeholder{color:rgba(255,255,255,.65)}form input:focus{outline:none;border-color:#fff;background:rgba(255,255,255,.14);box-shadow:0 0 0 4px rgba(255,255,255,.18)}
form button{width:100%;height:56px}

.faq .wrap{display:grid;grid-template-columns:.8fr 1.2fr;gap:72px}.faq .head{margin:0;position:sticky;top:110px;align-self:start}
.qa{border-bottom:1px solid var(--line)}.qa:first-child{border-top:1px solid var(--line)}
.q{width:100%;min-height:72px;display:flex;align-items:center;justify-content:space-between;gap:20px;background:none;border:0;padding:0;text-align:left;cursor:pointer;color:var(--ink);font:500 clamp(18px,1.8vw,22px)/1.3 var(--fd);letter-spacing:-.02em;transition:color .25s,padding .35s var(--ease)}
.q:hover{color:var(--a);padding-left:8px}.q i{position:relative;width:22px;height:22px;flex:none}.q i:before,.q i:after{content:"";position:absolute;left:50%;top:50%;width:14px;height:2px;margin:-1px 0 0 -7px;background:currentColor;transition:transform .4s var(--ease)}
.q i:after{transform:rotate(90deg)}.qa.open .q i:after{transform:rotate(0)}.a{display:grid;grid-template-rows:0fr;transition:grid-template-rows .5s var(--ease)}.qa.open .a{grid-template-rows:1fr}.a>div{overflow:hidden}.a p{margin:0 0 24px;color:var(--mut);max-width:34em}

footer{padding:72px 0 40px;font-size:14px;color:var(--mut)}footer .links{display:flex;flex-wrap:wrap;gap:0 26px;margin:0 0 20px}
footer a{display:inline-block;padding:13px 0;color:var(--ink);text-decoration:none;background:linear-gradient(currentColor,currentColor) 0 calc(100% - 10px)/0 1px no-repeat;transition:background-size .35s var(--ease)}footer a:hover{background-size:100% 1px}footer p{max-width:62em;margin:0 0 10px}
.callbar{display:none}

@media(max-width:1000px){
 .hero-grid,.free .wrap,.faq .wrap,.close .box{grid-template-columns:1fr;gap:44px}.hero{padding:124px 0 56px}.chip.c1{left:12px}.chip.c2{right:12px}
 .vs{grid-template-columns:1fr;gap:14px}.vsbadge{margin:-30px auto;width:64px;height:64px}
 .t1,.t2,.t3,.t4,.t5,.t6,.t7{grid-column:span 12;min-height:0}.t1{grid-row:auto;min-height:380px}.t2{min-height:300px}
 .scard{grid-template-columns:auto 1fr;padding:36px;gap:32px}.scard .ico{display:none}.faq .head{position:static}section{padding:84px 0}.close .box{padding:44px}
}
@media(max-width:640px){
 .wrap{padding:0 20px}.nav{height:56px;padding-left:14px}.nav.scrolled{height:52px}.brand{font-size:16px}.tel{height:42px;padding:0 16px}
 .hero{padding:104px 0 44px}.points li{font-size:16px}.cta-row .btn{width:100%}.chip{font-size:13px;padding:9px 14px 9px 12px}section{padding:64px 0}.head{margin-bottom:34px}
 .panel{padding:28px}.tile{padding:26px}.t1{min-height:340px}.t1 .big{font-size:180px}
 .scard{grid-template-columns:1fr;gap:6px;padding:28px 26px;min-height:250px;top:calc(76px + var(--k) * 14px);align-content:center}.scard .num{font-size:70px}.scard p{font-size:16px}
 .free,.close .box{border-radius:32px}.free{margin:0 8px;padding:80px 0}.nos{grid-template-columns:1fr}.close .box{padding:30px 24px}.glass{padding:22px}.q{min-height:64px}.q:hover{padding-left:0}
 .callbar{display:flex;position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom));z-index:75;transform:translateY(150%);transition:transform .5s var(--ease)}.callbar.show{transform:none}.callbar a{width:100%;box-shadow:0 14px 32px rgba(16,24,40,.3)}body{padding-bottom:84px}
}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*:before,*:after{animation:none!important;transition:none!important}.rise,.w,.js .reveal,.panel li{opacity:1!important;transform:none!important;filter:none!important}.scard{position:relative;top:auto}}"""
SPRITE = r"""<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<symbol id="i-check" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M8 12.5l3 3 5-6"/></symbol>
<symbol id="i-x" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/></symbol>
<symbol id="i-phone" viewBox="0 0 24 24"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.2a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/></symbol>
<symbol id="i-plane" viewBox="0 0 24 24"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/></symbol>
<symbol id="i-person" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/></symbol>
<symbol id="i-search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></symbol>
<symbol id="i-dollar" viewBox="0 0 24 24"><path d="M12 2v20"/><path d="M17 6.5C16 5 14.2 4.5 12 4.5c-2.8 0-4.5 1.2-4.5 3s1.7 2.6 4.5 3.2 4.5 1.4 4.5 3.3-1.7 3-4.5 3c-2.4 0-4.2-.7-5.2-2.2"/></symbol>
<symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></symbol>
<symbol id="i-share" viewBox="0 0 24 24"><circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="18" cy="18" r="2.5"/><path d="M8.2 10.8l7.6-3.6M8.2 13.2l7.6 3.6"/></symbol>
<symbol id="i-chat" viewBox="0 0 24 24"><path d="M21 12a8 8 0 0 1-11.5 7.2L4 21l1.8-5A8 8 0 1 1 21 12z"/></symbol>
<symbol id="i-list" viewBox="0 0 24 24"><path d="M8 6h13M8 12h13M8 18h13"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/></symbol>
<symbol id="i-cal" viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M8 3v4M16 3v4M3 11h18"/></symbol>
<symbol id="i-shield" viewBox="0 0 24 24"><path d="M12 3l8 3v6c0 4.5-3.2 8-8 9-4.8-1-8-4.5-8-9V6z"/></symbol>
<symbol id="i-ban" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M5.6 5.6l12.8 12.8"/></symbol>
<symbol id="i-heart" viewBox="0 0 24 24"><path d="M12 21s-7.5-4.6-9.3-9.3C1.4 8 3.6 4.5 7 4.5c2 0 3.5 1 5 3 1.5-2 3-3 5-3 3.4 0 5.6 3.5 4.3 7.2C19.5 16.4 12 21 12 21z"/></symbol>
</defs></svg>"""
SCRIPT_JS = r"""(function(){
  var keys=['_ef_transaction_id','eftid','oid','affid','sub1','sub2','sub3','sub4','sub5','click_id','gclid','fbclid','utm_source','utm_medium','utm_campaign'];
  var q=new URLSearchParams(location.search), t={};
  try{t=JSON.parse(sessionStorage.getItem('bwa_tracking')||'{}');}catch(e){}
  keys.forEach(function(k){var v=q.get(k); if(v){t[k]=v;}});
  try{sessionStorage.setItem('bwa_tracking',JSON.stringify(t));}catch(e){}
  window.BWA_TRACKING=t;
  document.querySelectorAll('input[data-track]').forEach(function(i){i.value=t[i.getAttribute('data-track')]||'';});
  var f=document.getElementById('lead-form');
  if(f){f.addEventListener('submit',function(ev){ev.preventDefault();f.innerHTML='<p style="margin:0;font-size:18px"><strong>Thank you.</strong> We will call you shortly.</p>';});}
})();
(function(){
  var d=document, reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var nav=d.querySelector('.nav'), bar=d.querySelector('.progress i'), call=d.querySelector('.callbar'), hero=d.querySelector('.hero'), vid=d.querySelector('.vid'), cards=[].slice.call(d.querySelectorAll('.scard')), ticking=false;
  function frame(){
    var y=window.scrollY||0, h=Math.max(1,d.body.scrollHeight-window.innerHeight);
    if(bar){bar.style.transform='scaleX('+Math.min(1,y/h)+')';}
    if(nav){nav.classList.toggle('scrolled',y>12);}
    if(call&&hero){call.classList.toggle('show',y>hero.offsetHeight*0.6);}
    if(vid&&!reduce&&y<1100){vid.style.setProperty('--py',(y*0.07).toFixed(1)+'px');}
    cards.forEach(function(c,i){
      if(i===cards.length-1){return;}
      var n=cards[i+1], top=parseFloat(getComputedStyle(n).top)||0, dist=Math.max(0,n.getBoundingClientRect().top-top);
      c.style.setProperty('--s',(1-0.05*(1-Math.min(1,dist/(c.offsetHeight*0.85)))).toFixed(4));
    });
    ticking=false;
  }
  addEventListener('scroll',function(){if(!ticking){ticking=true;requestAnimationFrame(frame);}},{passive:true});addEventListener('resize',frame);frame();

  var items=[].slice.call(d.querySelectorAll('.reveal,.scard'));
  var counted=false;
  function count(){
    if(counted)return;counted=true;
    var n=d.getElementById('tabsn'), strip=d.getElementById('tabstrip'), to=27, i=0;
    if(!n||!strip){return;}
    if(reduce){n.textContent=to;for(var k=0;k<to;k++){strip.appendChild(d.createElement('i'));}return;}
    var iv=setInterval(function(){i++;n.textContent=i;var s=d.createElement('i');s.style.animationDelay='0s';strip.appendChild(s);if(i>=to){clearInterval(iv);}},70);
  }
  if(!('IntersectionObserver' in window)||reduce){items.forEach(function(el){el.classList.add('in');});count();}
  else{
    var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){en.target.classList.add('in');if(en.target.id==='pbad'){setTimeout(count,500);}io.unobserve(en.target);}});},{threshold:0.15,rootMargin:'0px 0px -6% 0px'});
    items.forEach(function(el){io.observe(el);});
  }
  d.addEventListener('pointermove',function(e){var t=e.target.closest?e.target.closest('.tile'):null;if(t){var r=t.getBoundingClientRect();t.style.setProperty('--mx',(e.clientX-r.left)+'px');t.style.setProperty('--my',(e.clientY-r.top)+'px');}},{passive:true});
  [].slice.call(d.querySelectorAll('.qa .q')).forEach(function(b){b.addEventListener('click',function(){
    var qa=b.parentNode, open=!qa.classList.contains('open');
    [].slice.call(d.querySelectorAll('.qa.open')).forEach(function(o){o.classList.remove('open');o.querySelector('.q').setAttribute('aria-expanded','false');});
    if(open){qa.classList.add('open');b.setAttribute('aria-expanded','true');}});});

  var v=d.getElementById('v'), fb=d.getElementById('vfb'), pl=d.getElementById('play');
  function noVideo(){if(v){v.style.display='none';}if(fb){fb.style.display='grid';}if(pl){pl.style.display='none';}}
  if(v){
    if(fb){fb.style.display='none';}
    v.addEventListener('error',noVideo,true);
    v.querySelector('source').addEventListener('error',noVideo);
    if(!v.canPlayType||!v.canPlayType('video/mp4')){noVideo();}
    pl.addEventListener('click',function(){var q=v.play();if(q&&q.catch){q.catch(noVideo);}});
    v.addEventListener('playing',function(){vid.classList.add('playing');});
    v.addEventListener('pause',function(){vid.classList.remove('playing');});
    var p=v.play();if(p&&p.catch){p.catch(function(){});}
  }
  /* watch the full spokesperson video with sound in a player dialog; the hero loop pauses meanwhile */
  var wb=d.querySelector('.watch'), dlg=d.getElementById('vmodal'), vf=d.getElementById('vfull');
  if(wb&&dlg&&vf&&dlg.showModal){
    wb.addEventListener('click',function(){if(!vf.src){vf.src=wb.getAttribute('data-src');}if(v){v.pause();}dlg.showModal();var q=vf.play();if(q&&q.catch){q.catch(function(){});}});
    function shut(){vf.pause();if(dlg.open){dlg.close();}}
    dlg.querySelector('.vclose').addEventListener('click',shut);
    dlg.addEventListener('click',function(ev){if(ev.target===dlg){shut();}});
    dlg.addEventListener('close',function(){vf.pause();if(v){var r=v.play();if(r&&r.catch){r.catch(function(){});}}wb.focus();});
  } else if(wb){wb.addEventListener('click',function(){location.href=wb.getAttribute('data-src');});}
})();"""
