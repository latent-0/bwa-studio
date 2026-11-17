"""Legal review: a list of every brand's review state, and a per-brand screen where a reviewer (Tina or anyone on the team) edits the
page's wording line by line, marks flagged claims as fine, and signs off. Saving rebuilds the page with the new wording straight away."""
import ui
from ui import e, ico, shell

ui.CSS = ui.CSS + """
.rvtbl td:first-child{min-width:220px}
.rvst{display:flex;align-items:center;gap:8px}
.rv{display:grid;grid-template-columns:minmax(0,1fr) minmax(360px,44%);gap:18px;align-items:start}
.rvlist{display:grid;gap:8px}
.rvbar{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-bottom:12px}
.rvrow{background:var(--surface);border:1px solid var(--line);border-left:3px solid transparent;border-radius:10px;padding:12px 14px;transition:border-color .2s,box-shadow .2s var(--ease)}
.rvrow:focus-within{border-color:var(--line2);box-shadow:var(--shadow)}
.rvrow.flag{border-left-color:var(--warn)}.rvrow.flag.okd{border-left-color:var(--ok)}.rvrow.dirty{border-left-color:var(--accent)}
.rvh{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px}
.rvk{font:600 10.5px var(--fb);letter-spacing:.08em;text-transform:uppercase;color:var(--faint)}
.rvh .grow{flex:1}
.rvrow textarea{min-height:0;resize:vertical;line-height:1.5;padding:9px 11px;font-size:14px}
.rvwas{margin:8px 0 0;font-size:12.5px;color:var(--mut);line-height:1.5}.rvwas b{font-weight:600;color:var(--faint);font-size:11px;letter-spacing:.06em;text-transform:uppercase;margin-right:6px}
.rvflags{display:grid;gap:6px;margin-top:9px}
.rvflag{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:7px 10px;border-radius:8px;background:color-mix(in srgb,var(--warn) 9%,transparent);font-size:12.5px}
.rvflag.okd{background:color-mix(in srgb,var(--ok) 9%,transparent)}
.rvflag q{font-weight:600;quotes:"\\201C" "\\201D"}.rvflag .grow{flex:1;min-width:120px;color:var(--mut)}
.rvflag label{display:inline-flex;align-items:center;gap:6px;cursor:pointer;font-weight:500;white-space:nowrap}
.linkbtn{border:0;background:none;color:var(--accent);cursor:pointer;font:500 12.5px var(--fb);padding:0}.linkbtn:hover{text-decoration:underline}
.rvside{position:sticky;top:76px}
.rvprev{height:min(68vh,760px)}
.rvact{position:sticky;bottom:0;z-index:15;margin-top:16px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:12px 14px;border:1px solid var(--line2);border-radius:12px;
 background:color-mix(in srgb,var(--surface) 92%,transparent);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);box-shadow:0 -10px 30px -18px rgba(17,24,39,.35)}
.rvact .cnt{font:500 12.5px var(--fm);color:var(--mut);white-space:nowrap}
.rvact input[type=text]{flex:1 1 180px;height:36px;padding:0 12px}
.rvact .who{font-size:12.5px;color:var(--mut);white-space:nowrap}.rvact .who b{color:var(--ink);font-weight:600}
.rvsec{font:600 11px var(--fb);letter-spacing:.09em;text-transform:uppercase;color:var(--mut);margin:20px 0 8px}
.tabs#rvpages{overflow-x:auto;flex-wrap:nowrap}.tabs#rvpages button{flex:none}.tabs#rvpages button[disabled]{opacity:.4;cursor:not-allowed}
.rvhelp{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px}
.rvhelp div{padding:12px 14px;border-radius:10px;background:var(--surface);border:1px solid var(--line);font-size:12.5px;color:var(--mut);line-height:1.5}
.rvhelp b{display:block;color:var(--ink);font-weight:600;font-size:13px;margin-bottom:2px}.rvhelp i{font:500 11px var(--fm);font-style:normal;color:var(--accent);display:block;margin-bottom:6px}
@media(max-width:1180px){.rv{grid-template-columns:1fr}.rvside{position:static}.rvhelp{grid-template-columns:1fr}}
"""

STATE = {"approved": ("ok", "Approved"), "needs_review": ("acc", "Ready for sign-off"), "claims_open": ("warn", "Claims to clear"),
         "stale": ("bad", "Changed since sign-off"), "not_generated": ("", "No page yet")}


