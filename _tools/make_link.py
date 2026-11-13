"""Make a clean, branded share link for one client page.
Usage: python3 _tools/make_link.py SLUG ARTIFACT_ID "Kicker" "Address" "Prepared for ..." [photo.jpg]
Writes SLUG/index.html (forwards to the claude.ai page) and SLUG/og.jpg (the card shown in a text message)."""
import sys, os, shutil, html, subprocess, json
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
slug,aid,kicker,addr,forwho=sys.argv[1:6]; photo=sys.argv[6] if len(sys.argv)>6 else ''
d=os.path.join(R,slug); os.makedirs(d,exist_ok=True)
if photo: shutil.copy(photo,os.path.join(d,'photo.jpg'))
E=html.escape; url='https://franklucidohomes.github.io/trades/'+slug+'/'
title=addr+' · '+kicker
open(os.path.join(d,'index.html'),'w').write(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>{E(title)} · Frank Lucido</title>
<meta name="description" content="{E(forwho)}, from Frank Lucido, REALTOR® · Sine &amp; Monaghan.">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(forwho)} · Frank Lucido, REALTOR®">
<meta property="og:image" content="{url}og.jpg">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:url" content="{url}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<link rel="apple-touch-icon" href="../next/apple-touch-icon.png"><link rel="icon" href="../next/apple-touch-icon.png">
<style>body{{margin:0;font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;background:#0f2d5c;color:#fff;min-height:100vh;display:grid;place-items:center}}
.c{{max-width:420px;padding:28px 22px;text-align:center}}img{{width:120px;height:120px;border-radius:26px;border:3px solid #fff;object-fit:cover}}
h1{{font-size:24px;line-height:1.2;margin:16px 0 4px}}p{{margin:6px 0;color:#c8d6ee}}
a.btn{{display:block;background:#fff;color:#0f2d5c;font-weight:700;font-size:18px;text-decoration:none;border-radius:12px;padding:15px 18px;margin:22px 0 14px}}</style></head>
<body><div class="c"><img src="../next/apple-touch-icon.png" alt="Frank Lucido"><p style="color:#9fc3f0;font-weight:600;margin-top:14px">{E(kicker)}</p><h1>{E(addr)}</h1><p>{E(forwho)}</p>
<a class="btn" href="https://claude.ai/artifact/{aid}">Open your page</a>
<p style="font-size:14px">Frank Lucido, REALTOR® · Sine &amp; Monaghan · <a style="color:#fff" href="tel:5864197607">586-419-7607</a></p></div>
<script>setTimeout(function(){{location.replace('https://claude.ai/artifact/{aid}')}},700)</script></body></html>''')
# card image
pic=('file://'+os.path.join(d,'photo.jpg')) if photo else ''
head='file://'+os.path.join(R,'img','frank-centered.jpg')
left=(f'<div class="ph" style="background-image:url({pic})"><div class="hd" style="background-image:url({head})"></div></div>' if photo
      else f'<div class="ph" style="background:url(file://{R}/next/og.jpg) -80px -105px/1200px 630px"></div>')
card=f'''<html><head><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet"><style>
body{{margin:0;width:1200px;height:630px;background:#0f2d5c;font-family:Poppins,sans-serif;color:#fff;display:flex;align-items:center;gap:56px;padding:0 70px;box-sizing:border-box}}
.ph{{width:440px;height:440px;background-size:cover;background-position:center;flex:0 0 auto;border-radius:22px;position:relative;border:4px solid #fff}}
.hd{{position:absolute;right:-26px;bottom:-26px;width:150px;height:150px;border-radius:50%;border:6px solid #0f2d5c;background-size:cover;background-position:center 20%}}
.k{{font-size:30px;font-weight:600;color:#9fc3f0;letter-spacing:.02em}}h1{{font-size:58px;line-height:1.08;margin:6px 0 0}}
.f{{font-size:32px;font-weight:600;margin-top:22px}}.n{{white-space:nowrap;font-size:26px;color:#c8d6ee;margin-top:26px}}
</style></head><body>{left}<div><div class="k">{E(kicker)}</div><h1>{E(addr)}</h1><div class="f">{E(forwho)}</div><div class="n">Frank Lucido, REALTOR® · Top 5% All-Star</div></div></body></html>'''
open('/tmp/_card.html','w').write(card)
subprocess.run(['node','-e',"const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1200,height:630}});await p.goto('file:///tmp/_card.html');await p.waitForTimeout(1500);await p.screenshot({path:process.argv[1],type:'jpeg',quality:88});await b.close()})()",os.path.join(d,'og.jpg')],check=True)
print(url)
