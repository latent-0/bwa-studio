"""The Landing pages view: the two Google Sheet trackers as live, editable tables. Edits write back to the Sheet, Sheet edits show up here."""
import lp
from ui import CSS, e, ico, shell
import ui

ui.CSS = CSS + """
.lpbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:0 0 14px}.lpbar input[type=text]{max-width:280px;height:38px;padding:0 14px}
.lpbar .grow{flex:1}.lpmeta{color:var(--faint);font-size:12.5px}
#lpt{display:block;overflow:auto;max-height:70vh}#lpt thead th{position:sticky;top:0;background:var(--surface);z-index:1;white-space:nowrap}
#lpt td{white-space:nowrap}#lpt td.wrap{white-space:normal;min-width:240px;max-width:360px}
.cell{height:32px;border-radius:9px;border:1px solid var(--line);background:var(--surface2);color:var(--ink);font:inherit;font-size:13px;padding:0 8px;min-width:104px}
.cell.url{min-width:230px}.cell.note{min-width:260px}.cell:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 22%,transparent)}
.cell.saved{border-color:var(--ok);box-shadow:0 0 0 3px color-mix(in srgb,var(--ok) 20%,transparent)}.cell.err{border-color:var(--bad)}
.cell[disabled]{opacity:.55}.lpnote{display:block;font-size:12px;color:var(--mut);margin-top:3px;max-width:340px;white-space:normal}
"""


