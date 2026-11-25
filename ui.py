"""Brand Studio UI: dashboard and per-brand workspace. Fonts: Newsreader (display), IBM Plex Sans (text), IBM Plex Mono (figures).
Element ids used by the recording scripts are kept stable: #prompt #gen #st #buyer #setbuyer #cl #warns #vars #view [data-v]."""
import html

import auth
import core
import lp
import sheet
import ui_design

e = html.escape

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&display=swap" rel="stylesheet">')

SPRITE = """<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<symbol id="i-check" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></symbol>
<symbol id="i-x" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></symbol>
<symbol id="i-arrow" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></symbol>
<symbol id="i-back" viewBox="0 0 24 24"><path d="M19 12H5M11 6l-6 6 6 6"/></symbol>
<symbol id="i-ext" viewBox="0 0 24 24"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></symbol>
<symbol id="i-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></symbol>
<symbol id="i-moon" viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></symbol>
<symbol id="i-spark" viewBox="0 0 24 24"><path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/></symbol>
<symbol id="i-grid" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></symbol>
<symbol id="i-desktop" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/></symbol>
<symbol id="i-phone" viewBox="0 0 24 24"><rect x="7" y="3" width="10" height="18" rx="2.5"/><path d="M11 18h2"/></symbol>
<symbol id="i-copy" viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/></symbol>
<symbol id="i-warn" viewBox="0 0 24 24"><path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18h.01"/></symbol>
<symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></symbol>
<symbol id="i-menu" viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h10"/></symbol>
<symbol id="i-layers" viewBox="0 0 24 24"><path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/></symbol>
</defs></svg>"""

