from pathlib import Path
from reportlab.pdfgen import canvas
import shutil
r=Path(r'C:\Users\Abu\Documents\Python\CornerWork')
out=r/'demo-materials/cornerwork-pitch-deck-combined.pdf'
c=canvas.Canvas(str(out),pagesize=(960,540))
for p in sorted((r/'.demo-deck-build/previews-combined').glob('*.png')):
 c.drawImage(str(p),0,0,width=960,height=540);c.showPage()
c.save()
a=r/'demo-materials/original-pitch-backup';a.mkdir(exist_ok=True)
for ext in ['pptx','pdf']:
 source=r/f'cornerwork-pitch-deck.{ext}'; backup=a/source.name
 if backup.exists(): raise RuntimeError('Backup exists; refusing to overwrite')
 shutil.copy2(source,backup)
 shutil.copy2(r/f'demo-materials/cornerwork-pitch-deck-combined.{ext}',source)
(r/'demo-materials/combined-deck-guide.md').write_text('''# Main pitch deck

The main presentation is now `../cornerwork-pitch-deck.pptx`, with its PDF beside it. This 18-slide edition integrates the original pitch story and the demo flow. Earlier standalone demo files are superseded for a full presentation.

## Flow

1. Cover
2–4. Problem, member value, and coaching gap
5. Four-step overview
6–9. Post-class ping, member question, coach queue, next-class brief
10. Technical details: supporting Gymdesk and Mindbody
11. Integration acceptance test
12. Working prototype versus live-pilot requirements
13. Proposed $50–100 gym subscription and optional $10 member add-on
14. Coach ownership, time and compensation
15. Consent and staff-access requirements
16. Founder background from the original supplied deck
17–18. Pilot and discussion

The original deck consisted of slide images, so the combined edition rebuilds its narrative as editable text with the same cream, charcoal and teal palette. The original files are preserved in `original-pitch-backup/`.

Reconciled the old revenue split with current pricing hypotheses; removed unsupported retention statistics, categorical competitor claims, fixed response-time promises, and the unapproved free-pilot/one-week-launch offer. Anonymous reporting stays deferred. The founder-photo placeholder was removed. No acquisition or established-moat claim has been added.

All slides include presenter notes. For live demo controls, use the existing presenter guide: its demo walkthrough now corresponds to slides 6–9, its integration guidance to 10–12, and its discovery questions to slide 18.
''',encoding='utf-8')
print('Main PPTX/PDF updated; original backed up; 18 slides.')
