#!/usr/bin/env python3
"""Rebuild a seller's listing page from Frank's agent page + his saved edits.
usage: refresh_listing.py AGENT_HTML CLIENT_HTML STATE_JSON OUT_HTML
AGENT_HTML / CLIENT_HTML: the live claude.ai pages (full HTML). STATE_JSON: the agent page's db doc report/state (just its fields).
The new seller page = the agent page's code in client mode + the agent's data with Frank's edits applied and
everything he marked "Do not send" removed. Never includes his notes, take, price opinion or agent-only items."""
import json, re, sys
DRE = r'(<script id="data" type="application/json">)(.*?)(</script>)'
DATA_KEYS = ['stats','traffic','links','media','showNote','questions','qTitle','qLead','photos','plans','planSrc','showings','market','estimates']
def data(h): return json.loads(re.search(DRE, h, re.S).group(2).replace('<\\/', '</'))
def defaults(D):
    o = {s["id"]: s.get("inc", False) for s in D.get("stats", [])}
    o.update({"links": True, "media": True, "plans": True, "st-showings": True, "st-traffic": True, "showings": True, "fb-init": True})
    for sec in D.get("sections", []):
        if sec.get("kind") == "table": o[sec["id"]] = sec.get("inc", False)
        else:
            for i in sec.get("items", []): o[i["id"]] = i.get("inc", False)
    o["price"] = (D.get("price") or {}).get("inc", False)
    return o
def build(D, state, old_client):
    D = json.loads(json.dumps(D))
    for k, v in (state.get("data") or {}).items():
        if k in DATA_KEYS: D[k] = v
    if isinstance(state.get("shows"), list): D["showings"] = state["shows"]
    inc = defaults(D); inc.update(state.get("inc") or {})
    if not inc.get("show-agents"):
        D["showings"] = [dict(x, who="") for x in D.get("showings", [])]
    for k in ("initfb",):
        if isinstance(state.get(k), str): D[k] = state[k]
    if isinstance(state.get("sentlog"), list): D["sentlog"] = state["sentlog"]
    # website value estimates: only if Frank marked Send; never his private note
    if isinstance(D.get("estimates"), dict) and inc.get("estimates"):
        E = dict(D["estimates"]); E.pop("note", None); D["estimates"] = E
    else:
        D.pop("estimates", None)
    # market groups: only the ones he marked Send; never his private note
    if isinstance(D.get("market"), dict):
        M = dict(D["market"]); M.pop("note", None)
        M["tiers"] = [t for t in M.get("tiers", []) if inc.get("mk-" + str(t.get("id")))]
        if M["tiers"]: D["market"] = M
        else: D.pop("market", None)
    # Frank's dated comments: only the ones he marked Send
    D["comments"] = [c for c in (state.get("comments") or []) if inc.get("cm-" + str(c.get("id")))]
    if isinstance(state.get("contract"), dict): D["contract"] = state["contract"]
    if isinstance(state.get("pchanges"), list) and D.get("traffic"): D["traffic"]["changes"] = state["pchanges"]
    if isinstance(state.get("rec"), dict) and (state["rec"].get("text") or state["rec"].get("moved")): D["rec"] = state["rec"]
    for s in D.get("sections", []):
        for i in s.get("items", []):
            if i["id"] in (state.get("done") or {}): i["done"] = bool(state["done"][i["id"]])
            if (state.get("text") or {}).get(i["id"]): i["text"] = state["text"][i["id"]]
    # wording Frank typed over headings, numbers and table cells (keys start with "x:")
    D["textOv"] = {k: v for k, v in (state.get("text") or {}).items() if str(k).startswith("x:") and v}
    D["include"] = inc
    if isinstance(state.get("layout"), dict): D["layout"] = state["layout"]   # section order / width / hidden, set on his copy
    for s in D.get("sections", []):
        if s.get("kind") == "table": s.pop("note", None)
        else:
            for i in s.get("items", []): i["note"] = ""
    if D.get("media"):
        D.pop("showNote", None)
        D["media"] = {"by": D["media"].get("by"), "items": [x for x in D["media"].get("items", []) if not x.get("agentOnly")]}
    D["stats"] = [s for s in D.get("stats", []) if inc.get(s["id"])]
    D["sections"] = [s for s in D.get("sections", []) if s.get("kind") != "table" or inc.get(s["id"])]
    for s in D["sections"]:
        if s.get("kind") != "table": s["items"] = [i for i in s.get("items", []) if inc.get(i["id"])]
    D["price"] = {"id": "price", "inc": False, "title": "", "lead": "", "why": [], "steps": [], "comps": []}
    D["sources"] = ""
    for k in ("take", "notes"): D.pop(k, None)
    for k, v in old_client.items():          # keep seller-page-only keys (its own link etc.)
        if k not in D: D[k] = v
    return D
def main(a, c, s, out):
    A = open(a).read(); C = open(c).read(); S = json.load(open(s))
    S = S.get("data", S) if "inc" not in S and isinstance(S.get("data"), dict) and "inc" in S["data"] else S
    D = build(data(A), S, data(C))
    h = A
    h = h.replace('const MODE="agent"', 'const MODE="client"', 1)
    assert 'const MODE="client"' in h, "mode marker not found"
    h = re.sub(r'<a id="hq-back".*?</a><div aria-hidden="true" style="height:64px"></div>', '', h, flags=re.S)
    h = re.sub(r'<title>.*?</title>', lambda _: re.search(r'<title>.*?</title>', C).group(0), h, count=1)
    js = json.dumps(D, ensure_ascii=False).replace("</", "<\\/")
    m = re.search(DRE, h, re.S); h = h[:m.start(2)] + js + h[m.end(2):]
    bad = [w for w in ('"take"',) if w in js]
    assert not bad, bad
    open(out, "w").write(h); print("ok", out, len(h))
if __name__ == "__main__": main(*sys.argv[1:5])