CSS = """
:root{--bg:#f5f4f0;--side:#fbfaf7;--surface:#ffffff;--surface2:#f1efe9;--line:rgba(17,24,39,.09);--line2:rgba(17,24,39,.16);
--ink:#111827;--mut:#545d6b;--faint:#8b929e;--accent:#1d3866;--accent2:#142a50;--ok:#1d7a4e;--bad:#b23a30;--warn:#9a6410;--prio:#9c5a17;
--shadow:0 1px 2px rgba(17,24,39,.04),0 14px 34px -18px rgba(17,24,39,.22);--r:12px;--ease:cubic-bezier(.22,.8,.24,1);
--fd:Newsreader,Georgia,"Times New Roman",serif;--fb:"IBM Plex Sans",system-ui,"Segoe UI",Arial,sans-serif;--fm:"IBM Plex Mono",ui-monospace,Menlo,monospace;color-scheme:light}
:root[data-theme=dark]{--bg:#0c0f14;--side:#0f131a;--surface:#141920;--surface2:#1a2029;--line:rgba(255,255,255,.08);--line2:rgba(255,255,255,.15);
--ink:#e8ebf0;--mut:#9aa3b2;--faint:#687284;--accent:#6f93d8;--accent2:#5a80c8;--ok:#43b27c;--bad:#e06a5f;--warn:#d6a24a;--prio:#d99555;
--shadow:0 1px 2px rgba(0,0,0,.3),0 18px 40px -20px rgba(0,0,0,.6);color-scheme:dark}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:400 14.5px/1.55 var(--fb);-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
a{color:inherit;text-decoration:none}button{font:inherit;color:inherit}
.i{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex:none}
h1,h2,h3{font-family:var(--fd);font-weight:600;letter-spacing:-.02em;margin:0}

.app{display:grid;grid-template-columns:248px 1fr;min-height:100vh}
.side{position:sticky;top:0;height:100vh;background:var(--side);border-right:1px solid var(--line);padding:22px 14px;display:flex;flex-direction:column;gap:22px;overflow:auto}
.logo{display:flex;align-items:center;gap:12px;padding:2px 10px}
.logo i{width:34px;height:34px;border-radius:11px;background:linear-gradient(135deg,var(--accent),#9b7bff);display:grid;place-items:center;color:#fff;font:600 14px var(--fd);font-style:normal;box-shadow:0 8px 20px color-mix(in srgb,var(--accent) 40%,transparent)}
.logo b{font:600 16px var(--fd);letter-spacing:-.02em;display:block;line-height:1.1}.logo span{color:var(--mut);font-size:12px}
.navlabel{font:500 11px/1 var(--fb);letter-spacing:.14em;text-transform:uppercase;color:var(--faint);padding:0 10px;margin-bottom:8px}
.nav{display:grid;gap:2px}
.nav-item{display:flex;align-items:center;gap:11px;padding:9px 10px;border-radius:11px;color:var(--mut);transition:background .2s var(--ease),color .2s var(--ease)}
.nav-item:hover{background:var(--surface2);color:var(--ink)}.nav-item.active{background:var(--surface2);color:var(--ink);box-shadow:inset 0 0 0 1px var(--line)}
.nav-item .nm{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dot{width:8px;height:8px;border-radius:50%;background:var(--bad);flex:none}.dot.ok{background:var(--ok);box-shadow:0 0 0 3px color-mix(in srgb,var(--ok) 22%,transparent)}
.avatar{--c:#6b8cff;width:38px;height:38px;border-radius:12px;display:grid;place-items:center;font:600 16px var(--fd);color:#fff;background:linear-gradient(145deg,var(--c),color-mix(in srgb,var(--c) 55%,#000));flex:none;box-shadow:0 8px 18px color-mix(in srgb,var(--c) 35%,transparent)}
.avatar.sm{width:24px;height:24px;border-radius:8px;font-size:12px;box-shadow:none}
.side-foot{margin-top:auto;padding:12px;border:1px solid var(--line);border-radius:13px;background:var(--surface);font-size:12.5px;color:var(--mut)}
.side-foot b{display:block;color:var(--ink);font-weight:500;margin-bottom:2px}

.main{min-width:0}
.top{position:sticky;top:0;z-index:20;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 34px;background:color-mix(in srgb,var(--bg) 82%,transparent);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}
.crumbs{display:flex;align-items:center;gap:8px;color:var(--mut);font-size:13.5px;min-width:0}.crumbs a:hover{color:var(--ink)}.crumbs b{color:var(--ink);font-weight:500}
.tools{display:flex;align-items:center;gap:10px}
.pill{display:inline-flex;align-items:center;gap:8px;height:32px;padding:0 12px;border-radius:999px;border:1px solid var(--line);background:var(--surface);color:var(--mut);font-size:12.5px;white-space:nowrap}
.pill .dot{width:7px;height:7px}
a.pill-link{text-decoration:none;cursor:pointer;transition:border-color .2s,color .2s,background .2s}a.pill-link:hover{color:var(--ink);border-color:var(--line2);background:var(--surface2)}
.iconbtn{width:34px;height:34px;border-radius:50%;border:1px solid var(--line);background:var(--surface);display:grid;place-items:center;cursor:pointer;color:var(--mut);transition:color .2s,border-color .2s,transform .3s var(--ease)}
.iconbtn:hover{color:var(--ink);border-color:var(--line2);transform:rotate(18deg)}
:root:not([data-theme=dark]) .sun,[data-theme=dark] .moon{display:none}
.content{padding:34px;max-width:1360px;margin:0 auto}
.pagehead{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;margin-bottom:26px;flex-wrap:wrap}
.pagehead h1{font-size:30px;line-height:1.1}.pagehead p{margin:6px 0 0;color:var(--mut)}

.btn{display:inline-flex;align-items:center;justify-content:center;gap:9px;height:38px;padding:0 16px;border-radius:11px;border:1px solid var(--line2);background:var(--surface);color:var(--ink);font-weight:500;font-size:13.5px;cursor:pointer;white-space:nowrap;transition:transform .25s var(--ease),box-shadow .25s var(--ease),background .2s,border-color .2s}
.btn:hover{transform:translateY(-1px);border-color:color-mix(in srgb,var(--ink) 30%,transparent);background:var(--surface2)}.btn:active{transform:scale(.98)}
.btn.primary{background:var(--accent);border-color:transparent;color:#fff;box-shadow:0 8px 22px color-mix(in srgb,var(--accent) 38%,transparent)}
.btn.primary:hover{background:var(--accent2);box-shadow:0 12px 28px color-mix(in srgb,var(--accent) 48%,transparent)}
.btn.ghost{background:transparent}.btn[disabled]{opacity:.55;pointer-events:none}
.btn.lg{height:44px;padding:0 20px;border-radius:13px;font-size:14.5px;width:100%}
.spin{width:16px;height:16px;border-radius:50%;border:2px solid rgba(255,255,255,.35);border-top-color:#fff;animation:spin .7s linear infinite;display:none}.loading .spin{display:inline-block}.loading .i{display:none}
@keyframes spin{to{transform:rotate(360deg)}}

.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:18px 20px;transition:transform .35s var(--ease),border-color .3s}
.stat:hover{transform:translateY(-2px);border-color:var(--line2)}
.stat span{display:block;color:var(--mut);font-size:12.5px;margin-bottom:8px}.stat b{font:600 28px/1 var(--fd);letter-spacing:-.03em}.stat small{color:var(--mut);font-size:13px;font-weight:400;margin-left:4px}

.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}
.bcard{background:var(--surface);border:1px solid var(--line);border-radius:20px;padding:22px;display:flex;flex-direction:column;gap:18px;transition:transform .4s var(--ease),box-shadow .4s var(--ease),border-color .3s}
.bcard:hover{transform:translateY(-4px);box-shadow:var(--shadow);border-color:var(--line2)}
.bhead{display:flex;align-items:center;gap:14px}.bhead h3{font-size:18px;line-height:1.2}.bhead .sub{color:var(--mut);font-size:12.5px;text-transform:capitalize}.bhead>div{flex:1;min-width:0}
.badge{display:inline-flex;align-items:center;gap:7px;height:26px;padding:0 11px;border-radius:999px;font-size:12px;font-weight:500;white-space:nowrap}
.badge:before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor}
.badge.ready{color:var(--ok);background:color-mix(in srgb,var(--ok) 14%,transparent)}.badge.pending{color:var(--mut);background:var(--surface2)}
.prog{display:flex;align-items:center;gap:14px}.ring{width:54px;height:54px;flex:none}.ring circle{fill:none;stroke-width:5;stroke-linecap:round}
.ring .bg{stroke:var(--surface2)}.ring .fg{stroke:var(--ok);transition:stroke-dashoffset .8s var(--ease)}.ring text{font:600 13px var(--fd);fill:var(--ink);text-anchor:middle}
.prog b{display:block;font-weight:500}.prog span{color:var(--mut);font-size:12.5px}
.steps{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:8px}
.steps li{display:flex;align-items:center;gap:9px;font-size:13px;color:var(--mut)}
.mark{width:20px;height:20px;border-radius:50%;display:grid;place-items:center;flex:none;background:color-mix(in srgb,var(--bad) 16%,transparent);color:var(--bad)}.mark .i{width:12px;height:12px;stroke-width:2.4}
.mark.ok{background:color-mix(in srgb,var(--ok) 18%,transparent);color:var(--ok)}.steps li.done{color:var(--ink)}
.bfoot{display:flex;gap:8px;margin-top:auto;flex-wrap:wrap}.bfoot .btn.primary{flex:1 1 100%}.bfoot .btn.ghost{flex:1}

.panel{background:var(--surface);border:1px solid var(--line);border-radius:20px;padding:22px}.panel+.panel{margin-top:16px}
.panel h2{font-size:12px;font-family:var(--fb);font-weight:500;letter-spacing:.14em;text-transform:uppercase;color:var(--mut);margin-bottom:16px}
.metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:14px}.metric span{display:block;color:var(--mut);font-size:12.5px}.metric b{font:600 22px/1.3 var(--fd);letter-spacing:-.02em}
.note{color:var(--faint);font-size:12.5px;margin:14px 0 0}

.ws{display:grid;grid-template-columns:minmax(330px,390px) 1fr;gap:18px;align-items:start}
.col{min-width:0}.sticky{position:sticky;top:78px;max-height:calc(100vh - 94px);overflow:auto;padding:2px 4px 2px 0;scrollbar-width:thin;scrollbar-color:var(--line2) transparent}
.bh{display:flex;align-items:center;gap:16px;margin-bottom:24px;flex-wrap:wrap}.bh h1{font-size:28px;line-height:1.1}.bh .meta{color:var(--mut);margin-top:4px;font-size:13px}.bh .grow{flex:1;min-width:200px}.bh .acts{display:flex;gap:8px;flex-wrap:wrap}
label.lab{display:block;font-size:12.5px;color:var(--mut);margin:0 0 8px}
textarea,input[type=text]{width:100%;background:var(--surface2);color:var(--ink);border:1px solid var(--line);border-radius:12px;padding:12px 14px;font:inherit;outline:none;transition:border-color .2s,box-shadow .2s,background .2s}
textarea{resize:vertical;min-height:120px;line-height:1.55}
textarea:focus,input[type=text]:focus{border-color:var(--accent);box-shadow:0 0 0 4px color-mix(in srgb,var(--accent) 22%,transparent)}
.row{display:flex;gap:8px}.row input{flex:1}.hint{color:var(--faint);font-size:12px;margin:10px 0 0}
.drop{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;text-align:center;padding:22px 16px;border:1.5px dashed var(--line2);border-radius:16px;background:var(--surface2);cursor:pointer;transition:border-color .2s,background .2s,transform .3s var(--ease)}
.drop:hover,.drop.over{border-color:var(--accent);background:color-mix(in srgb,var(--accent) 8%,var(--surface2));transform:translateY(-1px)}
.drop b{font-weight:500}.drop span{color:var(--mut);font-size:12.5px;max-width:26em}
.refthumb{width:100%;max-height:180px;object-fit:cover;object-position:top;border-radius:11px;border:1px solid var(--line);margin-bottom:6px}
.pipe{list-style:none;margin:14px 0 0;padding:0;display:grid;gap:8px}.pipe li{display:flex;align-items:center;gap:10px;font-size:13px;color:var(--faint)}
.pipe .mark{background:var(--surface2);color:var(--faint)}.pipe li.active{color:var(--ink)}.pipe li.active .mark{background:color-mix(in srgb,var(--accent) 20%,transparent);color:var(--accent)}
.pipe li.active .mark .i{animation:spin 1s linear infinite}.pipe li.done{color:var(--ink)}.pipe li.done .mark{background:color-mix(in srgb,var(--ok) 18%,transparent);color:var(--ok)}
.pipe li.fail{color:var(--bad)}.pipe li.fail .mark{background:color-mix(in srgb,var(--bad) 16%,transparent);color:var(--bad)}
.stline{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:12px;min-height:20px}#st{color:var(--mut);font-size:12.5px}
kbd{font:500 11px var(--fb);border:1px solid var(--line2);border-bottom-width:2px;border-radius:6px;padding:1px 6px;color:var(--mut)}

.meter{height:6px;border-radius:99px;background:var(--surface2);overflow:hidden;margin:2px 0 16px}.meter i{display:block;height:100%;border-radius:inherit;background:linear-gradient(90deg,var(--accent),var(--ok));transition:width .7s var(--ease)}
.chk{display:grid;gap:4px}.chkrow{display:flex;align-items:center;gap:12px;padding:9px 6px;border-radius:11px;transition:background .2s}.chkrow:hover{background:var(--surface2)}
.chkrow .t{flex:1;min-width:0}.chkrow .t b{display:block;font-weight:500;font-size:13.5px}.chkrow .t span{display:block;color:var(--mut);font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.go{display:flex;align-items:center;gap:10px;margin-top:14px;padding:12px 14px;border-radius:13px;background:color-mix(in srgb,var(--ok) 14%,transparent);color:var(--ok);font-weight:500}
.warns{display:grid;gap:8px;margin-top:14px}.warn{display:flex;gap:10px;align-items:flex-start;padding:10px 12px;border-radius:12px;background:color-mix(in srgb,var(--warn) 12%,transparent);color:color-mix(in srgb,var(--warn) 85%,var(--ink));font-size:12.5px;line-height:1.45}
.warn .i{width:16px;height:16px;margin-top:2px}

.bar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px;flex-wrap:wrap}
.seg{display:inline-flex;padding:3px;border-radius:12px;background:var(--surface2);border:1px solid var(--line);gap:2px}
.seg button{height:32px;padding:0 14px;border:0;border-radius:9px;background:transparent;color:var(--mut);cursor:pointer;font-size:13px;font-weight:500;display:inline-flex;align-items:center;gap:7px;transition:background .2s,color .2s}
.seg button:hover{color:var(--ink)}.seg button.on{background:var(--surface);color:var(--ink);box-shadow:0 1px 3px rgba(0,0,0,.25),inset 0 0 0 1px var(--line)}
.seg .i{width:15px;height:15px}
.frames{display:grid;gap:14px;grid-template-columns:1fr}.frames.two{grid-template-columns:1fr 1fr}
.frame{border:1px solid var(--line2);border-radius:16px;overflow:hidden;background:var(--surface);display:flex;flex-direction:column;min-width:0}
.fbar{display:flex;align-items:center;gap:10px;padding:10px 12px;border-bottom:1px solid var(--line);background:var(--surface2)}
.dots3{display:flex;gap:6px}.dots3 i{width:9px;height:9px;border-radius:50%;background:var(--line2)}
.url{flex:1;min-width:0;height:24px;border-radius:7px;background:var(--surface);border:1px solid var(--line);color:var(--mut);font-size:11.5px;display:flex;align-items:center;padding:0 10px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.tag{font:500 11px var(--fb);letter-spacing:.1em;text-transform:uppercase;color:var(--mut)}
.stage{position:relative;overflow:hidden;height:min(72vh,780px);min-height:460px;background:repeating-conic-gradient(var(--surface2) 0 25%,transparent 0 50%) 0 0/20px 20px}
.stage iframe{position:absolute;top:0;left:0;border:0;background:#fff;transform-origin:0 0;width:1280px;height:800px}
.frames.phone .stage iframe{border-radius:24px;box-shadow:0 0 0 8px #1a1d24,0 24px 50px rgba(0,0,0,.35)}

.vlist{display:grid;gap:8px}.v{border:1px solid var(--line);border-radius:14px;background:var(--surface2);overflow:hidden}
.vh{display:flex;align-items:center;gap:10px;padding:10px 12px;cursor:pointer}.vh:hover{background:color-mix(in srgb,var(--ink) 4%,transparent)}
.vid{font:500 12.5px var(--fb);flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis}.chipx{height:22px;padding:0 9px;border-radius:99px;background:var(--surface);border:1px solid var(--line);font-size:11.5px;color:var(--mut);display:inline-flex;align-items:center}
.vb{display:none;padding:2px 14px 14px;color:var(--mut);font-size:13px;line-height:1.6}.v.open .vb{display:block}.vb p{margin:0 0 10px;white-space:pre-line}
.vsmall{padding:8px 12px;height:auto}
.empty{padding:28px;text-align:center;color:var(--mut);border:1px dashed var(--line2);border-radius:14px}

.toasts{position:fixed;right:22px;bottom:22px;display:grid;gap:10px;z-index:99}
.toast{display:flex;align-items:center;gap:10px;padding:12px 16px;border-radius:13px;background:var(--surface);border:1px solid var(--line2);box-shadow:var(--shadow);font-size:13.5px;animation:tin .4s var(--ease)}
.toast .mark{width:22px;height:22px}@keyframes tin{from{opacity:0;transform:translateY(10px)}}

@media(max-width:1180px){.ws{grid-template-columns:1fr}.sticky{position:static}.metrics{grid-template-columns:repeat(3,1fr)}.stats{grid-template-columns:repeat(2,1fr)}}
@media(max-width:900px){.app{grid-template-columns:1fr}.side{display:none}.content{padding:22px 18px}.top{padding:12px 18px}.frames.two{grid-template-columns:1fr}}
@media(max-width:560px){.stats,.metrics{grid-template-columns:1fr 1fr}.steps{grid-template-columns:1fr}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}}
"""

