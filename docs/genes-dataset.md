# Genes reference archive / 新增表型参考图

The project owner supplied `Genes.zip` with folder labels and authorized its use in the demo. The original archive stays local and untouched. The importer packages actual photo derivatives; it does not generate specimen images or train a classifier.

## Import result

- **868** decodable images across 12 folders, plus the existing 18 course references: **886** demo references.
- JPEG derivatives total **114,797,614 bytes** (109.48 MiB). Orientation is corrected, embedded metadata removed, and the longest edge capped at 1024 px; quality 80, with a lower-size fallback for large images.
- No exact-byte duplicates, conflicting exact duplicates, or corrupt image entries occurred in this archive.
- Six pairs meet the dHash similarity threshold. These are flagged for similarity only; this does not establish common or separate snake identity.
- Labels come from the owner's supplied folder labels, not independent expert review. All records have `labels_complete=false`, `individual_id=null`, and `independent_test_eligible=false`.

当前资料可以作为多模态辅助判断的实拍参考上下文。未标注性状仍是未知，不能当作阴性；相近照片与不同文件均不能证明不同蛇只，因此不能从这批参考图计算独立测试准确率。

## Folder interpretation

| Folder / 原标签 | Count | Visible trait states |
| --- | ---: | --- |
| 白化 | 66 | Albino expressed |
| 白化康达 | 71 | Albino expressed + Anaconda heterozygous |
| 白化超级康达 | 36 | Albino expressed + Anaconda homozygous |
| 超级北极 | 97 | Arctic homozygous |
| 超级北极康达 | 95 | Arctic homozygous + Anaconda heterozygous |
| 超级北极超级康达 | 90 | Arctic homozygous + Anaconda homozygous |
| 白化超级北极 | 80 | Albino expressed + Arctic homozygous |
| 白化超级北极康达 | 72 | Albino expressed + Arctic homozygous + Anaconda heterozygous |
| 白化超级北极超级康达 | 49 | Albino expressed + Arctic homozygous + Anaconda homozygous |
| 雪白 | 80 | Snow: Albino expressed + Axanthic expressed |
| 雪白康达 | 77 | Yeti: Albino expressed + Axanthic expressed + Anaconda heterozygous |
| 雪白超级康达 | 55 | Super Yeti: Albino expressed + Axanthic expressed + Anaconda homozygous |

States describe the labelled visible phenotype. They are not proof of genotype from a photo. Hidden carrier states are never inferred. Labels outside a folder's components remain unrecorded.

## Provenance and reproducibility

The [reference manifest](../data/demo_references.json) records original byte SHA-256, packaged JPEG SHA-256, source archive paths/folder labels, partial trait states, resolution, transformations and authorization. The [import summary](../data/genes_import_summary.json) records the archive hash, folder counts, rejected entries, exact-duplicate handling, and perceptual similarity pairs.

```bash
python scripts/import_genes_references.py /path/to/Genes.zip
python -m unittest discover -s tests/data -v
```

The importer decodes legacy ZIP filename encodings and refuses absolute paths, parent traversal, Windows-style path escapes, and symlink entries. macOS resource-fork metadata is skipped. Exact-byte repeats within the same label retain one derivative with every source recorded; exact-byte repeats across conflicting labels are quarantined in the summary and excluded from public references. The course references are preserved. No archive member is directly extracted onto the filesystem.

The code MIT license does not relicense these photographs. Authorization is for this project demo. The original ZIP is not part of the public repository.
