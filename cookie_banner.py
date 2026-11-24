"""Cookie consent banner for brand pages (turned on per brand with legal/<slug>/settings.json {"cookie_banner": true}).

Visitors can accept all, reject non-essential cookies, or choose per category. The choice is kept in localStorage ("bw_consent") and shared with
other scripts as window.bwConsent plus a "bw:consent" event, so analytics or marketing tags can wait for consent. A browser Global Privacy Control
signal is treated as a rejection of marketing. "Cookie settings" in the footer reopens the panel. Essential cookies (calls, forms, security) always run."""

BANNER = """<div id="bw-consent" class="bwc" role="dialog" aria-modal="false" aria-labelledby="bwc-t" hidden>
<style>
.bwc{position:fixed;left:16px;right:16px;bottom:16px;z-index:9999;max-width:560px;margin:0 auto;background:#fff;color:#15181d;border:1px solid rgba(21,24,29,.12);border-radius:16px;box-shadow:0 18px 50px -12px rgba(21,24,29,.35);padding:20px 20px 16px;font:400 14.5px/1.55 Inter,system-ui,"Segoe UI",Arial,sans-serif}
.bwc[hidden]{display:none}.bwc h2{font:600 16px/1.3 Inter,system-ui,sans-serif;margin:0 0 6px;letter-spacing:0}.bwc p{margin:0 0 14px;color:#3a404a}.bwc a{color:inherit;text-decoration:underline}
.bwc .row{display:flex;flex-wrap:wrap;gap:8px}.bwc button{flex:1 1 auto;min-height:44px;padding:10px 16px;border-radius:999px;border:1px solid rgba(21,24,29,.2);background:#fff;color:#15181d;font:600 14px Inter,system-ui,sans-serif;cursor:pointer}
.bwc button.pri{background:#15181d;border-color:#15181d;color:#fff}.bwc button:focus-visible{outline:2px solid #2563eb;outline-offset:2px}
.bwc .prefs{margin:0 0 14px;border-top:1px solid rgba(21,24,29,.1)}.bwc .prefs[hidden]{display:none}
.bwc label{display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-bottom:1px solid rgba(21,24,29,.1);cursor:pointer}.bwc label b{display:block;font-weight:600}.bwc label span{color:#5d6470;font-size:13.5px}
.bwc input{width:20px;height:20px;margin:2px 0 0;flex:none;accent-color:#15181d}
</style>
<h2 id="bwc-t">Your privacy choices</h2>
<p>We use essential cookies to run this site and handle your call or request. With your permission we also use analytics and marketing cookies. You can accept or reject non-essential cookies, or choose below. See our <a href="cookies.html">Cookie Policy</a>.</p>
<div class="prefs" id="bwc-prefs" hidden>
<label><input type="checkbox" checked disabled><span><b>Essential</b>Needed for calls, forms and security, so these stay on.</span></label>
<label><input type="checkbox" id="bwc-an"><span><b>Analytics</b>Helps us understand how the site is used.</span></label>
<label><input type="checkbox" id="bwc-mk"><span><b>Marketing</b>Attributes calls and leads to campaigns and partners, and may be used for advertising.</span></label>
</div>
<div class="row"><button type="button" class="pri" data-c="all">Accept all</button><button type="button" data-c="none">Reject non-essential</button><button type="button" data-c="prefs" id="bwc-mg">Manage preferences</button></div>
</div>
<script>
(function(){
  var K="bw_consent",box=document.getElementById("bw-consent"),prefs=document.getElementById("bwc-prefs"),an=document.getElementById("bwc-an"),mk=document.getElementById("bwc-mk"),mg=document.getElementById("bwc-mg");
  if(!box)return;
  var gpc=navigator.globalPrivacyControl===true;
  function read(){try{return JSON.parse(localStorage.getItem(K)||"null")}catch(e){return null}}
  function publish(c){window.bwConsent=c;try{window.dispatchEvent(new CustomEvent("bw:consent",{detail:c}))}catch(e){}}
  function save(a,m){var c={essential:true,analytics:!!a,marketing:!!m&&!gpc,gpc:gpc,ts:new Date().toISOString(),v:1};try{localStorage.setItem(K,JSON.stringify(c))}catch(e){}publish(c);box.hidden=true}
  function open(){var c=read();an.checked=c?!!c.analytics:false;mk.checked=c?!!c.marketing:false;prefs.hidden=true;mg.textContent="Manage preferences";box.hidden=false}
  box.addEventListener("click",function(ev){var b=ev.target.closest("button");if(!b)return;var k=b.getAttribute("data-c");
    if(k==="all")save(true,true);else if(k==="none")save(false,false);
    else if(k==="prefs"){if(prefs.hidden){prefs.hidden=false;b.textContent="Save choices"}else save(an.checked,mk.checked)}});
  var links=document.querySelector("footer .links");
  if(links){var a=document.createElement("a");a.href="#";a.textContent="Cookie settings";a.addEventListener("click",function(ev){ev.preventDefault();open()});links.appendChild(a)}
  var c=read();if(c){publish(c)}else{window.bwConsent={essential:true,analytics:false,marketing:false,gpc:gpc,pending:true};open()}
})();
</script>"""
