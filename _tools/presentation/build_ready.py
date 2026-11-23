"""Build Frank's "Get Ready to List" seller prep presentation.

Usage:  python3 _tools/presentation/build_ready.py spec.json OUTDIR
Writes OUTDIR/index.html (+img/ and a US Letter PDF). On screen the boxes can be checked and
are remembered on that phone/computer; printed, they are empty boxes to check by hand.
The same pages can go inside a listing presentation: add "Get Ready to List" to its pages.

spec.json keys
  address, cityline, prepared_for, date (optional), photo (optional cover photo)
  intro      optional note from Frank on the plan page
  prep       house-specific items: [{item, room, priority: must|should|nice, who, cost: $|$$|$$$, due, note}]
             (empty -> the plan page prints blank rows to fill in at the walkthrough)
  skip       optional list of checklist section ids to leave out: outside inside rooms systems showready
"""
import sys, os, json, html, re, shutil, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_presentation as BP
T = os.path.dirname(os.path.abspath(__file__)); E = html.escape
R = json.load(open(os.path.join(T, 'ready_items.json')))

def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

def ready_pages(S, start=0):
    """returns list of (kicker, title, content) for the prep section (no cover)"""
    out = []
    tl = ''.join(f'<div class="w">{E(w)}</div><div class="d">{E(d)}</div>' for w, d in R['timeline'])
    out.append(('Get Ready to List', 'Your Path to Market',
        f'<p class="lead">A great sale starts weeks before the sign goes up. Here is how we get your home ready, step by step — and what is worth doing.</p><div class="rl-tl">{tl}</div>'
        '<div class="callout"><b>You don’t have to do it alone.</b> I’ll walk the home with you, tell you what matters for your buyers, and connect you with my trusted local trades — painters, handymen, cleaners, landscapers and stagers.</div>'))
    cls = ['do', '', 'skip']
    cols = ''.join(f'<div class="col {cls[i]}"><b class="h">{h}</b><ul>' + ''.join(f'<li>{E(x)}</li>' for x in items) + '</ul></div>' for i, (h, items) in enumerate(R['payoff']))
    out.append(('Get Ready to List', 'What Pays Off — and What to Skip',
        '<p class="lead">The best pre-listing money goes to things buyers notice in photos and in the first minute of a showing.</p>'
        f'<div class="rl-pay">{cols}</div>'
        '<div class="callout"><b>My rule of thumb:</b> clean, bright, neutral and in good repair beats a renovation. If something big needs attention, my preference is to talk it through first — sometimes it’s smarter to price for it than to fix it.</div>'))
    skip = set(S.get('skip') or [])
    for sec in R['sections']:
        if sec['id'] in skip: continue
        groups = ''
        for g, items in sec['groups']:
            rows = ''.join(f'<label class="ck"><input type="checkbox" data-ck="{sec["id"]}-{slug(t)[:40]}"><span>{t}{"<small>"+E(n)+"</small>" if n else ""}</span></label>' for t, n in items)
            groups += f'<div class="ckg"><h4>{g}</h4>{rows}</div>'
        grid = 'ckgrid one' if len(sec['groups']) == 1 else 'ckgrid'
        out.append((sec['kicker'], sec['title'], f'<p class="lead">{sec["lead"]}</p><div class="{grid}">{groups}</div>'))
    # house plan
    prep = S.get('prep') or []
    if prep:
        order = {'must': 0, 'should': 1, 'nice': 2}
        prep = sorted(prep, key=lambda x: order.get(str(x.get('priority', 'should')).lower(), 1))
        rows = ''.join(f'<tr><td class="c"><label class="ck" style="border:0;padding:0"><input type="checkbox" data-ck="plan-{slug(p["item"])[:40]}"></label></td><td><b>{E(p["item"])}</b>{"<small>"+E(p["note"])+"</small>" if p.get("note") else ""}</td><td>{E(p.get("room",""))}</td><td class="c"><span class="pr {str(p.get("priority","should")).lower()}">{E(str(p.get("priority","Should")).title())}</span></td><td>{E(p.get("who",""))}</td><td class="c">{E(p.get("cost",""))}</td><td>{E(p.get("due",""))}</td></tr>' for p in prep)
    else:
        rows = ''.join('<tr class="blank"><td class="c">☐</td><td></td><td></td><td></td><td></td><td></td><td></td></tr>' for _ in range(14))
    intro = S.get('intro') or f'After we walk through {E(S["address"])} together, this is the short list for your home — what to do first, who will do it, and when. Everything else in this guide is optional polish.'
    out.append(('Get Ready to List', 'Your Home’s Plan',
        f'<p class="lead">{intro}</p><table class="plan"><tr><th style="width:.35in">Done</th><th>What</th><th>Room</th><th>Priority</th><th>Who</th><th>Cost</th><th>By</th></tr>{rows}</table>'
        '<p class="note">Priority: <span class="pr must">Must</span> before photos · <span class="pr should">Should</span> if time allows · <span class="pr nice">Nice</span> extra polish. Cost: $ under a few hundred · $$ a few hundred to a couple thousand · $$$ more — I’ll get you quotes from my local trades.</p>'))
    return out

