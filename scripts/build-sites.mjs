// Build the same interface and packaged reference library for Sites.
import { cp, mkdir, rm, stat } from 'node:fs/promises';
import { resolve } from 'node:path';
const root=resolve(new URL('..',import.meta.url).pathname);
const client=resolve(root,'dist/client');
await rm(resolve(root,'dist'),{recursive:true,force:true});
await mkdir(client,{recursive:true});
const assets=['index.html','styles.css','build','assets','docs','data/catalog.json','data/ontology.json','data/demo_references.json','data/demo_references','data/genes_import_summary.json','data/reference_gallery.json','data/incoming_summary.json','data/species_manifest.json','data/captive_species_manifest.json','data/species_only'];
for(const path of assets){
 const src=resolve(root,path); if(!(await stat(src).catch(()=>null))) continue;
 const dst=resolve(client,path);await mkdir(resolve(dst,'..'),{recursive:true});await cp(src,dst,{recursive:true});
}
await mkdir(resolve(root,'dist/server'),{recursive:true});
await cp(resolve(root,'scripts/sites-worker.mjs'),resolve(root,'dist/server/index.js'));
console.log('Sites output includes the interface, real references and cloud API adapter.');
