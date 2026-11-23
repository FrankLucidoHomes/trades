"""Frank Lucido's standard listing flyer: one layout, every listing.

Usage:
  python3 _tools/flyer/build_flyer.py spec.json OUTDIR

Writes OUTDIR/index.html (the flyer, plus a small top bar with PDF / Print buttons that never prints),
OUTDIR/img/ and OUTDIR/<slug>-flyer.pdf (US Letter, one page, print at actual size).

spec.json keys
  address     "29142 Jefferson Court"
  cityline    "St. Clair Shores, Michigan 48081"
  banner      "For Sale" | "Just Listed" | "Open House" | "Price Improvement"   (default "For Sale")
  tagline     one line under the address, e.g. "Lakefront townhome in the Lakeview Club"
  price       875000
  facts       [["3","Bedrooms"],["3.5","Baths"],["2,500","Sq. ft. above grade"],["2-car","Attached garage"]]
  hero        path to the main professional photo
  photos      up to 3 more professional photo paths (shown in a strip)
  highlights  5-7 short bullets
  note        optional small line under highlights (e.g. "Open Sunday 1-3")
  pdf_name    optional file name for the PDF
Only professional photos. Sq ft is above grade from the MLS; $/sq ft is computed from it.
"""
import sys, os, json, html, shutil, re

T = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(T, '..', 'presentation', 'img')
E = html.escape

CSS = """
@page { size: 8.5in 11in; margin: 0; }
:root { --navy:#0E2A5C; --navy2:#16397a; --blue:#2F6FCC; --sky:#EAF1FB; --silver:#9AA6B6; --ink:#1d2433; --muted:#5b6578; --gold:#C9A227; }
* { box-sizing:border-box; }
html,body { margin:0; padding:0; background:#dfe5ee; }
body { font-family:'Montserrat',Arial,sans-serif; color:var(--ink); -webkit-print-color-adjust:exact; print-color-adjust:exact; }
.bar { position:sticky; top:0; z-index:5; background:var(--navy); color:#fff; display:flex; gap:10px; align-items:center; padding:10px 14px; font-size:13px; }
.bar b { flex:1; font-weight:600; }
.bar a, .bar button { font:inherit; font-weight:700; color:var(--navy); background:#fff; border:0; border-radius:999px; padding:8px 14px; text-decoration:none; cursor:pointer; }
.sheet { width:8.5in; height:11in; margin:18px auto; background:#fff; position:relative; overflow:hidden; box-shadow:0 6px 30px rgba(0,0,0,.18); }
.head { position:absolute; left:.4in; right:.4in; top:.4in; height:.95in; display:flex; align-items:center; gap:14px; }
.head img { height:.8in; }
.head .brand { flex:1; }
.head .brand b { display:block; font-family:'Lora',serif; font-size:19pt; color:var(--navy); line-height:1.1; }
.head .brand span { font-size:8.5pt; letter-spacing:.16em; text-transform:uppercase; color:var(--muted); }
.ribbon { background:var(--gold); color:#fff; font-weight:800; letter-spacing:.18em; text-transform:uppercase; font-size:11pt; padding:10px 18px; border-radius:4px; }
.hero { position:absolute; left:.4in; right:.4in; top:1.45in; height:3.6in; border-radius:6px; overflow:hidden; }
.hero img { width:100%; height:100%; object-fit:cover; display:block; }
.hero .cap { position:absolute; left:0; right:0; bottom:0; padding:42px 22px 16px; background:linear-gradient(transparent, rgba(8,24,54,.88)); color:#fff; }
.hero .cap h1 { margin:0; font-family:'Lora',serif; font-size:28pt; line-height:1.05; }
.hero .cap div { font-size:11pt; margin-top:4px; color:#dbe6f7; }
.pricebar { position:absolute; left:.4in; right:.4in; top:5.15in; height:.95in; background:var(--navy); color:#fff; border-radius:6px; display:flex; align-items:stretch; }
.pricebar .p { padding:12px 20px; border-right:1px solid rgba(255,255,255,.18); min-width:2.4in; }
.pricebar .p b { display:block; font-family:'Lora',serif; font-size:24pt; line-height:1.05; }
.pricebar .p span { font-size:8.5pt; color:#b9cbea; }
.pricebar .f { flex:1; display:flex; align-items:center; justify-content:space-around; text-align:center; }
.pricebar .f div b { display:block; font-family:'Lora',serif; font-size:16pt; }
.pricebar .f div span { font-size:7.5pt; text-transform:uppercase; letter-spacing:.08em; color:#b9cbea; }
.strip { position:absolute; left:.4in; right:.4in; top:6.22in; height:1.3in; display:flex; gap:.12in; }
.strip img { flex:1; min-width:0; height:100%; object-fit:cover; border-radius:5px; display:block; }
.body { position:absolute; left:.4in; right:.4in; top:7.68in; height:1.7in; }
.body h2 { margin:0 0 4px; font-family:'Lora',serif; font-size:13pt; color:var(--navy); }
.body ul { margin:0; padding:0; list-style:none; columns:2; column-gap:.3in; }
.body li { font-size:9.5pt; line-height:1.35; padding-left:14px; position:relative; margin-bottom:5px; break-inside:avoid; }
.body li:before { content:''; position:absolute; left:0; top:.48em; width:6px; height:6px; background:var(--gold); border-radius:50%; }
.body .note { margin-top:4px; font-size:9pt; font-weight:700; color:var(--navy); }
.foot { position:absolute; left:0; right:0; bottom:0; height:1.38in; background:var(--sky); border-top:4px solid var(--navy); display:flex; align-items:center; gap:14px; padding:0 .4in; }
.foot .hs { width:.98in; height:.98in; border-radius:50%; object-fit:cover; border:3px solid #fff; box-shadow:0 0 0 2px var(--navy); }
.foot .who { flex:1; }
.foot .who b { display:block; font-family:'Lora',serif; font-size:16pt; color:var(--navy); }
.foot .who span { display:block; font-size:9pt; color:var(--ink); line-height:1.4; }
.foot .who .top { font-weight:700; color:var(--navy2); }
.foot .badge { height:.95in; }
.legal { position:absolute; left:.4in; right:.4in; bottom:1.42in; font-size:6.5pt; color:#8a93a3; text-align:right; }
@media print { html,body { background:#fff; } .bar { display:none; } .sheet { margin:0; box-shadow:none; } }
@media screen and (max-width: 840px) { .sheet { zoom: calc(100vw / 8.7in); } }
"""

