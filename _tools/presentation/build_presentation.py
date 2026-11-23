"""Build Frank's branded listing presentation (CMA) from one data file.

Usage:
  python3 _tools/presentation/build_presentation.py spec.json OUTDIR

Writes OUTDIR/agent/index.html, OUTDIR/client/index.html (each with img/ and a US Letter PDF).
The look and the fixed pages (About Me, Marketing Action Plan, Offer Handling, ...) come from
the approved 31566 Juniper (Mace) presentation; only the data pages change per home.

spec.json keys
  address        "198 Lakeview"
  cityline       "Grosse Pointe Farms, Michigan 48236"
  area           neighborhood / complex name used in labels ("Grosse Pointe Farms")
  prepared_for   "Eric & Lisa Thams"
  date           "November 22, 2026"            (optional, default today)
  subject        {beds, baths, sqft (above grade), year}
  photo          path to the home photo (cover)           optional
  map            path to the comp map image (box around comps + area outline)
  map_note       sentence under the map                    optional
  comps_note     sentence under the comps table (source, dates)
  sold   [{a, beds, baths, sf, lp, sp, date "9/28/26", dom, hoa}]   hoa optional (0/None = none)
  active [{a, beds, baths, sf, lp, listed, dom, hoa}]
  match_beds     bedroom count for the "closest match" table (default subject beds)
  range          [low, high]  suggested price range (agent copy only)
  range_note     optional override for "How I set this range"
  pages          list of page ids (put in Cloud CMA order unless keep_order is true):
                 cover glance about commitment loyalty map comps actives psf value range time
                 highlow choosing intelligent marketing ready offer testimonials resume
                 (ready = the Get Ready to List pages; spec may then also carry prep/skip/intro, see build_ready.py)
                 (map, comps and actives are always included)
  keep_order     true = keep the pages in the order listed (Frank arranges them by dragging on his dashboard);
                 "comps" (or the name "Comp map, comparable sales & actives") marks where map/comps/actives go
  quote          optional cover quote [text, author]
"""
import sys, os, json, html, shutil, re, datetime, statistics as st

T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, T)
E = html.escape
ORDER = ['cover','glance','about','commitment','loyalty','map','comps','actives','psf','value','range','time',
         'highlow','choosing','intelligent','marketing1','marketing2','ready','offer','testimonials1','testimonials2','resume']
ALIAS = {'marketing':['marketing1','marketing2'],'testimonials':['testimonials1','testimonials2'],
         'title':['glance'],'suggested':['range'],'pricepersqft':['psf'],'comps':['map','comps','actives']}
TOCNAME = {'about':'About Me','commitment':'My Personal Commitment','loyalty':'Loyalty &amp; Commitment','map':'{area} Map',
           'comps':'Comparable Sales &amp; Actives','psf':'Average Price per Sq. Ft.','value':'The Value of Your Home',
           'range':'Suggested Price Range','time':'Time to Sell','highlow':'High / Low Pricing Strategies',
           'intelligent':'Intelligent Pricing &amp; Timing',
           'marketing1':'Marketing Action Plan','ready':'Get Ready to List','offer':'Offer Handling Strategy','testimonials1':'Client Testimonials','resume':'Resume'}

def money(v): return '${:,.0f}'.format(v)
def num(v): return '{:,.0f}'.format(v)
def psf(p, sf): return p / sf if sf else 0
def pct(v): return '{:.1f}%'.format(v)
def avg(xs): xs = [x for x in xs if x]; return sum(xs) / len(xs) if xs else 0
def bb(r): return '{} / {}'.format(r.get('beds', '—'), r.get('baths', '—'))

