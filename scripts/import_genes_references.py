#!/usr/bin/env python3
"""Import owner-labelled Genes.zip as partial phenotype references, never a test split."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile
from PIL import Image, ImageOps

FOLDERS = {
 '超级北极': [('arctic','homozygous')],
 '超级北极康达': [('arctic','homozygous'),('anaconda','heterozygous')],
 '超级北极超级康达': [('arctic','homozygous'),('anaconda','homozygous')],
 '白化超级北极': [('albino','expressed'),('arctic','homozygous')],
 '白化超级北极康达': [('albino','expressed'),('arctic','homozygous'),('anaconda','heterozygous')],
 '白化超级北极超级康达': [('albino','expressed'),('arctic','homozygous'),('anaconda','homozygous')],
 '白化': [('albino','expressed')],
 '白化康达': [('albino','expressed'),('anaconda','heterozygous')],
 '白化超级康达': [('albino','expressed'),('anaconda','homozygous')],
 '雪白': [('albino','expressed'),('axanthic','expressed')],
 '雪白康达': [('albino','expressed'),('axanthic','expressed'),('anaconda','heterozygous')],
 '雪白超级康达': [('albino','expressed'),('axanthic','expressed'),('anaconda','homozygous')],
}

def decoded_name(info):
 name=info.filename
 if not info.flag_bits & 0x800:
  try: name=name.encode('cp437').decode('utf-8')
  except (UnicodeEncodeError,UnicodeDecodeError): pass
 return name

def safe_name(info):
 name=decoded_name(info)
 path=PurePosixPath(name)
 mode=info.external_attr >> 16
 if path.is_absolute() or '..' in path.parts or '\\' in name or (path.parts and ':' in path.parts[0]) or stat.S_ISLNK(mode):
  raise ValueError(f'Unsafe ZIP entry: {name}')
 return path

def dhash(im):
 small=im.convert('L').resize((9,8))
 pixels=[small.getpixel((x,y)) for y in range(8) for x in range(9)]
 return sum((pixels[y*9+x]>pixels[y*9+x+1]) << (y*8+x) for y in range(8) for x in range(8))

def derivative(raw):
 with Image.open(BytesIO(raw)) as src:
  im=ImageOps.exif_transpose(src).convert('RGB')
  im.thumbnail((1024,1024))
  perceptual=dhash(im)
  out=BytesIO(); im.save(out,format='JPEG',quality=80,optimize=True)
  if len(out.getvalue())>220000:
   im.thumbnail((900,900)); out=BytesIO(); im.save(out,format='JPEG',quality=73,optimize=True)
  return out.getvalue(),perceptual,list(im.size)

def import_archive(archive,root):
 root=Path(root); archive=Path(archive)
 manifest_path=root/'data/demo_references.json'; manifest=json.loads(manifest_path.read_text())
 course=[r for r in manifest['images'] if not r['id'].startswith('genes-')]
 ontology=json.loads((root/'data/ontology.json').read_text()); traits={x['id']:x for x in ontology['traits']}
 pending=defaultdict(list); rejected=[]; counts=Counter(); metadata=0
 with zipfile.ZipFile(archive) as z:
  for info in z.infolist():
   path=safe_name(info)
   if info.is_dir(): continue
   if '__MACOSX' in path.parts or path.name.startswith('.'):
    metadata+=1; continue
   if len(path.parts)!=3 or path.parts[0]!='Genes' or path.parts[1] not in FOLDERS:
    rejected.append({'source':str(path),'reason':'unknown_folder_or_structure'}); continue
   folder=path.parts[1]; raw=z.read(info); counts[folder]+=1; digest=hashlib.sha256(raw).hexdigest()
   try: packed,perceptual,size=derivative(raw)
   except Exception as error:
    rejected.append({'source':str(path),'reason':'invalid_image','error_type':type(error).__name__}); continue
   components=sorted(FOLDERS[folder])
   pending[digest].append({'source':str(path),'folder':folder,'components':components,'packed':packed,'dhash':perceptual,'size':size})
 outdir=root/'data/demo_references/genes'; outdir.mkdir(parents=True,exist_ok=True)
 records=[]; conflicts=[]; duplicates=[]; phashes=[]
 for digest,items in sorted(pending.items()):
  signatures={tuple(i['components']) for i in items}
  sources=[{'archive_path':i['source'],'folder_label':i['folder']} for i in items]
  if len(signatures)>1:
   conflicts.append({'source_sha256':digest,'sources':sources,'reason':'exact_bytes_have_conflicting_folder_labels','status':'quarantine','not_published':True}); continue
  first=items[0]; ident='genes-'+digest[:16]; file=outdir/f'{ident}.jpg'; file.write_bytes(first['packed'])
  components=[{'trait_id':t,'state':s} for t,s in first['components']]
  alias=next((a for a in ontology['aliases'] if sorted((t['trait_id'],t['state']) for t in a['components'])==first['components']),None)
  def names(lang):
   if alias:return alias['name_'+lang]
   return ' + '.join(('Superconda' if t=='anaconda' else 'Super '+traits[t]['name_en']) if s=='homozygous' and lang=='en' else ('超级' if s=='homozygous' else '')+traits[t]['name_'+lang] for t,s in first['components'])
  records.append({'id':ident,'image':f'data/demo_references/genes/{ident}.jpg','traits':components,'name_en':names('en'),'name_zh':names('zh'),'review_status':'user_labeled','role':'phenotype_reference','labels_complete':False,'label_source':'user-provided ZIP folder label; not independent expert review','source_folder':first['folder'],'source_records':sources,'source_sha256':digest,'sha256':hashlib.sha256(first['packed']).hexdigest(),'image_rights':'owner_authorized_demo','attribution':'Owner-provided labelled Genes archive; authorized for project demo','modifications':'Orientation corrected, resized to at most 1024 px longest edge, compressed JPEG, embedded metadata removed.','dimensions':first['size'],'width':first['size'][0],'height':first['size'][1],'source_group':'genes','perceptual_hash_dhash':f'{first["dhash"]:016x}','individual_id':None,'independent_test_eligible':False})
  phashes.append((ident,first['dhash']))
  if len(items)>1:duplicates.append({'retained_id':ident,'source_sha256':digest,'source_count':len(items),'sources':sources})
 near=[]
 for i,(ident,h) in enumerate(phashes):
  for other,k in phashes[:i]:
   distance=(h^k).bit_count()
   if distance<=3: near.append({'ids':[other,ident],'dhash_distance':distance})
 manifest['images']=course+records; manifest['purpose']='Owner-confirmed course and owner-folder-labelled phenotype references for multimodal demo comparison; partial labels, not an independent evaluation set.'
 manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 summary={'schema_version':'1.0.0','archive_name':archive.name,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'source_archive_local_only':True,'folder_source_counts':dict(sorted(counts.items())),'source_image_count':sum(counts.values()),'packaged_genes_references':len(records),'retained_course_references':len(course),'total_demo_references':len(course)+len(records),'packaged_jpeg_bytes':sum((root/r['image']).stat().st_size for r in records),'metadata_entries_ignored':metadata,'exact_duplicate_groups':duplicates,'conflicting_exact_duplicates_quarantined':conflicts,'rejected_entries':rejected,'perceptually_similar_pairs':near,'similarity_rule':'64-bit dHash Hamming distance <=3; similarity flag only, not proof of duplicate or independent animal identity.','individual_identity_known':False,'independent_test_eligible':False,'labels_complete':False}
 (root/'data/genes_import_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 return summary

if __name__=='__main__':
 parser=argparse.ArgumentParser(); parser.add_argument('archive',type=Path); parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]); args=parser.parse_args()
 summary=import_archive(args.archive,args.root)
 print(json.dumps({k:summary[k] for k in ['source_image_count','packaged_genes_references','total_demo_references','packaged_jpeg_bytes']},indent=2))