THEME_BOOT = "<script>try{var t=localStorage.getItem('bs_theme');if(t){document.documentElement.setAttribute('data-theme',t);}}catch(e){}</script>"
THEME_JS = """<script>
(function(){
  var b=document.getElementById('theme');
  if(b){b.addEventListener('click',function(){
    var cur=document.documentElement.getAttribute('data-theme')==='dark'?'dark':'light', nx=cur==='light'?'dark':'light';
    document.documentElement.setAttribute('data-theme',nx);try{localStorage.setItem('bs_theme',nx);}catch(e){}
  });}
  var so=document.getElementById('signout');if(so){so.onclick=function(){fetch('/api/logout',{method:'POST',body:'{}'}).then(function(){location.href='/login';});};}
  window.toast=function(msg,ok){
    var w=document.getElementById('toasts');if(!w){return;}
    var t=document.createElement('div');t.className='toast';
    t.innerHTML='<span class="mark '+(ok===false?'':'ok')+'"><svg class="i"><use href="#i-'+(ok===false?'x':'check')+'"/></svg></span><span></span>';
    t.lastChild.textContent=msg;w.appendChild(t);setTimeout(function(){t.style.transition='opacity .4s';t.style.opacity=0;setTimeout(function(){t.remove();},400);},3200);
  };
})();
</script>"""