def page(S, n, kicker, title, content, cls=''):
    return f'''<section class="page {cls}">
  <div class="topbar"><img src="img/logo.png" class="tlogo"><span>{E(S['address'])} · {E(S['short'])}</span><span class="pfor">Prepared for {E(S['prepared_for'])}</span></div>
  <div class="ph"><div class="kicker">{kicker}</div><h1>{title}</h1><div class="rule"></div></div>
  <div class="content">
{content}
</div>
  <footer>
    <img src="img/frank.jpg" class="fhead">
    <div class="fname"><b>S. Frank Lucido</b><br>REALTOR® · Lucido Sales partnered with Sine &amp; Monaghan Realty<br>Cell 586-419-7607 · frankjr@fjlucido.com · franklucidohomes.com</div>
    <div class="fbadge"><img src="img/badge.png"><span>Top 5%<br><small>Metro Detroit</small></span></div>
    <div class="pnum">{n}</div>
  </footer>
</section>'''

def scatter(points, xlab, ylab_fmt, w=640, h=330, ref=None, reflabel='', vline=None, vlabel=''):
    """points: [(x, y, label, cls)]  ->  svg in the Mace chart style"""
    xs = [p[0] for p in points] + ([vline] if vline else []); ys = [p[1] for p in points] + ([ref] if ref else [])
    x0, x1 = min(xs), max(xs); y0, y1 = min(ys), max(ys)
    def nice(a, b, n=6):
        span = (b - a) or 1; raw = span / n
        mag = 10 ** len(str(int(raw))) / 10 if raw >= 1 else 0.1
        step = min([s * mag for s in (1, 2, 2.5, 5, 10)], key=lambda s: abs(span / s - n))
        lo = (a // step) * step; hi = -(-b // step) * step
        return lo, hi, step
    xl, xh, xs_ = nice(x0, x1); yl, yh, ys_ = nice(y0, y1)
    L, R, Tp, B = 64, w - 18, 18, h - 40
    X = lambda v: L + (v - xl) / ((xh - xl) or 1) * (R - L)
    Y = lambda v: B - (v - yl) / ((yh - yl) or 1) * (B - Tp)
    o = [f'<svg viewBox="0 0 {w} {h}" class="chart">']
    v = yl
    while v <= yh + 1e-9:
        o.append(f'<line x1="{L}" x2="{R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="grid"/><text x="{L-8}" y="{Y(v)+4:.1f}" class="ax" text-anchor="end">{ylab_fmt(v)}</text>'); v += ys_
    v = xl
    while v <= xh + 1e-9:
        o.append(f'<text x="{X(v):.1f}" y="{B+18}" class="ax" text-anchor="middle">{num(v)}</text>'); v += xs_
    o.append(f'<text x="{(L+R)/2:.1f}" y="{h-2}" class="ax" text-anchor="middle">{xlab}</text>')
    if ref is not None:
        o.append(f'<line x1="{L}" x2="{R}" y1="{Y(ref):.1f}" y2="{Y(ref):.1f}" class="avgl"/>')
        if reflabel: o.append(f'<text x="{R-4}" y="{Y(ref)-6:.1f}" class="avgt" text-anchor="end">{reflabel}</text>')
    for x, y, lab, cls in points:
        o.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="9" class="{cls}"/><text x="{X(x):.1f}" y="{Y(y)+3.5:.1f}" class="dl">{lab}</text>')
    if vline:
        o.append(f'<line x1="{X(vline):.1f}" x2="{X(vline):.1f}" y1="{Tp}" y2="{B}" class="subjl"/><text x="{X(vline)+6:.1f}" y="30" class="subjt">{vlabel}</text>')
    o.append('</svg>'); return ''.join(o)

def build(S, copy):
    agent = copy == 'agent'
    sub = S['subject']; sold = S['sold']; act = S.get('active', [])
    for i, r in enumerate(sold): r['n'] = i + 1
    for i, r in enumerate(act): r['n'] = len(sold) + i + 1
    area = S.get('area') or S['cityline'].split(',')[0]
    want = []
    for p in S['pages']:
        k = re.sub(r'[^a-z]', '', p.lower())
        k = {'cover':'cover','titlepage':'glance','averagepricepersqft':'psf','thevalueofyourhome':'value','suggestedlistprice':'range',
             'suggestedpricerange':'range','timetosell':'time','highlowpricingstrategies':'highlow','intelligentpricingandtiming':'intelligent',
             'marketingactionplan':'marketing','offerhandlingstrategy':'offer','aboutme':'about','personalcommitment':'commitment',
             'mypersonalcommitment':'commitment','loyaltycommitment':'loyalty','clienttestimonials':'testimonials','resume':'resume',
             'choosingtherightstrategy':'choosing','getreadytolist':'ready','readytolist':'ready',
             'compmapcomparablesalesactives':'comps','compmap':'comps'}.get(k, k)
        want += ALIAS.get(k, [k])
    if 'highlow' in want: want.insert(want.index('highlow') + 1, 'choosing')
    if 'comps' not in want:                      # map, comps and actives are always included
        later = [i for i, w in enumerate(want) if w in ('psf', 'value', 'range', 'time')]
        at = later[0] if later else len(want)
        want[at:at] = ['map', 'comps', 'actives']
    if not agent: want = [w for w in want if w != 'range']
    if S.get('keep_order'):
        pages = []
        for w in want:
            if w in ORDER and w not in pages: pages.append(w)
    else:
        pages = [p for p in ORDER if p in want]

    # numbers
    sp = [r['sp'] for r in sold]; spsf = [psf(r['sp'], r['sf']) for r in sold]; lpsf = [psf(r['lp'], r['sf']) for r in sold]
    ratio = [r['sp'] / r['lp'] * 100 for r in sold if r.get('lp')]; dom = [r['dom'] for r in sold if r.get('dom') is not None]
    mb = S.get('match_beds', sub['beds']); match = [r for r in sold if str(r.get('beds')) == str(mb)]
    hoas = [r['hoa'] for r in sold + act if r.get('hoa')]
    A = dict(n=len(sold), spsf=avg(spsf), lpsf=avg(lpsf), dom=avg(dom), ratio=avg(ratio),
             msf=avg([psf(r['sp'], r['sf']) for r in match]), apsf=avg([psf(r['lp'], r['sf']) for r in act]))
    lo, hi = (S.get('range') or [0, 0])
    S['short'] = S.get('short') or re.sub(r',\s*Michigan', ', MI', S['cityline'])
    out = []; pn = 0

    def P(k, t, c, cls=''):
        nonlocal pn; pn += 1; out.append(page(S, pn, k, t, c, cls))

    for p in pages:
        if p == 'cover':
            pn += 1
            q = S.get('quote') or ['In God we trust. All others bring data.', 'W. Edwards Deming']
            photo = '<img src="img/home.jpg" class="cv-photo">' if S.get('photo') else ''
            out.append(f'''<section class="page cover">
  <div class="cv-band"></div>
  <img src="img/logo.png" class="cv-logo">
  <div class="cv-kicker">LISTING PRESENTATION</div>
  <h1 class="cv-title">Comparative<br>Market Analysis</h1>
  <div class="cv-addr">{E(S['address'])}<br><span>{E(S['cityline'])}</span></div>
  <div class="cv-for">Prepared for <b>{E(S['prepared_for'])}</b><br>{E(S['date'])}</div>
  {photo}
  <div class="cv-quote">“{E(q[0])}”<span>— {E(q[1])}</span></div>
  <div class="cv-foot">
    <div><b>S. Frank Lucido</b><br>REALTOR® · Lucido Sales partnered with Sine &amp; Monaghan Realty<br>586-419-7607 · frankjr@fjlucido.com · franklucidohomes.com</div>
    <div class="cv-badge"><img src="img/badge.png"><span>Top 5%<br><small>Metro Detroit</small></span></div>
  </div>
</section>''')
        elif p == 'glance':
            toc = [TOCNAME[x].replace('{area}', E(area)) for x in pages if x in TOCNAME]
            toc = ''.join(f'<li><span>{i+1:02d}</span>{t}</li>' for i, t in enumerate(toc))
            P(f'Listing Presentation · {E(S["date"])}', 'Comparative Market Analysis', f'''<div class="glance">
  <div class="gl-left">
    <div class="eyebrow">Your home at a glance</div>
    <h2 class="big">{E(S['address'])}</h2>
    <div class="sub">{E(area)} · {E(S['cityline'])}</div>
    <div class="facts">
      <div><b>{sub['beds']}</b><span>Bedrooms</span></div>
      <div><b>{sub['baths']}</b><span>Baths</span></div>
      <div><b>{num(sub['sqft'])}</b><span>Above-grade sq ft</span></div>
      <div><b>{sub.get('year','—')}</b><span>Year built</span></div>
    </div>
    <div class="eyebrow" style="margin-top:28px">What the market says</div>
    <div class="kpis">
      <div class="kpi"><b>{A['n']}</b><span>{E(area)} sales<br>{E(S.get('period_short','in the comparison period'))}</span></div>
      <div class="kpi"><b>{money(A['spsf'])}</b><span>Average sold<br>price per sq ft</span></div>
      <div class="kpi"><b>{A['dom']:.0f}</b><span>Average days<br>on market</span></div>
      <div class="kpi"><b>{pct(A['ratio'])}</b><span>Average sold-to-<br>list price</span></div>
    </div>
  </div>
  <div class="gl-right">
    <div class="eyebrow">Inside this presentation</div>
    <ol class="toc">{toc}</ol>
  </div>
</div>''')
        elif p == 'map':
            leg = ''.join(f'<div class="lg"><i class="sold">{r["n"]}</i>{E(r["a"])}</div>' for r in sold) + \
                  ''.join(f'<div class="lg"><i class="act">{r["n"]}</i>{E(r["a"])}</div>' for r in act)
            img = '<img src="img/map.png" class="map">' if S.get('map') else '<div class="callout">Map to come.</div>'
            P('The Neighborhood', f'{E(area)} Comp Map', f'''{img}
<div class="maplegend">
  <div class="mlk"><span class="key star">★</span>Your home &nbsp; <span class="key sold"></span>Sold &nbsp; <span class="key act"></span>Active &nbsp; <span class="key box"></span>Comparable sales area &nbsp; <span class="key dash"></span>{E(area)} (outline approximate)</div>
  <div class="lgrid">{leg}</div>
</div>
<p class="note">{E(S.get('map_note',''))}</p>''')
        elif p == 'comps':
            head = '<tr><th>#</th><th>Address</th><th>Bed / Bath</th><th>Sq Ft</th><th>List Price<small>$ / sq ft</small></th><th>Sold Price<small>$ / sq ft</small></th><th>Sold / List</th><th>Date</th><th>DOM</th><th>HOA / mo</th></tr>'
            subjp = (f'<td class="r strong">{money(lo)} – {money(hi)}<small>${psf(lo,sub["sqft"]):.0f} – ${psf(hi,sub["sqft"]):.0f}/sf · suggested range</small></td>'
                     if agent and lo else '<td class="r">—</td>')
            rows = [f'<tr class="subj"><td class="c">★</td><td class="addr">{E(S["address"])} <small>(your home)</small></td><td class="c">{sub["beds"]} / {sub["baths"]}</td><td class="r">{num(sub["sqft"])}</td>{subjp}<td class="r">—</td><td class="c">—</td><td class="c">—</td><td class="c">—</td><td class="r">—</td></tr>']
            for r in sold:
                rows.append(f'<tr><td class="c">{r["n"]}</td><td class="addr">{E(r["a"])}</td><td class="c">{bb(r)}</td><td class="r">{num(r["sf"])}</td><td class="r">{money(r["lp"])}<small>${psf(r["lp"],r["sf"]):.0f}/sf</small></td><td class="r strong">{money(r["sp"])}<small>${psf(r["sp"],r["sf"]):.0f}/sf</small></td><td class="c">{pct(r["sp"]/r["lp"]*100)}</td><td class="c">{E(r["date"])}</td><td class="c">{r.get("dom","—")}</td><td class="r">{money(r["hoa"]) if r.get("hoa") else "—"}</td></tr>')
            rows.append(f'<tr class="avg"><td></td><td class="addr">Averages — {len(sold)} sales</td><td></td><td class="r">{num(avg([r["sf"] for r in sold]))}</td><td class="r">{money(avg([r["lp"] for r in sold]))}<small>${A["lpsf"]:.0f}/sf</small></td><td class="r">{money(avg(sp))}<small>${A["spsf"]:.0f}/sf</small></td><td class="c">{pct(A["ratio"])}</td><td></td><td class="c">{A["dom"]:.0f}</td><td class="r">{money(avg([r.get("hoa") for r in sold])) if any(r.get("hoa") for r in sold) else "—"}</td></tr>')
            P('The Numbers', 'Comparable Sales', f'<table class="comps">{head}{"".join(rows)}</table>\n<p class="note">{E(S.get("comps_note",""))} Square footage is above-grade; $/sq ft is figured on above-grade square footage. DOM = days on market as reported by the MLS. HOA is the monthly association fee.</p>')
        elif p == 'actives':
            c = '<h3 class="sec">Currently for sale — your competition</h3>'
            if act:
                rows = ''.join(f'<tr><td class="c">{r["n"]}</td><td class="addr">{E(r["a"])}</td><td class="c">{bb(r)}</td><td class="r">{num(r["sf"])}</td><td class="r">{money(r["lp"])}<small>${psf(r["lp"],r["sf"]):.0f}/sf</small></td><td class="r muted">For sale</td><td class="c">—</td><td class="c">{E(r.get("listed",""))}</td><td class="c">{r.get("dom","—")}</td><td class="r">{money(r["hoa"]) if r.get("hoa") else "—"}</td></tr>' for r in act)
                c += f'<table class="comps"><tr><th>#</th><th>Address</th><th>Bed / Bath</th><th>Sq Ft</th><th>List Price<small>$ / sq ft</small></th><th>Sold Price</th><th>Sold / List</th><th>Listed</th><th>DOM</th><th>HOA / mo</th></tr>{rows}<tr class="avg"><td></td><td class="addr">Average asking — {len(act)} active{"s" if len(act)!=1 else ""}</td><td></td><td class="r">{num(avg([r["sf"] for r in act]))}</td><td class="r">{money(avg([r["lp"] for r in act]))}<small>${A["apsf"]:.0f}/sf</small></td><td></td><td></td><td></td><td class="c">{avg([r.get("dom") for r in act]):.0f}</td><td class="r">{money(avg([r.get("hoa") for r in act])) if any(r.get("hoa") for r in act) else "—"}</td></tr></table>'
            else:
                c += '<p>No comparable homes are for sale right now.</p>'
            if match:
                rows = ''.join(f'<tr><td class="c">{r["n"]}</td><td class="addr">{E(r["a"])}</td><td class="c">{bb(r)}</td><td class="r">{num(r["sf"])}</td><td class="r">{money(r["lp"])}<small>${psf(r["lp"],r["sf"]):.0f}/sf</small></td><td class="r strong">{money(r["sp"])}<small>${psf(r["sp"],r["sf"]):.0f}/sf</small></td><td class="c">{pct(r["sp"]/r["lp"]*100)}</td><td class="c">{E(r["date"])}</td><td class="c">{r.get("dom","—")}</td><td class="r">{money(r["hoa"]) if r.get("hoa") else "—"}</td></tr>' for r in match)
                c += f'<h3 class="sec">{mb}-bedroom sales — the closest match to your home</h3><table class="comps"><tr><th>#</th><th>Address</th><th>Bed / Bath</th><th>Sq Ft</th><th>List Price<small>$ / sq ft</small></th><th>Sold Price<small>$ / sq ft</small></th><th>Sold / List</th><th>Date</th><th>DOM</th><th>HOA / mo</th></tr>{rows}<tr class="avg"><td></td><td class="addr">Averages — {len(match)} {mb}-bedroom sales</td><td></td><td class="r">{num(avg([r["sf"] for r in match]))}</td><td class="r">{money(avg([r["lp"] for r in match]))}<small>${avg([psf(r["lp"],r["sf"]) for r in match]):.0f}/sf</small></td><td class="r">{money(avg([r["sp"] for r in match]))}<small>${A["msf"]:.0f}/sf</small></td><td class="c">{pct(avg([r["sp"]/r["lp"]*100 for r in match]))}</td><td></td><td class="c">{avg([r.get("dom") for r in match]):.0f}</td><td class="r">{money(avg([r.get("hoa") for r in match])) if any(r.get("hoa") for r in match) else "—"}</td></tr></table>'
            if hoas:
                c += f'<div class="hoabox"><b>HOA dues in {E(area)}:</b> {money(min(hoas))} – {money(max(hoas))} per month across these homes (average {money(avg(hoas))}). Amounts are as listed in each home’s MLS record.</div>'
            P('The Numbers', f'Active Listings &amp; {mb}-Bedroom Sales', c)
        elif p == 'psf':
            pts = [(r['sf'], psf(r['sp'], r['sf']), r['n'], 'dsold') for r in sold] + [(r['sf'], psf(r['lp'], r['sf']), r['n'], 'dact') for r in act]
            svg = scatter(pts, 'Above-grade square feet', lambda v: '$%d' % v, ref=A['spsf'], reflabel=f'Sold avg ${A["spsf"]:.0f}/sf',
                          vline=sub['sqft'], vlabel=f'Your home · {num(sub["sqft"])} sq ft')
            # size groups: quartiles of sold sq ft
            srt = sorted(sold, key=lambda r: r['sf']); k = max(1, round(len(srt) / 4)); grp = [srt[i:i+k] for i in range(0, len(srt), k)]
            rows = ''.join(f'<tr><td>{num(g[0]["sf"])} – {num(g[-1]["sf"])} sq ft</td><td class="c">{len(g)}</td><td class="r">{money(avg([r["sp"] for r in g]))}</td><td class="r strong">${avg([psf(r["sp"],r["sf"]) for r in g]):.0f}</td></tr>' for g in grp)
            P('The Numbers', 'Average Price per Square Foot', f'''<div class="kpis row">
  <div class="kpi"><b>${A['spsf']:.0f}</b><span>Average sold $/sq ft<br>{len(sold)} sales</span></div>
  <div class="kpi"><b>${A['lpsf']:.0f}</b><span>Average list $/sq ft<br>same {len(sold)} homes</span></div>
  <div class="kpi"><b>{('$%.0f' % A['msf']) if match else '—'}</b><span>{mb}-bedroom sold $/sq ft<br>{len(match)} sales</span></div>
  <div class="kpi"><b>{('$%.0f' % A['apsf']) if act else '—'}</b><span>Active asking $/sq ft<br>{len(act)} for sale</span></div>
</div>
{svg}
<div class="legend2"><span class="key sold"></span>Sold (sold price) &nbsp;&nbsp; <span class="key act"></span>Active (asking price) &nbsp;&nbsp; numbers match the map and tables</div>
<table class="mini"><tr><th>Home size</th><th>Sales</th><th>Avg sold</th><th>Avg $/sq ft</th></tr>{rows}</table>''')
        elif p == 'range':
            inr = [r for r in sold if lo <= r['sp'] <= hi]
            steps = list(range(int(lo), int(hi) + 1, 5000))
            lad = ''.join(f'<tr><td class="r strong">{money(v)}</td><td class="r">${psf(v,sub["sqft"]):.0f}</td><td class="c">{", ".join("#%d" % r["n"] for r in sold if abs(r["sp"]-v) <= 2500) or "—"}</td></tr>' for v in steps)
            mt = ''.join(f'<tr><td>#{r["n"]} {E(r["a"])}</td><td class="r">{num(r["sf"])}</td><td class="r">{money(r["sp"])}</td><td class="r strong">${psf(r["sp"],r["sf"]):.0f}</td></tr>' for r in match)
            note = S.get('range_note') or f'I start with what homes in {E(area)} have actually sold for and their price per square foot. That gives us the range. From there, my preference is to see your home in person — updates, condition, finishes, basement, and lot — so I can zero in and suggest a specific list price that fits your goals.'
            P('Pricing', 'Suggested Price Range', f'''<div class="slp">
  <div class="slp-hero"><div class="eyebrow light">Suggested price range</div><div class="slp-price range">{money(lo)} – {money(hi)}</div><div class="slp-psf">${psf(lo,sub['sqft']):.0f} – ${psf(hi,sub['sqft']):.0f} per above-grade sq ft · {num(sub['sqft'])} sq ft</div></div>
  <div class="slp-side">
    <div class="kpi"><b>{('$%.0f' % A['msf']) if match else '—'}</b><span>{mb}-bed sold avg $/sq ft</span></div>
    <div class="kpi"><b>${A['spsf']:.0f}</b><span>All sales avg $/sq ft</span></div>
    <div class="kpi"><b>{len(inr)} of {len(sold)}</b><span>{E(area)} sales closed in this range</span></div>
  </div>
</div>
<div class="callout"><b>How I set this range.</b> {note}</div>
<div class="two">
  <div><h3 class="sec">Price ladder — $5,000 steps</h3><table class="mini ladder"><tr><th>Price</th><th>$ / sq ft</th><th>Sold near this price</th></tr>{lad}</table>
  <p class="note">“Sold near this price” lists comps (by map number) that sold within $2,500 of that step.</p></div>
  <div><h3 class="sec">{mb}-bedroom sales</h3><table class="mini"><tr><th>Home</th><th>Sq ft</th><th>Sold</th><th>$/sf</th></tr>
  {mt}</table></div>
</div>''')
        elif p == 'time':
            pts = [(r['dom'], r['sp'] / r['lp'] * 100, r['n'], 'dsold') for r in sold if r.get('dom') is not None]
            fast = [r for r in sold if (r.get('dom') or 0) <= 14]; slow = [r for r in sold if (r.get('dom') or 0) > 14]
            svg = scatter(pts, 'Days on market', lambda v: '%d%%' % v, h=250, ref=100)
            fr = avg([r['sp'] / r['lp'] * 100 for r in fast]); sr = avg([r['sp'] / r['lp'] * 100 for r in slow])
            P('Pricing', 'Time to Sell', f'''<div class="kpis row">
  <div class="kpi"><b>{A['dom']:.0f}</b><span>Average days<br>on market</span></div>
  <div class="kpi"><b>{pct(A['ratio'])}</b><span>Average sold-to-<br>list price</span></div>
  <div class="kpi"><b>{len(fast)} of {len(sold)}</b><span>sold within<br>2 weeks</span></div>
  <div class="kpi"><b>{pct(fr) if fast else '—'}</b><span>sold-to-list when<br>sold within 2 weeks</span></div>
</div>
{svg}
<div class="two tight">
  <div class="card"><b>Sold within 2 weeks ({len(fast)} homes)</b><span>Average sold-to-list price <b>{pct(fr) if fast else '—'}</b> · average {avg([r['dom'] for r in fast]):.0f} days</span></div>
  <div class="card"><b>On the market longer than 2 weeks ({len(slow)} homes)</b><span>Average sold-to-list price <b>{pct(sr) if slow else '—'}</b> · average {avg([r['dom'] for r in slow]):.0f} days</span></div>
</div>
<p class="note">Each dot is a {E(area)} sale (numbers match the map and tables). The line marks 100% of list price.</p>''')
        elif p == 'ready':
            import build_ready
            for k, t, c in build_ready.ready_pages(S): P(k, t, c)
        else:
            d = json.load(open(os.path.join(T, 'static', p + '.json')))
            P(d['kicker'], d['title'], d['content'], d.get('cls', ''))
    return out

def write(S, copy, od, pdfname):
    secs = build(S, copy)
    css = open(os.path.join(T, 'style.css')).read()
    tag = ' · Agent copy' if copy == 'agent' else ''
    title = f"{S['address']} · Listing Presentation"
    doc = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{E(title)}{tag}</title>
<style>{css}</style></head><body><div class="bar"><div class="t"><b>{E(title)}{tag}</b><span>Prepared for {E(S['prepared_for'])} · Frank Lucido, REALTOR®</span></div>
<button class="hb" onclick="shareIt()">Share</button><a class="hb" href="{pdfname}" download>PDF</a><a class="hb" href="tel:5864197607">Call Frank</a></div>
<div class="help"><b>Share</b> sends this page by text or email · <b>PDF</b> downloads a print-ready copy (US Letter, print at actual size) · <b>Call Frank</b> dials 586-419-7607</div><div class="wrap" id="wrap">{"".join(secs)}</div><script>
function shareIt(){{var d={{title:{json.dumps(title)},text:{json.dumps('Listing presentation for ' + S['address'] + ' from Frank Lucido')},url:location.href}};
 if(navigator.share){{navigator.share(d).catch(function(){{}})}}else{{try{{navigator.clipboard.writeText(location.href);document.querySelector('.help').textContent='Link copied'}}catch(e){{prompt('Copy this link',location.href)}}}}}}
function fit(){{var w=document.documentElement.clientWidth-16,pw=816,s=Math.min(1,w/pw),wr=document.getElementById('wrap');
 document.querySelectorAll('.page').forEach(function(p){{p.style.transform='scale('+s+')';p.style.marginBottom=(22-(1-s)*1056)+'px'}});
 wr.style.width=(pw*s)+'px';}}
window.addEventListener('resize',fit);fit();
</script></body></html>'''
    os.makedirs(os.path.join(od, 'img'), exist_ok=True)
    for f in os.listdir(os.path.join(T, 'img')): shutil.copy(os.path.join(T, 'img', f), os.path.join(od, 'img', f))
    if S.get('photo'): shutil.copy(S['photo'], os.path.join(od, 'img', 'home.jpg'))
    if S.get('map'): shutil.copy(S['map'], os.path.join(od, 'img', 'map.png'))
    if copy == 'agent':  # Frank's copy: Home button back to his dashboard (never on client copies)
        doc = doc.replace('</body>', open(os.path.join(T, 'home_button.html')).read() + '</body>', 1)
    open(os.path.join(od, 'index.html'), 'w').write(doc)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(); pg = b.new_page()
            pg.goto('file://' + os.path.abspath(os.path.join(od, 'index.html'))); pg.emulate_media(media='print')
            pg.pdf(path=os.path.join(od, pdfname), width='8.5in', height='11in', print_background=True, prefer_css_page_size=True)
            b.close()
    except Exception as e:
        print('PDF not made:', e)
    return len(secs)

if __name__ == '__main__':
    S = json.load(open(sys.argv[1])); od = sys.argv[2]
    S.setdefault('date', datetime.date.today().strftime('%B %-d, %Y'))
    base = re.sub(r'[^A-Za-z0-9]+', '-', S['address']).strip('-')
    for copy in ('agent', 'client'):
        n = write(json.loads(json.dumps(S)), copy, os.path.join(od, copy), f'{base}-Listing-Presentation{"-Agent" if copy=="agent" else ""}.pdf')
        print(copy, n, 'pages ->', os.path.join(od, copy, 'index.html'))
