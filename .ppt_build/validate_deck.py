from io import BytesIO
from pathlib import Path
import json
import re
import zipfile
import xml.etree.ElementTree as ET

from openpyxl import load_workbook
from PIL import Image, ImageStat

root = Path(__file__).resolve().parents[1]
path = root / 'deliverables' / 'Snake_RL_10min_editable.pptx'
ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart'}
specs = [(1, 'state_experiments/*/comparison.json', 'state_modes', ['v1', 'v2']),
         (2, 'reward_experiments/reward_v2_*/comparison.json', 'reward_modes', ['sparse', 'distance', 'distance_step']),
         (3, 'exploration_experiments/*/comparison.json', 'explorations', ['0.9998', '0.9999', '0.99995'])]
with zipfile.ZipFile(path) as z:
    slides = sorted([n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)],
                    key=lambda n: int(re.search(r'(\d+)\.xml', n).group(1)))
    assert len(slides) == 12
    assert len([n for n in z.namelist() if re.fullmatch(r'ppt/charts/chart\d+\.xml', n)]) == 3
    durations = []
    for i in range(1, 13):
        notes = ET.fromstring(z.read(f'ppt/notesSlides/notesSlide{i}.xml'))
        body = ''.join(t.text or '' for t in notes.findall('.//a:t', ns))
        assert '讲稿' in body and '汇报人' in body and '项目事实来源' in body
        durations.append(int(re.search(r'建议时长：(\d+) 秒', body).group(1)))
        im = Image.open(root / '.ppt_build' / 'preview' / f'slide-{i:02d}.png').convert('RGB')
        assert im.size == (1600, 900)
        assert min(ImageStat.Stat(im).stddev) > 10
    assert durations == [20, 40, 50, 55, 45, 50, 50, 45, 60, 45, 75, 35]
    for page in [5, 11]:
        assert ET.fromstring(z.read(f'ppt/slides/slide{page}.xml')).find('.//a:tbl', ns) is not None
    for num, pattern, group, labels in specs:
        src = next((root / 'results').glob(pattern))
        official = json.loads(src.read_text(encoding='utf-8'))[group]
        wb = load_workbook(BytesIO(z.read(f'ppt/embeddings/chart_data{num}.xlsx')), data_only=True)
        rows = list(wb.active.values)[1:]
        chart = ET.fromstring(z.read(f'ppt/charts/chart{num}.xml'))
        cache = [float(v.text) for v in chart.findall('.//c:ser/c:val/c:numRef/c:numCache/c:pt/c:v', ns)]
        errors = [float(v.text) for v in chart.findall('.//c:errBars/c:plus/c:numRef/c:numCache/c:pt/c:v', ns)]
        for index, key in enumerate(labels):
            expected_mean = round(official[key]['mean_score'], 2)
            expected_sd = round(official[key]['std_of_model_mean_scores'], 2)
            assert rows[index][1:] == (expected_mean, expected_sd)
            assert cache[index] == expected_mean and errors[index] == expected_sd
    page11 = ''.join(t.text or '' for t in ET.fromstring(z.read('ppt/slides/slide11.xml')).findall('.//a:t', ns))
    pairs = [('algorithm_experiments/e5_*/algorithm_comparison.json', 'algorithms'),
             ('algorithm_experiments/e5_*/algorithm_comparison.json', 'holdout_algorithms'),
             ('final_experiments/e6_*/algorithm_comparison.json', 'algorithms'),
             ('final_experiments/e6_*/algorithm_comparison.json', 'holdout_algorithms')]
    for pattern, group in pairs:
        data = json.loads(next((root / 'results').glob(pattern)).read_text(encoding='utf-8'))[group]
        for v in data.values():
            value = f"{v['mean_score']:.2f} ± {v['std_of_model_mean_scores']:.2f}"
            assert value in page11, value
assert json.loads((root / '.ppt_build' / 'render_issues.json').read_text(encoding='utf-8')) == []
result = {'slides': 12, 'native_charts': 3, 'embedded_workbooks': 3, 'native_tables': 2,
          'speaker_notes': 12, 'content_seconds': sum(durations), 'total_with_buffer_seconds': 600,
          'source_mean_sd_pairs_verified': 16, 'text_overflow_candidates': 0,
          'rendered_pages_checked': 12, 'render_application': 'WPS Presentation',
          'artifact_runtime': 'Unavailable; native Office COM and OOXML authoring used',
          'no_real_game_video': True}
(root / '.ppt_build' / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
