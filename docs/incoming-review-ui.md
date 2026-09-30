# Incoming photo review UI / 待审照片复核界面

## Use / 使用

After staging the metadata-stripped previews, start the local server:

```sh
python3 scripts/serve_incoming_review.py
```

Open `http://127.0.0.1:8765`. To use another local port, pass `--port 8766`; the bind address is fixed to `127.0.0.1`. Stop the server with Ctrl-C. The UI defaults to candidate images; use the filter to review uncertain images. English is shown first; use the language button for Chinese.

完成去除元数据的预览图预处理后，启动本地服务并打开 `http://127.0.0.1:8765`。可用 `--port 8766` 指定其他端口；监听地址固定为 `127.0.0.1`。按 Ctrl-C 停止服务。界面默认显示候选照片，也可筛选待确认照片。默认英文，可切换中文。

### Optional Chinese/English morph-name OCR hints

The private review batch may contain Chinese captions that the original English-only OCR pass could not read. If Tesseract 5 and its `chi_sim` and `eng` language data are available locally, scan the metadata-stripped review previews:

```sh
python3 scripts/scan_incoming_morph_text.py \
  --inventory "$HOME/Library/Application Support/HogMorphStudio/incoming-review/active_inventory.json" \
  --output "$HOME/Library/Application Support/HogMorphStudio/incoming-review/morph-ocr-hints.json" \
  --tessdata-dir "/path/to/tessdata" \
  --include-uncertain
```

The private output contains only source index/hash, possible term, OCR line confidence, and a human-review-required state. It omits the image, local filename, and recognized free text. OCR hits are search hints only: they do not establish a morph label, genotype, image ownership, or training permission. A reviewer must inspect the original source and supporting breeding/genetic evidence before recording any trait.

Tesseract's [official fast Simplified Chinese model](https://github.com/tesseract-ocr/tessdata_fast/blob/main/chi_sim.traineddata) and English model are required; the upstream [language-data repository](https://github.com/tesseract-ocr/tessdata_fast) uses Apache-2.0, and [Tesseract documents how to install language data](https://github.com/tesseract-ocr/tessdoc/blob/main/Installation.md). Install the files locally and retain their license notices. Do not copy OCR model weights into a dataset release or treat OCR as image-label verification.

Review annotations are stored in this browser's `localStorage`, one record per source SHA-256. Use **Download JSON review export** to save a copy. Clearing browser storage removes browser annotations unless you exported them. A confirmed non-Western-Hognose decision is also recorded server-side in the fixed Application Support `review_state.json`, keyed by inventory index and source SHA-256; it is written atomically. This state file contains no annotations or image data and is outside the repository.

The queue shows field-entry counts for manual species confirmation, individual IDs, reviewed morph evidence, and rights scopes. These counters describe what has been entered; they do not independently verify permissions or mark records training eligible. **Next unreviewed** advances within the selected candidate/uncertain queue based on the local review-status field. Export and inspect evidence before treating any count as a completed curation milestone.

复核标注保存在当前浏览器的 `localStorage` 中，并按来源 SHA-256 区分。使用“Download JSON review export”下载副本。清除浏览器存储会删除未导出的浏览器标注。确认“非西部猪鼻蛇”的决定也会写入固定 Application Support 目录下的 `review_state.json`，以清单序号和来源 SHA-256 标识，并通过原子替换保存。此状态文件不含标注或图像数据，也不在代码仓库中。

队列会分别统计人工物种确认、蛇只个体 ID、已复核的形态证据和图片使用范围字段。计数只表示已填写，不会自行核实授权，也不表示记录已符合训练资格。“下一条未复核”会根据本地复核状态，在当前候选／待确认队列内继续浏览。导出后仍要检查证据，不能将计数直接当作完成的语料里程碑。

The source URL field records image provenance and remains separate from the morph evidence URL and rights evidence URL. Marking a photo as confirmed not Western Hognose moves it out of the server's active inventory, blocks its preview endpoint, and omits it from JSON exports. Use the **Excluded · restore** queue and **Restore to review queue** to reverse that decision. Candidate and uncertain photos can both receive this review decision. Confirmed Western Hognose and uncertain choices remain in the review export.

来源网址用于记录照片来源，与形态证据网址、权利证据网址分别保存。将照片标记为“已确认非西部猪鼻蛇”后，服务器会将其从活动清单移出、阻止预览接口，并从 JSON 导出中排除。可在“Excluded · restore”队列选择“Restore to review queue”撤销此决定。候选及待确认照片都可作此标记。已确认西部猪鼻蛇或仍待确认的照片可保留在复核导出中。

Combination aliases such as Sunburst are saved as alias IDs in the JSON export, with their canonical components shown in the form (for example, Sunburst = Sable + Albino). The manifest bridge preserves those IDs, and the existing ontology validator expands them into the component traits before training eligibility is evaluated. Do not also enter the same components as separate labels; conflicting labels are rejected. Alias names are shorthand for documented combinations, not independent genes.