def slugify(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

def build(spec, out):
    os.makedirs(os.path.join(out, 'img'), exist_ok=True)
    def cp(src, name):
        shutil.copy(src, os.path.join(out, 'img', name)); return 'img/' + name
    logo = cp(os.path.join(P, 'logo.png'), 'logo.png')
    badge = cp(os.path.join(P, 'badge.png'), 'badge.png')
    head = cp(os.path.join(P, 'frank.jpg'), 'frank.jpg')
    hero = cp(spec['hero'], 'hero' + os.path.splitext(spec['hero'])[1])
    strip = [cp(p, 'p%d%s' % (i, os.path.splitext(p)[1])) for i, p in enumerate(spec.get('photos', [])[:3])]
    slug = slugify(spec['address'])
    pdf = spec.get('pdf_name') or f'{slug}-flyer.pdf'
    price = spec['price']
    sf = None
    for v, k in spec.get('facts', []):
        if 'sq' in k.lower():
            sf = float(v.replace(',', ''))
    psf = f'${price/sf:,.0f} per sq. ft. above grade' if sf else ''
    facts = ''.join(f'<div><b>{E(v)}</b><span>{E(k)}</span></div>' for v, k in spec.get('facts', []))
    lis = ''.join(f'<li>{E(h)}</li>' for h in spec.get('highlights', []))
    note = f'<div class="note">{E(spec["note"])}</div>' if spec.get('note') else ''
    title = f"{spec['address']} Flyer"
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,600;0,700;1,500&family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<div class="bar"><b>{E(spec['address'])} · Flyer</b><a href="{E(pdf)}" download>PDF</a><button onclick="print()">Print</button></div>
<div class="sheet">
  <div class="head"><img src="{logo}" alt="Lucido Homes"><div class="brand"><b>Frank Lucido</b><span>REALTOR® · Sine &amp; Monaghan</span></div><div class="ribbon">{E(spec.get('banner','For Sale'))}</div></div>
  <div class="hero"><img src="{hero}" alt=""><div class="cap"><h1>{E(spec['address'])}</h1><div>{E(spec['cityline'])}{(' · ' + E(spec['tagline'])) if spec.get('tagline') else ''}</div></div></div>
  <div class="pricebar"><div class="p"><b>${price:,.0f}</b><span>{E(psf)}</span></div><div class="f">{facts}</div></div>
  <div class="strip">{''.join(f'<img src="{s}" alt="">' for s in strip)}</div>
  <div class="body"><h2>Highlights</h2><ul>{lis}</ul>{note}</div>
  <div class="legal">Information deemed reliable but not guaranteed. Square footage is approximate, above grade. Equal Housing Opportunity.</div>
  <div class="foot"><img class="hs" src="{head}" alt="Frank Lucido"><div class="who"><b>Frank Lucido, REALTOR®</b><span class="top">Top 5% in Metro Detroit · Hour Detroit Real Estate All-Star</span><span>Cell 586-419-7607 · frankjr@fjlucido.com</span><span>Sine &amp; Monaghan Realtors · franklucidohomes.com</span></div><img class="badge" src="{badge}" alt="Hour Detroit Real Estate All-Stars"></div>
</div></body></html>"""
    open(os.path.join(out, 'index.html'), 'w').write(doc)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        pg.goto('file://' + os.path.abspath(os.path.join(out, 'index.html')))
        pg.wait_for_load_state('networkidle')
        pg.pdf(path=os.path.join(out, pdf), width='8.5in', height='11in', print_background=True, prefer_css_page_size=True)
        pg.set_viewport_size({'width': 900, 'height': 1200})
        pg.screenshot(path=os.path.join(out, '_check.png'), full_page=True)
        b.close()
    return pdf

if __name__ == '__main__':
    spec = json.load(open(sys.argv[1]))
    base = os.path.dirname(os.path.abspath(sys.argv[1]))
    for k in ('hero',):
        spec[k] = os.path.join(base, spec[k]) if not os.path.isabs(spec[k]) else spec[k]
    spec['photos'] = [p if os.path.isabs(p) else os.path.join(base, p) for p in spec.get('photos', [])]
    print(build(spec, sys.argv[2]))