import ui2_tabs
CHECKS = [("Page", 0), ("Number", 1), ("Tracking", 2), ("Compliance", 3), ("Buyer", 4)]


def ico(name, cls="i"):
    return f'<svg class="{cls}"><use href="#i-{name}"/></svg>'


def shell(title, body, active=None, crumbs="", extra_js=""):
    brands = core.load_brands()
    nav = ""
    for b in brands:
        ready = core.checklist(b["slug"])["ready"]
        nav += (f'<a class="nav-item{" active" if b["slug"] == active else ""}" href="/studio/{e(b["slug"])}">'
                f'<span class="avatar sm" style="--c:{e(b["accent_color"] or b["primary_color"] or "#6b8cff")}">{e(b["name"][:1])}</span>'
                f'<span class="nm">{e(b["name"])}</span><span class="dot{" ok" if ready else ""}"></span></a>')
    ops_nav = "".join(f'<a class="nav-item{" active" if active == k else ""}" href="/{k}">{ico(ic)}<span class="nm">{lab}</span></a>'
                      for k, ic, lab in (("board", "grid", "Priority board"), ("launch", "rocket", "Launch board"), ("review", "shield", "Legal review"), ("pages", "layers", "Landing pages"), ("ops", "chart", "Operations"), ("crm", "users", "CRM pipeline"), ("publishers", "chart", "Publishers"), ("buyers", "check", "Partner onboarding"), ("integrations", "plug", "Integrations")))
    src = core.config_source()
    live = "live" in src.lower()
    who = auth.who()
    user_ui = (f'<span class="pill" title="Signed in">{e(who)}</span><button class="btn ghost" id="signout" style="height:34px">Sign out</button>' if who else "")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(title)} | Brand Studio</title>{FONTS}{THEME_BOOT}<style>{CSS}{ui_design.CSS}</style></head><body>{SPRITE}'
            f'<div class="app"><div class="sidescrim" id="sidescrim"></div><aside class="side" id="side"><a class="logo" href="/"><i>BS</i><div><b>Brand Studio</b><span>Day One x BWA</span></div></a>'
            f'<div><div class="navlabel">Overview</div><nav class="nav"><a class="nav-item{" active" if active is None else ""}" href="/">{ico("grid")}<span class="nm">Dashboard</span></a>'
            f'<a class="nav-item{" active" if active == "history" else ""}" href="/history">{ico("clock")}<span class="nm">History</span></a></nav></div>'
            f'<div><div class="navlabel">Operate</div><nav class="nav">{ops_nav}</nav></div>'
            f'<div><div class="navlabel">Brands</div><nav class="nav">{nav}</nav></div>'
            f'<div class="side-foot"><b>Control panel</b>{e(src)}<br>{"Edit the Sheet to change a brand." if live else "Edit brands.csv, or publish a Sheet and set SHEET_CSV_URL."}</div></aside>'
            f'<div class="main"><header class="top"><button class="iconbtn menubtn" id="menubtn" aria-label="Open menu" aria-controls="side" aria-expanded="false">{ico("menu")}</button><div class="crumbs">{crumbs}</div><div class="tools">'
            f'<a class="pill pill-link" href="{e(lp.sheet_url())}" target="_blank" rel="noopener" title="Open the Google Sheet"><span class="dot{" ok" if live else ""}"></span>{e(src)}</a>'
            f'{user_ui}'
            f'<button class="iconbtn" id="theme" aria-label="Toggle theme"><span class="sun">{ico("sun")}</span><span class="moon">{ico("moon")}</span></button></div></header>'
            f'<div class="content">{body}</div></div></div><div class="toasts" id="toasts"></div>{THEME_JS}{extra_js}{ui_design.JS}</body></html>')


