#!/usr/bin/env python3
"""Export the first-party course workbook into a transparent demo catalog."""
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import json

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / '猪鼻蛇大作业'
WORKBOOK = SOURCE / '基因.xlsx'
IMAGES = SOURCE / 'image_data'
OUTPUT = Path(__file__).resolve().parents[1] / 'data' / 'catalog.json'
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main', 'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
LABELS_EN = ['Anaconda', 'Arctic', 'Super Arctic', 'Superconda', 'Lemon Ghost', 'Albino', 'Toffee Belly', 'Lavender', 'Pink Pastel Albino', 'Axanthic', 'Lucy', 'Sable', 'Chocolate', 'Skull Face', 'Extreme Red', 'Diablo eyes', 'White Wall']

with ZipFile(WORKBOOK) as zf:
    shared = []
    if 'xl/sharedStrings.xml' in zf.namelist():
        root = ET.fromstring(zf.read('xl/sharedStrings.xml'))
        shared = [''.join(x.itertext()) for x in root.findall('.//m:si', NS)]
    wb = ET.fromstring(zf.read('xl/workbook.xml'))
    rel_root = ET.fromstring(zf.read('xl/_rels/workbook.xml.rels'))
    rels = {item.attrib['Id']: item.attrib['Target'] for item in rel_root}
    sheet = wb.find('.//m:sheet', NS)
    target = rels[sheet.attrib[f"{{{NS['r']}}}id"]].lstrip('/')
    target = target if target.startswith('xl/') else 'xl/' + target
    xml = ET.fromstring(zf.read(target))
    rows = []
    for row in xml.findall('.//m:sheetData/m:row', NS):
        values = {}
        for cell in row.findall('m:c', NS):
            ref = cell.attrib['r']
            col = ''.join(c for c in ref if c.isalpha())
            v = cell.find('m:v', NS)
            value = v.text if v is not None else None
            if value is not None and cell.attrib.get('t') == 's':
                value = shared[int(value)]
            values[col] = value
        rows.append(values)

header = rows[0]
label_columns = [chr(x) for x in range(ord('B'), ord('S'))]
labels = [{'id': col.lower(), 'name_zh': header.get(col), 'name_en': LABELS_EN[i]} for i, col in enumerate(label_columns)]
images = []
for row in rows[1:]:
    filename = row.get('A')
    if not filename:
        continue
    image_name = f'{filename}.png'
    image_path = IMAGES / image_name
    label_state = {}
    for col, label in zip(label_columns, labels):
        raw = row.get(col)
        label_state[label['id']] = int(raw) if raw in ('0', '1') else None
    images.append({
        'id': filename,
        'file': image_name,
        'image': f'../猪鼻蛇大作业/image_data/{image_name}',
        'available': image_path.is_file(),
        'labels': label_state,
        'individual_id': None,
        'source_url': None,
        'image_rights': 'unknown',
        'genotype_evidence': 'unavailable',
        'review_status': 'unverified'
    })

existing = [item for item in images if item['available']]
for label in labels:
    label['positive_examples'] = sum(item['labels'][label['id']] == 1 for item in existing)
    label['unknown_examples'] = sum(item['labels'][label['id']] is None for item in existing)

document = {
    'title': 'HogMorph Studio',
    'source_workbook': '猪鼻蛇大作业/基因.xlsx',
    'source_note': 'Labels are copied from the historical course workbook. They are not independently verified genotype ground truth.',
    'label_semantics': '0 = recorded negative in workbook; 1 = recorded positive in workbook; null = blank cell / unknown.',
    'images': images,
    'labels': labels
}
OUTPUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Wrote {OUTPUT}: {len(images)} workbook records, {len(existing)} matching images, {len(labels)} label columns.')
print('Positive examples per label:', ', '.join(f"{x['name_en']}={x['positive_examples']}" for x in labels))
