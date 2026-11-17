"""The sign-in page. Reuses the studio's design tokens so it looks like part of the same product."""
import html

import ui
from ui import FONTS, THEME_BOOT, THEME_JS, ico

e = html.escape

CSS = """
.login{min-height:100vh;display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr)}
.lbrand{position:relative;display:flex;flex-direction:column;justify-content:space-between;padding:44px 52px;background:
  radial-gradient(900px 520px at 10% 0%,color-mix(in srgb,var(--accent) 26%,transparent),transparent 60%),var(--side);border-right:1px solid var(--line)}
.lbrand .logo{display:flex;align-items:center;gap:12px}
.lbrand h2{font:600 clamp(28px,3.2vw,40px)/1.12 var(--fd);letter-spacing:-.03em;margin:0 0 14px;max-width:14em}
.lbrand p{color:var(--mut);max-width:30em;margin:0}
.lbrand ul{list-style:none;margin:28px 0 0;padding:0;display:grid;gap:12px;color:var(--mut);font-size:14px}
.lbrand li{display:flex;gap:12px;align-items:flex-start}
.lbrand li .mark{margin-top:2px}
.lform{display:grid;place-items:center;padding:36px 22px;position:relative}
.lcard{width:100%;max-width:400px}
.lcard h1{font:600 28px/1.15 var(--fd);letter-spacing:-.03em;margin:0 0 6px}
.lcard .sub{color:var(--mut);margin:0 0 26px}
.lcard label.f{display:block;font-size:13px;color:var(--mut);margin:16px 0 6px}
.lcard input[type=email],.lcard input[type=password],.lcard input[type=text]{width:100%;height:46px;padding:0 14px;border-radius:12px;border:1px solid var(--line2);background:var(--surface);color:var(--ink);font:inherit;outline:none;transition:border-color .2s var(--ease),box-shadow .2s var(--ease)}
.lcard input:focus{border-color:var(--accent);box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 22%,transparent)}
.pw{position:relative}.pw input{padding-right:70px}
.pw button{position:absolute;right:6px;top:6px;height:34px;padding:0 12px;border:0;border-radius:9px;background:transparent;color:var(--mut);font:500 13px var(--fb);cursor:pointer}
.pw button:hover{color:var(--ink);background:var(--surface2)}
.rem{display:flex;align-items:center;gap:10px;margin:16px 0 22px;color:var(--mut);font-size:13.5px;cursor:pointer}
.lcard .btn.lg{width:100%;justify-content:center;height:48px}
.lerr{min-height:22px;margin-top:14px;font-size:13.5px;color:var(--bad)}
.lfoot{margin-top:26px;color:var(--faint);font-size:12.5px}
.ltheme{position:absolute;top:20px;right:20px}
@media(max-width:860px){.login{grid-template-columns:1fr}.lbrand{padding:26px 22px;border-right:0;border-bottom:1px solid var(--line);gap:26px}.lbrand ul{display:none}.lbrand h2{font-size:26px}}
"""

JS = """<script>
(function(){
  var f=document.getElementById('lf'),err=document.getElementById('err'),btn=document.getElementById('go'),pw=document.getElementById('pw');
  document.getElementById('showpw').onclick=function(){var on=pw.type==='password';pw.type=on?'text':'password';this.textContent=on?'Hide':'Show';};
  f.onsubmit=function(ev){ev.preventDefault();err.textContent='';btn.disabled=true;btn.classList.add('loading');
    fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:f.email.value,password:pw.value,remember:f.remember.checked,next:f.next.value})})
      .then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});})
      .then(function(x){if(x.ok&&x.j.ok){location.href=x.j.next||'/';}else{err.textContent=x.j.error||'Could not sign in.';btn.disabled=false;btn.classList.remove('loading');pw.select();}})
      .catch(function(){err.textContent='Could not reach the studio. Try again.';btn.disabled=false;btn.classList.remove('loading');});
  };
})();
</script>"""


def login_page(next_url="/", notice=""):
    points = [("Every brand in one place", "Launch board, ops and CRM driven by the Google Sheet."),
              ("Live Ringba, Everflow and LeadProsper data", "Calls, clicks and lead delivery side by side."),
              ("Nothing goes live unchecked", "Seven go-live checks and a legal sign-off first.")]
    pts = "".join(f'<li><span class="mark ok">{ico("check")}</span><span><b style="color:var(--ink);font-weight:500">{e(t)}</b><br>{e(d)}</span></li>' for t, d in points)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">'
            f'<title>Sign in | Brand Studio</title>{FONTS}{THEME_BOOT}<style>{ui.CSS}{CSS}</style></head><body>{ui.SPRITE}'
            f'<main class="login"><section class="lbrand"><a class="logo" href="/login"><i>BS</i><div><b>Brand Studio</b><span>Day One x BWA</span></div></a>'
            f'<div><h2>Build, check and launch every brand.</h2><p>Sign in to manage pages, campaigns and go-live checks.</p><ul>{pts}</ul></div>'
            f'<span class="lfoot" style="margin:0">Access is limited to Blue Wing Ads and Day One.</span></section>'
            f'<section class="lform"><button class="iconbtn ltheme" id="theme" aria-label="Toggle theme"><span class="sun">{ico("sun")}</span><span class="moon">{ico("moon")}</span></button>'
            f'<div class="lcard"><h1>Sign in</h1><p class="sub">Use your Blue Wing Ads email.</p>'
            f'<form id="lf" novalidate><input type="hidden" name="next" value="{e(next_url)}">'
            f'<label class="f" for="email">Email</label><input id="email" name="email" type="email" autocomplete="username" autofocus required placeholder="name@bluewingads.com">'
            f'<label class="f" for="pw">Password</label><div class="pw"><input id="pw" name="password" type="password" autocomplete="current-password" required><button type="button" id="showpw">Show</button></div>'
            f'<label class="rem"><input type="checkbox" name="remember"> Keep me signed in for 30 days</label>'
            f'<button class="btn primary lg" id="go" type="submit"><span class="spin"></span>Sign in</button>'
            f'<div class="lerr" id="err" role="alert" aria-live="polite">{e(notice)}</div></form></div></section></main>'
            f'<div class="toasts" id="toasts"></div>{THEME_JS}{JS}</body></html>')