def ring(done, total):
    c = 2 * 3.14159 * 22
    off = c * (1 - done / total)
    return (f'<svg class="ring" viewBox="0 0 54 54"><circle class="bg" cx="27" cy="27" r="22"/>'
            f'<circle class="fg" cx="27" cy="27" r="22" stroke-dasharray="{c:.1f}" stroke-dashoffset="{off:.1f}" transform="rotate(-90 27 27)"/>'
            f'<text x="27" y="31.5">{done}/{total}</text></svg>')


def dashboard():
    brands = core.load_brands()
    cls = {b["slug"]: core.checklist(b["slug"]) for b in brands}
    ready = sum(1 for c in cls.values() if c["ready"])
    import publish
    lives = {b["slug"]: publish.live_status(b["slug"]) for b in brands}
    nlive = sum(1 for v in lives.values() if v["live"])
    m = core.metrics_summary()
    cards = ""
    for b in brands:
        c = cls[b["slug"]]
        done = sum(1 for i in c["items"] if i["ok"])
        steps = "".join(
            f'<li class="{"done" if i["ok"] else ""}" title="{e(i["detail"])}"><span class="mark{" ok" if i["ok"] else ""}">{ico("check" if i["ok"] else "x")}</span>{e(i["label"])}</li>'
            for i in c["items"])
        page_ok = c["items"][0]["ok"]
        mock = f'<a class="btn ghost" href="/site/{b["slug"]}/">{ico("layers")}Mockup</a>' if (core.ROOT / "sites" / b["slug"]).exists() else ""
        prev = f'<a class="btn ghost" href="/p/{b["slug"]}/" target="_blank">{ico("ext")}Preview</a>' if page_ok else ""
        cards += (f'<article class="bcard"><div class="bhead"><span class="avatar" style="--c:{e(b["accent_color"] or b["primary_color"] or "#6b8cff")}">{e(b["name"][:1])}</span>'
                  f'<div><h3>{e(b["name"])}</h3><span class="sub">{e(b["vertical"])}</span></div>'
                  f'<span class="badge {"ready" if (c["ready"] or lives[b["slug"]]["live"]) else "pending"}">{"Live" if lives[b["slug"]]["live"] else ("Ready" if c["ready"] else "Not ready")}</span></div>'
                  f'<div class="prog">{ring(done, len(c["items"]))}<div><b>{"Ready to go live" if c["ready"] else f"{len(c["items"]) - done} to go"}</b>'
                  f'<span>Go-live checklist</span></div></div><ul class="steps">{steps}</ul>'
                  f'<div class="bfoot"><a class="btn primary" href="/studio/{b["slug"]}">Open studio{ico("arrow")}</a>{prev}{mock}</div></article>')
    if m["runs"]:
        cost = f'${m["est_llm_cost"]}' if m["est_llm_cost"] is not None else "n/a"
        met = (f'<div class="metric"><span>Generations</span><b>{m["runs"]}</b></div><div class="metric"><span>Avg time per page</span><b>{m["avg_seconds"]}s</b></div>'
               f'<div class="metric"><span>Claude runs</span><b>{m["llm_runs"]}</b></div><div class="metric"><span>Tokens in / out</span><b>{m["tokens_in"]} / {m["tokens_out"]}</b></div>'
               f'<div class="metric"><span>Est. LLM cost</span><b>{cost}</b></div>')
        note = "" if m["est_llm_cost"] is not None else '<p class="note">Set RATE_IN_PER_M and RATE_OUT_PER_M to see an estimated cost per page.</p>'
    else:
        met, note = '<div class="empty" style="grid-column:1/-1">No runs yet. Open a brand and hit Generate.</div>', ""
    body = (f'<div class="pagehead"><div><h1>Brands</h1><p>One row in the Sheet is one brand. Generate a page, check the go-live list, ship.</p></div></div>'
            f'<div class="stats"><div class="stat"><span>Brands</span><b>{len(brands)}</b></div><div class="stat"><span>Ready to go live</span><b>{ready}<small>/ {len(brands)}</small></b></div>'
            f'<div class="stat"><span>Live now</span><b>{nlive}<small>/ {len(brands)}</small></b></div>'
            f'<div class="stat"><span>Pages generated</span><b>{m["runs"]}</b></div></div>'
            f'<div class="cards">{cards}</div><section class="panel" style="margin-top:22px"><h2>Cost and speed</h2><div class="metrics">{met}</div>{note}</section>')
    return shell("Dashboard", body, None, "<b>Dashboard</b>")


