"""Design layer for the studio: the institutional look (type, spacing, surfaces, tables, controls) and the micro-interactions.
It is loaded after every page module's CSS, so it is the single place to tune the look. Markup and element ids are untouched."""

CSS = """
/* ---------- type and base */
body{font:400 14px/1.55 var(--fb);letter-spacing:-.003em;font-feature-settings:"tnum" 1}
h1,h2,h3{font-family:var(--fb);letter-spacing:-.01em}
.pagehead h1,.bh h1,.lcard h1,.lbrand h2{font-family:var(--fd);font-weight:500;letter-spacing:-.015em}
.pagehead{align-items:flex-end;margin-bottom:24px;padding-bottom:20px;border-bottom:1px solid var(--line)}
.pagehead h1{font-size:34px;line-height:1.08}.pagehead p{max-width:62em;font-size:14px;line-height:1.6;margin-top:8px}
.pagehead h1 .chip2{vertical-align:middle;margin-left:6px;font-family:var(--fb)}
.content{padding:30px 36px 56px;max-width:1440px}
::selection{background:color-mix(in srgb,var(--accent) 22%,transparent)}
code{font:500 12px var(--fm);background:var(--surface2);border:1px solid var(--line);border-radius:5px;padding:1px 5px;overflow-wrap:anywhere}
*{scrollbar-width:thin;scrollbar-color:var(--line2) transparent}
::-webkit-scrollbar{width:10px;height:10px}::-webkit-scrollbar-thumb{background:var(--line2);border-radius:10px;border:3px solid transparent;background-clip:padding-box}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

/* ---------- sidebar */
.app{grid-template-columns:252px 1fr}
.side{padding:20px 12px;gap:20px;background:var(--side)}
.logo{padding:4px 10px 14px;border-bottom:1px solid var(--line);border-radius:0}
.logo i{width:32px;height:32px;border-radius:8px;background:var(--accent);box-shadow:none;font:500 15px/1 var(--fd);letter-spacing:.02em}
.logo b{font:600 15px var(--fb);letter-spacing:-.01em}.logo span{font-size:12px;color:var(--faint)}
.navlabel{font:600 10.5px/1 var(--fb);letter-spacing:.12em;color:var(--faint)}
.nav-item{position:relative;padding:8px 10px;border-radius:8px;font-size:13.5px;transition:background .18s var(--ease),color .18s var(--ease)}
.nav-item:before{content:"";position:absolute;left:-12px;top:8px;bottom:8px;width:3px;border-radius:0 3px 3px 0;background:var(--accent);transform:scaleY(0);transition:transform .25s var(--ease)}
.nav-item.active{background:var(--surface);box-shadow:inset 0 0 0 1px var(--line);font-weight:500}.nav-item.active:before{transform:scaleY(1)}
.nav-item .i{width:17px;height:17px;transition:transform .25s var(--ease)}.nav-item:hover .i{transform:translateX(1px)}
.side-foot{border-radius:10px;font-size:12px;line-height:1.5;background:var(--surface)}
.dot{width:7px;height:7px;background:color-mix(in srgb,var(--faint) 60%,transparent)}
.dot.ok{background:var(--ok);box-shadow:0 0 0 3px color-mix(in srgb,var(--ok) 18%,transparent)}
.pill .dot.ok{animation:pulse 2.4s var(--ease) infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 color-mix(in srgb,var(--ok) 45%,transparent)}70%{box-shadow:0 0 0 6px transparent}100%{box-shadow:0 0 0 0 transparent}}

/* ---------- avatars: flat monograms */
.avatar{border-radius:9px;font:600 15px var(--fb);color:color-mix(in srgb,var(--c) 78%,var(--ink));background:color-mix(in srgb,var(--c) 13%,var(--surface));
 box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--c) 28%,transparent)}
.avatar.sm{width:22px;height:22px;border-radius:6px;font-size:11px;box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--c) 28%,transparent)}

/* ---------- top bar */
.top{padding:12px 36px;min-height:58px;background:color-mix(in srgb,var(--bg) 86%,transparent)}
.crumbs{font-size:13px}.crumbs .i{width:14px;height:14px;color:var(--faint)}
.pill{height:30px;border-radius:7px;font-size:12px}
.iconbtn{width:32px;height:32px;border-radius:8px}.iconbtn:hover{transform:none}
#theme:hover .i{transform:rotate(25deg)}#theme .i{transition:transform .4s var(--ease)}
.menubtn{display:none}

/* ---------- buttons */
.btn{height:36px;padding:0 14px;border-radius:8px;font-size:13px;font-weight:500;gap:8px;box-shadow:0 1px 1px rgba(17,24,39,.04)}
.btn:hover{transform:none;background:var(--surface2);border-color:var(--line2)}
.btn:active{transform:scale(.975)}
.btn .i{width:16px;height:16px;transition:transform .25s var(--ease)}
.btn:hover .i:has(use[href="#i-arrow"]){transform:translateX(2px)}.btn:hover .i:has(use[href="#i-ext"]){transform:translate(1px,-1px)}
.btn:hover .i:has(use[href="#i-spark"]){transform:rotate(18deg) scale(1.06)}
.btn.primary{background:var(--accent);box-shadow:0 1px 2px rgba(17,24,39,.12),inset 0 1px 0 rgba(255,255,255,.08)}
.btn.primary:hover{background:var(--accent2);box-shadow:0 6px 16px -8px color-mix(in srgb,var(--accent) 70%,transparent)}
.btn.lg{height:44px;border-radius:9px;font-size:14px}
.btn[disabled]{opacity:.5}
.loading{cursor:progress}

/* ---------- surfaces */
.panel{border-radius:14px;padding:22px 24px;box-shadow:0 1px 2px rgba(17,24,39,.03)}
.panel h2{font:600 11px/1.2 var(--fb);letter-spacing:.09em;color:var(--mut);margin-bottom:16px}
.panel h2 span:last-child:not(:first-child){font-family:var(--fm);letter-spacing:0;text-transform:none;font-weight:500}
.note,.hint{color:var(--faint)}
.note2{border-radius:10px;border-style:solid;border-color:var(--line);background:var(--surface2);line-height:1.6}
.empty{border-radius:12px;font-size:13.5px;background:color-mix(in srgb,var(--surface2) 50%,transparent)}

/* ---------- KPI tiles */
.stats,.kpis{gap:12px}
.stat,.kpi{border-radius:12px;padding:16px 18px;position:relative;overflow:hidden;transition:border-color .25s var(--ease),box-shadow .25s var(--ease)}
.stat:hover,.kpi:hover{transform:none;border-color:var(--line2);box-shadow:var(--shadow)}
.stat span,.kpi span{font-size:12px;color:var(--mut);margin-bottom:10px}
.stat b,.kpi b,.kstrip b{font:500 32px/1 var(--fd);letter-spacing:-.02em;font-variant-numeric:lining-nums tabular-nums}
.stat small{font:400 13px var(--fb);color:var(--faint)}
.metric b{font:500 22px/1.3 var(--fd)}

/* ---------- brand cards (dashboard) */
.cards{grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}
.bcard{border-radius:14px;padding:20px;gap:16px;transition:transform .35s var(--ease),box-shadow .35s var(--ease),border-color .25s}
.bcard:hover{transform:translateY(-2px);box-shadow:var(--shadow)}
.bhead{align-items:flex-start}.bhead h3{font:600 16px/1.3 var(--fb);overflow-wrap:anywhere}.bhead .sub{font-size:12px}
.badge{height:22px;padding:0 8px;border-radius:6px;font-size:11.5px;gap:6px}.badge:before{width:6px;height:6px}
.badge.pending{color:var(--mut);background:var(--surface2);box-shadow:inset 0 0 0 1px var(--line)}
.ring{width:48px;height:48px}.ring .bg{stroke:var(--line2)}.ring circle{stroke-width:4}.ring text{font:500 12px var(--fm)}
.ring .fg{animation:ringin 1.1s var(--ease) both}
@keyframes ringin{from{stroke-dashoffset:138.2}}
.prog{padding:12px;border-radius:10px;background:var(--surface2)}
.steps{gap:7px 12px}.steps li{font-size:12.5px;min-width:0}
.steps li,.chkrow .t b{overflow-wrap:anywhere}
.steps .mark:not(.ok),.chk .mark:not(.ok){background:transparent;color:var(--faint);box-shadow:inset 0 0 0 1.5px var(--line2)}
.steps .mark:not(.ok) .i,.chk .mark:not(.ok) .i{display:none}
.mark{width:18px;height:18px}.mark .i{width:11px;height:11px}
.bfoot{gap:8px}
.bcard .bfoot .btn.primary{background:var(--surface);color:var(--ink);border-color:var(--line2);box-shadow:0 1px 1px rgba(17,24,39,.04)}
.bcard:hover .bfoot .btn.primary{border-color:color-mix(in srgb,var(--accent) 45%,transparent);color:var(--accent)}
.bcard .bfoot .btn.primary:hover{background:var(--accent);color:#fff;border-color:transparent}

/* ---------- tables */
.panel:has(>table.tbl){overflow-x:auto}
table.tbl{display:table;width:100%;font-size:13px;border-collapse:separate;border-spacing:0}
.tbl th{font:600 10.5px var(--fb);letter-spacing:.08em;color:var(--faint);padding:0 12px 10px;white-space:nowrap}
.tbl td{padding:12px;vertical-align:middle;transition:background .15s}
.tbl tbody tr:hover td{background:color-mix(in srgb,var(--surface2) 70%,transparent)}
.tbl tbody tr td:first-child{border-radius:8px 0 0 8px}.tbl tbody tr td:last-child{border-radius:0 8px 8px 0}
.tbl td b{font-weight:600}.sb{gap:12px}.sb>div{min-width:0}
.tbl td.mut{max-width:28ch}
.dots7{gap:3px}.dots7 i{width:12px;height:6px;border-radius:2px;background:var(--line2)}.dots7 i.ok{background:var(--ok)}

/* ---------- chips */
.chip2{height:22px;padding:0 8px;border-radius:6px;font-size:11.5px}
.chip2.bad,.chip2.ok,.chip2.warn,.chip2.acc{border-color:transparent}

/* ---------- segmented controls, filters and tabs */
.seg,.pill-tabs,.filters{display:inline-flex;gap:2px;padding:3px;border-radius:9px;background:var(--surface2);border:1px solid var(--line)}
.filters{flex-wrap:wrap}
.seg button,.pill-tabs button,.filters button{height:30px;padding:0 12px;border:0;border-radius:7px;background:transparent;color:var(--mut);font-size:12.5px;font-weight:500;cursor:pointer;transition:background .2s var(--ease),color .2s var(--ease),box-shadow .2s var(--ease)}
.seg button:hover,.pill-tabs button:hover,.filters button:hover{color:var(--ink)}
.seg button.on,.pill-tabs button.on,.filters button.on{background:var(--surface);color:var(--ink);box-shadow:0 1px 2px rgba(17,24,39,.08),inset 0 0 0 1px var(--line)}
.tabs{background:transparent;border:0;border-bottom:1px solid var(--line);border-radius:0;padding:0;gap:4px;margin-bottom:16px}
.tabs button{height:40px;padding:0 12px;border-radius:0;font-size:13px;box-shadow:inset 0 -2px 0 transparent;transition:color .2s,box-shadow .25s var(--ease)}
.tabs button.on{background:transparent;box-shadow:inset 0 -2px 0 var(--accent);color:var(--ink)}
.tabs .tdot{height:17px;min-width:17px;border-radius:5px;font:600 10.5px var(--fm)}
.tp.on{animation:fadein .35s var(--ease)}

/* ---------- forms */
textarea,input[type=text],select{border-radius:9px!important;border-color:var(--line2)!important;background:var(--surface)!important;font-size:13.5px}
textarea:focus,input[type=text]:focus,select:focus{border-color:var(--accent)!important;box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 16%,transparent)}
.drop{border-radius:12px;background:var(--surface2)}
.drop:hover,.drop.over{transform:none;border-color:var(--accent)}
.refthumb{border-radius:8px}

/* ---------- alerts and banners */
.al,.warn{border-radius:10px;font-size:13px}
.al{border-left:3px solid var(--line2)}.al.bad{border-left-color:var(--bad)}.al.warn{border-color:color-mix(in srgb,var(--warn) 30%,transparent);border-left-color:var(--warn);color:var(--ink)}
.banner{border-radius:12px}.banner b{font:500 18px var(--fd)}
.icard{border-radius:12px;background:var(--surface);transition:border-color .25s,box-shadow .25s var(--ease)}.icard:hover{border-color:var(--line2);box-shadow:var(--shadow)}
.icard h3{font:600 14.5px var(--fb)}

/* ---------- CRM columns */
.kanban{grid-auto-columns:minmax(210px,1fr)}
.kcol{border-radius:12px;background:var(--surface2);min-height:140px}
.kcol h4{font:600 10.5px var(--fb);letter-spacing:.08em}
.kcard{background:var(--surface);border-radius:9px;overflow-wrap:anywhere}

/* ---------- studio workspace */
.bh{padding-bottom:20px;border-bottom:1px solid var(--line)}.bh h1{font-size:32px}
.stage{border-radius:0 0 12px 12px}.frame{border-radius:12px}.fbar{background:var(--surface2)}
.url{font-family:var(--fm);font-size:11px}
.meter{height:5px}.meter i{background:var(--ok);animation:grow 1s var(--ease) both;transform-origin:left}
@keyframes grow{from{transform:scaleX(0)}}
.go{border-radius:10px}

/* ---------- toasts */
.toasts{right:20px;bottom:20px}
.toast{border-radius:10px;background:var(--ink);color:var(--bg);border:0;padding:11px 14px 13px;position:relative;overflow:hidden;animation:tin .45s var(--ease)}
.toast:after{content:"";position:absolute;left:0;bottom:0;height:2px;width:100%;background:color-mix(in srgb,var(--bg) 45%,transparent);transform-origin:left;animation:tbar 3.2s linear forwards}
@keyframes tbar{to{transform:scaleX(0)}}
@keyframes tin{from{opacity:0;transform:translateY(12px) scale(.98)}}

/* ---------- entrance motion */
@keyframes fadein{from{opacity:0}}
@keyframes rise{from{opacity:0;transform:translateY(8px)}}
.content>*{animation:rise .5s var(--ease) both}
.content>*:nth-child(2){animation-delay:.05s}.content>*:nth-child(3){animation-delay:.1s}.content>*:nth-child(4){animation-delay:.14s}.content>*:nth-child(n+5){animation-delay:.18s}
.stagger>*{animation:rise .5s var(--ease) both;animation-delay:calc(var(--i,0) * 35ms + .12s)}
.skel{position:relative;overflow:hidden;color:transparent!important}
.skel:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,transparent,color-mix(in srgb,var(--ink) 6%,transparent),transparent);animation:shim 1.2s infinite}
@keyframes shim{from{transform:translateX(-100%)}to{transform:translateX(100%)}}

/* ---------- mobile */
.sidescrim{display:none}
@media(max-width:900px){
 .menubtn{display:grid}
 .side{display:flex;position:fixed;left:0;top:0;bottom:0;width:276px;z-index:90;transform:translateX(-102%);transition:transform .3s var(--ease);box-shadow:20px 0 50px -30px rgba(0,0,0,.5)}
 .side.open{transform:none}
 .sidescrim{display:block;position:fixed;inset:0;background:rgba(10,14,20,.38);opacity:0;pointer-events:none;transition:opacity .25s;z-index:85}
 .sidescrim.on{opacity:1;pointer-events:auto}
 .top{padding:10px 16px;gap:10px}.top .tools .pill-link{display:none}.crumbs{flex:1}
 .content{padding:22px 16px 40px}.pagehead h1{font-size:28px}
}
@media(max-width:560px){.top #signout,.top .pill[title="Signed in"]{display:none}}
@media(prefers-reduced-motion:reduce){.content>*,.stagger>*{animation:none!important}}
"""