def list_page():
    body = ('<div class="pagehead"><div><h1>Legal review</h1><p>Review the wording on every brand\'s landing page and its legal pages (privacy, terms, CCPA and the rest). Edit any line, mark flagged claims as fine, '
            'and sign off. Saving rebuilds the page straight away, and your edits are kept when the page is regenerated.</p></div></div>'
            '<div class="filters" id="rvf"><button data-f="todo" class="on">Needs review</button><button data-f="approved">Approved</button><button data-f="all">All</button></div>'
            '<section class="panel"><table class="tbl rvtbl"><thead><tr><th>Brand</th><th>Status</th><th>Flagged claims</th><th>Wording edits</th><th>Last sign-off</th><th></th></tr></thead>'
            '<tbody id="rvl"><tr><td colspan="6"><div class="empty">Loading</div></td></tr></tbody></table></section>')
    js = r"""<script>(function(){
 var ST=""" + str({k: list(v) for k, v in STATE.items()}).replace("'", '"') + r""",rows=[],f='todo';
 function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
 var ORDER={stale:0,claims_open:1,needs_review:2,not_generated:4,approved:3};
 function draw(){
  var rs=rows.filter(function(r){return f==='all'||(f==='approved'?r.state==='approved':(r.state!=='approved'&&r.state!=='not_generated'));});
  rs.sort(function(a,b){return ORDER[a.state]-ORDER[b.state]||a.name.localeCompare(b.name);});
  var tb=document.getElementById('rvl');
  if(!rs.length){tb.innerHTML='<tr><td colspan="6"><div class="empty">'+(f==='todo'?'Nothing waiting for review.':'No brands here yet.')+'</div></td></tr>';return;}
  tb.innerHTML=rs.map(function(r){var s=ST[r.state]||['',r.state];
   return '<tr><td><div class="sb"><span class="avatar sm" style="--c:'+esc(r.color)+'">'+esc(r.name[0])+'</span><div><b>'+esc(r.name)+'</b><div class="mut" style="font-size:12px;text-transform:capitalize">'+esc(r.vertical)+'</div></div></div></td>'+
    '<td><span class="chip2 '+s[0]+'">'+s[1]+'</span><div class="mut" style="font-size:12px;margin-top:4px">'+esc(r.label)+'</div></td>'+
    '<td>'+(r.flags?(r.open?'<b>'+r.open+'</b> open of '+r.flags:r.flags+' cleared'):'<span class="mut">None</span>')+'</td>'+
    '<td>'+(r.edits?r.edits:'<span class="mut">None</span>')+'</td>'+
    '<td class="mut">'+(r.reviewed?esc(r.reviewed.by)+'<br>'+esc(r.reviewed.date):'Not yet')+'</td>'+
    '<td style="text-align:right">'+(r.state==='not_generated'?'<a class="btn" href="/studio/'+esc(r.slug)+'">Open studio</a>':'<a class="btn'+(r.state==='approved'?'':' primary')+'" href="/review/'+esc(r.slug)+'">Review<svg class="i"><use href="#i-arrow"/></svg></a>')+'</td></tr>';}).join('');
  if(window.stagger){tb.classList.remove('stagger');window.stagger(tb.parentNode.parentNode);}
 }
 [].forEach.call(document.querySelectorAll('#rvf button'),function(b){b.onclick=function(){f=b.getAttribute('data-f');[].forEach.call(document.querySelectorAll('#rvf button'),function(x){x.classList.toggle('on',x===b);});draw();};});
 fetch('/api/review').then(function(r){return r.json();}).then(function(j){rows=j;
  var todo=rows.filter(function(r){return r.state!=='approved'&&r.state!=='not_generated';}).length,ap=rows.filter(function(r){return r.state==='approved';}).length;
  var bs=document.querySelectorAll('#rvf button');bs[0].textContent='Needs review ('+todo+')';bs[1].textContent='Approved ('+ap+')';bs[2].textContent='All ('+rows.length+')';draw();});
})();</script>"""
    return shell("Legal review", body, "review", "<b>Legal review</b>", js)