STUDIO_JS = """<script>
(function(){
  var slug='__SLUG__', mode='after', dev='desktop';
  var $=function(id){return document.getElementById(id);};
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function frames(){
    var t=Date.now(), a='<div class="frame"><div class="fbar"><div class="dots3"><i></i><i></i><i></i></div><div class="url">localhost/p/'+slug+'/</div><span class="tag">After</span></div><div class="stage"><iframe src="/p/'+slug+'/?t='+t+'" title="After"></iframe></div></div>';
    var bs=dev==='phone'?'/before-mobile/':'/before/';
    var b='<div class="frame"><div class="fbar"><div class="dots3"><i></i><i></i><i></i></div><div class="url">Current page (snapshot)</div><span class="tag">Current</span></div><div class="stage"><iframe src="'+bs+slug+'?t='+t+'" title="Current"></iframe></div></div>';
    var c='<div class="frame"><div class="fbar"><div class="dots3"><i></i><i></i><i></i></div><div class="url">Original concept (image)</div><span class="tag">Original</span></div><div class="stage"><iframe src="/before-concept/'+slug+'?t='+t+'" title="Original"></iframe></div></div>';
    var f=$('view'); f.className='frames'+((mode==='both'||mode==='cmp')?' two':'')+(dev==='phone'?' phone':'');
    f.innerHTML= mode==='after'?a : mode==='before'?b : mode==='concept'?c : mode==='cmp'?c+a : b+a;
    fit();
  }
  function fit(){
    var W=dev==='phone'?390:1280, pad=dev==='phone'?18:0;
    [].slice.call(document.querySelectorAll('.stage')).forEach(function(st){
      var f=st.querySelector('iframe'); if(!f){return;}
      var sw=st.clientWidth, sh=st.clientHeight, k=Math.min(1,(sw-pad*2)/W);
      f.style.width=W+'px'; f.style.height=((sh-pad*2)/k)+'px'; f.style.transform='scale('+k+')';
      f.style.left=Math.max(0,(sw-W*k)/2)+'px'; f.style.top=pad+'px';
    });
  }
  window.addEventListener('resize',fit);
  if(window.ResizeObserver){new ResizeObserver(fit).observe($('view'));}
  function row(i){return '<div class="chkrow"><span class="mark '+(i.ok?'ok':'')+'"><svg class="i"><use href="#i-'+(i.ok?'check':'x')+'"/></svg></span><div class="t"><b>'+esc(i.label)+'</b><span>'+esc(i.detail)+'</span></div></div>';}
  function loadCL(){
    fetch('/api/checklist/'+slug).then(function(r){return r.json();}).then(function(c){
      var n=c.items.filter(function(i){return i.ok;}).length;
      $('cl').innerHTML='<div class="meter"><i style="width:'+(n/c.items.length*100)+'%"></i></div><div class="chk">'+c.items.map(row).join('')+'</div>'+(c.ready?'<div class="go"><svg class="i"><use href="#i-check"/></svg>Ready to go live</div>':'');
      $('count').textContent=n+' / '+c.items.length;
      $('warns').innerHTML=c.warnings.length?'<div class="warns">'+c.warnings.map(function(w){return '<div class="warn"><svg class="i"><use href="#i-warn"/></svg><span>'+esc(w)+'</span></div>';}).join('')+'</div>':'';
      var bd=$('badge'); bd.className='badge '+(c.ready?'ready':'pending'); bd.textContent=c.ready?'Ready':'Not ready';
    });
    fetch('/api/variants/'+slug).then(function(r){return r.json();}).then(function(v){
      if(!$('vars')){return;}
      if(!v.length){$('vars').innerHTML='<div class="empty">Generate to build the script variants.</div>';return;}
      $('vcount').textContent=v.length+' variants';
      $('vars').innerHTML='<div class="vlist">'+v.map(function(x,i){return '<div class="v"><div class="vh" data-i="'+i+'"><span class="vid">'+esc(x.id)+'</span><span class="chipx">'+x.opener+' + '+x.cta+'</span><span class="chipx">~'+x.est_seconds+'s</span></div><div class="vb"><p>'+esc(x.script)+'</p><button class="btn ghost vsmall" data-copy="'+i+'"><svg class="i"><use href="#i-copy"/></svg>Copy script</button></div></div>';}).join('')+'</div>';
      window.__v=v;
    });
  }
  document.addEventListener('studio:refresh',function(){loadCL();});
  document.addEventListener('click',function(ev){
    var vh=ev.target.closest('.v .vh'); if(vh){vh.parentNode.classList.toggle('open');}
    var cp=ev.target.closest('[data-copy]'); if(cp){try{navigator.clipboard.writeText(window.__v[+cp.getAttribute('data-copy')].script);toast('Script copied');}catch(e){toast('Copy failed',false);}}
  });
  [].slice.call(document.querySelectorAll('[data-v]')).forEach(function(b){b.onclick=function(){mode=b.getAttribute('data-v');[].slice.call(document.querySelectorAll('[data-v]')).forEach(function(x){x.classList.toggle('on',x===b);});frames();};});
  [].slice.call(document.querySelectorAll('[data-dev]')).forEach(function(b){b.onclick=function(){dev=b.getAttribute('data-dev');[].slice.call(document.querySelectorAll('[data-dev]')).forEach(function(x){x.classList.toggle('on',x===b);});frames();};});
  function generate(){
    var g=$('gen'); if(g.classList.contains('loading')){return;} g.classList.add('loading'); $('st').textContent='Generating...';
    fetch('/api/generate',{method:'POST',body:JSON.stringify({slug:slug,prompt:$('prompt').value})}).then(function(r){return r.json();}).then(function(j){
      g.classList.remove('loading'); $('st').textContent='Done in '+j.seconds+'s ('+j.source+')'; toast('Page, '+j.compliance_pages+' compliance pages and '+j.variants+' variants ready'); frames(); document.dispatchEvent(new Event('studio:refresh'));
    }).catch(function(){g.classList.remove('loading');$('st').textContent='Failed';toast('Generation failed',false);});
  }
  $('gen').onclick=generate;
  $('prompt').addEventListener('keydown',function(e){if((e.ctrlKey||e.metaKey)&&e.key==='Enter'){generate();}});
  $('setbuyer').onclick=function(){fetch('/api/buyer',{method:'POST',body:JSON.stringify({slug:slug,buyer:$('buyer').value})}).then(function(){toast($('buyer').value?'Buyer assigned':'Buyer cleared');document.dispatchEvent(new Event('studio:refresh'));});};
  function pipe(step,state){
    var order=['upload','read','gen'];
    order.forEach(function(s){var li=document.querySelector('.pipe [data-s="'+s+'"]');if(!li){return;}li.className='';});
    order.forEach(function(s,i){
      var li=document.querySelector('.pipe [data-s="'+s+'"]'); if(!li){return;}
      var k=order.indexOf(step);
      if(i<k){li.className='done';li.querySelector('use').setAttribute('href','#i-check');}
      else if(i===k){li.className=state;li.querySelector('use').setAttribute('href',state==='done'?'#i-check':state==='fail'?'#i-x':'#i-spark');}
    });
  }
  function post(url,body){return fetch(url,{method:'POST',body:JSON.stringify(body)}).then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});});}
  function readAndGenerate(){
    pipe('read','active'); $('st').textContent='Reading the pitch from the image...';
    return post('/api/extract',{slug:slug,mode:($('refmode')||{}).value||'inspire'}).then(function(x){
      var ok=x.ok&&x.j.ok, why=ok?'':(x.j.error||'Could not read the image');
      if(!ok){toast(why,false);}
      pipe('gen','active'); $('st').textContent='Generating...';
      return post('/api/generate',{slug:slug,prompt:$('prompt').value}).then(function(y){
        pipe('gen','done'); $('st').textContent='Done in '+y.j.seconds+'s ('+y.j.source+')';
        frames(); document.dispatchEvent(new Event('studio:refresh')); var h=$('pitchnote');
        if(ok){toast('Site generated from the image'); if(h){h.textContent='Pitch read from the image by '+(x.j.provider||'the model')+': '+x.j.hero;}}
        else{var li=document.querySelector('.pipe [data-s="read"]'); if(li){li.className='fail';li.querySelector('use').setAttribute('href','#i-x');} toast('Built the page from the prompt instead'); if(h){h.textContent=why+' The page was built from the prompt instead. The image is kept as a reference.';}}
      });
    }).catch(function(){pipe('read','fail');toast('Generation failed',false);$('st').textContent='Failed';});
  }
  function shrink(src){
    /* big photos and screenshots can pass the 4.5 MB request limit of the hosted studio: scale to 2000px and re-encode when over 2.5 MB */
    return new Promise(function(resolve){
      if(src.length<2500000){resolve(src);return;}
      var im=new Image();
      im.onload=function(){var k=Math.min(1,2000/Math.max(im.width,im.height)),c=document.createElement('canvas');c.width=Math.round(im.width*k);c.height=Math.round(im.height*k);c.getContext('2d').drawImage(im,0,0,c.width,c.height);resolve(c.toDataURL('image/jpeg',0.9));};
      im.onerror=function(){resolve(src);};
      im.src=src;
    });
  }
  function fromFile(file){
    if(!file||file.type.indexOf('image/')!==0){toast('Choose an image file',false);return;}
    pipe('upload','active'); $('st').textContent='Uploading...';
    var rd=new FileReader();
    rd.onload=function(){
      shrink(rd.result).then(function(data){return post('/api/reference',{slug:slug,data:data});}).then(function(x){
        if(!x.ok){pipe('upload','fail');toast('Upload failed',false);return;}
        var t=$('refthumb'); if(t){t.src='/before-img/'+slug+'-concept.png?t='+Date.now();t.style.display='block';}
        pipe('upload','done'); return readAndGenerate();
      });
    };
    rd.readAsDataURL(file);
  }
  var drop=$('drop'), inp=$('reffile');
  if(inp){inp.addEventListener('change',function(){fromFile(inp.files[0]);inp.value='';});}
  if(drop){
    ['dragenter','dragover'].forEach(function(n){drop.addEventListener(n,function(ev){ev.preventDefault();drop.classList.add('over');});});
    ['dragleave','drop'].forEach(function(n){drop.addEventListener(n,function(ev){ev.preventDefault();drop.classList.remove('over');});});
    drop.addEventListener('drop',function(ev){fromFile(ev.dataTransfer.files[0]);});
  }
  var rr=$('reread'); if(rr){rr.onclick=function(){pipe('read','active');readAndGenerate();};}
  frames(); loadCL();
})();
</script>"""


