from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

root = Path(__file__).resolve().parents[1]
path = root / 'deliverables' / 'Snake_RL_10min_editable.pptx'
with zipfile.ZipFile(path) as z:
    files = {n: z.read(n) for n in z.namelist()}
ct = 'http://schemas.openxmlformats.org/package/2006/content-types'
ET.register_namespace('', ct)
files['[Content_Types].xml'] = ET.tostring(ET.fromstring(files['[Content_Types].xml']), encoding='utf-8', xml_declaration=True)
ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'}
for prefix, uri in ns.items():
    ET.register_namespace(prefix, uri)
tree = ET.fromstring(files['ppt/slides/slide9.xml'])
updated = 0
for shape in tree.findall('.//p:sp', ns):
    combined = ''.join(t.text or '' for t in shape.findall('.//a:t', ns))
    if combined.startswith('Score：22.19'):
        para = shape.find('p:txBody/a:p', ns)
        for child in list(para):
            if child.tag != '{' + ns['a'] + '}pPr':
                para.remove(child)
        run = ET.SubElement(para, '{' + ns['a'] + '}r')
        rp = ET.SubElement(run, '{' + ns['a'] + '}rPr', {'lang': 'zh-CN', 'sz': '1600'})
        fill = ET.SubElement(rp, '{' + ns['a'] + '}solidFill')
        ET.SubElement(fill, '{' + ns['a'] + '}srgbClr', {'val': '61716A'})
        for script in ['latin', 'ea', 'cs']:
            ET.SubElement(rp, '{' + ns['a'] + '}' + script, {'typeface': 'Microsoft YaHei'})
        ET.SubElement(run, '{' + ns['a'] + '}t').text = '误差棒：跨训练种子总体 SD（ddof=0）；三组 SD：0.65 / 0.15 / 0.27'
        updated += 1
assert updated == 1, updated
files['ppt/slides/slide9.xml'] = ET.tostring(tree, encoding='utf-8', xml_declaration=True)
candidate = root / '.ppt_build' / 'reviewed.pptx'
with zipfile.ZipFile(candidate, 'w', zipfile.ZIP_DEFLATED) as z:
    for name, data in files.items():
        z.writestr(name, data)
path.write_bytes(candidate.read_bytes())
print('Normalized content types and clarified slide 9 SD caption.')