def review_page(slug):
    import core
    b = core.get_brand(slug)
    body = (f'<div class="bh"><span class="avatar" style="--c:{e(b["accent_color"] or b["primary_color"] or "#6b8cff")};width:48px;height:48px;font-size:20px">{e(b["name"][:1])}</span>'
            f'<div class="grow"><h1>{e(b["name"])}</h1><div class="meta">Legal wording review</div></div>'
            f'<span class="chip2" id="rvchip">Loading</span>'
            f'<div class="acts"><a class="btn" id="rvopen" href="/p/{e(slug)}/" target="_blank">{ico("ext")}Open the page</a><a class="btn" href="/studio/{e(slug)}">Studio</a></div></div>'
            '<div class="rvhelp"><div><i>01</i><b>Edit the wording</b>Pick a page above, then change any line. Lines with risky claims are marked in amber.</div>'
            '<div><i>02</i><b>Clear what is fine</b>If a flagged claim is acceptable as written, tick "OK as written".</div>'
            '<div><i>03</i><b>Save or sign off</b>Saving rebuilds the page now. Sign off records your approval for go-live.</div></div>'
            '<div class="tabs" id="rvpages"></div>'
            '<div class="rv"><div class="col"><div class="rvbar"><div class="seg" id="rvseg"><button data-m="flag" class="on">Flagged</button><button data-m="edited">Edited</button><button data-m="all">All text</button></div>'
            '<input type="text" id="rvq" placeholder="Search the wording" style="max-width:240px;height:34px;padding:0 12px"></div>'
            '<div class="rvlist" id="rvlist"><div class="empty">Loading</div></div><div id="rvextra"></div>'
            '<div class="rvact"><span class="cnt" id="rvcnt">0 changes</span><span class="who" id="rvwho"></span>'
            '<input type="text" id="rvnote" placeholder="Note for the record (optional)">'
            '<button class="btn" id="rvsave"><span class="spin"></span>Save changes</button>'
            f'<button class="btn primary" id="rvsign"><span class="spin"></span>{ico("check")}Save and sign off</button></div></div>'
            '<aside class="rvside"><section class="panel" style="padding:14px"><div class="rvbar" style="margin-bottom:10px"><span class="tag" id="rvptitle">Live preview</span>'
            '<button class="linkbtn" id="rvreload">Reload</button></div><div class="frame"><div class="stage rvprev" id="rvstage">'
            f'<iframe id="rvframe" src="about:blank" title="Page preview"></iframe></div></div>'
            '<p class="hint">Saving updates this page right away. One sign-off covers the landing page and all its legal pages. If the brand is already live, publish again from the Go-live tab to push the new wording to the live site.</p></section></aside></div>')
    js = r"""<script>(function(){
 var slug='""" + e(slug) + r"""',data=null,mode='flag',q='',dirty={},clear={},busy=false,pg=(location.hash.slice(1)||'index');
 var ST=""" + str({k: list(v) for k, v in STATE.items()}).replace("'", '"') + r""";
 var $=function(id){return document.getElementById(id);};
 function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
 function fit(){var st=$('rvstage'),f=$('rvframe');if(!st||!f)return;var k=Math.min(1,st.clientWidth/1280);f.style.width='1280px';f.style.height=(st.clientHeight/k)+'px';f.style.transform='scale('+k+')';}
 window.addEventListener('resize',fit);
 function count(){var n=Object.keys(dirty).length,c=Object.keys(clear).length;$('rvcnt').textContent=n+' edit'+(n===1?'':'s')+(c?', '+c+' cleared':'');}
 function grow(t){t.style.height='auto';t.style.height=(t.scrollHeight+2)+'px';}
 function row(b){
  var fl=b.flags||[],open=fl.filter(function(h){return !h.cleared&&!clear[h.id];}).length,val=dirty[b.id]!=null?dirty[b.id]:b.text;
  var cls='rvrow'+(fl.length?' flag':'')+(fl.length&&!open?' okd':'')+(dirty[b.id]!=null?' dirty':'');
  var h='<div class="'+cls+'" data-id="'+b.id+'"><div class="rvh"><span class="rvk">'+esc(b.kind)+'</span>';
  if(b.edited){h+='<span class="chip2 acc" title="Edited by '+esc(b.by)+' on '+esc(b.ts)+'">Edited by '+esc(b.by)+'</span>';}
  if(fl.length){h+='<span class="chip2 '+(open?'warn':'ok')+'">'+(open?open+' claim'+(open===1?'':'s')+' to check':'Claims cleared')+'</span>';}
  h+='<span class="grow"></span>';
  if(b.edited||dirty[b.id]!=null){h+='<button class="linkbtn" data-undo="'+b.id+'">'+(dirty[b.id]!=null?'Discard':'Restore original')+'</button>';}
  h+='</div><textarea rows="1" data-t="'+b.id+'" aria-label="'+esc(b.kind)+'">'+esc(val)+'</textarea>';
  if(b.edited||dirty[b.id]!=null){h+='<p class="rvwas"><b>Original</b>'+esc(b.original)+'</p>';}
  if(fl.length){h+='<div class="rvflags">'+fl.map(function(f){var ok=f.cleared||clear[f.id];return '<div class="rvflag'+(ok?' okd':'')+'"><q>'+esc(f.phrase)+'</q><span class="grow">'+esc(f.category)+'</span>'+
   (f.cleared?'<span class="chip2 ok">Cleared</span>':'<label><input type="checkbox" data-c="'+f.id+'"'+(clear[f.id]?' checked':'')+'> OK as written</label>')+'</div>';}).join('')+'</div>';}
  return h+'</div>';
 }
 function draw(){
  var bs=data.blocks.filter(function(b){
   if(mode==='flag'&&!(b.flags&&b.flags.length))return false;
   if(mode==='edited'&&!(b.edited||dirty[b.id]!=null))return false;
   return !q||(b.text+' '+b.original).toLowerCase().indexOf(q)>=0;});
  var nf=data.blocks.filter(function(b){return b.flags&&b.flags.length;}).length,ne=data.blocks.filter(function(b){return b.edited;}).length;
  var sb=document.querySelectorAll('#rvseg button');sb[0].textContent='Flagged ('+nf+')';sb[1].textContent='Edited ('+ne+')';sb[2].textContent='All text ('+data.blocks.length+')';
  $('rvlist').innerHTML=bs.length?bs.map(row).join(''):'<div class="empty">'+(mode==='flag'?'No flagged claims on this page.':(mode==='edited'?'No edits yet.':'Nothing matches.'))+'</div>';
  [].forEach.call(document.querySelectorAll('#rvlist textarea'),grow);
  var x='';
  if(data.loose_flags.length){x+='<div class="rvsec">Other flagged claims</div><div class="rvlist">'+data.loose_flags.map(function(f){var ok=f.cleared||clear[f.id];return '<div class="rvrow flag'+(ok?' okd':'')+'"><div class="rvflag'+(ok?' okd':'')+'"><q>'+esc(f.phrase)+'</q><span class="grow">'+esc(f.category)+': '+esc(f.context)+'</span>'+(f.cleared?'<span class="chip2 ok">Cleared</span>':'<label><input type="checkbox" data-c="'+f.id+'"'+(clear[f.id]?' checked':'')+'> OK as written</label>')+'</div></div>';}).join('')+'</div>';}
  if(data.unmatched.length){x+='<div class="rvsec">Edits that no longer match the page</div><p class="hint" style="margin:0 0 8px">The page was regenerated and these lines changed, so the edits could not be applied. Re-apply the wording above if it is still needed.</p><div class="rvlist">'+
   data.unmatched.map(function(u){return '<div class="rvrow"><p class="rvwas" style="margin:0"><b>Was</b>'+esc(u.original)+'</p><p class="rvwas"><b>Edited to</b>'+esc(u.text)+'</p><div class="rvh" style="margin:8px 0 0"><span class="mut" style="font-size:12px">'+esc(u.by||'')+' '+esc(u.ts||'')+'</span><span class="grow"></span><button class="linkbtn" data-forget="'+esc(u.original)+'">Remove</button></div></div>';}).join('')+'</div>';}
  $('rvextra').innerHTML=x;
  var s=ST[data.status.state]||['',''];$('rvchip').className='chip2 '+s[0];$('rvchip').textContent=s[1];$('rvchip').title=data.status.label;
  $('rvwho').innerHTML=data.who?'Reviewing as <b>'+esc(data.who)+'</b>':'';
  if(!data.who&&!$('rvby')){var i=document.createElement('input');i.type='text';i.id='rvby';i.placeholder='Your name';i.style.flex='0 1 150px';$('rvnote').parentNode.insertBefore(i,$('rvnote'));}
  count();
 }
 function purl(){var f=(data&&data.pages.filter(function(p){return p.key===pg;})[0]);return '/p/'+slug+'/'+(pg==='index'?'':(f?f.file:pg+'.html'));}
 function tabs(){
  $('rvpages').innerHTML=data.pages.map(function(p){return '<button data-pg="'+p.key+'" class="'+(p.key===pg?'on':'')+'"'+(p.exists?'':' disabled title="Not generated yet"')+'>'+esc(p.title)+(p.edits?'<span class="tdot" style="background:var(--accent)">'+p.edits+'</span>':'')+'</button>';}).join('');
  $('rvopen').href=purl();var cur=data.pages.filter(function(p){return p.key===pg;})[0];$('rvptitle').textContent='Live preview: '+(cur?cur.title:'');
  $('rvseg').querySelector('[data-m=flag]').style.display=pg==='index'?'':'none';
 }
 function load(first){return fetch('/api/review/'+slug+'?page='+encodeURIComponent(pg)).then(function(r){return r.json();}).then(function(j){
  data=j;if(pg!=='index'&&mode==='flag'){mode='all';}
  if(first&&pg==='index'&&!data.blocks.some(function(b){return b.flags&&b.flags.length;})&&!data.loose_flags.length){mode='all';}
  [].forEach.call(document.querySelectorAll('#rvseg button'),function(x){x.classList.toggle('on',x.getAttribute('data-m')===mode);});
  tabs();draw();var fr=$('rvframe');if(fr.getAttribute('data-pg')!==pg){fr.setAttribute('data-pg',pg);fr.src=purl();}});}
 $('rvpages').addEventListener('click',function(ev){var b=ev.target.closest('[data-pg]');if(!b||b.disabled||b.getAttribute('data-pg')===pg)return;
  if(Object.keys(dirty).length&&!confirm('You have unsaved edits on this page. Switch and discard them?'))return;
  dirty={};clear={};pg=b.getAttribute('data-pg');history.replaceState(null,'','#'+pg);mode=pg==='index'?'flag':'all';q='';$('rvq').value='';load(true);});
 document.addEventListener('input',function(ev){var t=ev.target;
  if(t.getAttribute&&t.getAttribute('data-t')){var id=t.getAttribute('data-t'),b=data.blocks.filter(function(x){return x.id===id;})[0];grow(t);
   if(t.value.trim()===b.text.trim()){delete dirty[id];}else{dirty[id]=t.value;}
   var r=t.closest('.rvrow');r.classList.toggle('dirty',dirty[id]!=null);count();}
  if(ev.target.id==='rvq'){q=ev.target.value.trim().toLowerCase();draw();}});
 document.addEventListener('change',function(ev){var c=ev.target.getAttribute&&ev.target.getAttribute('data-c');if(c){if(ev.target.checked){clear[c]=1;}else{delete clear[c];}draw();}});
 document.addEventListener('click',function(ev){
  var u=ev.target.closest('[data-undo]');if(u){var id=u.getAttribute('data-undo'),b=data.blocks.filter(function(x){return x.id===id;})[0];
   if(dirty[id]!=null){delete dirty[id];}else{dirty[id]=b.original;}draw();return;}
  var fg=ev.target.closest('[data-forget]');if(fg){fetch('/api/review/forget',{method:'POST',body:JSON.stringify({slug:slug,page:pg,original:fg.getAttribute('data-forget')})}).then(function(r){return r.json();}).then(function(j){data=j;draw();toast('Removed');});}
 });
 [].forEach.call(document.querySelectorAll('#rvseg button'),function(b){b.onclick=function(){mode=b.getAttribute('data-m');[].forEach.call(document.querySelectorAll('#rvseg button'),function(x){x.classList.toggle('on',x===b);});draw();};});
 function submit(approve,btn){
  if(busy)return;var edits=Object.keys(dirty).map(function(id){var b=data.blocks.filter(function(x){return x.id===id;})[0];return {original:b.original,text:dirty[id]};});
  if(!approve&&!edits.length&&!Object.keys(clear).length){toast('Nothing to save yet',false);return;}
  busy=true;btn.classList.add('loading');
  fetch('/api/review/save',{method:'POST',body:JSON.stringify({slug:slug,page:pg,edits:edits,clear:Object.keys(clear),approve:approve,note:$('rvnote').value,by:($('rvby')||{}).value||''})})
   .then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});}).then(function(x){
    busy=false;btn.classList.remove('loading');
    if(x.j.blocks){data=x.j;dirty={};clear={};tabs();draw();$('rvframe').src=purl()+'?t='+Date.now();}
    toast(x.ok?x.j.message:(x.j.error||'Could not save'),x.ok);
   }).catch(function(){busy=false;btn.classList.remove('loading');toast('Could not reach the studio',false);});
 }
 $('rvsave').onclick=function(){submit(false,this);};$('rvsign').onclick=function(){submit(true,this);};
 $('rvreload').onclick=function(){$('rvframe').src=purl()+'?t='+Date.now();};
 window.addEventListener('beforeunload',function(ev){if(Object.keys(dirty).length){ev.preventDefault();ev.returnValue='';}});
 fit();if(window.ResizeObserver){new ResizeObserver(fit).observe($('rvstage'));}
 load(true);
})();</script>"""
    crumbs = f'<a href="/review">Legal review</a>{ico("arrow")}<b>{e(b["name"])}</b>'
    return shell(f'Review: {b["name"]}', body, "review", crumbs, js)