def studio(slug):
    b = core.get_brand(slug)
    default = (f"Rebuild {b['name']}'s landing page for {b['vertical']} calls. Trustworthy, real people not AI faces, one clear call to action.")
    has_before = (core.BEFORE / f"{slug}.html").exists() or (core.BEFORE / f"{slug}-desktop.png").exists()
    before_note = "Before is a snapshot of the current page." if has_before else "No saved copy of the current page yet. Save one to studio/before/."
    cl = core.checklist(slug)
    has_concept = (core.BEFORE / f"{slug}-concept.png").exists()
    pitch = core.load_pitch(slug)
    pitch_note = (f"Using the pitch read from the image: {pitch['hero']}" if pitch else "No pitch yet. Drop an image, or use the prompt below.")
    concept_btn = '<button data-v="concept">Original</button>' if has_concept else ""
    cmp_btn = '<button data-v="cmp">Original vs After</button>' if has_concept else ""
    before_label = "Current" if has_concept else "Before"
    both_label = "Current vs After" if has_concept else "Side by side"
    if has_concept:
        before_note = "Original is the first concept image. Current is a snapshot of the live page."
    mock = f'<a class="btn" href="/site/{slug}/">{ico("layers")}Mockup site</a>' if (core.ROOT / "sites" / slug).exists() else ""
    body = (
        f'<div class="bh"><span class="avatar" style="--c:{e(b["accent_color"] or b["primary_color"] or "#6b8cff")};width:52px;height:52px;font-size:22px">{e(b["name"][:1])}</span>'
        f'<div class="grow"><h1>{e(b["name"])}</h1><div class="meta">{e(b["vertical"]).title()} &middot; {e(b["phone"])}'
        f'{" &middot; " + e(b["hours"]) if b["hours"] else ""}</div></div>'
        f'<span class="badge {"ready" if cl["ready"] else "pending"}" id="badge">{"Ready" if cl["ready"] else "Not ready"}</span>'
        f'<div class="acts"><a class="btn" href="/p/{slug}/" target="_blank">{ico("ext")}Open live preview</a>{mock}</div></div>'
        f'<div class="ws"><div class="col sticky">'
        f'<section class="panel" id="refpanel"><h2>Reference image</h2>'
        f'<label class="drop" id="drop" for="reffile"><input type="file" id="reffile" accept="image/*" hidden>'
        f'<img class="refthumb" id="refthumb" alt="Reference image"{f' src="/before-img/{slug}-concept.png"' if has_concept else ''} style="display:{"block" if has_concept else "none"}">'
        f'<b>Drop a landing page image here</b><span>The studio reads its sales pitch and builds the site from it. Click to choose a file.</span></label>'
        f'<ol class="pipe"><li data-s="upload"><span class="mark">{ico("spark")}</span>Upload the image</li>'
        f'<li data-s="read"><span class="mark">{ico("spark")}</span>Read the sales pitch</li><li data-s="gen"><span class="mark">{ico("spark")}</span>Generate the site</li></ol>'
        f'<p class="hint" id="pitchnote">{e(pitch_note)}</p>'
        f'<label class="lab" for="refmode" style="margin-top:14px">Use the image as</label>'
        f'<select id="refmode" style="width:100%;height:42px;border-radius:11px;border:1px solid var(--line2);background:var(--surface);color:var(--ink);padding:0 12px;font:inherit">'
        f'<option value="inspire">Inspiration: new sales copy for this brand</option><option value="exact">Exact wording from the image</option></select>'
        f'<div class="row" style="margin-top:12px"><button class="btn" id="reread" style="flex:1">Read this image again</button></div></section>'
        f'<section class="panel"><h2>Prompt</h2><label class="lab" for="prompt">What should the new page do?</label>'
        f'<textarea id="prompt" rows="5">{e(default)}</textarea>'
        + ('<p class="hint">This brand has a pitch from its reference image, so Generate uses that and ignores the prompt.</p>' if pitch else '') +
        f'<div class="stline"><span id="st"></span><span class="hint" style="margin:0"><kbd>Ctrl</kbd> <kbd>Enter</kbd> to generate</span></div>'
        f'<button class="btn primary lg" id="gen" style="margin-top:6px"><span class="spin"></span>{ico("spark")}Generate page, compliance and variants</button></section>'
        f'<section class="panel"><h2>Buyer</h2><div class="row"><input type="text" id="buyer" value="{e(b["buyer"])}" placeholder="e.g. Integrity Marketing">'
        f'<button class="btn" id="setbuyer">Assign</button></div><p class="hint">With a live Sheet, set the buyer in the Sheet instead.</p></section>'
        f'<section class="panel"><h2 style="display:flex;justify-content:space-between"><span>Go-live checklist</span><span id="count" style="letter-spacing:0">0 / 7</span></h2>'
        f'<div id="cl"></div><div id="warns"></div></section></div>'
        f'<div class="col"><div class="tabs">'+''.join(f'<button data-tab="{k}" class="{"on" if k == "preview" else ""}">{lab}<span class="tdot" id="td-{k}" style="display:none"></span></button>' for k, lab in ui2_tabs.TABS)+'</div>'
        f'<div class="tp on" data-tp="preview"><section class="panel"><div class="bar"><div class="seg"><button data-v="after" class="on">After</button>{concept_btn}<button data-v="before">{before_label}</button>{cmp_btn}<button data-v="both">{both_label}</button></div>'
        f'<div class="seg"><button data-dev="desktop" class="on">{ico("desktop")}Desktop</button><button data-dev="phone">{ico("phone")}Phone</button></div></div>'
        f'<div id="view" class="frames"></div><p class="hint">{e(before_note)}</p></section>'
        f'<section class="panel"><h2 style="display:flex;justify-content:space-between"><span>Video script variants</span><span id="vcount" style="letter-spacing:0"></span></h2>'
        f'<div id="vars"><div class="empty">Generate to build the script variants.</div></div></section></div>'
        + ''.join(f'<div class="tp" data-tp="{k}"><section class="panel" id="pn-{k}"><div class="empty">Loading...</div></section></div>' for k, _ in ui2_tabs.TABS[1:]) + '</div></div>')
    crumbs = f'<a href="/">Dashboard</a>{ico("arrow")}<b>{e(b["name"])}</b>'
    return shell(b["name"], body, slug, crumbs, STUDIO_JS.replace("__SLUG__", slug) + ui2_tabs.studio2_js(slug))