def pages_page():
    st = lp.status()
    banner = ("" if st["bridge"] else
              '<div class="note2" style="margin:0 0 14px">Edits here cannot reach the Google Sheet yet because the Sheet bridge is not connected. The tables below still show the live Sheet. '
              'Add LP_BRIDGE_URL and LP_BRIDGE_TOKEN to turn editing on.</div>')
    body = (f'<div class="pagehead"><div><h1>Landing pages</h1><p>The Campaign Tracker, live from the Google Sheet. '
            f'Change a cell here and it is written to the Sheet. Change the Sheet and it appears here within seconds.</p></div>'
            f'<div style="display:flex;gap:8px"><button class="btn" id="lprefresh">{ico("spark")}Refresh</button>'
            f'<a class="btn" id="lpsheet" href="{e(st["sheet"])}" target="_blank" rel="noopener">Open the Sheet{ico("ext")}</a></div></div>'
            f'{banner}<div class="kpis" id="lpk" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr))"></div>'
            f'<div class="lpbar">'
            f'<input type="text" id="lpq" placeholder="Search brand, campaign or URL"><span class="grow"></span><span class="lpmeta" id="lpmeta"></span></div>'
            f'<section class="panel" style="padding:8px 10px"><table class="tbl" id="lpt"><thead></thead><tbody></tbody></table></section>'
            f'<p class="note2">Jeff approval, the go-live check and the production stage are read only here. Only the owner, status, date, URL and note columns can be edited.</p>')
    js = """<script>(function(){
 var src='campaign',data=null,busy=0,q='';
 function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
 var MON={Jan:1,Feb:2,Mar:3,Apr:4,May:5,Jun:6,Jul:7,Aug:8,Sep:9,Oct:10,Nov:11,Dec:12};
 function iso(s){var m=/^(\\d{1,2}) (\\w{3}) (\\d{4})$/.exec(s||'');if(!m||!MON[m[2]])return '';return m[3]+'-'+(MON[m[2]]<10?'0':'')+MON[m[2]]+'-'+(+m[1]<10?'0':'')+(+m[1]);}
 var LAYOUT={
  campaign:[['brand','Brand'],['campaign','Campaign'],['stage','Video stage'],['variant','Variant'],['build_owner','Build owner'],['build_date','Built on'],['approval','Jeff approval'],['deploy_owner','Deploy owner'],['deploy_status','Deploy'],['live_url','Live URL'],['deploy_date','Deployed on'],['feedback','Jeff feedback'],['jeff_notes','Notes from Jeff'],['team_notes','Notes from Tina/Ryan'],['notes','Review notes']]
 };
 function chip(v){var c=v==='Approved'?'ok':(v==='Not submitted'||!v?'':'warn');return '<span class="chip2 '+c+'">'+esc(v||'None')+'</span>';}
 function cell(r,f){
  var v=r[f]||'',can=data.editable.indexOf(f)>=0,id=esc(r.rid);
  if(f==='approval')return '<td>'+chip(v)+'</td>';
  if(f==='stage')return '<td>'+(v?'<span class="chip2">'+esc(v)+'</span>':'')+'</td>';
  if(f==='feedback'||f==='jeff_notes'||f==='team_notes')return '<td class="wrap">'+esc(v)+'</td>';
  if(!can){return '<td'+(f==='notes'?' class="wrap"':'')+'>'+(f==='id'?'<span class="mut">'+esc(v)+'</span>':(f==='brand'||f==='campaign'?'<b style="font-weight:500">'+esc(v)+'</b>':esc(v)))+'</td>';}
  var dis=data.status.bridge?'':' disabled title="Sheet bridge not connected"';
  if(data.options[f]){var o='<option value=""></option>'+data.options[f].map(function(x){return '<option'+(x===v?' selected':'')+'>'+esc(x)+'</option>';}).join('');if(v&&data.options[f].indexOf(v)<0)o+='<option selected>'+esc(v)+'</option>';return '<td><select class="cell" data-r="'+id+'" data-f="'+f+'"'+dis+'>'+o+'</select></td>';}
  if(f==='build_date'||f==='deploy_date')return '<td><input class="cell" type="date" data-r="'+id+'" data-f="'+f+'" value="'+iso(v)+'"'+dis+'></td>';
  if(f==='live_url')return '<td><input class="cell url" type="text" data-r="'+id+'" data-f="'+f+'" value="'+esc(v)+'" placeholder="https://"'+dis+'>'+(v?' <a href="'+esc(v)+'" target="_blank" rel="noopener" class="mut">Open</a>':'')+'</td>';
  return '<td><input class="cell note" type="text" data-r="'+id+'" data-f="'+f+'" value="'+esc(v)+'"'+dis+'></td>';
 }
 function kpis(rows){
  var dep=rows.filter(function(r){return r.deploy_status==='Deployed';}).length,built=rows.filter(function(r){return r.build_status==='Built'||(r.build_owner&&r.build_date);}).length;
  var appr=rows.filter(function(r){return r.approval==='Approved';}).length,fb=rows.filter(function(r){return r.feedback;}).length;
  var items=[['Rows',rows.length],['Built',built],['Deployed',dep],['Jeff feedback',fb]];
  document.getElementById('lpk').innerHTML=items.map(function(i){return '<div class="kpi"><span>'+i[0]+'</span><b>'+i[1]+'</b></div>';}).join('');
 }
 function render(){
  var rows=data.rows.filter(function(r){return !q||JSON.stringify(r).toLowerCase().indexOf(q)>=0;}),L=LAYOUT[src];
  kpis(data.rows);
  document.querySelector('#lpt thead').innerHTML='<tr>'+L.map(function(c){return '<th>'+c[1]+'</th>';}).join('')+'</tr>';
  document.querySelector('#lpt tbody').innerHTML=rows.map(function(r){return '<tr>'+L.map(function(c){return cell(r,c[0]);}).join('')+'</tr>';}).join('')||'<tr><td colspan="'+L.length+'" class="mut">No rows match.</td></tr>';
  document.getElementById('lpmeta').textContent=(data.status.source||'')+' - checked '+data.fetched+(data.status.error?' ('+data.status.error+')':'');
 }
 function load(fresh,quiet){
  return fetch('/api/lp?src='+src+(fresh?'&fresh=1':'')).then(function(r){return r.json();}).then(function(j){
   if(!j.ok){if(!quiet)toast(j.error||'Could not load the tracker',false);return;}
   var changed=!data||data.src!==j.src||JSON.stringify(data.rows)!==JSON.stringify(j.rows);
   var typing=document.activeElement&&document.activeElement.classList&&document.activeElement.classList.contains('cell');
   if(quiet&&(typing||busy))return;
   data=j;if(changed||!quiet)render();else document.getElementById('lpmeta').textContent=(j.status.source||'')+' - checked '+j.fetched;
  }).catch(function(){if(!quiet)toast('Could not reach the studio',false);});
 }
 document.querySelector('#lpt').addEventListener('change',function(ev){
  var t=ev.target;if(!t.classList.contains('cell'))return;
  var body={src:src,rid:t.getAttribute('data-r'),set:{}};body.set[t.getAttribute('data-f')]=t.value;busy++;t.disabled=true;
  fetch('/api/lp/update',{method:'POST',body:JSON.stringify(body)}).then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});}).then(function(x){
   busy--;t.disabled=false;
   if(x.ok&&x.j.ok){t.classList.remove('err');t.classList.add('saved');setTimeout(function(){t.classList.remove('saved');},1400);toast('Saved to the Sheet');
    for(var i=0;i<data.rows.length;i++){if(data.rows[i].rid===body.rid){data.rows[i]=x.j.row;}}}
   else{t.classList.add('err');toast(x.j.error||'Could not save',false);load(true,false);}
  }).catch(function(){busy--;t.disabled=false;toast('Could not reach the studio',false);});
 });
 document.getElementById('lpq').oninput=function(){q=this.value.toLowerCase();if(data)render();};
 document.getElementById('lprefresh').onclick=function(){load(true,false).then(function(){toast('Reloaded from the Sheet');});};
 load(false,false);setInterval(function(){load(true,true);},20000);
})();</script>"""
    return shell("Landing pages", body, "pages", "<b>Landing pages</b>", js)