JS = """<script>
(function(){
  var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  /* mobile menu */
  var side=document.getElementById('side'),scrim=document.getElementById('sidescrim'),mb=document.getElementById('menubtn');
  function menu(on){if(!side)return;side.classList.toggle('open',on);scrim.classList.toggle('on',on);if(mb)mb.setAttribute('aria-expanded',on?'true':'false');}
  if(mb){mb.onclick=function(){menu(!side.classList.contains('open'));};}
  if(scrim){scrim.onclick=function(){menu(false);};}
  document.addEventListener('keydown',function(e){if(e.key==='Escape')menu(false);});
  /* keep the active brand visible in the sidebar */
  var act=document.querySelector('.side .nav-item.active');if(act&&act.scrollIntoView&&side&&act.offsetTop>side.clientHeight-80){side.scrollTop=act.offsetTop-side.clientHeight/2;}
  /* staggered entrance for lists and grids */
  window.stagger=function(root){
    [].forEach.call((root||document).querySelectorAll('.cards,.stats,.kpis,.cgrid,.alerts,.tbl tbody'),function(g){
      if(g.classList.contains('stagger'))return;g.classList.add('stagger');
      [].forEach.call(g.children,function(c,i){c.style.setProperty('--i',Math.min(i,16));});
    });
  };
  /* numbers count up from zero */
  window.countUp=function(root){
    if(reduce)return;
    [].forEach.call((root||document).querySelectorAll('.stat b,.kpi b,.kstrip b,.metric b'),function(el){
      if(el.__counted)return;el.__counted=1;
      var tn=null;for(var i=0;i<el.childNodes.length;i++){var n=el.childNodes[i];if(n.nodeType===3&&/\\d/.test(n.nodeValue)){tn=n;break;}}
      if(!tn)return;var m=tn.nodeValue.match(/^(\\D*?)([\\d,]+(?:\\.\\d+)?)(.*)$/);if(!m)return;
      var target=parseFloat(m[2].replace(/,/g,'')),dec=(m[2].split('.')[1]||'').length,comma=m[2].indexOf(',')>=0;if(!target)return;
      var t0=null,dur=900;
      function fmt(v){var s=v.toFixed(dec);if(comma){var p=s.split('.');p[0]=p[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g,',');s=p.join('.');}return m[1]+s+m[3];}
      function step(t){if(!t0)t0=t;var k=Math.min(1,(t-t0)/dur),e=1-Math.pow(1-k,3);tn.nodeValue=fmt(target*e);if(k<1)requestAnimationFrame(step);}
      tn.nodeValue=fmt(0);requestAnimationFrame(step);
    });
  };
  if(!reduce){window.stagger();}
  window.countUp();
})();
</script>"""
