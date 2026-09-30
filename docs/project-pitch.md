# Hackathon positioning

## 中文

**HogMorph Studio：为小样本动物形态研究建立可信的数据入口。** 项目把 2024 年 MATLAB 课程原型迁移为 Python 3/PyTorch 图像研究流程，并将 MATLAB GUI 重做为 TypeScript 双语浏览器应用。当前 demo 可在本地比较照片与历史档案、浏览形态词表、记录来源与复核证据；照片比较仍是 TypeScript 编写的颜色/布局相似度基线，不是训练好的基因分类器。Python 侧已实现旧 CNN 结构复现、FPPA 降噪实验和带数据门槛的 MobileNetV3-Small 多标签训练/评估流程，但因没有授权且按个体核实的形态记录，分类训练尚未运行。项目不声称能从照片确定基因型；下一步需要先建立有繁育证据、授权清楚且按蛇只隔离的测试数据。

## English

**HogMorph Studio: a provenance-first workbench for small-data phenotype research.** The 2024 MATLAB course pipeline has been ported to Python 3/PyTorch, and its GUI has been rebuilt as a bilingual TypeScript browser application. The local demo compares uploaded photos with the historical archive, presents the morph ontology, and supports evidence-aware curation. Photo comparison is a TypeScript color/layout similarity baseline, not a trained gene classifier. The Python side implements the legacy CNN shape, an FPPA denoising experiment, and a gated MobileNetV3-Small multi-label training/evaluation workflow; supervised training has not run because no rights-cleared, specimen-verified morph records are available. The project does not claim genotype identification from photos. Any future classifier must be evaluated on licensed, breeder- or genetics-supported records split by individual snake.

## Current technology / 当前技术栈

| Layer | Technology | Implemented role |
| --- | --- | --- |
| Browser application | TypeScript 7, HTML5, CSS3 | Bilingual collection, local photo comparison, ontology/reference browsing, and annotation export. TypeScript compiles into static browser modules. Uploaded demo photos stay in browser memory. |
| Image research and model pipeline | Python 3, PyTorch, NumPy, SciPy, Pillow | Executable legacy-CNN shape, FPPA/Butterworth image-processing methods, gated MobileNetV3-Small multi-label training, and identity-grouped evaluation. |
| Current photo-analysis result | TypeScript visual similarity | Color histogram and coarse spatial-grid overlap against available archive photos; explicitly not softmax, calibrated confidence, or genotype probability. |

The frontend stays framework-free because this static, local-first demo does not need a separate server or browser ML runtime. TypeScript provides checked source modules; Python/PyTorch is used for model research and reproducible training. The browser matcher and supervised model pipeline are separate implementations; a trained model is not connected to the upload page.

## Resume wording based on verified work

**HogMorph Studio — Western Hognose phenotype research prototype** | 2026
- Rebuilt a MATLAB course prototype as a bilingual TypeScript web demo, ported its CNN and image-processing research path to Python 3/PyTorch, and preserved unknown workbook labels instead of converting them to negatives.
- Implemented a gated MobileNetV3-Small multilabel training/evaluation pipeline with snake-grouped splits, plus structured image-rights and phenotype-evidence review. The classifier remains untrained because zero current records meet the rights, identity, and label-evidence gate.
- Measured FPPA reconstruction on 21 historical images (mean PSNR 22.3315→26.7765 dB; SSIM 0.5076→0.7598) under synthetic Gaussian noise; this measures denoising only, not morph-recognition accuracy.

Do not describe the MobileNetV3-Small workflow as trained, or the visual-similarity percentages as confidence scores. The FPPA values above are image-reconstruction results and do not establish better morph recognition. The optional Butterworth filter is implemented separately and has no measured classification effect.

## Demo walkthrough (English-first)

1. Upload a known Western Hognose photo on the first screen; explain that browser-side similarity is a visual clue, not a gene prediction.
2. Show nearest archive examples, support counts, and the insufficient-evidence state.
3. Open the collection and a specimen card to show blank/unknown labels and missing provenance.
4. Visit the reference guide and data-readiness panel; separate documented Python model work from the live TypeScript baseline.
5. Finish with local review/export and the training gate: no trained genotype classifier is claimed until individual-level evidence, rights, and an independent test set are available.
