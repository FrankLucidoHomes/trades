#!/usr/bin/env python3
"""Rebuild a client's pricing-opinion page from Frank's own copy plus the wording he typed over it.
usage: refresh_opinion.py SLUG AGENT_HTML STATE_JSON
SLUG: the page's folder on the site (must be in _tools/opinions.json). AGENT_HTML: Frank's live claude.ai page (full HTML).
STATE_JSON: the page's db doc opinion/state (its fields; {"ov": {...}}). Pass a file holding {} if there are no edits.
The client page = Frank's page with his edits applied, minus everything agent-only (class "agent"), the toolbar,
the share card, the "Agent copy" tag and all scripts. It never carries commission or net numbers."""
import json, os, re, subprocess, sys, tempfile
from bs4 import BeautifulSoup, NavigableString, Tag

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Must match the selector in the page's own script, in the same order.
SEL = ".sheet .head .k, .sheet .head h1, .sheet .head .t p, .sheet .body p, .sheet .body h2, .sheet .fact b, .sheet .fact span, .sheet .step b, .sheet .step span, .sheet .step strong, .sheet th, .sheet td, .sheet .body li"
OK = {"strong": "strong", "b": "strong", "em": "em", "i": "em"}
norm = lambda s: re.sub(r"\s+", " ", s or "").strip()

def clean(soup, html):
    """Keep only text, bold, italics and line breaks from what Frank typed."""
    src = BeautifulSoup("<div>" + (html or "") + "</div>", "html.parser").div
    out = soup.new_tag("div")
    def walk(n, into):
        for c in list(n.children):
            if isinstance(c, NavigableString): into.append(NavigableString(str(c)))
            elif isinstance(c, Tag):
                if c.name == "br": into.append(soup.new_tag("br"))
                elif c.name in OK:
                    e = soup.new_tag(OK[c.name]); walk(c, e); into.append(e)
                elif c.name in ("script", "style"): continue
                else:
                    if c.name in ("div", "p") and len(into.contents): into.append(soup.new_tag("br"))
                    walk(c, into)
    walk(src, out)
    return out

def build(agent_html, state):
    soup = BeautifulSoup(agent_html, "html.parser")
    ov = (state or {}).get("ov") or {}
    els = soup.select(SEL)
    applied, skipped = [], []
    for i, el in enumerate(els):
        o = ov.get("e%d" % i)
        if not isinstance(o, dict) or not o.get("h"): continue
        if norm(o.get("o")) != norm(el.get_text()):      # the page changed under this edit: do not guess
            skipped.append("e%d" % i); continue
        new = clean(soup, o["h"])
        el.clear()
        for c in list(new.contents): el.append(c)
        applied.append("e%d: %s" % (i, norm(el.get_text())[:90]))
    for x in soup.select(".agent, .tools, .share, .head .tag, script, #edHint, #hq-back, #hq-back + div"): x.decompose()
    for x in soup.select("[contenteditable]"): del x["contenteditable"]
    body = soup.body; body["class"] = ["client"]
    for st in soup.find_all("style"):
        if st.string: st.string = re.sub(r"/\*.*?\*/", "", st.string, flags=re.S)
    seen = norm(body.get_text()).lower()
    for w in ("commission", "transfer tax", "agent only", "agent copy", " nets", "break-even"):
        assert w not in seen, "agent-only wording left on the client page: " + w
    out = str(soup)
    return out, applied, skipped

def main(slug, agent, statef):
    cfg = json.load(open(os.path.join(R, "_tools", "opinions.json")))[slug]
    state = json.load(open(statef))
    if "ov" not in state and isinstance(state.get("data"), dict): state = state["data"]
    out, applied, skipped = build(open(agent).read(), state)
    tmp = tempfile.mkdtemp(); page = os.path.join(tmp, "page.html"); open(page, "w").write(out)
    empty = os.path.join(tmp, "assets"); os.makedirs(empty)
    subprocess.run([sys.executable, os.path.join(R, "_tools", "publish_page.py"), slug, page, empty, cfg["app"], cfg["title"], cfg["desc"]], check=True)
    print("ok", slug, "| edits applied:", len(applied), "| skipped (page changed):", skipped)
    for a in applied: print("  ", a)

if __name__ == "__main__": main(*sys.argv[1:4])
