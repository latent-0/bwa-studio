"""Brand workspace tabs: Preview, Go-live, Compliance, Integrations, Video, Activity. Markup plus the JS that drives them."""

TABS = [("preview", "Preview"), ("golive", "Go-live"), ("compliance", "Compliance"), ("integrations", "Integrations"), ("video", "Video"), ("media", "Media"), ("activity", "Activity")]


def workspace_right(slug, preview_html):
    bar = '<div class="tabs">' + "".join(
        f'<button data-tab="{k}" class="{"on" if k == "preview" else ""}">{label}<span class="tdot" id="td-{k}" style="display:none"></span></button>'
        for k, label in TABS) + "</div>"
    panels = f'<div class="tp on" data-tp="preview">{preview_html}</div>' + "".join(
        f'<div class="tp" data-tp="{k}"><section class="panel" id="pn-{k}"><div class="empty">Loading...</div></section></div>' for k, _ in TABS[1:])
    return f'<div class="col">{bar}{panels}</div>'


def studio2_js(slug):
    return STUDIO2_JS.replace("__SLUG__", slug)


STUDIO2_JS = r"""<script>
(function(){
  var slug='__SLUG__', cur='preview', queued={}, $=function(i){return document.getElementById(i);};
  function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function J(u,b){return fetch(u,b?{method:'POST',body:JSON.stringify(b)}:{}).then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});});}
  function tst(m,ok){if(typeof toast==='function'){toast(m,ok);}}
  function act(u,b,msg,after){return J(u,b).then(function(x){if(!x.ok||x.j.ok===false){tst(x.j.error||x.j.detail||'Something went wrong',false);}else{tst(msg,true);if(after){after(x);}}document.dispatchEvent(new Event('studio:refresh'));return x;});}
  function chip(t,c){return '<span class="chip2 '+(c||'')+'">'+esc(t)+'</span>';}
  function show(t){cur=t;[].slice.call(document.querySelectorAll('[data-tab]')).forEach(function(b){b.classList.toggle('on',b.getAttribute('data-tab')===t);});[].slice.call(document.querySelectorAll('[data-tp]')).forEach(function(p){p.classList.toggle('on',p.getAttribute('data-tp')===t);});load(t);}
  [].slice.call(document.querySelectorAll('[data-tab]')).forEach(function(b){b.onclick=function(){show(b.getAttribute('data-tab'));};});
  function load(t){ if(t==='golive')golive(); else if(t==='compliance')compl(); else if(t==='integrations')integ(); else if(t==='video')vid(); else if(t==='media')media(); else if(t==='activity')activity(); }
  function badge(id,txt,cls){var d=$('td-'+id);if(!d){return;}if(txt===''||txt==null){d.style.display='none';return;}d.style.display='inline-grid';d.textContent=txt;d.className='tdot '+(cls||'');}
  function badges(){J('/api/status/'+slug).then(function(x){var s=x.j,fail=s.checklist.items.filter(function(i){return !i.ok;}).length;badge('golive',s.live.live?'Live':(fail?fail:'OK'),s.live.live||!fail?'ok':'');var c=s.compliance;badge('compliance',c.approved?'OK':(c.open?c.open:'!'),c.approved?'ok':'');});}

  function stepActions(i,s){
    var m=s.delivery, a='';
    if(i.key==='page'||i.key==='tracking'||i.key==='compliance'){a='<button class="btn" data-a="gen">Generate</button>';}
    else if(i.key==='delivery'){
      a='<button class="btn" data-a="tab-integrations">Set up delivery</button>';
      if(m.indexOf('calls')>=0&&s.brand.ringba_campaign){a=(s.modes.ringba==='live'?'<button class="btn" data-a="number">Use the campaign number</button>':'<button class="btn" data-a="number">Assign sandbox number</button>')+a;}
    }
    else if(i.key==='buyer'){a='<button class="btn" data-a="buyerfocus">Enter a buyer</button>';}
    else if(i.key==='legal'){a='<button class="btn" data-a="tab-compliance">Open compliance</button>';}
    else if(i.key==='test'){
      if(m.indexOf('calls')>=0){a+='<button class="btn" data-a="testcall">'+(s.modes.ringba==='sandbox'?'Place test call':'I called it, check now')+'</button>';}
      if(m.indexOf('leads')>=0){a+='<button class="btn" data-a="testlead">Send test lead</button>';}
      if(m.indexOf('clicks')>=0){a+='<button class="btn" data-a="checkclicks">Check Everflow clicks</button>';}
    }
    return a;
  }
  function golive(){J('/api/status/'+slug).then(function(x){
    var s=x.j,L=s.live,cl=s.checklist,h='';
    h+='<div class="banner '+(L.live?'live':'')+'"><div class="grow"><b>'+(L.live?'Live':(L.paused?'Paused':'Not live'))+'</b><small>'+(L.release?('Release '+esc(L.release)):'Not published yet')+' &middot; Delivers by '+esc(s.delivery.join(', '))+' &middot; GoHighLevel stage: '+esc(s.stage)+'</small></div>';
    if(L.url){h+='<a class="btn" target="_blank" href="'+L.url+'">Open live page</a>';}
    h+=(L.paused?'<button class="btn" data-a="resume">Resume</button>':(L.release?'<button class="btn" data-a="pause">Pause</button>':''));
    if(L.history.length>1){h+='<button class="btn" data-a="rollback">Roll back</button>';}
    h+='<button class="btn primary" data-a="publish" '+(cl.ready?'':'disabled')+'>Publish</button></div>';
    var steps='';
    cl.items.forEach(function(i){ if(i.ok){return;}
      var d=i.detail; if(i.key==='buyer'&&s.sheet.buyers){d+='. The Sheet says: '+s.sheet.buyers;}
      steps+='<div class="st2"><span class="mark"><svg class="i"><use href="#i-x"/></svg></span><div class="t"><b>'+esc(i.label)+'</b><span>'+esc(d)+'</span></div>'+stepActions(i,s)+'</div>';});
    h+=steps?'<h2 style="margin-top:6px">Still to do</h2><div class="steps2">'+steps+'</div>':'<div class="go"><svg class="i"><use href="#i-check"/></svg>All seven checks passed. This brand can go live.</div>';
    var hist=L.history.slice().reverse();
    h+='<h2 style="margin-top:18px">Release history</h2>'+(hist.length?'<table class="tbl"><thead><tr><th>Release</th><th>When</th><th>Note</th></tr></thead><tbody>'+hist.map(function(r){return '<tr><td>'+esc(r.release)+(r.release===L.release?' '+chip('current','ok'):'')+'</td><td class="mut">'+esc(r.ts)+'</td><td class="mut">'+esc(r.note||'')+'</td></tr>';}).join('')+'</tbody></table>':'<div class="empty">Nothing published yet.</div>');
    h+='<p class="note2">Publishing copies the current page to an immutable release. Set PUBLISH_CMD to also deploy to real hosting. A later regenerate does not change what is live until you publish again.</p>';
    $('pn-golive').innerHTML=h;});}

  function compl(){J('/api/compliance/'+slug).then(function(x){
    var c=x.j,h='';
    h+='<div class="banner '+(c.approved?'live':'')+'"><div class="grow"><b>'+esc(c.label)+'</b><small>Every flagged claim must be cleared by counsel and signed off before this brand can go live. If the page text changes, approval goes stale.</small></div>';
    if(c.approved){h+='<button class="btn" data-a="revoke">Revoke approval</button>';}
    h+='</div>';
    if(c.state==='not_generated'){$('pn-compliance').innerHTML=h+'<div class="empty">Generate the page first.</div>';return;}
    h+='<h2>Flagged claims ('+c.hits.length+')</h2>';
    if(c.hits.length){h+='<table class="tbl"><thead><tr><th>Claim</th><th style="width:110px"></th></tr></thead><tbody>'+c.hits.map(function(k){return '<tr><td><b>'+esc(k.phrase)+'</b> '+chip(k.category,k.cleared?'ok':'warn')+'<div class="ctx">'+esc(k.context)+'</div></td><td style="text-align:right"><button class="btn" data-a="clear" data-id="'+k.id+'" data-on="'+(k.cleared?'0':'1')+'">'+(k.cleared?'Reopen':'Clear')+'</button></td></tr>';}).join('')+'</tbody></table>';
      if(c.open){h+='<div class="row" style="margin-top:10px"><button class="btn" data-a="clearall">Clear all '+c.open+' (counsel reviewed)</button></div>';}}
    else{h+='<div class="empty">No risky claims found.</div>';}
    h+='<h2 style="margin-top:18px">Legal sign-off</h2><div class="row"><input type="text" id="revname" placeholder="Reviewer name" value="'+esc(c.reviewed?c.reviewed.by:'')+'"><input type="text" id="revnote" placeholder="Note (optional)"></div><div class="row"><button class="btn primary" data-a="review" '+(c.open?'disabled':'')+'>Approve legal review</button></div>';
    h+='<p class="note2">This records who approved what and when. It is a workflow gate, not legal advice: a lawyer decides what is acceptable.</p>';
    $('pn-compliance').innerHTML=h;});}

  var SYS=[['ringba','Ringba','Calls','calls'],['everflow','Everflow','Clicks','clicks'],['leadprosper','LeadProsper','Lead delivery','leads']];
  function sheetPanel(s){
    var sh=s.sheet,h='<div class="icard" style="margin-bottom:14px"><h3><span>From the Google Sheet</span>'+(sh.priority?chip(sh.priority+' priority',sh.priority==='Done'?'ok':'acc'):'')+'</h3>';
    var rows=[['Website',sh.url?('<a target="_blank" href="'+esc(sh.url)+'">'+esc(sh.url.replace(/^https?:\/\//,''))+'</a>'+(String(sh.site_up).toUpperCase()==='N'?' '+chip('marked not up','bad'):'')):'Not listed'],['Buyers',esc(sh.buyers||'None listed')+(sh.buyers&&!sh.buyer_confirmed?' '+chip('not confirmed','warn'):'')],['Type',esc(sh.type||'Not set (treated as calls)')],['Category',esc(sh.category||sh.vertical_text||'')],['GoHighLevel',sh.ghl_subaccount?'Sub-account set':'No sub-account']];
    if(sh.note){rows.push(['Note',esc(sh.note)]);}
    h+='<table class="tbl"><tbody>'+rows.map(function(r){return '<tr><td class="mut" style="width:110px">'+r[0]+'</td><td>'+r[1]+'</td></tr>';}).join('')+'</tbody></table>';
    if(sh.campaigns.length){h+='<details style="margin-top:8px"><summary class="mut" style="cursor:pointer;font-size:13px">'+sh.campaigns.length+' inventory campaign'+(sh.campaigns.length===1?'':'s')+' in the Sheet</summary><table class="tbl"><thead><tr><th>Campaign</th><th>Stage</th><th>Landing page</th></tr></thead><tbody>'+sh.campaigns.map(function(c){return '<tr><td>'+esc(c.campaign)+'</td><td class="mut">'+esc(c.stage||'')+'</td><td class="mut">'+esc((c.landing_page||'').replace(/^https?:\/\//,''))+'</td></tr>';}).join('')+'</tbody></table></details>';}
    return h+'</div>';
  }
  function sysCard(k,s,mp){
    var key=k[0],name=k[1],role=k[2],mode=s.modes[key],used=s.delivery.indexOf(k[3])>=0,mapped=mp.mapped[key]||[],ids=mapped.map(function(x){return x.id;}),b=s.brand,h='';
    var sug=(mp.suggestions[key]||[]).filter(function(c){return ids.indexOf(c.id)<0;}),conf=sug.filter(function(c){return c.confident;});
    h+='<div class="icard" data-sys="'+key+'"><h3><span>'+name+' <span class="mut" style="font-weight:400">&middot; '+role+'</span></span><span>'+(used?chip('used by this brand','acc')+' ':'')+chip(mode,mode==='live'?'ok':'warn')+'</span></h3>';
    h+='<label>Mapped '+(key==='everflow'?'offers':'campaigns')+' ('+mapped.length+')</label>';
    h+=mapped.length?'<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:4px">'+mapped.map(function(x){return '<span class="chip2">'+esc(x.name)+' <button class="x" data-a="unmap" data-sys="'+key+'" data-id="'+esc(x.id)+'" aria-label="Remove">&times;</button></span>';}).join('')+'</div>':'<p>None yet.</p>';
    if(mode==='live'){
      if(conf.length){h+='<div class="row" style="margin-top:8px"><button class="btn" data-a="addconf" data-sys="'+key+'">Add '+conf.length+' matching '+(conf.length===1?'name':'names')+'</button></div>';}
      var others=sug.filter(function(c){return !c.confident;}).slice(0,4);
      if(others.length){h+='<label>Possible matches</label><div style="display:flex;flex-wrap:wrap;gap:6px">'+others.map(function(c){return '<button class="btn" style="height:28px" data-a="addmap" data-sys="'+key+'" data-id="'+esc(c.id)+'">+ '+esc(c.name)+'</button>';}).join('')+'</div>';}
      h+='<label>Search all</label><input type="text" list="dl-'+key+'" data-search="'+key+'" placeholder="Start typing a name"><datalist id="dl-'+key+'"></datalist>';
    } else {h+='<p>Sandbox: add credentials to pick real '+(key==='everflow'?'offers':'campaigns')+'.</p>';}
    h+='<div class="row" style="margin-top:10px">';
    if(key==='ringba'){h+='<button class="btn" data-a="number">'+(mode==='live'?'Use the campaign number':'Assign sandbox number')+'</button><button class="btn" data-a="testcall">'+(mode==='sandbox'?'Place test call':'Check my test call')+'</button>';}
    if(key==='everflow'){h+='<button class="btn" data-a="checkclicks">Check Everflow clicks</button>';if(mode==='sandbox'){h+='<button class="btn" data-a="simtraffic">Simulate 14 days of traffic</button>';}}
    if(key==='leadprosper'){h+='<button class="btn" data-a="testlead">Send test lead</button>';}
    if(mode==='live'){h+='<button class="btn" data-a="pull">Pull latest data</button>';}
    h+='</div>';
    if(key==='ringba'){h+='<p>Number on the page: <b>'+esc(b.phone||'none')+'</b>'+(s.snippets.ringba?'':'. No brand tag file yet.')+'</p>';}
    if(key==='leadprosper'){h+='<p>'+s.leads.total+' leads, '+s.leads.accepted+' accepted, $'+s.leads.revenue.toFixed(2)+' in the last 14 days.</p>';}
    if(key==='everflow'){h+='<p>'+s.clicks+' valid clicks in the last 14 days.'+(s.snippets.everflow?'':' No brand tag file yet.')+'</p>';}
    return h+'</div>';
  }
  function integ(){Promise.all([J('/api/status/'+slug),J('/api/mapping/'+slug)]).then(function(r){
    var s=r[0].j,mp=r[1].j,m=s.modes,h=sheetPanel(s);
    h+='<div class="icard" style="margin-bottom:14px"><h3><span>How this brand delivers</span></h3><div class="row" style="align-items:center;gap:16px">'+SYS.map(function(k){return '<label style="display:inline-flex;align-items:center;gap:8px;margin:0"><input type="checkbox" data-deliv="'+k[3]+'" '+(s.delivery.indexOf(k[3])>=0?'checked':'')+'> '+k[2]+' ('+k[1]+')</label>';}).join('')+'<button class="btn" data-a="savedeliv">Save</button></div><p>Calls use Ringba numbers, clicks use Everflow offers, lead forms deliver through LeadProsper. The go-live test follows what is ticked.</p></div>';
    h+='<div class="cgrid">'+SYS.map(function(k){return sysCard(k,s,mp);}).join('');
    h+='<div class="icard"><h3><span>GoHighLevel <span class="mut" style="font-weight:400">&middot; CRM</span></span>'+chip(m.ghl,m.ghl==='live'?'ok':'warn')+'</h3><p>Stage: <b>'+esc(s.stage)+'</b></p><p>'+s.calls+' calls, '+s.calls_pending_sync+' not yet in the CRM.</p><div class="row"><button class="btn" data-a="syncghl">Sync '+s.calls_pending_sync+' call'+(s.calls_pending_sync===1?'':'s')+'</button><button class="btn" data-a="stage">Update stage</button></div></div></div>';
    h+='<p class="note2">'+(['ringba','everflow','leadprosper'].some(function(n){return m[n]==='sandbox';})?'Some systems are in sandbox mode and their data is simulated and labeled. Add credentials on the Integrations page.':'Ringba, Everflow and LeadProsper are live. Mapping changes here are saved locally and never change anything inside those accounts.')+'</p>';
    $('pn-integrations').innerHTML=h;
    [].slice.call(document.querySelectorAll('[data-search]')).forEach(function(inp){var key=inp.getAttribute('data-search');inp.onfocus=function(){if(inp.getAttribute('data-ld')){return;}inp.setAttribute('data-ld','1');J('/api/catalog/'+key).then(function(c){window['__cat_'+key]=c.j.items;$('dl-'+key).innerHTML=c.j.items.map(function(i){return '<option value="'+esc(i.name)+'">';}).join('');});};
      inp.onchange=function(){var it=(window['__cat_'+key]||[]).filter(function(i){return i.name===inp.value;})[0];if(it){mapSet(key,it.id,true);}};});
  });}
  function mapSet(key,id,add,all){
    J('/api/mapping/'+slug).then(function(r){var ids=(r.j.mapped[key]||[]).map(function(x){return x.id;});
      if(all){(r.j.suggestions[key]||[]).forEach(function(c){if(c.confident&&ids.indexOf(c.id)<0){ids.push(c.id);}});}
      else if(add){if(ids.indexOf(id)<0){ids.push(id);}} else {ids=ids.filter(function(i){return i!==id;});}
      act('/api/mapping/set',{slug:slug,system:key,ids:ids},'Saved');});
  }

  function sheetVideos(v){
    if(!v.length){return '';}
    return '<details style="margin-top:12px"><summary class="mut" style="cursor:pointer;font-size:13px">'+v.length+' video'+(v.length===1?'':'s')+' tracked in the Google Sheet</summary><table class="tbl"><thead><tr><th>Video</th><th>Stage</th><th>Jeff notes</th></tr></thead><tbody>'+v.map(function(x){return '<tr><td><b>'+esc(x.idea)+'</b><div class="ctx">'+esc(x.final||'')+'</div></td><td class="mut">'+esc(x.stage||'')+(x.prep?' / '+esc(x.prep):'')+'</td><td class="ctx">'+esc((x.jeff||'').slice(0,160))+'</td></tr>';}).join('')+'</tbody></table></details>';
  }
  var VFMT='9x16';
  function vid(){Promise.all([J('/api/video/jobs/'+slug),J('/api/status/'+slug)]).then(function(rs){window.__sheetv=rs[1].j.sheet.videos;var x=rs[0];
    var jobs={},variants=x.j.variants,running=false;x.j.jobs.forEach(function(j){jobs[j.variant+'|'+j.fmt]=j;});window.__v=variants;
    var h='<div class="bar"><div class="seg" id="vfmt"><button data-f="9x16" class="'+(VFMT==='9x16'?'on':'')+'">9:16</button><button data-f="1x1" class="'+(VFMT==='1x1'?'on':'')+'">1:1</button><button data-f="16x9" class="'+(VFMT==='16x9'?'on':'')+'">16:9</button></div><div style="display:flex;gap:8px"><button class="btn primary" data-a="renderall">Render all '+variants.length+'</button><a class="btn" href="/api/video/tracker.csv">Tracker CSV</a></div></div>';
    if(!variants.length){$('pn-video').innerHTML=h+'<div class="empty">Generate the page to build the script variants.</div>';return;}
    h+='<div>'+variants.map(function(v){var j=jobs[v.id+'|'+VFMT],st;
      if(j&&j.status==='running'){running=true;st=chip('Rendering...','acc');}
      else if(j&&j.status==='done'){st=chip('Done in '+j.seconds+'s','ok');}
      else if(j&&j.status==='failed'){st='<span class="chip2 bad" title="'+esc(j.error)+'">Failed</span>';}
      else if(queued[v.id+'|'+VFMT]){running=true;st=chip('Queued','acc');}
      else{st=chip('Not rendered');}
      var done=j&&j.status==='done';
      return '<div class="vrow" data-vid="'+v.id+'"><div class="vh"><span class="vid">'+esc(v.id)+'</span><span class="chipx">'+v.opener+' + '+v.cta+'</span><span class="chipx">~'+v.est_seconds+'s</span>'+st+(done?'<button class="btn" data-a="play" data-id="'+v.id+'">Play</button>':'')+'<button class="btn" data-a="render" data-id="'+v.id+'">'+(done?'Re-render':'Render')+'</button></div><div class="vb" style="display:none"></div></div>';}).join('')+'</div>';
    h+=(rs[1].j.serverless?'<p class="note2">Video rendering needs ffmpeg, which Vercel does not provide. Render videos from the local studio. Scripts and the tracker still work here.</p>':'')+sheetVideos(window.__sheetv||[]);
    h+='<p class="note2">Local render with ffmpeg and a placeholder voice (Windows speech). Real footage and a licensed voice or avatar provider replace the placeholder in Stage 3. Files are saved in data/video/ and listed in the Tracker CSV.</p>';
    $('pn-video').innerHTML=h;
    if(rs[1].j.serverless){[].slice.call(document.querySelectorAll('#pn-video [data-a=render],#pn-video [data-a=renderall]')).forEach(function(x){x.disabled=true;x.title='Needs ffmpeg';});}
    [].slice.call(document.querySelectorAll('#vfmt button')).forEach(function(b){b.onclick=function(){VFMT=b.getAttribute('data-f');vid();};});
    if(running){setTimeout(function(){if(cur==='video'){vid();}},4000);}
  });}

  var ACC={};
  function fmtMB(n){return n?((n>10485760?Math.round(n/1048576):(n/1048576).toFixed(1))+' MB'):'size unknown';}
  function accChip(did){var a=ACC[did];if(!a){return '';}if(a.access==='public'){return chip('public, '+fmtMB(a.size),'ok');}if(a.access==='private'){return chip('private','warn');}if(a.access==='missing'){return chip('removed from Drive','bad');}return chip('unknown');}
  function media(){J('/api/media/'+slug).then(function(x){
    var m=x.j,h='';
    h+='<div class="banner"><div class="grow"><b>'+m.total+' asset'+(m.total===1?'':'s')+' tracked in the Sheet</b><small>Final videos, revisions, green screens, voiceovers, scripts, creatives folders and kits that the team keeps for this brand. Files stay in Google Drive until you download one.</small></div><button class="btn" data-a="mcheck">Check access</button></div>';
    if(m.library.length){
      h+='<h2>In the studio ('+m.library.length+')</h2><table class="tbl"><tbody>'+m.library.map(function(f){var vid=/\.(mp4|mov|webm)$/i.test(f.file),cur=m.hero_video==='brand-'+f.file;
        return '<tr><td><b>'+esc(f.title)+'</b>'+(cur?' '+chip('brand video','ok'):'')+'<div class="ctx">'+esc(f.file)+', '+fmtMB(f.size)+'</div>'+(vid?'<video controls preload="none" playsinline style="width:100%;max-height:260px;margin-top:8px;background:#000;border-radius:10px" src="/assets/'+slug+'/media/'+encodeURIComponent(f.file)+'"></video>':'')+'</td><td style="text-align:right;white-space:nowrap">'+(vid&&!cur?'<button class="btn" data-a="muse" data-file="'+esc(f.file)+'">Use as brand video</button>':'')+'</td></tr>';}).join('')+'</tbody></table><p class="note2">The brand video is the hero on the page and the background for rendered videos. Regenerate the page after changing it.</p>';
    }
    if(!m.groups.length){h+='<div class="empty">No media is tracked for this brand in the Sheet yet.</div>';}
    m.groups.forEach(function(g,gi){
      h+='<details '+(gi===0?'open':'')+' style="margin-top:12px"><summary style="cursor:pointer;font-weight:500">'+esc(g.label)+' <span class="mut">('+g.items.length+')</span></summary><table class="tbl"><tbody>'+g.items.map(function(a){
        var file=a.type==='file';
        return '<tr data-aid="'+esc(a.id)+'"><td><b>'+esc(a.title)+'</b>'+(a.context&&a.context!==a.title?'<div class="ctx">'+esc(a.context)+'</div>':'')+'</td><td class="mut" style="white-space:nowrap">'+esc(a.stage||'')+'</td><td class="acc-cell" data-did="'+esc(a.drive_id)+'">'+accChip(a.drive_id)+'</td><td style="text-align:right;white-space:nowrap"><a class="btn" style="height:30px" target="_blank" href="'+esc(a.url)+'">Open</a> '+(file&&!m.serverless?'<button class="btn" style="height:30px" data-a="mdl" data-id="'+esc(a.id)+'" data-did="'+esc(a.drive_id)+'" data-title="'+esc(a.title)+'">Download</button>':'')+'</td></tr>';}).join('')+'</tbody></table></details>';});
    $('pn-media').innerHTML=h;
  });}
  function mediaPoll(id,row){
    (function tick(){J('/api/media/progress/'+slug+'/'+id).then(function(r){var s=r.j;
      if(s.state==='running'){var el=document.querySelector('tr[data-aid="'+id+'"] .acc-cell');if(el){el.innerHTML=chip('Downloading '+fmtMB(s.bytes)+(s.total?' of '+fmtMB(s.total):''),'acc');}setTimeout(tick,1500);}
      else if(s.state==='failed'){tst(s.error||'Download failed',false);media();}
      else if(s.state==='done'){tst('Downloaded',true);media();}
    });})();
  }

  function activity(){J('/api/events/'+slug).then(function(x){var ev=x.j;$('pn-activity').innerHTML='<h2>Recent activity</h2>'+(ev.length?'<table class="tbl"><tbody>'+ev.map(function(e2){return '<tr><td class="mut" style="white-space:nowrap">'+esc(e2.ts)+'</td><td><b>'+esc(e2.kind)+'</b><div class="ctx">'+esc(e2.detail)+'</div></td><td class="mut">'+esc(e2.actor)+'</td></tr>';}).join('')+'</tbody></table>':'<div class="empty">No activity yet.</div>');});}

  document.addEventListener('click',function(ev){
    var t=ev.target.closest('[data-a]'); if(!t){return;} var a=t.getAttribute('data-a'), id=t.getAttribute('data-id');
    if(a==='publish'){t.disabled=true;act('/api/publish',{slug:slug,note:''},'Brand is live');}
    else if(a==='pause'){act('/api/pause',{slug:slug},'Paused');} else if(a==='resume'){act('/api/resume',{slug:slug},'Resumed');}
    else if(a==='rollback'){act('/api/rollback',{slug:slug},'Rolled back');}
    else if(a==='gen'){$('gen').click();}
    else if(a==='number'){act('/api/ringba/number',{slug:slug},'Number assigned, regenerating the page',function(){$('gen').click();});}
    else if(a==='setphone'){var p=($('phoneset')||$('f-phone'));act('/api/brand/fields',{slug:slug,fields:{phone:p.value}},'Number saved',function(){$('gen').click();});}
    else if(a==='buyerfocus'){$('buyer').focus();tst('Type the buyer on the left and press Assign',true);}
    else if(a==='tab-compliance'){show('compliance');}
    else if(a==='testcall'){act('/api/ringba/test-call',{slug:slug},'Test call recorded');}
    else if(a==='clear'){act('/api/legal/clear',{slug:slug,id:id,on:t.getAttribute('data-on')==='1',by:($('revname')||{}).value||'counsel'},'Updated');}
    else if(a==='clearall'){act('/api/legal/clear-all',{slug:slug,by:($('revname')||{}).value||'counsel'},'All claims cleared');}
    else if(a==='review'){act('/api/legal/review',{slug:slug,reviewer:($('revname')||{}).value,note:($('revnote')||{}).value},'Legal review approved');}
    else if(a==='revoke'){act('/api/legal/revoke',{slug:slug},'Approval revoked');}
    else if(a==='mcheck'){var ids=[].slice.call(document.querySelectorAll('#pn-media details[open] [data-a=mdl]')).map(function(b){return b.getAttribute('data-did');}).filter(function(d){return d&&!ACC[d];}).slice(0,30);
      if(!ids.length){tst('Open a group with files to check, or everything shown is already checked.',true);}
      else{t.disabled=true;J('/api/media/check',{drive_ids:ids}).then(function(r){var res=r.j.results||{};Object.keys(res).forEach(function(k){ACC[k]=res[k];});[].slice.call(document.querySelectorAll('.acc-cell')).forEach(function(c){var d=c.getAttribute('data-did');if(ACC[d]){c.innerHTML=accChip(d);}});t.disabled=false;});}}
    else if(a==='mdl'){var did=t.getAttribute('data-did'),ttl=t.getAttribute('data-title');
      var start=function(){var size=(ACC[did]||{}).size;if(!confirm('Download "'+ttl+'" ('+fmtMB(size)+') from Google Drive into the studio?')){return;}J('/api/media/download',{slug:slug,id:id}).then(function(r){if(r.j.ok===false){tst(r.j.error||'Could not start',false);}else{tst('Download started',true);mediaPoll(id);}});};
      if(ACC[did]){if(ACC[did].access==='public'){start();}else{tst('This file is '+ACC[did].access+' in Drive. Open it there instead.',false);}}
      else{J('/api/media/check',{drive_ids:[did]}).then(function(r){ACC[did]=(r.j.results||{})[did]||{access:'unknown'};var c=document.querySelector('.acc-cell[data-did="'+did+'"]');if(c){c.innerHTML=accChip(did);}if(ACC[did].access==='public'){start();}else{tst('This file is '+ACC[did].access+' in Drive. Open it there instead.',false);}});}}
    else if(a==='muse'){act('/api/media/use',{slug:slug,file:t.getAttribute('data-file')},'Brand video set',function(){media();});}
    else if(a==='testlead'){if(confirm('Send one test lead, flagged as a test, to this brand\'s LeadProsper campaign?')){act('/api/leadprosper/test-lead',{slug:slug},'Test lead accepted');}}
    else if(a==='checkclicks'){act('/api/everflow/check',{slug:slug},'Clicks are reaching Everflow');}
    else if(a==='tab-integrations'){show('integrations');}
    else if(a==='addmap'){mapSet(t.getAttribute('data-sys'),id,true);}
    else if(a==='unmap'){mapSet(t.getAttribute('data-sys'),id,false);}
    else if(a==='addconf'){mapSet(t.getAttribute('data-sys'),null,true,true);}
    else if(a==='savedeliv'){var v=[].slice.call(document.querySelectorAll('[data-deliv]')).filter(function(x){return x.checked;}).map(function(x){return x.getAttribute('data-deliv');});act('/api/brand/fields',{slug:slug,fields:{delivery:v.join(',')||'calls'}},'Saved');}
    else if(a==='simtraffic'){act('/api/sandbox/traffic',{slug:slug,days:14},'Simulated traffic added');}
    else if(a==='pull'){act('/api/ringba/pull',{slug:slug},'Pulled');}
    else if(a==='syncghl'){act('/api/ghl/sync',{slug:slug},'Calls synced to GoHighLevel');}
    else if(a==='stage'){act('/api/ghl/stage',{slug:slug},'Stage updated');}
    else if(a==='render'){queued[id+'|'+VFMT]=1;act('/api/video/render',{slug:slug,variants:[id],fmt:VFMT},'Render started',function(){setTimeout(vid,800);});}
    else if(a==='renderall'){(window.__v||[]).forEach(function(v){queued[v.id+'|'+VFMT]=1;});act('/api/video/render',{slug:slug,variants:(window.__v||[]).map(function(v){return v.id;}),fmt:VFMT},'Rendering all variants',function(){setTimeout(vid,800);});}
    else if(a==='play'){var row=document.querySelector('.vrow[data-vid="'+id+'"] .vb');if(row.style.display==='block'){row.style.display='none';row.innerHTML='';}else{row.style.display='block';row.innerHTML='<video controls autoplay playsinline src="/video/'+slug+'/'+id+'/'+VFMT+'"></video>';}}
  });
  document.addEventListener('studio:refresh',function(){badges();if(cur!=='preview'){load(cur);}});
  badges();
})();
</script>"""
