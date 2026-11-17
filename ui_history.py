"""History: one ledger of everything that happened in the studio, newest first, grouped by day, with filters, before/after wording
for edits, and a CSV export of exactly what is on screen."""
import ui
from ui import ico, shell

ui.CSS = ui.CSS + """
.hx-filters{display:grid;grid-template-columns:minmax(200px,1.4fr) repeat(4,minmax(140px,1fr));gap:10px;align-items:end;padding:16px 18px;margin-bottom:12px}
.hx-filters label{display:block;font:600 10.5px var(--fb);letter-spacing:.08em;text-transform:uppercase;color:var(--faint);margin-bottom:6px}
.hx-filters input[type=text],.hx-filters select{width:100%;height:36px;padding:0 10px;font:inherit;font-size:13px;color:var(--ink)}
.hx-cats{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:16px}
.hx-auto{display:inline-flex;align-items:center;gap:8px;font-size:12.5px;color:var(--mut);cursor:pointer;white-space:nowrap}
.hx-sum{color:var(--faint);font-size:12.5px;margin:0 0 10px}
.hx-day{position:sticky;top:58px;z-index:5;display:flex;align-items:baseline;justify-content:space-between;gap:10px;padding:14px 4px 8px;margin-top:6px;
 background:linear-gradient(var(--bg) 70%,transparent);font:500 19px var(--fd);letter-spacing:-.01em}
.hx-day small{font:500 11.5px var(--fm);color:var(--faint);letter-spacing:0}
.hx-list{background:var(--surface);border:1px solid var(--line);border-radius:12px;overflow:hidden;box-shadow:0 1px 2px rgba(17,24,39,.03)}
.hx{display:grid;grid-template-columns:62px 150px minmax(0,1fr) 190px;gap:14px;align-items:start;padding:12px 16px;border-top:1px solid var(--line);transition:background .15s}
.hx:first-child{border-top:0}.hx:hover{background:color-mix(in srgb,var(--surface2) 55%,transparent)}
.hx .tm{font:500 12px/20px var(--fm);color:var(--mut)}
.hx .ct{display:flex;align-items:center;gap:7px;font-size:12px;color:var(--mut);line-height:20px;min-width:0}
.hx .ct i{width:8px;height:8px;border-radius:2px;flex:none;background:var(--cc,var(--faint))}
.hx .ct span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hx .wh{min-width:0}.hx .wh b{font-weight:500;font-size:13.5px;line-height:20px;overflow-wrap:anywhere}
.hx .wh .br{color:var(--accent);font-weight:600;margin-right:6px}.hx .wh .br:hover{text-decoration:underline}
.hx .wh .nt{display:block;color:var(--mut);font-size:12.5px;line-height:1.5;margin-top:2px;overflow-wrap:anywhere;white-space:pre-line}
.hx .tn{display:inline-block;width:6px;height:6px;border-radius:50%;margin:0 7px 2px 0;vertical-align:middle;background:var(--faint)}
.hx .tn.t-ok{background:var(--ok)}.hx .tn.t-warn{background:var(--warn)}.hx .tn.t-bad{background:var(--bad)}
.hx .by{display:flex;align-items:center;gap:8px;min-width:0;font-size:12.5px;color:var(--mut);justify-content:flex-end}
.hx .by span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hx .by em{flex:none;width:22px;height:22px;border-radius:6px;display:grid;place-items:center;font:600 10.5px var(--fb);font-style:normal;color:var(--accent);background:color-mix(in srgb,var(--accent) 10%,var(--surface));box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--accent) 22%,transparent)}
.hx .by em.sys{color:var(--faint);background:var(--surface2);box-shadow:inset 0 0 0 1px var(--line)}
.hx .auto{font:500 10px var(--fb);letter-spacing:.06em;text-transform:uppercase;color:var(--faint);border:1px solid var(--line);border-radius:4px;padding:0 5px;margin-left:6px;vertical-align:1px}
.hx-tg{border:0;background:none;color:var(--accent);font:500 12px var(--fb);cursor:pointer;padding:0;margin-top:6px;display:flex;align-items:center;gap:5px}
.hx-tg svg{width:12px;height:12px;transition:transform .25s var(--ease)}.hx.open .hx-tg svg{transform:rotate(90deg)}
.hx-ch{display:none;margin-top:10px;border:1px solid var(--line);border-radius:9px;overflow:hidden}.hx.open .hx-ch{display:block;animation:rise .3s var(--ease)}
.hx-ch>div{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid var(--line)}.hx-ch>div:first-child{border-top:0}
.hx-ch p{margin:0;padding:9px 12px;font-size:12.5px;line-height:1.5;overflow-wrap:anywhere}
.hx-ch .bf{background:color-mix(in srgb,var(--bad) 5%,transparent);color:var(--mut);text-decoration:line-through;text-decoration-color:color-mix(in srgb,var(--bad) 45%,transparent)}
.hx-ch .af{background:color-mix(in srgb,var(--ok) 6%,transparent);border-left:1px solid var(--line)}
.hx-ch .hd2{background:var(--surface2);font:600 10px var(--fb);letter-spacing:.08em;text-transform:uppercase;color:var(--faint);text-decoration:none;padding:6px 12px}
.hx-more{display:flex;justify-content:center;margin:16px 0 4px}
@media(max-width:1100px){.hx-filters{grid-template-columns:1fr 1fr}.hx{grid-template-columns:56px minmax(0,1fr)}.hx .ct,.hx .by{grid-column:2;justify-content:flex-start}.hx .ct{order:-1}}
"""

