from pathlib import Path
import json
import win32com.client

root = Path(__file__).resolve().parents[1]
preview = root / '.ppt_build' / 'preview'
preview.mkdir(exist_ok=True)
path = root / 'deliverables' / 'Snake_RL_10min_editable.pptx'
app = win32com.client.DispatchEx('PowerPoint.Application')
p = app.Presentations.Open(str(path), -1, 0, 0)
issues = []
try:
    print('Reopened PPTX, slides:', p.Slides.Count, flush=True)
    for s in p.Slides:
        s.Export(str(preview / f'slide-{s.SlideIndex:02d}.png'), 'PNG', 1600, 900)
        for sh in s.Shapes:
            if sh.HasTextFrame and sh.TextFrame.HasText:
                t = sh.TextFrame.TextRange
                if t.BoundHeight > sh.Height + 3:
                    issues.append({'slide': s.SlideIndex, 'text': t.Text,
                                   'height': sh.Height, 'bound': t.BoundHeight})
        print('Rendered', s.SlideIndex, flush=True)
    p.SaveAs(str(root / 'deliverables' / 'Snake_RL_10min_preview.pdf'), 32)
    print('PDF saved', flush=True)
finally:
    p.Close()
(root / '.ppt_build' / 'render_issues.json').write_text(json.dumps(issues, ensure_ascii=False, indent=2), encoding='utf-8')
print('Text overflow candidates:', len(issues), flush=True)

# Contact sheets are QA artifacts only, never slide content.
from PIL import Image, ImageOps, ImageDraw
for start in (1, 7):
    sheet = Image.new('RGB', (1600, 3 * 485), '#dce6e0')
    draw = ImageDraw.Draw(sheet)
    for offset in range(6):
        n = start + offset
        im = Image.open(preview / f'slide-{n:02d}.png').convert('RGB')
        im.thumbnail((780, 439))
        x = 10 + (offset % 2) * 800
        y = 28 + (offset // 2) * 485
        sheet.paste(im, (x, y))
        draw.text((x, y - 20), str(n), fill='black')
    sheet.save(root / '.ppt_build' / f'contact-{start:02d}.png')
