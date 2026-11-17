"""The Priority board: a Jira style board. Columns are stages, cards are brands with seven check markers and an orange priority number.
Drag a card to reorder it (priority) or to another column (stage). Every change is kept in a history you can open as a timeline."""
import lp
import ui
from ui import e, ico, shell

ui.CSS = ui.CSS + """
.kstrip{display:grid;grid-template-columns:repeat(5,1fr);background:var(--surface);border:1px solid var(--line);border-radius:20px;margin-bottom:18px;overflow:hidden}
.kstrip>div{padding:16px 20px;border-right:1px solid var(--line);min-width:0}.kstrip>div:last-child{border-right:0}
.kstrip span{display:block;color:var(--mut);font-size:12.5px;margin-bottom:4px}.kstrip b{display:block;font:500 34px/1.1 var(--fd);letter-spacing:-.03em}.kstrip small{display:block;color:var(--faint);font-size:12.5px;margin-top:3px}
.kb{display:flex;gap:12px;overflow-x:auto;padding:2px 2px 14px;align-items:flex-start}
.kcol2{flex:0 0 292px;width:292px;background:color-mix(in srgb,var(--surface2) 70%,transparent);border:1px solid var(--line);border-radius:18px;transition:box-shadow .18s,border-color .18s,background .18s}
.kcol2 header{display:flex;align-items:center;justify-content:space-between;padding:13px 14px;border-bottom:1px solid var(--line)}
.kcol2 header b{font-weight:600;font-size:14.5px}.kcol2 header em{font-style:normal;min-width:26px;height:22px;padding:0 8px;border-radius:99px;background:var(--surface);border:1px solid var(--line);color:var(--mut);font-size:12px;display:inline-grid;place-items:center}
.kcol2 .hint{padding:8px 14px 0;color:var(--faint);font-size:12px}
.kcol2 .kbody{padding:10px;min-height:96px;display:flex;flex-direction:column;gap:8px}
.kcol2.lockcol{background:color-mix(in srgb,var(--surface2) 40%,transparent);border-style:dashed}
.kcol2.deny{border-color:color-mix(in srgb,var(--bad) 55%,transparent);box-shadow:0 0 0 3px color-mix(in srgb,var(--bad) 13%,transparent)}
.kcol2.ok{border-color:var(--accent);background:color-mix(in srgb,var(--accent) 7%,var(--surface2));box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 16%,transparent)}
.kc{position:relative;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:12px 14px 11px 12px;cursor:grab;transition:box-shadow .15s,border-color .15s,transform .15s;user-select:none;-webkit-user-select:none}
.kc:hover{border-color:var(--line2);box-shadow:0 8px 20px -12px rgba(0,0,0,.5)}.kc:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.kc .t{display:flex;align-items:center;gap:8px}.kc .grip{flex:none;width:14px;height:18px;color:var(--faint);opacity:.55;cursor:grab;touch-action:none;display:grid;place-items:center;margin-left:-4px}.kc:hover .grip{opacity:1}
.kc .grip svg{width:12px;height:16px;fill:currentColor}
.kc .nm{flex:1;min-width:0;font-weight:600;font-size:14.5px;color:var(--ink);text-decoration:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.kc .nm:hover{text-decoration:underline}
.kc .n{color:#e8762c;font-weight:600;font-size:13.5px;flex:none;font-variant-numeric:tabular-nums}
.kc .s{color:var(--mut);font-size:13px;margin:3px 0 0 14px;text-transform:capitalize;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kc .m{display:flex;align-items:center;gap:5px;margin:10px 0 0 14px;color:var(--mut);font-size:12.5px}.kc .m i{width:9px;height:9px;border-radius:50%;background:color-mix(in srgb,var(--bad) 85%,transparent);display:block;flex:none}.kc .m i.ok{background:var(--ok)}
.kc .m span{margin-left:6px}.kc .x{margin:8px 0 0 14px;color:var(--faint);font-size:12px;line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.kc .h{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:9px 0 0 14px;padding-top:8px;border-top:1px dashed var(--line)}
.kc .hb{display:inline-flex;align-items:center;gap:6px;border:0;background:transparent;color:var(--faint);font:inherit;font-size:12px;padding:2px 4px;margin-left:-4px;border-radius:7px;cursor:pointer;min-width:0}
.kc .hb:hover{color:var(--ink);background:var(--surface2)}.kc .hb svg{width:13px;height:13px;flex:none}.kc .hb span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kc .chip2{height:20px;font-size:11px;padding:0 8px;flex:none}
.kc.lock .grip{opacity:.25}
.ghost{position:fixed;z-index:80;pointer-events:none;cursor:grabbing;box-shadow:0 18px 40px -12px rgba(0,0,0,.55);border-color:var(--accent);transform-origin:50% 20%;opacity:.97}
.ph{border:2px dashed color-mix(in srgb,var(--accent) 60%,transparent);border-radius:14px;background:color-mix(in srgb,var(--accent) 8%,transparent);flex:none}
body.dragging,body.dragging *{cursor:grabbing!important;user-select:none!important;-webkit-user-select:none!important}
.kfoot{display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;color:var(--faint);font-size:12.5px;margin-top:2px}
.scrim{position:fixed;inset:0;background:rgba(0,0,0,.35);opacity:0;pointer-events:none;transition:opacity .2s;z-index:60}.scrim.on{opacity:1;pointer-events:auto}
.hd{position:fixed;top:0;right:0;bottom:0;width:400px;max-width:100vw;background:var(--surface);border-left:1px solid var(--line);z-index:70;transform:translateX(102%);transition:transform .25s cubic-bezier(.2,.8,.2,1);display:flex;flex-direction:column;box-shadow:-20px 0 50px -30px rgba(0,0,0,.5)}
.hd.on{transform:none}.hd header{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:18px 20px 12px}
.hd header b{font:600 18px var(--fd);display:block}.hd header span{color:var(--mut);font-size:13px;display:block;margin-top:3px}
.hd .x{border:0;background:var(--surface2);color:var(--mut);width:32px;height:32px;border-radius:10px;cursor:pointer;font-size:18px;line-height:1}.hd .x:hover{color:var(--ink)}
.hd .hf{display:flex;gap:6px;padding:0 20px 12px;border-bottom:1px solid var(--line)}
.hd .hf button{height:30px;padding:0 12px;border-radius:99px;border:1px solid var(--line);background:transparent;color:var(--mut);cursor:pointer;font-size:12.5px}.hd .hf button.on{background:var(--surface2);color:var(--ink);border-color:var(--line2)}
.hd .hbody{flex:1;overflow-y:auto;padding:6px 20px 24px}
.hday{font:500 11px var(--fb);letter-spacing:.12em;text-transform:uppercase;color:var(--faint);margin:18px 0 8px}
.he{display:flex;gap:12px;padding:9px 0;position:relative}.he:before{content:"";position:absolute;left:5px;top:24px;bottom:-9px;width:1px;background:var(--line)}.he:last-child:before{display:none}
.he .dot{flex:none;width:11px;height:11px;border-radius:50%;margin-top:5px;background:var(--accent);box-shadow:0 0 0 3px var(--surface)}.he .dot.rank{background:#e8762c}.he .dot.auto{background:var(--ok)}
.he .hl{font-size:13.5px;line-height:1.5}.he .hl b{font-weight:600}.he .arrow{color:var(--faint);margin:0 4px}
.he .pill2{display:inline-block;padding:1px 8px;border-radius:99px;background:var(--surface2);border:1px solid var(--line);font-size:12px;color:var(--ink);white-space:nowrap}
.he .pill2.num{color:#e8762c;font-weight:600}.he .hm{color:var(--faint);font-size:12px;margin-top:2px}
.hempty{color:var(--mut);font-size:13.5px;text-align:center;padding:36px 12px}.hempty b{display:block;color:var(--ink);margin-bottom:4px}
@media(max-width:900px){.kstrip{grid-template-columns:repeat(2,1fr)}.kstrip>div{border-bottom:1px solid var(--line)}.kcol2{flex-basis:84vw;width:84vw}}
"""

