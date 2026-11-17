"""Lucido logo-style buttons: rounded house outline (like the logo) drawn as an SVG background, with the round LS mark in the peak."""
from urllib.parse import quote
PATH="M46 3 Q50 1 54 3 L95.5 25.5 Q97.5 26.8 97.5 29.5 L97.5 92.5 Q97.5 97.5 92.5 97.5 L7.5 97.5 Q2.5 97.5 2.5 92.5 L2.5 29.5 Q2.5 26.8 4.5 25.5 Z"
def house(fill,stroke,w=5):
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" preserveAspectRatio="none">'
         f'<path d="{PATH}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" stroke-linejoin="round" vector-effect="non-scaling-stroke"/></svg>')
    return 'url("data:image/svg+xml,'+quote(svg,safe=' =:/')+'")'
def bg(fill,stroke,mark=True,w=5,size=34,top=14):
    s=house(fill,stroke,w)+' 0 0/100% 100% no-repeat'
    return (f'url(img/ls-roundel.png) center {top}px/{size}px no-repeat,'+s) if mark else s
