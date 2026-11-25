#!/usr/bin/env python3
"""Frank's ONE deal tracker template ("This is what happens now"), for every purchase.

usage:
  build_deal.py new SPEC.json OUT.html            # brand-new deal from a short spec (agent copy)
  build_deal.py page DEAL.json OUT.html [--client] [--state STATE.json]
                                                  # render an existing deal's data (agent copy, or the buyers' copy)

Files here:
  template.html  the page (agent and client copies are the same code; MODE switches what shows)
  panels.js      the "Answer questions" / "What changed?" / add-ons code (already merged into template.html;
                 kept separately so it's easy to read)
  library.json   core steps every deal gets + add-on packs (financing, condo, sale of buyer's home, sellers stay
                 after closing, early possession, city C of O, lead paint, repairs/credit, home warranty, survey)
  img/           logo, All-Stars badge, Frank's photos (publish them next to the page as img/...)

SPEC.json for a new deal (anything left out can be answered later on the page with "Answer questions"):
  {"address","short","city","buyers","first","sellers","price","accepted":"YYYY-MM-DD","close":"YYYY-MM-DD",
   "inspDays":7,"emd":"$7,500","title":"ATA Title","included":"...","emails":[],"phones":[{"name","num"}],
   "people":[{"role","name","org","phone","email","mine":true}],   # listing agent: mine=true (only Frank sees)
   "answers":{"pay":"cash|fin|tbd","condo":"yes|no","pre78":"yes|no","cofo":"yes|no","sale":"yes|no",
              "poss":"close|stay|early","repairs":"yes|no|tbd","warranty":"yes|no","survey":"yes|no"}}

STATE.json: the agent page's db doc deal/state (steps/inc/notes/sentlog/data). With --client, Frank's saved edits
are applied and everything private is removed: "only you" steps and people, steps marked Do not send, his notes,
step notes, sellers' names, the sent log, and steps of add-ons that are off.
"""
import json, os, re, sys, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = json.load(open(os.path.join(HERE, 'library.json')))
TPL = open(os.path.join(HERE, 'template.html')).read()
ANS2ADDON = {'condo': 'condo', 'pre78': 'lead', 'cofo': 'cofo', 'sale': 'sale', 'repairs': 'repairs',
             'warranty': 'warranty', 'survey': 'survey'}


def addd(s, n):
    return (dt.date.fromisoformat(s) + dt.timedelta(days=n)).isoformat() if s else ''


def rel_of(r):
    return ['accepted', 'insp', r[1]] if r[0] == 'insp' else [r[0], r[1]]


def date_of(D, r):
    R = rel_of(r)
    base = D.get(R[0])
    n = (int(D.get('inspDays') or 7) if R[1] == 'insp' else R[1]) + (R[2] if len(R) > 2 else 0)
    return addd(base, n)


def fill(D, s):
    first = str(D.get('first', '')).replace(' and ', ' & ')
    return str(s or '').replace('{first}', first).replace('{title}', D.get('title') or 'the title company')


def addons_from(ans):
    A = {k2: True for k, k2 in ANS2ADDON.items() if ans.get(k) == 'yes'}
    if ans.get('pay') == 'fin': A['financing'] = True
    if ans.get('poss') == 'stay': A['occupancy'] = True
    if ans.get('poss') == 'early': A['early'] = True
    return A