CK_JS = r'''<div class="rl-prog" id="rlprog"></div><script>
(function(){var K="rl:"+location.pathname+":"+document.title,st={};try{st=JSON.parse(localStorage.getItem(K)||"{}")}catch(e){}
var bs=[].slice.call(document.querySelectorAll("input[data-ck]"));function prog(){var n=bs.filter(function(b){return b.checked}).length,p=document.getElementById("rlprog");if(p)p.textContent=n+" of "+bs.length+" done"}
bs.forEach(function(b){b.checked=!!st[b.dataset.ck];b.addEventListener("change",function(){st[b.dataset.ck]=b.checked;try{localStorage.setItem(K,JSON.stringify(st))}catch(e){}prog()})});prog();})();
</script>'''

def build(S, od):
    S.setdefault('date', datetime.date.today().strftime('%B %-d, %Y'))
    S['short'] = re.sub(r',\s*Michigan', ', MI', S['cityline'])
    photo = '<img src="img/home.jpg" class="cv-photo">' if S.get('photo') else ''
    secs = [f'''<section class="page cover">
  <div class="cv-band"></div><img src="img/logo.png" class="cv-logo">
  <div class="cv-kicker">SELLER PREP GUIDE</div>
  <h1 class="cv-title">Get Ready<br>to List</h1>
  <div class="cv-addr">{E(S['address'])}<br><span>{E(S['cityline'])}</span></div>
  <div class="cv-for">Prepared for <b>{E(S['prepared_for'])}</b><br>{E(S['date'])}</div>
  {photo}
  <div class="cv-quote">“You never get a second chance to make a first impression.”<span>— Will Rogers</span></div>
  <div class="cv-foot"><div><b>S. Frank Lucido</b><br>REALTOR® · Lucido Sales partnered with Sine &amp; Monaghan Realty<br>586-419-7607 · frankjr@fjlucido.com · franklucidohomes.com</div>
    <div class="cv-badge"><img src="img/badge.png"><span>Top 5%<br><small>Metro Detroit</small></span></div></div>
</section>''']
    for i, (k, t, c) in enumerate(ready_pages(S)):
        secs.append(BP.page(S, i + 2, k, t, c))
    css = open(os.path.join(T, 'style.css')).read()
    title = f"{S['address']} · Get Ready to List"
    pdf = re.sub(r'[^A-Za-z0-9]+', '-', S['address']).strip('-') + '-Get-Ready-to-List.pdf'
    doc = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{E(title)}</title>
<style>{css}</style></head><body><div class="bar"><div class="t"><b>{E(title)}</b><span>Prepared for {E(S['prepared_for'])} · Frank Lucido, REALTOR®</span></div>
<button class="hb" onclick="shareIt()">Share</button><a class="hb" href="{pdf}" download>PDF</a><a class="hb" href="tel:5864197607">Call Frank</a></div>
<div class="help"><b>Tap a box</b> to check it off — your checks are saved on this phone or computer · <b>Share</b> sends this page · <b>PDF</b> prints it (US Letter) · <b>Call Frank</b> dials 586-419-7607</div><div class="wrap" id="wrap">{"".join(secs)}</div>{CK_JS}<script>
function shareIt(){{var d={{title:{json.dumps(title)},text:{json.dumps('Your Get Ready to List guide for ' + S['address'] + ' from Frank Lucido')},url:location.href}};
 if(navigator.share){{navigator.share(d).catch(function(){{}})}}else{{try{{navigator.clipboard.writeText(location.href);document.querySelector('.help').textContent='Link copied'}}catch(e){{prompt('Copy this link',location.href)}}}}}}
function fit(){{var w=document.documentElement.clientWidth-16,pw=816,s=Math.min(1,w/pw),wr=document.getElementById('wrap');
 document.querySelectorAll('.page').forEach(function(p){{p.style.transform='scale('+s+')';p.style.marginBottom=(22-(1-s)*1056)+'px'}});wr.style.width=(pw*s)+'px';}}
window.addEventListener('resize',fit);fit();
</script></body></html>'''
    os.makedirs(os.path.join(od, 'img'), exist_ok=True)
    for f in os.listdir(os.path.join(T, 'img')): shutil.copy(os.path.join(T, 'img', f), os.path.join(od, 'img', f))
    if S.get('photo'): shutil.copy(S['photo'], os.path.join(od, 'img', 'home.jpg'))
    open(os.path.join(od, 'index.html'), 'w').write(doc)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(); pg = b.new_page()
            pg.goto('file://' + os.path.abspath(os.path.join(od, 'index.html'))); pg.emulate_media(media='print')
            pg.pdf(path=os.path.join(od, pdf), width='8.5in', height='11in', print_background=True, prefer_css_page_size=True); b.close()
    except Exception as e: print('PDF not made:', e)
    return len(secs)

if __name__ == '__main__':
    S = json.load(open(sys.argv[1])); n = build(S, sys.argv[2]); print(n, 'pages ->', os.path.join(sys.argv[2], 'index.html'))