CAT_COLORS = {"legal": "var(--accent)", "pages": "#2f7d6b", "board": "var(--prio)", "delivery": "#6b5bb5", "crm": "#3f7fb0", "sheet": "#2f8a4c",
              "media": "#a05a8c", "system": "var(--faint)"}


def history_page():
    body = ('<div class="pagehead"><div><h1>History</h1><p>A complete record of what happened in the studio: legal reviews and sign-offs, wording edits, '
            'generated and published pages, board moves, integrations and errors. Each entry shows who did it and when; wording edits keep the exact before and after.</p></div>'
            f'<div style="display:flex;gap:8px"><a class="btn" id="hxcsv" href="/api/history.csv">{ico("ext")}Export CSV</a></div></div>'
            '<section class="panel hx-filters"><div><label for="hxq">Search</label><input type="text" id="hxq" placeholder="Words, names, claims"></div>'
            '<div><label for="hxb">Brand</label><select id="hxb"><option value="">All brands</option></select></div>'
            '<div><label for="hxa">Person</label><select id="hxa"><option value="">Everyone</option></select></div>'
            '<div><label for="hxs">Period</label><select id="hxs"><option value="1">Last 24 hours</option><option value="7">Last 7 days</option>'
            '<option value="30" selected>Last 30 days</option><option value="90">Last 90 days</option><option value="">All time</option></select></div>'
            '<div><label for="hxc">Category</label><select id="hxc"><option value="">All categories</option></select></div></section>'
            '<div class="hx-cats"><p class="hx-sum" id="hxsum" style="margin:0">Loading</p>'
            '<label class="hx-auto"><input type="checkbox" id="hxauto"> Include automatic activity (syncs, refreshes, simulated data)</label></div>'
            '<div id="hxout"><div class="empty">Loading</div></div><div class="hx-more"><button class="btn" id="hxmore" style="display:none">Load older entries</button></div>')
    js = r"""<script>(function(){
 var CC=""" + str(CAT_COLORS).replace("'", '"') + r""",LB={},F={},next=null,busy=false,lastDay='',count=0;
 var $=function(id){return document.getElementById(id);};
 function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
 function pd(ts){return new Date(String(ts).replace(' ','T')+'Z');}
 function dayKey(d){return d.getFullYear()+'-'+d.getMonth()+'-'+d.getDate();}
 function dayLabel(d){var t=new Date(),y=new Date(Date.now()-864e5);if(dayKey(d)===dayKey(t))return 'Today';if(dayKey(d)===dayKey(y))return 'Yesterday';
  return d.toLocaleDateString(undefined,{weekday:'long',day:'numeric',month:'long',year:'numeric'});}
 function initials(a){if(!a||a==='system')return 'S';var n=a.split('@')[0].split(/[._\-\s]+/);return ((n[0]||'')[0]+((n[1]||'')[0]||'')).toUpperCase();}
 function who(a){return a==='system'?'System':(a.indexOf('@')>0?a.split('@')[0].replace(/[._]/g,' ').replace(/\b\w/g,function(c){return c.toUpperCase();}):a);}
 function row(e){
  var d=pd(e.ts),tm=d.toLocaleTimeString(undefined,{hour:'2-digit',minute:'2-digit'}),h='';
  h+='<div class="hx" data-id="'+e.id+'"><span class="tm" title="'+esc(d.toString())+'">'+tm+'</span>';
  h+='<span class="ct" style="--cc:'+(CC[e.category]||'var(--faint)')+'"><i></i><span>'+esc(LB[e.category]||e.category)+'</span></span>';
  h+='<div class="wh">'+(e.tone?'<span class="tn t-'+e.tone+'"></span>':'')+(e.slug?'<a class="br" href="/studio/'+esc(e.slug)+'">'+esc(e.brand)+'</a>':'')+'<b>'+esc(e.summary)+'</b>'+(e.automatic?'<span class="auto">Auto</span>':'');
  if(e.note){h+='<span class="nt">'+esc(e.note)+'</span>';}
  if(e.changes&&e.changes.length){
   h+='<button class="hx-tg" data-tg><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M9 6l6 6-6 6"/></svg>Show '+(e.changes.length===1?'the change':'all '+e.changes.length+' changes')+'</button>';
   h+='<div class="hx-ch"><div><p class="hd2">Before</p><p class="hd2" style="border-left:1px solid var(--line)">After</p></div>'+e.changes.map(function(c){return '<div><p class="bf">'+esc(c.from)+'</p><p class="af">'+esc(c.to)+(c.restored?' <span class="auto">Restored</span>':'')+'</p></div>';}).join('')+'</div>';}
  h+='</div><span class="by" title="'+esc(e.actor)+'"><span>'+esc(who(e.actor))+'</span><em class="'+(e.actor==='system'?'sys':'')+'">'+esc(initials(e.actor))+'</em></span></div>';
  return h;
 }
 function render(list,append){
  var out=$('hxout'),html='',groups=[],cur=null;
  if(!append){out.innerHTML='';lastDay='';count=0;}
  list.forEach(function(e){var d=pd(e.ts),k=dayKey(d);if(!cur||cur.k!==k){cur={k:k,d:d,items:[]};groups.push(cur);}cur.items.push(e);});
  groups.forEach(function(g){
   var host;
   if(g.k===lastDay){var ls=out.querySelectorAll('.hx-list');host=ls[ls.length-1];}
   if(!host){var hd=document.createElement('div');hd.className='hx-day';hd.innerHTML=esc(dayLabel(g.d))+'<small data-n="'+g.k+'"></small>';out.appendChild(hd);
    host=document.createElement('div');host.className='hx-list stagger';out.appendChild(host);}
   var start=host.children.length;host.insertAdjacentHTML('beforeend',g.items.map(row).join(''));
   [].slice.call(host.children,start).forEach(function(n,i){n.style.setProperty('--i',Math.min(i,12));});
   var sm=out.querySelector('small[data-n="'+g.k+'"]');sm.textContent=host.children.length+(host.children.length===1?' entry':' entries');
   lastDay=g.k;
  });
  count+=list.length;
  if(!count){out.innerHTML='<div class="empty">Nothing recorded for these filters yet.</div>';}
 }
 function params(){var p={};['q','slug','actor','cat','auto'].forEach(function(k){if(F[k])p[k]=F[k];});
  if(F.days){var d=new Date(Date.now()-F.days*864e5);p.since=d.toISOString().slice(0,19).replace('T',' ');}return p;}
 function qs(p){return Object.keys(p).map(function(k){return k+'='+encodeURIComponent(p[k]);}).join('&');}
 function load(append){
  if(busy)return;busy=true;var p=params();if(append&&next){p.before=next;}
  $('hxcsv').href='/api/history.csv?'+qs(params());
  fetch('/api/history?'+qs(p)).then(function(r){return r.json();}).then(function(j){
   busy=false;next=j.next;render(j.events,append);$('hxmore').style.display=j.more?'':'none';
   $('hxsum').textContent=count?('Showing '+count+(j.more?'+':'')+' entr'+(count===1?'y':'ies')+'. Times are in your local time zone.'):'';
  }).catch(function(){busy=false;toast('Could not load the history',false);});
 }
 function sync(){var p={};['q','slug','actor','cat'].forEach(function(k){if(F[k])p[k]=F[k];});if(F.days!=='30')p.days=F.days;if(F.auto)p.auto='1';
  history.replaceState(null,'',location.pathname+(Object.keys(p).length?'?'+qs(p):''));}
 function read(){F={q:$('hxq').value.trim(),slug:$('hxb').value,actor:$('hxa').value,cat:$('hxc').value,days:$('hxs').value,auto:$('hxauto').checked?'1':''};}
 function go(){read();sync();next=null;load(false);}
 var t=null;$('hxq').addEventListener('input',function(){clearTimeout(t);t=setTimeout(go,300);});
 ['hxb','hxa','hxc','hxs','hxauto'].forEach(function(id){$(id).addEventListener('change',go);});
 $('hxmore').onclick=function(){load(true);};
 $('hxout').addEventListener('click',function(ev){var b=ev.target.closest('[data-tg]');if(!b)return;var r=b.closest('.hx');r.classList.toggle('open');
  var n=r.querySelectorAll('.hx-ch>div').length-1;b.lastChild.textContent=r.classList.contains('open')?'Hide':('Show '+(n===1?'the change':'all '+n+' changes'));});
 fetch('/api/history/facets').then(function(r){return r.json();}).then(function(f){
  f.categories.forEach(function(c){LB[c[0]]=c[1];$('hxc').insertAdjacentHTML('beforeend','<option value="'+c[0]+'">'+esc(c[1])+'</option>');});
  f.brands.forEach(function(b){$('hxb').insertAdjacentHTML('beforeend','<option value="'+esc(b[0])+'">'+esc(b[1])+'</option>');});
  f.people.forEach(function(p){$('hxa').insertAdjacentHTML('beforeend','<option value="'+esc(p)+'">'+esc(who(p))+' ('+esc(p)+')</option>');});
  var u=new URLSearchParams(location.search);$('hxq').value=u.get('q')||'';$('hxb').value=u.get('slug')||'';$('hxa').value=u.get('actor')||'';$('hxc').value=u.get('cat')||'';
  if(u.has('days'))$('hxs').value=u.get('days');$('hxauto').checked=u.get('auto')==='1';
  read();load(false);
 });
})();</script>"""
    return shell("History", body, "history", "<b>History</b>", js)
