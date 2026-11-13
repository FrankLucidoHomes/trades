"""Put a client page on Frank's site as a home-screen app.
Usage: python3 _tools/publish_page.py SLUG PAGE.html ASSET_DIR "Home-screen name" "Card title" "Card description" [icon_photo.jpg]
- copies the page to SLUG/index.html and its img/, photos/, plans/ folders,
- adds the home-screen app bits (manifest, icon) and the text-message card tags (SLUG/og.jpg from make_link.py).
No service worker: the page always loads the latest copy, so it updates as Frank updates."""
import sys, os, shutil, json, html, re
from PIL import Image, ImageOps
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
slug,page,assets,appname,title,desc=sys.argv[1:7]; iconsrc=sys.argv[7] if len(sys.argv)>7 else os.path.join(R,'img','frank-centered.jpg')
d=os.path.join(R,slug); os.makedirs(d,exist_ok=True)
for sub in ('img','photos','plans'):
    s=os.path.join(assets,sub)
    if os.path.isdir(s): shutil.copytree(s,os.path.join(d,sub),dirs_exist_ok=True)
for sz,name in ((180,'apple-touch-icon.png'),(192,'icon-192.png'),(512,'icon-512.png')):
    im=ImageOps.fit(Image.open(iconsrc).convert('RGB'),(sz,sz),centering=(0.5,0.35)); im.save(os.path.join(d,name))
url='https://franklucidohomes.github.io/trades/'+slug+'/'
json.dump({"name":appname,"short_name":appname,"start_url":"./","scope":"./","display":"standalone","background_color":"#ffffff","theme_color":"#0d2a5e",
  "icons":[{"src":"icon-192.png","sizes":"192x192","type":"image/png"},{"src":"icon-512.png","sizes":"512x512","type":"image/png"}]},open(os.path.join(d,'manifest.json'),'w'))
E=html.escape
head=f'''<link rel="manifest" href="manifest.json"><link rel="apple-touch-icon" href="apple-touch-icon.png"><link rel="icon" href="icon-192.png">
<meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="{E(appname)}"><meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"><meta name="theme-color" content="#0d2a5e"><meta name="robots" content="noindex">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:image" content="{url}og.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:url" content="{url}"><meta property="og:type" content="website"><meta name="twitter:card" content="summary_large_image">'''
h=open(page).read()
if '<!doctype' not in h[:200].lower():
    h='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'+head+'</head><body>'+h+'</body></html>'
else:
    h=re.sub(r'(<meta charset=[^>]*>)',lambda m:m.group(1)+head,h,count=1)
h=h.replace('<meta name="claude','<meta name="x-claude')
open(os.path.join(d,'index.html'),'w').write(h)
print(url)
