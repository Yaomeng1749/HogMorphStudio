# Course workbook audit

This audit reads the locally supplied course workbook without copying it or its images into the repository. The workbook and course photo archive remain private local source material; the counts below are a derived audit summary.

## Inventory

- The workbook has 101 named rows (`figure1`–`figure101`) and 17 historical annotation columns.
- Only `figure1`–`figure21` have corresponding image files. All 21 image rows contain at least one `1` annotation.
- `figure22`–`figure101` contain no labels. They are empty placeholders, not images, negative examples, or additional samples.
- The populated annotation values are `1`, `0`, and blank. A blank means unknown; it must not be converted to `0`.
- Historical positive counts across the 21 image rows range from 0 to 7 per column. Arctic has no positive examples. The low support is insufficient for a defensible held-out per-trait evaluation.
- The workbook records `White Wall` as positive once and negative 18 times, with two blanks. It is retained only as historical appearance annotation and is excluded from genetic trait labels, consistent with the corrected ontology.

## Historical label counts

Counts below are workbook annotations, not independently verified ground truth. `0` means an explicit workbook zero and `blank` means unknown.

| Historical column | Positive (`1`) | Explicit `0` | Blank | Project treatment |
| --- | ---: | ---: | ---: | --- |
| Anaconda / 康达 | 3 | 16 | 2 | Candidate trait; row claims unverified |
| Arctic / 北极 | 0 | 19 | 2 | Candidate trait; no positive support |
| Super Arctic / 超级北极 | 1 | 18 | 2 | Candidate homozygous state; row claims unverified |
| Superconda / 超级康达 | 1 | 18 | 2 | Candidate homozygous state; row claims unverified |
| Lemon Ghost / 柠檬鬼 | 1 | 18 | 2 | Historical alias; inheritance unresolved |
| Albino / 白化 | 7 | 12 | 2 | Candidate trait; row claims unverified |
| Toffee Belly / 太妃糖腹 | 3 | 17 | 1 | Candidate trait; row claims unverified |
| Lavender / 薰衣草 | 1 | 17 | 3 | Candidate trait; row claims unverified |
| Pink Pastel / 粉蜡笔 | 1 | 18 | 2 | Historical alias; inheritance unresolved |
| Axanthic / 缺黄 | 4 | 16 | 1 | Candidate trait; row claims unverified |
| Lucy / 露西 | 1 | 18 | 2 | Historical alias; inheritance unresolved |
| Sable / 紫貂 | 5 | 16 | 0 | Candidate trait; row claims unverified |
| Chocolate / 巧克力 | 1 | 18 | 2 | Historical alias; inheritance unresolved |
| Skull Face / 骷髅脸 | 1 | 18 | 2 | Historical alias; inheritance unresolved |
| Extreme Red / 极端红 | 2 | 17 | 2 | Line/polygenic candidate; row claims unverified |
| Diablo Eyes / 魔眼 | 2 | 17 | 2 | Historical alias; inheritance unresolved |
| White Wall / 白墙 | 1 | 18 | 2 | Appearance descriptor; not a genetic trait |

## What the audit does not establish

The workbook does not provide reviewed individual-snake IDs, source and rights records, a label codebook, breeder/pedigree evidence, or an independent test split. Therefore the 21 images are not eligible morph-training or evaluation examples. The annotation frequencies above describe the spreadsheet only; they are not model metrics, biological prevalence estimates, or proof of genotype. FPPA image-quality measurements use the 21 images as image inputs only and do not evaluate morph recognition.

The source workbook and images are not distributed. See the [data rights note](../ASSET_RIGHTS.md), [model baseline](model-architecture.md), and [incoming photo audit](incoming-audit.md) for separate data sources and current training gates.
