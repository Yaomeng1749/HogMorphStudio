// Build only tracked public interface assets; private files and symlinks are excluded.
import { cp, mkdir, rm, lstat } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { resolve, dirname, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const client=resolve(root,'dist/client');
await rm(resolve(root,'dist'),{recursive:true,force:true});
await mkdir(client,{recursive:true});
const exact=new Set(['index.html','styles.css','data/catalog.json','data/ontology.json','data/demo_references.json','data/genes_import_summary.json','data/reference_gallery.json','data/incoming_summary.json','data/species_manifest.json','data/captive_species_manifest.json']);
const prefixes=['build/','assets/','docs/','data/demo_references/','data/species_only/'];
const extensions=new Set(['.js','.css','.md','.png','.jpg','.jpeg','.webp','.svg']);
const files=execFileSync('git',['ls-files','-z'],{cwd:root,encoding:'utf8'}).split('\0').filter(Boolean);
for(const path of files){
 if(path.split('/').some(part=>part.startsWith('.'))) continue;
 if(!exact.has(path) && !(prefixes.some(prefix=>path.startsWith(prefix)) && extensions.has(extname(path).toLowerCase()))) continue;
 for(let current=root, i=0, parts=path.split('/'); i<parts.length; i++){
  current=resolve(current,parts[i]);if((await lstat(current)).isSymbolicLink()) throw new Error('Public assets must not use symbolic links: '+path);
 }
 const src=resolve(root,path), info=await lstat(src);
 if(!info.isFile() || info.isSymbolicLink()) throw new Error('Public assets must be regular files: '+path);
 const dst=resolve(client,path);await mkdir(dirname(dst),{recursive:true});await cp(src,dst);
}
await mkdir(resolve(root,'dist/server'),{recursive:true});
await cp(resolve(root,'scripts/sites-worker.mjs'),resolve(root,'dist/server/index.js'));
console.log('Sites output includes the interface, real references and cloud API adapter.');