GRIP = '<svg viewBox="0 0 12 16"><circle cx="3" cy="3" r="1.4"/><circle cx="9" cy="3" r="1.4"/><circle cx="3" cy="8" r="1.4"/><circle cx="9" cy="8" r="1.4"/><circle cx="3" cy="13" r="1.4"/><circle cx="9" cy="13" r="1.4"/></svg>'


def board_page():
    body = (f'<div class="pagehead"><div><h1>Priority board</h1><p>Drag a card up or down to change its priority, or to another column to move its stage. '
            f'Every change is saved here and in the Google Sheet, and kept in the history.</p></div>'
            f'<div style="display:flex;gap:8px"><button class="btn" id="khist">{ico("clock")}History</button><button class="btn" id="kbrefresh">{ico("spark")}Refresh</button>'
            f'<a class="btn" href="{e(lp.sheet_url())}" target="_blank" rel="noopener">Open the Sheet{ico("ext")}</a></div></div>'
            f'<div class="kstrip" id="kk"></div><div class="kb" id="kb"></div>'
            f'<div class="kfoot"><span id="kmeta"></span><span>Seven checks: page, delivery set up, tracking, compliance pages, buyer, legal review, test delivery. '
            f'Live and Paused are set by publishing. A "Manual" card sits in a column its checks have not earned yet.</span></div>'
            f'<div class="scrim" id="scrim"></div><aside class="hd" id="hd" aria-hidden="true"><header><div><b id="hdt">History</b><span id="hds"></span></div>'
            f'<button class="x" id="hdx" aria-label="Close history">&times;</button></header>'
            f'<div class="hf"><button data-f="all" class="on">All</button><button data-f="stage">Stage moves</button><button data-f="rank">Priority</button></div>'
            f'<div class="hbody" id="hdb"></div></aside>')
    js = r"""<script>(function(){
 var GRIP='""" + GRIP + r"""', data=null, drag=null, saving=false, justDragged=false, hist={slug:null,filter:'all',entries:[]};
 function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
 function pd(s){return new Date(String(s).replace(' ','T')+'Z');}
 function rel(ts){var d=(pd(data?data.now:ts)-pd(ts))/1000;if(d<60)return 'just now';if(d<3600)return Math.floor(d/60)+' min ago';if(d<86400)return Math.floor(d/3600)+' h ago';if(d<172800)return 'yesterday';if(d<1209600)return Math.floor(d/86400)+' days ago';return Math.floor(d/604800)+' weeks ago';}
 function clock(ts){var d=pd(ts);return d.toLocaleString('en-GB',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit',timeZone:'UTC'});}
 function dayLabel(ts){var a=String(ts).slice(0,10),n=String(data.now).slice(0,10);if(a===n)return 'Today';var y=new Date(pd(data.now).getTime()-86400000).toISOString().slice(0,10);if(a===y)return 'Yesterday';return pd(ts).toLocaleDateString('en-GB',{weekday:'short',day:'numeric',month:'short',timeZone:'UTC'});}
 function kpis(k){var it=[['Brands',k.brands,k.live+' live, '+k.ready+' ready to launch'],['Ready to launch',k.ready,'All seven checks pass'],['In review',k.review,'Legal review or ready to test'],['Building',k.draft,'Draft or generated'],['Checks passing',k.checks_pct+'%',k.checks_ok+' of '+k.checks_total+' checks']];
  document.getElementById('kk').innerHTML=it.map(function(i){return '<div><span>'+i[0]+'</span><b>'+i[1]+'</b><small>'+i[2]+'</small></div>';}).join('');}
 function card(c){
  var dots=c.checks.map(function(x){return '<i class="'+(x.ok?'ok':'')+'" title="'+esc(x.label+': '+x.detail)+'"></i>';}).join('');
  var del=c.delivery&&c.delivery.length?' · '+c.delivery.join(', '):'';
  var mv=c.moved?('Moved from '+esc(c.moved.from)+' · '+rel(c.moved.ts)):'No moves yet';
  return '<div class="kc'+(c.locked?' lock':'')+'" tabindex="0" data-s="'+esc(c.slug)+'" data-st="'+esc(c.stage)+'"><div class="t"><span class="grip" title="Drag to move">'+GRIP+'</span><a class="nm" draggable="false" href="/studio/'+esc(c.slug)+'">'+esc(c.name)+'</a><span class="n">#'+c.priority+'</span></div>'+
   '<div class="s">'+esc(c.vertical||'Brand')+esc(del)+'</div><div class="m">'+dots+'<span>'+c.passed+' of '+c.checks.length+' checks</span></div><div class="x">'+esc(c.next)+'</div>'+
   '<div class="h"><button class="hb" data-h="'+esc(c.slug)+'" title="Show this brand\'s history"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg><span>'+mv+'</span></button>'+(c.manual?'<span class="chip2 warn" title="Its checks say '+esc(c.derived)+'">Manual</span>':'')+'</div></div>';
 }
 function render(){
  kpis(data.kpis);
  document.getElementById('kb').innerHTML=data.stages.map(function(st){
   var cs=data.cards.filter(function(c){return c.stage===st;}),lockcol=data.movable.indexOf(st)<0;
   return '<section class="kcol2'+(lockcol?' lockcol':'')+'" data-st="'+esc(st)+'"><header><b>'+esc(st)+'</b><em>'+cs.length+'</em></header><div class="hint">'+esc(data.hints[st]||'')+'</div><div class="kbody">'+cs.map(card).join('')+'</div></section>';
  }).join('');
  document.getElementById('kmeta').textContent='Updated '+data.fetched;
 }
 function load(fresh,quiet){
  return fetch('/api/board'+(fresh?'?fresh=1':'')).then(function(r){return r.json();}).then(function(j){
   if(!j.ok)return;if(quiet&&(drag||saving))return;
   var same=data&&JSON.stringify(data.cards)===JSON.stringify(j.cards);data=j;if(!same||!quiet){render();if(isOpen())loadHist();}
  });
 }
 /* ---- ordering */
 function cardOf(slug){return data.cards.filter(function(c){return c.slug===slug;})[0];}
 function newOrder(slug,toStage,idx){
  var cur=data.cards.map(function(c){return c.slug;});
  var members=data.cards.filter(function(c){return c.stage===toStage&&c.slug!==slug;}).map(function(c){return c.slug;});
  var list=members.slice();list.splice(Math.max(0,Math.min(idx,list.length)),0,slug);
  var pos=[];cur.forEach(function(s,i){if(members.indexOf(s)>=0||s===slug)pos.push(i);});
  var out=cur.slice();pos.forEach(function(p,i){out[p]=list[i];});return out;
 }
 function applyMove(slug,toStage,idx){
  var c=cardOf(slug),from=c.stage,order=newOrder(slug,toStage,idx),cur=data.cards.map(function(x){return x.slug;});
  if(toStage===from&&JSON.stringify(order)===JSON.stringify(cur)){render();return;}
  var oldRank=c.priority,prev=JSON.parse(JSON.stringify(data.cards));
  c.stage=toStage;c.manual=toStage!==c.derived;
  var by={};data.cards.forEach(function(x){by[x.slug]=x;});data.cards=order.map(function(s,i){by[s].priority=i+1;return by[s];});
  render();saving=true;
  fetch('/api/board/priority',{method:'POST',body:JSON.stringify({order:order,move:{slug:slug,to:toStage}})}).then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});}).then(function(x){
   saving=false;
   if(x.ok&&x.j.ok){
    var msg=(toStage!==from?(c.name+' moved to '+toStage+'. '):'')+(c.priority!==oldRank?('Priority #'+oldRank+' to #'+c.priority+'. '):'');
    toast((msg||'Saved. ')+(x.j.sheet===true?'Saved in the Sheet too.':'Sheet not updated: '+x.j.sheet),x.j.sheet===true);
    load(true,false);
   }else{data.cards=prev;render();toast(x.j.error||'Could not save the move',false);load(true,false);}
  }).catch(function(){saving=false;data.cards=prev;render();toast('Could not reach the studio',false);});
 }
 /* ---- drag with pointer events (mouse, pen and touch) */
 var kb=document.getElementById('kb'),last={x:0,y:0},raf=0;
 function target(x,y){
  var el=document.elementFromPoint(x,y),col=el&&el.closest?el.closest('.kcol2'):null;
  [].forEach.call(document.querySelectorAll('.kcol2'),function(c){c.classList.remove('ok','deny');});
  if(!col){drag.target=null;return;}
  var st=col.getAttribute('data-st'),same=st===drag.st,c=cardOf(drag.slug),allowed=same||(data.movable.indexOf(st)>=0&&!c.locked);
  if(!allowed){col.classList.add('deny');drag.target=null;return;}
  col.classList.add('ok');var body=col.querySelector('.kbody'),cs=[].filter.call(body.querySelectorAll('.kc'),function(n){return n!==drag.c;}),i=0;
  for(;i<cs.length;i++){var r=cs[i].getBoundingClientRect();if(y<r.top+r.height/2)break;}
  if(cs[i])body.insertBefore(drag.ph,cs[i]);else body.appendChild(drag.ph);drag.target={st:st,idx:i};
 }
 function loop(){
  if(!drag||!drag.active)return;
  var r=kb.getBoundingClientRect();
  if(last.x>r.right-70)kb.scrollLeft+=16;else if(last.x<r.left+70)kb.scrollLeft-=16;
  if(last.y>window.innerHeight-80)window.scrollBy(0,16);else if(last.y<80)window.scrollBy(0,-16);
  target(last.x,last.y);raf=requestAnimationFrame(loop);
 }
 function start(e){
  var c=drag.c,r=c.getBoundingClientRect(),g=c.cloneNode(true);g.classList.add('ghost');g.style.width=r.width+'px';g.style.left=r.left+'px';g.style.top=r.top+'px';
  document.body.appendChild(g);var ph=document.createElement('div');ph.className='ph';ph.style.height=r.height+'px';c.parentNode.insertBefore(ph,c);c.style.display='none';
  drag.ghost=g;drag.ph=ph;drag.active=true;document.body.classList.add('dragging');raf=requestAnimationFrame(loop);
 }
 function finish(commit){
  if(!drag)return;var d=drag;drag=null;cancelAnimationFrame(raf);
  if(d.active){d.ghost.remove();d.ph.remove();d.c.style.display='';document.body.classList.remove('dragging');
   [].forEach.call(document.querySelectorAll('.kcol2'),function(c){c.classList.remove('ok','deny');});
   justDragged=true;setTimeout(function(){justDragged=false;},0);
   if(commit&&d.target){applyMove(d.slug,d.target.st,d.target.idx);}
   else if(commit&&!d.target){var c=cardOf(d.slug);toast(c.locked?c.name+' is '+c.derived.toLowerCase()+'. Use publish or pause to change that.':'Drop it inside a column. Live and Paused are set by publishing.',false);}
  }
 }
 kb.addEventListener('pointerdown',function(e){
  if(e.button!==0||saving)return;var c=e.target.closest('.kc');if(!c||e.target.closest('button'))return;
  if(e.pointerType==='touch'&&!e.target.closest('.grip'))return;
  drag={c:c,slug:c.getAttribute('data-s'),st:c.getAttribute('data-st'),x:e.clientX,y:e.clientY,pid:e.pointerId,active:false,target:null};last={x:e.clientX,y:e.clientY};
 });
 document.addEventListener('pointermove',function(e){
  if(!drag||e.pointerId!==drag.pid)return;last={x:e.clientX,y:e.clientY};
  if(!drag.active){if(Math.hypot(e.clientX-drag.x,e.clientY-drag.y)<6)return;start(e);}
  e.preventDefault();drag.ghost.style.transform='translate('+(e.clientX-drag.x)+'px,'+(e.clientY-drag.y)+'px) rotate(2deg)';
 },{passive:false});
 document.addEventListener('pointerup',function(e){if(drag&&e.pointerId===drag.pid)finish(true);});
 document.addEventListener('pointercancel',function(){finish(false);});
 document.addEventListener('keydown',function(e){if(e.key==='Escape'){if(drag&&drag.active)finish(false);else closeHist();}});
 kb.addEventListener('click',function(e){if(justDragged){e.preventDefault();e.stopPropagation();}},true);
 kb.addEventListener('dragstart',function(e){e.preventDefault();});
 kb.addEventListener('mousedown',function(e){var c=e.target.closest&&e.target.closest('.kc');if(c&&!e.target.closest('button')){e.preventDefault();c.focus({preventScroll:true});}});
 /* keyboard: Alt+Up/Down changes priority inside the column, Alt+Left/Right moves the stage */
 kb.addEventListener('keydown',function(e){
  var c=e.target.closest&&e.target.closest('.kc');if(!c||!e.altKey)return;var slug=c.getAttribute('data-s'),k=cardOf(slug);
  var st=k.stage,col=data.cards.filter(function(x){return x.stage===st;}).map(function(x){return x.slug;}),i=col.indexOf(slug);
  if(e.key==='ArrowUp'||e.key==='ArrowDown'){e.preventDefault();var j=i+(e.key==='ArrowUp'?-1:1);if(j<0||j>=col.length)return;applyMove(slug,st,j);}
  else if(e.key==='ArrowLeft'||e.key==='ArrowRight'){
   e.preventDefault();if(k.locked)return;var mv=data.movable,m=mv.indexOf(st)+(e.key==='ArrowLeft'?-1:1);if(m<0||m>=mv.length)return;
   var tgt=mv[m],idx=data.cards.filter(function(x){return x.stage===tgt&&x.priority<k.priority;}).length;applyMove(slug,tgt,idx);
  }else return;
  setTimeout(function(){var n=document.querySelector('.kc[data-s="'+slug+'"]');if(n)n.focus();},60);
 });
 /* ---- history drawer */
 function isOpen(){return document.getElementById('hd').classList.contains('on');}
 function drawHist(){
  var f=hist.filter,es=hist.entries.filter(function(x){return f==='all'||x.type===f;}),b=document.getElementById('hdb'),html='',day='';
  if(!es.length){b.innerHTML='<div class="hempty"><b>No '+(f==='all'?'changes':(f==='stage'?'stage moves':'priority changes'))+' yet</b>Drag a card to start the history.</div>';return;}
  es.forEach(function(x){
   var dl=dayLabel(x.ts);if(dl!==day){day=dl;html+='<div class="hday">'+esc(dl)+'</div>';}
   var what=x.type==='stage'?('<b>'+esc(x.name)+'</b> <span class="pill2">'+esc(x.from)+'</span><span class="arrow">→</span><span class="pill2">'+esc(x.to)+'</span>'):('<b>'+esc(x.name)+'</b> priority <span class="pill2 num">#'+esc(x.from)+'</span><span class="arrow">→</span><span class="pill2 num">#'+esc(x.to)+'</span>');
   var by=x.mode==='checks'?'its checks moved it':(x.mode==='sheet'?'changed in the Sheet':'by '+esc(x.by));
   html+='<div class="he"><span class="dot '+(x.type==='rank'?'rank':(x.mode==='checks'?'auto':''))+'"></span><div><div class="hl">'+what+'</div><div class="hm" title="'+esc(clock(x.ts))+'">'+by+' · '+rel(x.ts)+' · '+esc(clock(x.ts))+'</div></div></div>';
  });
  b.innerHTML=html;
 }
 function loadHist(){
  return fetch('/api/board/history?limit=150'+(hist.slug?'&slug='+encodeURIComponent(hist.slug):'')).then(function(r){return r.json();}).then(function(j){hist.entries=j.entries||[];if(j.now&&data)data.now=j.now;drawHist();});
 }
 function openHist(slug){
  hist.slug=slug||null;var c=slug?cardOf(slug):null;
  document.getElementById('hdt').textContent=c?('History: '+c.name):'History';
  document.getElementById('hds').textContent=c?('Now in '+c.stage+', priority #'+c.priority):'Every move and priority change, newest first';
  document.getElementById('hd').classList.add('on');document.getElementById('scrim').classList.add('on');document.getElementById('hd').setAttribute('aria-hidden','false');
  document.getElementById('hdb').innerHTML='<div class="hempty">Loading</div>';loadHist();
 }
 function closeHist(){document.getElementById('hd').classList.remove('on');document.getElementById('scrim').classList.remove('on');document.getElementById('hd').setAttribute('aria-hidden','true');}
 document.getElementById('khist').onclick=function(){openHist(null);};
 document.getElementById('hdx').onclick=closeHist;document.getElementById('scrim').onclick=closeHist;
 [].forEach.call(document.querySelectorAll('.hf button'),function(b){b.onclick=function(){hist.filter=b.getAttribute('data-f');[].forEach.call(document.querySelectorAll('.hf button'),function(x){x.classList.toggle('on',x===b);});drawHist();};});
 kb.addEventListener('click',function(e){var h=e.target.closest&&e.target.closest('.hb');if(h){e.preventDefault();openHist(h.getAttribute('data-h'));}});
 document.getElementById('kbrefresh').onclick=function(){load(true,false).then(function(){toast('Reloaded from the Sheet');});};
 load(false,false);setInterval(function(){load(true,true);},20000);
})();</script>"""
    return shell("Priority board", body, "board", "<b>Priority board</b>", js)
