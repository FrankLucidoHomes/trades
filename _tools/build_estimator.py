#!/usr/bin/env python3
"""Build the public estimator page (estimator/index.html) from the Claude artifact HTML.

Usage: python3 _tools/build_estimator.py <artifact.html> [repo_root]

The Claude artifact "Lucido Sales Buyer Cost Estimator Tool" stays the master copy.
This script swaps in a real web-page head (icons, link preview, home-screen name),
makes Call / Text / Email / Save-contact work, and makes the PDF download work
outside Claude. Every replacement is checked, so a layout change fails loudly
instead of shipping a half-converted page.
"""
import re, sys, pathlib

SITE = "https://franklucidohomes.github.io/trades/estimator/"
SMS = "sms:+15864197607?&body="
TEL = "tel:+15864197607"
MAIL = "mailto:frankjr@fjlucido.com"

HEAD = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="Frank Lucido's Buyer Cost Estimator: monthly payment, property taxes by city, closing costs and cash to close for any home in Metro Detroit.">
<meta name="theme-color" content="#0f2d5c">
<meta name="apple-mobile-web-app-title" content="Call Frank">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="icon" href="apple-touch-icon.png">
<link rel="manifest" href="manifest.json">
<meta property="og:title" content="Lucido Sales Buyer Cost Estimator">
<meta property="og:description" content="What will this home really cost? Monthly payment, taxes by city and cash to close, from Frank Lucido, REALTOR&reg;.">
<meta property="og:image" content="{SITE}img/og.jpg">
<meta property="og:url" content="{SITE}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<title>Lucido Sales Buyer Cost Estimator Tool</title>
<style>[hidden]{{display:none!important}}body{{margin:0}}</style>
</head>
<body>
"""

EXTRA_CSS = """
.reachbtns{flex:1 1 100%;display:flex;flex-wrap:wrap;gap:8px;order:1}
.contact .addbtn{order:2}
.reachbtns a{font:inherit;font-size:15px;font-weight:700;text-decoration:none;border-radius:999px;padding:10px 16px;display:inline-flex;align-items:center;gap:6px;border:2px solid #fff;color:#fff;background:transparent}
.reachbtns a.call{background:#2e9e62;border-color:#2e9e62}
.reachbtns a.save{background:#fff;color:#0f2d5c}
.contact a.big{color:var(--band-ink);text-decoration:none}
.sendbtns{display:flex;flex-wrap:wrap;gap:8px}
"""

def sub(s, old, new, count=1):
    n = s.count(old)
    if n != count:
        sys.exit(f"build_estimator: expected {count} of {old[:70]!r}, found {n}")
    return s.replace(old, new)

def build(src: str) -> str:
    s = src
    # 1. Real page head instead of the artifact wrapper
    s = re.sub(r"\A.*?<title>Lucido Sales Buyer Cost Estimator Tool</title>\n", lambda m: HEAD, s, count=1, flags=re.S)
    if not s.startswith("<!doctype html>\n<html lang"):
        sys.exit("build_estimator: head swap failed")
    s = sub(s, "</style>\n\n<div class=\"wrap\">", EXTRA_CSS + "</style>\n\n<div class=\"wrap\">")

    # 2. Phone + email become tap-to-call / tap-to-email, plus a row of reach-out buttons
    s = sub(s, '<div><span class="lbl">Call or text</span><span class="big">586-419-7607</span></div>',
            f'<div><span class="lbl">Call or text</span><a class="big" href="{TEL}">586-419-7607</a></div>')
    s = sub(s, '<div><span class="lbl">Email</span><span class="big mail">frankjr@fjlucido.com</span></div>',
            f'<div><span class="lbl">Email</span><a class="big mail" href="{MAIL}">frankjr@fjlucido.com</a></div>')
    s = sub(s, '<a class="btn" href="#reach" id="reachJump">Request Frank to reach out</a>\n      </div>\n',
            '<a class="btn" href="#reach" id="reachJump">Request Frank to reach out</a>\n      </div>\n'
            '      <div class="reachbtns">'
            f'<a class="call" href="{TEL}">Call Frank</a>'
            f'<a href="{SMS}Hi%20Frank%2C%20I%20was%20using%20your%20Buyer%20Cost%20Estimator%20and%20have%20a%20question%3A%20">Text Frank</a>'
            f'<a href="{MAIL}?subject=Buyer%20Cost%20Estimator&amp;body=Hi%20Frank%2C%0A%0A">Email Frank</a>'
            '<a class="save" href="frank-lucido.vcf" download="Frank Lucido.vcf">Save Frank to my contacts</a>'
            '</div>\n')

    # 3. Contact card: real "Save to contacts" instead of copy-and-paste
    s = sub(s, "On a computer or tablet: point your phone's camera at the code and tap <b>Add contact</b>. On your phone: tap Copy contact info and paste it into a new contact.",
            "On your phone: tap <b>Save Frank to my contacts</b>. On a computer: point your phone's camera at the code and tap <b>Add contact</b>.")
    s = sub(s, '<div class="copyrow"><button class="btn ghost" type="button" id="copyContact">Copy contact info</button>',
            '<div class="copyrow"><a class="btn" href="frank-lucido.vcf" download="Frank Lucido.vcf">Save Frank to my contacts</a><button class="btn ghost" type="button" id="copyContact">Copy contact info</button>')

    # 4. "Text or email it yourself" now opens Messages / Mail with the request filled in
    s = sub(s, '<summary>Prefer to text or email it yourself?</summary>',
            '<summary>Prefer to text or email it yourself?</summary>\n'
            '          <div class="sendbtns" style="margin-top:10px"><a class="btn" id="smsReq" href="#">Text it to Frank</a><a class="btn" id="mailReq" href="#">Email it to Frank</a></div>')

    # 5. PDF download outside Claude
    s = sub(s, '  const dl=await claude.use("downloads").catch(()=>null);\n  if(!dl){pdfStatus("Downloading isn\'t available in this view.",true);return;}',
            '  const dl=(window.claude&&window.claude.use)?await window.claude.use("downloads").catch(()=>null):null;\n'
            '  if(!dl){const a=document.createElement("a");a.href=URL.createObjectURL(lastPdf.blob);a.download=lastPdf.filename;document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},4000);'
            'pdfStatus(`<span><b>${esc(lastPdf.filename)}</b> is ready. If it opened in a new screen, tap Share to save it or send it to Frank.</span>`);return;}')
    s = sub(s, '    const mcp=await claude.use("mcp").catch(()=>null);',
            '    const mcp=(window.claude&&window.claude.use)?await window.claude.use("mcp").catch(()=>null):null;')

    # 6. Share link always points at the public site
    s, n = re.subn(r'const SHARE_URL="[^"]*";', f'const SHARE_URL="{SITE}";', s)
    if n != 1:
        sys.exit("build_estimator: SHARE_URL not found")

    # 7. Site-only script: text/email buttons, install prompt, offline
    site_js = """
/* ---------- Public-site extras ---------- */
(function(){
  const go=(id,fn)=>{const a=$(id);if(a)a.addEventListener("click",()=>{refreshReach();a.href=fn(requestText(true));});};
  go("smsReq",t=>"%(sms)s"+encodeURIComponent(t));
  go("mailReq",t=>"%(mail)s?subject="+encodeURIComponent("Please reach out - Buyer Cost Estimator")+"&body="+encodeURIComponent(t));
  let installEvt=null;
  window.addEventListener("beforeinstallprompt",e=>{e.preventDefault();installEvt=e;});
  $("homeBtn").addEventListener("click",async e=>{
    if(!installEvt) return;
    e.stopImmediatePropagation();
    try{installEvt.prompt();await installEvt.userChoice;}catch(_){}
    installEvt=null;
  },true);
  if("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(()=>{});
})();
""" % {"sms": SMS, "mail": MAIL}
    s = sub(s, "\nbuildCitySelect();buildDownChips();buildCostEditor();renderContactQR();render();\n",
            "\nbuildCitySelect();buildDownChips();buildCostEditor();renderContactQR();render();\n" + site_js)
    return s

if __name__ == "__main__":
    src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
    root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else pathlib.Path(__file__).resolve().parents[1])
    out = root / "estimator" / "index.html"
    out.write_text(build(src), encoding="utf-8")
    print("wrote", out)
