from pathlib import Path
from PIL import Image,ImageChops
from reportlab.pdfgen import canvas
r=Path(r'C:\Users\Abu\Documents\Python\CornerWork')
for i in range(1,10):
 a=Image.open(r/f'.demo-deck-build/previews/{i:02}.png').convert('RGB'); b=Image.open(r/f'.demo-deck-build/previews-v2/{i:02}.png').convert('RGB')
 assert ImageChops.difference(a,b).getbbox() is None, f'Slide {i} changed'
c=canvas.Canvas(str(r/'demo-materials/cornerwork-demo-flow-v2.pdf'),pagesize=(960,540))
for p in sorted((r/'.demo-deck-build/previews-v2').glob('*.png')):
 c.drawImage(str(p),0,0,width=960,height=540); c.showPage()
c.save()
p=r/'demo-materials/presenter-guide.md'; s=p.read_text(encoding='utf-8-sig');s=s.replace('`cornerwork-demo-flow.pptx`','`cornerwork-demo-flow-v2.pptx`').replace('All nine slides contain presenter notes.','All ten slides contain presenter notes. Slide 10 is an optional technical appendix: supporting both systems is feasible, but reliable syncing, approved access and ongoing maintenance are the main work.');p.write_text(s,encoding='utf-8')
print('First nine slides unchanged; ten-page PDF ready.')