def new_deal(spec):
    D = dict(spec)
    ans = D.setdefault('answers', {})
    D.setdefault('inspDays', 7)
    D['addons'] = addons_from(ans)
    pay = {'cash': 'Cash', 'fin': 'Financing', 'tbd': 'Cash or financing (still deciding)'}.get(ans.get('pay'), '')
    terms = [['Purchase price', '${:,.0f}'.format(D.get('price', 0))]]
    if pay: terms.append(['Financing', pay])
    if D.get('emd'): terms.append(['Earnest money', D['emd'] + ' held in escrow by Sine & Monaghan'])
    terms += [['Offer accepted', ''], ['Inspection period', ''], ['Closing', ''],
              ['Possession', 'At closing' if ans.get('poss', 'close') == 'close' else 'To be confirmed']]
    if D.get('title'): terms.append(['Title company', D['title']])
    if D.get('included'): terms.append(['Included', D['included']])
    D['terms'] = terms
    steps, rel = [], {}
    packs = [(None, LIB['core'])] + [(a['key'], a['steps']) for a in LIB['addons']]
    for key, lst in packs:
        for x in lst:
            s = {'id': x['id'], 't': fill(D, x['t']), 'who': fill(D, x['who']), 'what': fill(D, x['what']),
                 'd': date_of(D, x['rel'])}
            if x.get('agent'): s['agent'] = True
            if key: s['pack'] = key
            if x['id'] == 'accept': s['status'] = 'Done'
            steps.append(s); rel[x['id']] = rel_of(x['rel'])
    # client steps in date order, Frank's own steps after them
    D['steps'] = sorted([s for s in steps if not s.get('agent')], key=lambda s: (s['d'], s['id'] != 'accept')) + \
                 [s for s in steps if s.get('agent')]
    D['rel'] = rel
    D.setdefault('people', [])
    if not any(re.search('your agent', p.get('role', ''), re.I) for p in D['people']):
        D['people'].insert(0, {'role': 'Your agent', 'name': 'Frank Lucido', 'org': 'Sine & Monaghan',
                               'phone': '586-419-7607', 'email': 'frankjr@fjlucido.com'})
    D.setdefault('agentCell', '5864197607'); D.setdefault('agentEmail', 'frankjr@fjlucido.com')
    D.setdefault('emails', []); D.setdefault('phones', [])
    D.setdefault('state', {'steps': {}, 'inc': {}})
    return D


def client_copy(D, state):
    """Frank's data + his saved edits, with everything private taken out."""
    D = json.loads(json.dumps(D))
    for k, v in (state.get('data') or {}).items(): D[k] = v
    inc = state.get('inc') or {}
    on = D.get('addons') or {}
    D['steps'] = [s for s in D['steps'] if not s.get('agent') and inc.get(s['id']) is not False
                  and (not s.get('pack') or on.get(s['pack']))]
    keep = {s['id'] for s in D['steps']}
    D['people'] = [p for p in D.get('people', []) if not p.get('mine')]
    D['state'] = {'steps': {k: {kk: vv for kk, vv in v.items() if kk != 'note'}
                            for k, v in (state.get('steps') or {}).items() if k in keep}, 'inc': {}}
    for k in ('sellers', 'notes', 'sentlog'): D.pop(k, None)
    return D


def render(D, mode):
    data = json.dumps(D, ensure_ascii=True).replace('</', '<\\/')
    lib = json.dumps(LIB if mode == 'agent' else {}, ensure_ascii=True).replace('</', '<\\/')
    title = '%s · %s' % (D.get('short') or D.get('address'), 'What happens now' if mode == 'agent' else 'Your next steps')
    return TPL.replace('__TITLE__', title.replace('&', '&amp;').replace('<', '&lt;')) \
              .replace("const MODE='__MODE__';", "const MODE='%s';" % mode) \
              .replace('__LIB__', lib).replace('__DATA__', data)


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == 'new':
        open(a[2], 'w').write(render(new_deal(json.load(open(a[1]))), 'agent'))
    elif len(a) >= 3 and a[0] == 'page':
        D = json.load(open(a[1]))
        state = json.load(open(a[a.index('--state') + 1])) if '--state' in a else (D.get('state') or {})
        if '--client' in a: open(a[2], 'w').write(render(client_copy(D, state), 'client'))
        else: open(a[2], 'w').write(render(D, 'agent'))
    else:
        print(__doc__); sys.exit(1)
    print('wrote', a[2])
