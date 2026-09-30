import importlib.util
import io
import json
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile
from PIL import Image

spec=importlib.util.spec_from_file_location('genes_import',Path(__file__).resolve().parents[2]/'scripts/import_genes_references.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
ROOT=Path(__file__).resolve().parents[2]

class ImportTests(unittest.TestCase):
 def image(self,color='red'):
  buf=io.BytesIO(); Image.new('RGB',(1200,800),color).save(buf,'PNG'); return buf.getvalue()
 def root(self,directory):
  root=Path(directory)/'root'; (root/'data').mkdir(parents=True)
  (root/'data/ontology.json').write_text((ROOT/'data/ontology.json').read_text())
  (root/'data/demo_references.json').write_text(json.dumps({'images':[{'id':'figure06'}]})); return root
 def test_safe_paths_and_symlink(self):
  for filename in ['../outside.png','/outside.png','C:/outside.png','Genes/../outside.png','Genes\\outside.png']:
   with self.assertRaises(ValueError): module.safe_name(zipfile.ZipInfo(filename))
  info=zipfile.ZipInfo('Genes/白化/image.png'); info.external_attr=(stat.S_IFLNK|0o777)<<16
  with self.assertRaises(ValueError):module.safe_name(info)
 def test_legacy_utf8_name(self):
  info=zipfile.ZipInfo('Genes/白化/a.png'.encode('utf-8').decode('cp437'))
  self.assertEqual(str(module.safe_name(info)),'Genes/白化/a.png')
 def test_states(self):
  self.assertEqual(dict(module.FOLDERS['雪白超级康达']),{'albino':'expressed','axanthic':'expressed','anaconda':'homozygous'})
  self.assertEqual(dict(module.FOLDERS['超级北极康达']),{'arctic':'homozygous','anaconda':'heterozygous'})
 def test_conflicts_and_dedup(self):
  with tempfile.TemporaryDirectory() as d:
   root=self.root(d); archive=Path(d)/'Genes.zip'; raw=self.image()
   with zipfile.ZipFile(archive,'w') as z:
    z.writestr('Genes/白化/a.png',raw);z.writestr('Genes/雪白/b.png',raw)
    z.writestr('Genes/白化/c.png',self.image('blue'));z.writestr('Genes/白化/d.png',self.image('blue'))
    z.writestr('Genes/白化/corrupt.png',b'bad');z.writestr('Genes/.DS_Store',b'x')
   summary=module.import_archive(archive,root)
   self.assertEqual(summary['packaged_genes_references'],1)
   self.assertEqual(len(summary['conflicting_exact_duplicates_quarantined']),1)
   self.assertEqual(len(summary['exact_duplicate_groups']),1)
   self.assertEqual(len(summary['rejected_entries']),1)
   row=json.loads((root/'data/demo_references.json').read_text())['images'][1]
   self.assertFalse(row['labels_complete']);self.assertIsNone(row['individual_id']);self.assertEqual(len(row['source_records']),2)
   with Image.open(root/row['image']) as im:
    self.assertLessEqual(max(im.size),1024);self.assertFalse(im.getexif())

if __name__=='__main__': unittest.main()