复合形态别名（例如 Sunburst）会以别名 ID 保存在 JSON 导出中，表单同时显示其标准组件（例如 Sunburst = Sable + Albino）。清单桥接程序会保留这些 ID，现有本体校验器再将其展开为基础性状后判断训练资格。不要再把相同组件重复录成独立标签；冲突标签会被拒绝。别名是有文档支持的组合简称，不是独立基因。

## Export-to-manifest bridge / 导出转清单

After downloading the UI's `hogmorph-incoming-review.json`, run the local bridge:

```sh
python3 scripts/build_reviewed_manifest.py "$HOME/Downloads/hogmorph-incoming-review.json" \
  --inventory "$HOME/Library/Application Support/HogMorphStudio/incoming-review/reviewed_inventory.json"
```

It writes `eligible-candidates.jsonl` and a sibling report under `~/Library/Application Support/HogMorphStudio/training-review/` by default. Each export row must match the private inventory by index and original SHA-256; the original file hash is rechecked, and training images point only to metadata-stripped previews. Only manually confirmed captive Western Hognoses proceed to the existing `prepare_training_manifest.py` validator. Missing source evidence, individual ID, visible-trait review, rights evidence, permission scopes, or reviewer information stays rejected. A passing record is only a per-image candidate: `train_multilabel.py` still requires at least 100 eligible photos from 30 individuals plus class support in identity-grouped train/validation/test splits. This bridge does not create labels, infer permissions, or train a model.

下载界面生成的 `hogmorph-incoming-review.json` 后，在本地运行上述转换器。它会默认在 `~/Library/Application Support/HogMorphStudio/training-review/` 下生成 `eligible-candidates.jsonl` 和同名审计报告。每行导出必须通过序号和原始 SHA-256 匹配私有清单，且重新校验原图哈希；训练图像只指向已去除元数据的预览图。只有人工确认的圈养西部猪鼻蛇记录才会进入现有训练清单验证器。缺失来源证据、个体 ID、可见性状复核、图片权利、许可范围或复核人信息的记录会被拒绝。单条记录通过只代表满足单图清单条件；`train_multilabel.py` 仍要求至少 100 张合格照片、30 个个体，以及按个体切分后的类别支持度。该桥接程序不会创建标签、推断授权或训练模型。

## Data boundary and safety / 数据边界与安全

The server reads only `~/Library/Application Support/HogMorphStudio/incoming-review/`. It prefers `active_inventory.json`, then `reviewed_inventory.json`, then `inventory.json` when earlier files are absent. It serves only validated inventory previews and the UI's own static assets. The active inventory response includes only source index, source SHA-256, visual triage, and preview URL; it never returns original filenames, source paths, or EXIF/GPS data. Upstream rows triaged as unrelated, excluded, or pending are omitted. Server-excluded rows appear only in the restore queue as index/hash metadata, and their preview routes return 404. All mutations validate the index/SHA pair against the fixed inventory; no filesystem path is accepted from the browser. No external requests, CDN assets, analytics, or third-party scripts are used.

服务只读取 `~/Library/Application Support/HogMorphStudio/incoming-review/`。优先读取 `active_inventory.json`；若不存在，则依次回退至 `reviewed_inventory.json` 和 `inventory.json`。仅提供清单引用的预览图和本界面的静态文件。活动清单响应只含来源序号、SHA-256、视觉初筛结果和预览网址；不会返回原文件名、来源路径或 EXIF/GPS 信息。上游标为非目标、排除或待处理的记录会被过滤。服务器排除的记录只在恢复队列中显示序号和哈希，预览接口返回 404。所有变更均通过固定清单中的序号与 SHA 配对验证；浏览器不能传入文件系统路径。不会请求外部服务、CDN、分析服务或第三方脚本。

Similarity groups are not confirmed individual snakes. Blank review fields mean unknown; they are not negative labels. Combination names add their canonical base trait/state components. Never assign carrier status from a photo. The UI's JSON is a review export, not a training manifest, and it does not include a local source-image path. An annotation becomes eligible for training only after it is mapped to a manifest record and passes the existing `scripts/prepare_training_manifest.py` validation, including image, evidence, rights, and explicit training/evaluation scope checks.

相似图片分组不代表已确认是同一条蛇。空白表示未知，不是阴性标签。组合名称会拆解为标准基础性状／状态。绝不能从照片标注携带状态。界面 JSON 是复核导出，不是训练清单，也不含本地源图路径。只有将标注映射到清单记录并通过现有 `scripts/prepare_training_manifest.py` 验证（包括图像、证据、权利以及明确的训练／评估许可范围）后，才可能用于训练。
