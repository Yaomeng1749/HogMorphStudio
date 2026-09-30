#!/usr/bin/env python3
"""Extract the user-supplied field-guide images as local visual references."""
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
DOCX = Path(__file__).resolve().parents[1] / 'source' / '猪鼻蛇基因分类.docx'
OUT = Path(__file__).resolve().parents[1] / 'data'
IMAGE_DIR = OUT / 'reference_images'
CAPTIONS = [
    'Arctic', 'Super Arctic', 'Anaconda — spot pattern', 'Anaconda — White Wall', 'Anaconda — watermelon pattern',
    'Super Arctic', 'Diablo eye detail', 'Head pattern combination', 'Superconda', 'Lemon Ghost Anaconda',
    'Albino', 'Extreme Red Albino', 'Toffee Belly', 'Lavender', 'Pink Pastel Albino', 'Axanthic',
    'Leucistic', 'Sable', 'Chocolate', 'Skullface', 'Snow (Albino + Axanthic)', 'Toxic (Toffee Belly + Axanthic)',
    'Sunburst (Albino + Sable)', 'Extreme Red Sunburst', 'Maitai (Toffee Belly + Sable)',
    'Storm Cloud (Axanthic + Sable)', 'Moonstone (Super Arctic + Lavender)',
    'Juvenile Lavender and juvenile Coral comparison', 'Adult Coral', 'Albino Super Arctic Anaconda',
    'Albino Super Arctic Superconda', 'Extreme Red Albino Superconda', 'Arctic Lavender',
    'Lavender Superconda', 'Super Arctic Leucistic', 'Super Arctic Sunburst',
    'Extreme Red Albino Chocolate', 'Super Arctic Anaconda'
]
CAPTIONS_ZH = [
    '北极', '超级北极', '康达波点状纹路', '康达侧腹白墙', '西瓜纹',
    '超级北极', '魔眼细节', '头部勾玉状纹路', '超级康达', '柠檬鬼康达',
    '白化', '极端红白化', '太妃糖腹', '薰衣草', '粉蜡笔白化', '缺黄',
    '露西', '紫貂', '巧克力', '骷髅脸', '雪白（白化 + 缺黄）', '毒药（太妃 + 缺黄）',
    '太阳爆炸（白化 + 紫貂）', '极端红太阳爆炸', '埋汰（太妃 + 紫貂）',
    '暴风云（缺黄 + 紫貂）', '月光石（超级北极 + 薰衣草）',
    '幼年薰衣草与幼年珊瑚对比', '成年珊瑚', '白化超级北极康达',
    '白化超级北极超级康达', '极端红白化超级康达', '北极薰衣草',
    '薰衣草超级康达', '超级北极露西', '超级北极太阳爆炸',
    '极端红白化巧克力', '超级北极康达'
]
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main', 'a': 'http://schemas.openxmlformats.org/drawingml/2006/main', 'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
IMAGE_DIR.mkdir(parents=True, exist_ok=True)
with ZipFile(DOCX) as zf:
    rel_root = ET.fromstring(zf.read('word/_rels/document.xml.rels'))
    rels = {x.attrib['Id']: x.attrib['Target'] for x in rel_root}
    root = ET.fromstring(zf.read('word/document.xml'))
    occurrences = []
    for blip in root.findall('.//a:blip', NS):
        rid = blip.attrib[f"{{{NS['r']}}}embed"]
        occurrences.append(rels[rid])
    if len(occurrences) != len(CAPTIONS) or len(CAPTIONS_ZH) != len(CAPTIONS):
        raise SystemExit(f'Expected {len(CAPTIONS)} figure image occurrences; found {len(occurrences)}')
    records = []
    seen_targets = {}
    for index, (target, caption, caption_zh) in enumerate(zip(occurrences, CAPTIONS, CAPTIONS_ZH), start=1):
        suffix = Path(target).suffix.lower() or '.jpg'
        filename = f'reference-{index:02d}{suffix}'
        (IMAGE_DIR / filename).write_bytes(zf.read('word/' + target))
        record = {
            'id': f'ref-{index:02d}', 'caption': caption, 'caption_zh': caption_zh, 'file': f'reference_images/{filename}',
            'source_docx': '猪鼻蛇基因分类.docx', 'source_asset': Path(target).name,
            'image_rights': 'unknown', 'genotype_evidence': 'descriptive reference only',
            'training_eligible': False
        }
        if target in seen_targets:
            record['duplicate_media_of'] = f"ref-{seen_targets[target]:02d}"
            record['duplicate_media_note'] = f"The same embedded DOCX asset {Path(target).name} appears under more than one figure context; individual identity is unverified."
        else:
            seen_targets[target] = index
        records.append(record)
commons_file = IMAGE_DIR / 'commons-western-hognose-anaconda-cc0.jpg'
if not commons_file.is_file():
    raise SystemExit(f'Missing previously reviewed CC0 derivative: {commons_file}')
records.append({
    'id': 'open-cc0-anaconda-001',
    'caption': 'Anaconda morph · store label, unverified',
    'caption_zh': 'Anaconda 形态 · 店铺标签，未核实',
    'file': 'reference_images/commons-western-hognose-anaconda-cc0.jpg',
    'record_kind': 'open_license_candidate',
    'source_title': 'Western hognose at a pet store.jpg',
    'source_url': 'https://commons.wikimedia.org/wiki/File:Western_hognose_at_a_pet_store.jpg',
    'source_asset_url': 'https://upload.wikimedia.org/wikipedia/commons/2/22/Western_hognose_at_a_pet_store.jpg',
    'source_asset': 'Western hognose at a pet store.jpg',
    'source_author': 'ArtemisiaGentileschiFan',
    'attribution': 'ArtemisiaGentileschiFan (voluntary credit)',
    'image_rights': 'CC0-1.0',
    'license_url': 'https://creativecommons.org/publicdomain/zero/1.0/',
    'source_claim': 'Uploader reports that the pet-store label called this snake an Anaconda morph.',
    'source_claim_zh': '上传者说明：宠物店标签称此蛇为 Anaconda 形态。',
    'label_status': 'reported_source_claim_unverified',
    'canonical_trait_suggestion': {'trait_id': 'anaconda', 'state': 'zygosity_unspecified'},
    'reported_individual_name': 'Miss Piggy',
    'individual_id': None,
    'source_sha256': '020b65cb7b916c1cc233b12908b2abd6cad70f60791107f06271be8ea369f157',
    'local_sha256': hashlib.sha256(commons_file.read_bytes()).hexdigest(),
    'metadata_stripped': True,
    'genotype_evidence': 'store_label_report_only',
    'training_eligible': False,
    'rights_scopes': {'training': True, 'evaluation': True, 'hackathon_demo': True, 'public_web': True}
})
(OUT / 'reference_gallery.json').write_text(json.dumps({
    'source': '猪鼻蛇基因分类.docx',
    'note': 'The 38 DOCX image occurrences are local educational references; rights and individual identities are unverified. An additional CC0 Commons photo is included as one provisional source-claim candidate; its reported Anaconda label is not expert or breeder verified and it is not training data.',
    'images': records
}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Extracted {len(occurrences)} DOCX occurrences plus one CC0 source-claim candidate to {IMAGE_DIR}')
