const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char] ?? char));
let catalog;
let references;
let view = 'grid';
const drafts = [];
let language = 'en';
const COPY = {
    en: {
        'nav.collection': 'Collection', 'nav.readiness': 'Readiness', 'nav.contribute': 'Contribute',
        'hero.eyebrow': 'SMALL-DATA RESEARCH TOOLKIT', 'hero.title': 'See the pattern.<br><em>Respect the unknown.</em>',
        'hero.description': 'A provenance-aware review and curation workbench for Western Hognose photos. Organize images, labels, and sources before asking what a model can learn.', 'hero.visualNote': 'AI-GENERATED VISUAL / NOT SPECIMEN DATA', 'hero.alt': 'AI-generated Western Hognose visual illustration, not a specimen photo',
        'hero.browse': 'Browse the collection ↘', 'hero.why': 'How the model reasons →', 'hero.year': 'Course project · 2024', 'hero.stamp': 'DEMO<br>REFERENCE PHOTOS',
        'stats.photos': 'demo reference photos', 'stats.labels': 'supported trait states', 'stats.supported': 'states with references', 'stats.boundary': 'Multimodal assistance · phenotype evidence',
        'collection.eyebrow': 'THE COLLECTION', 'collection.title': 'Specimen archive', 'collection.description': 'Browse the 18 approved demo photos by supported trait state. Missing traits stay unknown; these are comparison references, not an independent test set.', 'collection.empty': 'No specimens match. Try clearing the filters.',
        'filter.allLabels': 'All labels', 'filter.allStatuses': 'All review statuses', 'filter.pending': 'Pending review', 'filter.reviewed': 'Reviewed', 'filter.clear': 'Clear filters ×', 'filter.search': 'Search specimen IDs…', 'filter.labelAria': 'Filter by label', 'filter.statusAria': 'Filter by review status', 'filter.grid': 'Grid view', 'filter.list': 'List view', 'filter.close': 'Close',
        'filter.loading': 'Loading…', 'filter.failed': 'Could not load the local data. Start the preview using the README instructions.', 'filter.records': 'records', 'filter.of': 'of',
        'card.pending': 'Unverified', 'card.reviewed': 'Reviewed', 'card.tablePositives': 'supported traits', 'card.unlabeled': 'fields unknown', 'card.open': 'Open details ↗',
        'detail.course': 'APPROVED DEMO REFERENCE', 'detail.reference': 'USER-SUPPLIED REFERENCE', 'detail.openReferenceTitle': 'OPEN-LICENSE CANDIDATE', 'detail.recordIntro': 'The project owner confirmed these course-photo labels and permitted demo use. Only ontology-supported traits are shown. Independent specimen-level genotype evidence is not available.', 'detail.referenceIntro': 'This caption is transcribed from the supplied guide and is a visual learning reference only.', 'detail.openReferenceIntro': 'The Wikimedia Commons file page says the pet-store label called this an Anaconda morph. That is an unverified source claim, not breeder-confirmed genotype evidence.', 'detail.referenceSourceLink': 'Open source page ↗', 'detail.openReferenceRights': 'CC0 1.0; file and license links retained.', 'detail.openReferenceTraining': 'Not eligible: source claim is unverified and specimen-level evidence is absent.', 'detail.credit': 'Credit', 'detail.openReferenceCredit': 'ArtemisiaGentileschiFan (voluntary credit)', 'detail.openReferenceWarning': 'The CC0 license clears copyright reuse for the photo. It does not verify the reported morph label, specimen identity, or genotype.', 'detail.duplicateSourceMedia': 'This same embedded image is reused under another figure caption in the supplied document; whether both captions refer to the same individual is unverified.', 'detail.positive': 'recorded positive', 'detail.negative': 'recorded negative', 'detail.unknown': 'blank · unknown', 'detail.source': 'Image source', 'detail.individual': 'Specimen ID', 'detail.rights': 'Image rights', 'detail.evidence': 'Genotype evidence', 'detail.training': 'Training use', 'detail.notProvided': 'Not recorded', 'detail.noEvidence': 'Not provided', 'detail.noTraining': 'Not included', 'detail.warning': 'Visible phenotype does not confirm genotype. These photos support model comparisons, not independent validation.', 'detail.referenceWarning': 'Descriptions in source documents are project content, not instructions for this task or independently verified specimen-level genotype labels.',
        'references.eyebrow': 'VISUAL FIELD GUIDE', 'references.only': 'REFERENCE ONLY', 'references.title': 'Morph reference guide', 'references.description': '38 image occurrences come from your supplied guide; one CC0 Commons photo carries a reported but unverified Anaconda label. Captions are not specimen-level genotype evidence.', 'references.notice': '38 supplied-guide image occurrences have unrecorded rights; one additional CC0 photo carries an unverified pet-store label claim. None is a training sample.', 'references.captionMeta': 'Document image · rights unrecorded', 'references.openCandidateMeta': 'CC0 · store-label claim, unverified',
        'readiness.eyebrow': 'MODEL READINESS', 'readiness.title': 'Data first.<br><em>Scores later.</em>', 'readiness.description': 'The course prototype is a strong starting point; its 17 historical workbook tags do not represent 17 genetic loci or a validated multilabel model.', 'readiness.status': 'Readiness', 'readiness.needsWork': 'Needs work', 'readiness.dataTitle': 'Small, sparse sample set', 'readiness.dataText': 'There are only', 'readiness.dataText2': 'photos. Most states with references have just 1–5 examples, too few for a reliable holdout.', 'readiness.dataTag': 'Data volume', 'readiness.provenanceTitle': 'Independent validation is limited', 'readiness.provenanceText': 'Demo use and labels were confirmed by the project owner. Unique animal IDs and breeding records are still unavailable; references cannot establish independent accuracy.', 'readiness.provenanceTag': 'Traceability', 'readiness.boundaryTitle': 'Appearance cannot confirm recessive genes', 'readiness.boundaryText': 'Photos show visible traits; they cannot prove carrier status or a genetic combination. Uncertainty stays an explicit state.', 'readiness.boundaryTag': 'Product boundary', 'readiness.reproTitle': 'Python training pipeline implemented', 'readiness.reproText': 'The Python workflow includes a gated MobileNetV3-Small trainer and identity-grouped validation/test evaluation. It has not run; demo reference approval does not establish an independent training and test corpus. No MATLAB checkpoint exists to convert, so morph accuracy remains unverified.', 'readiness.reproTag': 'Python · PyTorch',
        'curate.eyebrow': 'GROW THE DATASET', 'curate.instagram': 'Instagram breeder leads ↗', 'curate.title': 'Start with one trusted record', 'curate.description': 'New records stay in this page’s memory. Add source, specimen, and review evidence, then export structured JSON.', 'curate.addTitle': 'Add photos for review', 'curate.addDescription': 'Preview locally; nothing is uploaded. Export includes images and their source, rights, and label evidence.', 'curate.choose': 'Choose images', 'curate.export': 'Export annotations', 'curate.guidanceLabel': 'Curation guide:', 'curate.guidance': 'Capture a unique specimen ID, photo source and license, breeding/genotype evidence, annotator, and reviewer. Split by individual; augment training data only.', 'curate.plan': 'View evaluation plan ↗', 'curate.selectFile': 'Select one or more image files first.', 'curate.exportError': ' record(s) are marked reviewed but need a reviewer, label evidence, and uncertainty resolved. Complete those fields or change the review status to pending before exporting.', 'curate.file': 'File', 'curate.specimen': 'Specimen ID', 'curate.sourceUrl': 'Photo source URL', 'curate.rights': 'Image license', 'curate.unknownRights': 'Unknown', 'curate.granted': 'Permission granted', 'curate.restricted': 'Restricted / private use only', 'curate.evidence': 'Genotype / label evidence', 'curate.annotator': 'Annotator', 'curate.reviewer': 'Reviewer', 'curate.unreviewed': 'Pending review', 'curate.reviewed': 'Reviewed', 'curate.visibleTraits': 'Visible traits recorded (select all that apply)', 'curate.uncertain': 'Needs expert review / uncertain',
        'footer.boundary': 'Education and curation prototype · not for genotype diagnosis', 'reference.unknown': 'not documented'
    },
    zh: {
        'nav.collection': '样本库', 'nav.readiness': '数据就绪度', 'nav.contribute': '新增标注',
        'hero.eyebrow': '小样本研究工具', 'hero.title': '看见花纹。<br><em>尊重未知。</em>',
        'hero.description': '为西部猪鼻蛇照片打造的可追溯观察与标注工作台。先整理图像、标签和来源，再判断模型能学到什么。', 'hero.visualNote': 'AI 生成示意图 / 非样本照片', 'hero.alt': 'AI生成的西部猪鼻蛇示意视觉图，不是实际样本照片',
        'hero.browse': '浏览样本 ↘', 'hero.why': '模型如何判断 →', 'hero.year': '课程项目 · 2024', 'hero.stamp': '演示<br>参考照片',
        'stats.photos': '演示参考照片', 'stats.labels': '支持的性状状态', 'stats.supported': '有参考图的状态', 'stats.boundary': '多模态辅助判断 · 表型证据',
        'collection.eyebrow': '样本档案', 'collection.title': '样本档案', 'collection.description': '按支持的性状状态浏览 18 张已确认可用的演示照片。缺失性状保留为未知；这些是对照参考图，不是独立测试集。', 'collection.empty': '没有符合条件的样本。试试清除筛选。',
        'filter.allLabels': '所有标签', 'filter.allStatuses': '所有核验状态', 'filter.pending': '待核验', 'filter.reviewed': '已核验', 'filter.clear': '清除筛选 ×', 'filter.search': '搜索样本编号…', 'filter.labelAria': '按标签筛选', 'filter.statusAria': '按核验状态筛选', 'filter.grid': '网格视图', 'filter.list': '列表视图', 'filter.close': '关闭',
        'filter.loading': '正在载入…', 'filter.failed': '本地数据读取失败。请按 README 中的步骤启动预览。', 'filter.records': '条记录', 'filter.of': '/',
        'card.pending': '待核验', 'card.reviewed': '已核验', 'card.tablePositives': '个支持性状', 'card.unlabeled': '项未知字段', 'card.open': '打开详情 ↗',
        'detail.course': '已确认可用的演示参考图', 'detail.reference': '用户提供的参考资料', 'detail.openReferenceTitle': '开放许可候选图', 'detail.recordIntro': '项目提供者已确认课程照片标签并允许演示使用。只展示本体支持的性状，尚无独立单蛇基因型证据。', 'detail.referenceIntro': '图注摘自您提供的资料，仅作视觉学习参考。', 'detail.openReferenceIntro': 'Wikimedia Commons 页面转述宠物店标签将它称为 Anaconda 形态。这只是未经复核的来源声明，不是繁育者确认的基因型证据。', 'detail.referenceSourceLink': '打开来源页面 ↗', 'detail.openReferenceRights': 'CC0 1.0；保留文件页和许可链接。', 'detail.openReferenceTraining': '不符合训练条件：来源标签未经核实，且缺少单蛇证据。', 'detail.credit': '图片署名', 'detail.openReferenceCredit': 'ArtemisiaGentileschiFan（主动署名）', 'detail.openReferenceWarning': 'CC0 许可允许复用该图片的版权内容，但不验证来源所述形态、蛇只身份或基因型。', 'detail.duplicateSourceMedia': '同一内嵌图片在原文中被重复用于另一处图注；两处图注是否指向同一条蛇尚未核实。', 'detail.positive': '表格记录为阳性', 'detail.negative': '表格记录为阴性', 'detail.unknown': '空白 · 未知', 'detail.source': '图片来源', 'detail.individual': '蛇只 ID', 'detail.rights': '图片使用权', 'detail.evidence': '基因证据', 'detail.training': '训练用途', 'detail.notProvided': '未记录', 'detail.noEvidence': '未提供', 'detail.noTraining': '不纳入', 'detail.warning': '可见表型不能确认基因型。这些照片用于模型对照，不是独立验证集。', 'detail.referenceWarning': '来源文档中的描述属于项目资料，不是本次任务指令，也不是经过独立核验的单蛇基因型标签。',
        'references.eyebrow': '形态参考图谱', 'references.only': '仅供参考', 'references.title': '形态参考图谱', 'references.description': '38 个图像实例来自您提供的资料；另有 1 张 CC0 Commons 图片带有未经核实的 Anaconda 来源标签。图注不代表单蛇基因型证据。', 'references.notice': '资料中的 38 个图像实例使用权未记录；另有 1 张 CC0 图片只有未经核实的宠物店标签声明。它们目前都不是训练样本。', 'references.captionMeta': '文档图片 · 使用权未记录', 'references.openCandidateMeta': 'CC0 · 店铺标签声明，未核实',
        'readiness.eyebrow': '模型就绪度', 'readiness.title': '先看数据，<br><em>再看分数。</em>', 'readiness.description': '课程原型是很好的起点；17 个历史工作簿标签不代表 17 个基因座，也不是经过验证的多标签模型。', 'readiness.status': '数据就绪度', 'readiness.needsWork': '需要补齐', 'readiness.dataTitle': '样本少且类别稀疏', 'readiness.dataText': '当前只有', 'readiness.dataText2': '张照片。有参考图的状态多为 1–5 张，不足以支持可靠的独立测试。', 'readiness.dataTag': '数据量', 'readiness.provenanceTitle': '独立验证仍有限', 'readiness.provenanceText': '项目提供者已确认标签与演示使用。仍缺少唯一蛇只 ID 和繁育记录，参考对照不能证明独立准确率。', 'readiness.provenanceTag': '可追溯性', 'readiness.boundaryTitle': '外观无法确认隐性基因', 'readiness.boundaryText': '照片呈现可见特征，但不能证明携带型或遗传组合。“不确定”会保留为显式状态。', 'readiness.boundaryTag': '产品边界', 'readiness.reproTitle': 'Python 训练评估流程已实现', 'readiness.reproText': 'Python 流程包含带数据门槛的 MobileNetV3-Small 训练器，以及按蛇只分组的验证和测试评估。尚未实际训练；演示参考图的确认并不能建立独立的训练和测试数据集。没有可转换的 MATLAB 权重，因此基因分类准确率仍未验证。', 'readiness.reproTag': 'Python · PyTorch',
        'curate.eyebrow': '补充可靠数据', 'curate.instagram': 'Instagram 繁育者线索 ↗', 'curate.title': '从一条可信记录开始', 'curate.description': '新记录暂存在当前页面。补全来源、蛇只和核验依据，再导出结构化 JSON。', 'curate.addTitle': '添加待核验照片', 'curate.addDescription': '仅在本地预览，不会上传。导出文件包含图片、来源、使用权和标签证据。', 'curate.choose': '选择图片', 'curate.export': '导出标注', 'curate.guidanceLabel': '标注建议：', 'curate.guidance': '记录唯一蛇只 ID、图片来源和许可、繁育/基因型证据、标注者及复核者。按蛇只分组切分；只增强训练集。', 'curate.plan': '查看评估方案 ↗', 'curate.selectFile': '请先选择一个或多个图片文件。', 'curate.exportError': '条记录标记为“已核验”，但缺少复核者或标签证据，或仍存在不确定项。请补齐信息或改回“待核验”再导出。', 'curate.file': '文件', 'curate.specimen': '蛇只 ID', 'curate.sourceUrl': '图片来源链接', 'curate.rights': '图片许可', 'curate.unknownRights': '未知', 'curate.granted': '已取得授权', 'curate.restricted': '受限 / 仅个人使用', 'curate.evidence': '基因 / 标签证据', 'curate.annotator': '标注者', 'curate.reviewer': '复核者', 'curate.unreviewed': '待核验', 'curate.reviewed': '已核验', 'curate.visibleTraits': '记录的可见表型（可多选）', 'curate.uncertain': '需要专家复核 / 不确定',
        'footer.boundary': '教育与数据整理原型 · 不用于基因型诊断', 'reference.unknown': '未记录'
    }
};
function t(key) { return COPY[language][key] ?? COPY.en[key] ?? key; }
function labelName(label) {
    if (label.id === 'r')
        return language === 'zh' ? `${label.name_zh}（可见表型描述，非基因）` : `${label.name_en} (visible descriptor, not a gene)`;
    return language === 'zh' ? label.name_zh : label.name_en;
}
function setLanguage(next) {
    language = next;
    document.documentElement.lang = language === 'en' ? 'en' : 'zh-CN';
    document.title = language === 'en' ? 'HogMorph Studio — Western Hognose Field Notes' : 'HogMorph Studio — 猪鼻蛇形态观察工作台';
    $('.stat-strip').setAttribute('aria-label', language === 'en' ? 'Project overview' : '项目概况');
    document.querySelectorAll('[data-copy]').forEach((node) => { node.textContent = t(node.dataset.copy); });
    document.querySelectorAll('[data-copy-html]').forEach((node) => { node.innerHTML = t(node.dataset.copyHtml); });
    $('.hero-image').alt = t('hero.alt');
    $('#search').placeholder = t('filter.search');
    $('#search').setAttribute('aria-label', t('filter.search'));
    $('#label-filter').setAttribute('aria-label', t('filter.labelAria'));
    $('#review-filter').setAttribute('aria-label', t('filter.statusAria'));
    $('.view-button[data-view="grid"]').setAttribute('aria-label', t('filter.grid'));
    $('.view-button[data-view="list"]').setAttribute('aria-label', t('filter.list'));
    $('.dialog-close').setAttribute('aria-label', t('filter.close'));
    $('#language-toggle').textContent = language === 'en' ? '中文' : 'English';
    $('#language-toggle').href = language === 'en' ? '?lang=zh' : '?lang=en';
    $('#language-toggle').setAttribute('aria-label', language === 'en' ? 'Switch to Chinese' : '切换到英文');
    $('#label-filter').options[0].textContent = t('filter.allLabels');
    $('#review-filter').options[0].textContent = t('filter.allStatuses');
    $('#review-filter').options[1].textContent = t('filter.pending');
    $('#review-filter').options[2].textContent = t('filter.reviewed');
    if (catalog)
        renderGallery();
    if (references)
        renderReferences();
    if (catalog && drafts.length)
        renderDrafts();
}
async function init() {
    [catalog, references] = await Promise.all([
        fetch('/api/references').then(async (response) => {
            if (!response.ok)
                return null;
            const data = await response.json();
            const records = Array.isArray(data) ? data : data.references ?? data.images ?? [];
            const names = { 'anaconda': ['Anaconda', '康达'], 'arctic': ['Arctic', '北极'], 'albino': ['Albino', '白化'], 'axanthic': ['Axanthic', '缺黄'], 'sable': ['Sable', '紫貂'], 'toffee-belly': ['Toffee Belly', '太妃糖腹'], 'lavender': ['Lavender', '薰衣草'] };
            const labels = new Map();
            const images = records.map((record) => {
                const values = {};
                for (const trait of record.traits ?? []) {
                    const superForm = /super|homozygous/.test(trait.state) && ['anaconda', 'arctic'].includes(trait.trait_id);
                    const id = superForm ? 'super-' + trait.trait_id : trait.trait_id;
                    const base = names[trait.trait_id];
                    if (!base)
                        continue;
                    if (!labels.has(id))
                        labels.set(id, { id, name_en: (superForm ? 'Super ' : '') + base[0], name_zh: (superForm ? '超级' : '') + base[1], positive_examples: 0 });
                    labels.get(id).positive_examples++;
                    values[id] = 1;
                }
                return { id: record.id, image: record.image, labels: values, available: true, review_status: 'reviewed' };
            });
            for (const image of images)
                for (const id of labels.keys())
                    image.labels[id] ??= null;
            return { images, labels: [...labels.values()] };
        }).catch(() => null),
        fetch('data/reference_gallery.json?v=ui-open-candidate-1').then((response) => response.ok ? response.json() : null).catch(() => null)
    ]);
    // A clean clone intentionally works without the locally retained course-image archive.
    // Empty fallbacks keep the curation UI usable without exposing unlicensed source media.
    catalog ??= { images: [], labels: [] };
    references ??= { images: [] };
    const existing = catalog.images.filter((image) => image.available);
    $('#collection').hidden = existing.length === 0;
    $('#references').hidden = references.images.length === 0;
    const supported = catalog.labels.filter((label) => label.positive_examples > 0).length;
    $('#stat-images').textContent = existing.length;
    $('#hero-stamp-count').textContent = existing.length;
    $('#stat-labels').textContent = catalog.labels.length;
    $('#stat-supported').textContent = `${supported}/${catalog.labels.length}`;
    $('#ready-images').textContent = existing.length;
    $('#record-count').textContent = String(existing.length).padStart(2, '0');
    $('#reference-count').textContent = String(references.images.length).padStart(2, '0');
    const filter = $('#label-filter');
    catalog.labels.forEach((label) => {
        const option = document.createElement('option');
        option.value = label.id;
        option.textContent = `${labelName(label)} (${label.positive_examples})`;
        filter.append(option);
    });
    renderGallery();
    renderReferences();
}
function activeImages() {
    const query = $('#search').value.trim().toLowerCase();
    const label = $('#label-filter').value;
    const status = $('#review-filter').value;
    return catalog.images.filter((image) => image.available).filter((image) => {
        const matchesQuery = !query || image.id.toLowerCase().includes(query);
        const matchesLabel = !label || image.labels[label] === 1;
        const matchesStatus = !status || image.review_status === status;
        return matchesQuery && matchesLabel && matchesStatus;
    });
}
function renderGallery() {
    const items = activeImages();
    const gallery = $('#gallery');
    gallery.classList.toggle('list-view', view === 'list');
    gallery.innerHTML = items.map((image) => {
        const positives = catalog.labels.filter((label) => image.labels[label.id] === 1);
        const unknowns = catalog.labels.filter((label) => image.labels[label.id] === null);
        const shown = positives.slice(0, 3).map((label) => `<span class="label-chip positive">${escapeHtml(labelName(label))}</span>`).join('');
        const missing = unknowns.length ? `<span class="label-chip unknown">${unknowns.length} ${t('card.unlabeled')}</span>` : '';
        const remainder = positives.length > 3 ? `<span class="label-chip">+${positives.length - 3}</span>` : '';
        const reviewed = image.review_status === 'reviewed';
        const review = reviewed ? t('card.reviewed') : t('card.pending');
        const alt = language === 'en' ? `Course archive image ${image.id}` : `课程档案图片 ${image.id}`;
        return `<article class="sample-card" data-id="${escapeHtml(image.id)}" tabindex="0" role="button" aria-label="${escapeHtml(image.id)}"><div class="sample-image"><img src="${escapeHtml(image.image)}" alt="${escapeHtml(alt)}" loading="lazy"><span class="sample-id">${escapeHtml(image.id.toUpperCase())}</span></div><div class="sample-meta"><div class="sample-meta-top"><h3>${escapeHtml(image.id)}</h3><span class="review-chip ${reviewed ? 'reviewed' : ''}">${review}</span></div><div class="sample-tags">${shown}${remainder}${missing}</div><div class="card-foot"><span>${positives.length} ${t('card.tablePositives')}</span><span>${t('card.open')}</span></div></div></article>`;
    }).join('');
    const total = catalog.images.filter((image) => image.available).length;
    $('#result-summary').textContent = language === 'en' ? `${items.length} ${t('filter.of')} ${total} ${t('filter.records')}` : `${items.length} / ${total} ${t('filter.records')}`;
    $('#empty-state').hidden = items.length > 0;
    gallery.hidden = items.length === 0;
    gallery.querySelectorAll('.sample-card').forEach((card) => {
        card.addEventListener('click', () => showDetail(card.dataset.id));
        card.addEventListener('keydown', (event) => { if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            showDetail(card.dataset.id);
        } });
    });
}
function showDetail(id) {
    const image = catalog.images.find((item) => item.id === id);
    const labels = catalog.labels.map((label) => {
        const state = image.labels[label.id];
        const status = state === 1 ? t('detail.positive') : state === 0 ? t('detail.negative') : t('detail.unknown');
        return `<span class="label-chip ${state === 1 ? 'positive' : state === null ? 'unknown' : ''}">${escapeHtml(labelName(label))} · ${escapeHtml(status)}</span>`;
    }).join('');
    $('#detail-content').innerHTML = `<div class="detail-layout"><img src="${escapeHtml(image.image)}" alt="${escapeHtml(image.id)}"><div class="detail-copy"><div class="eyebrow"><span class="eyebrow-line"></span> ${t('detail.course')}</div><h2>${escapeHtml(image.id.toUpperCase())}</h2><p>${t('detail.recordIntro')}</p><div class="detail-labels">${labels}</div><div class="detail-meta"><div><b>${t('detail.source')}</b> ${t('detail.notProvided')}</div><div><b>${t('detail.individual')}</b> ${t('detail.notProvided')}</div><div><b>${t('detail.rights')}</b> ${language === 'zh' ? '项目提供者确认可用于演示' : 'Demo use confirmed by project owner'}</div><div><b>${t('detail.evidence')}</b> ${t('detail.noEvidence')}</div></div><p class="fine-print">${t('detail.warning')}</p></div></div>`;
    $('#detail-dialog').showModal();
}
function renderReferences() {
    $('#reference-gallery').innerHTML = references.images.map((item) => {
        const caption = language === 'zh' ? item.caption_zh : item.caption;
        const meta = item.record_kind === 'open_license_candidate' ? t('references.openCandidateMeta') : t('references.captionMeta');
        return `<article class="reference-card" data-ref="${escapeHtml(item.id)}" tabindex="0" role="button"><div class="reference-image"><img loading="lazy" src="data/${escapeHtml(item.file)}" alt="${escapeHtml(caption)}"><span>${escapeHtml(item.id.toUpperCase())}</span></div><div class="reference-caption"><strong>${escapeHtml(caption)}</strong><small>${meta}</small></div></article>`;
    }).join('');
    $('#reference-gallery').querySelectorAll('.reference-card').forEach((card) => {
        const open = () => {
            const item = references.images.find((entry) => entry.id === card.dataset.ref);
            const caption = language === 'zh' ? item.caption_zh : item.caption;
            const openCandidate = item.record_kind === 'open_license_candidate';
            const source = openCandidate
                ? `<a href="${escapeHtml(item.source_url)}" target="_blank" rel="noopener noreferrer">${t('detail.referenceSourceLink')}</a>`
                : '猪鼻蛇基因分类.docx';
            const rights = openCandidate
                ? `<a href="${escapeHtml(item.license_url)}" target="_blank" rel="noopener noreferrer">${t('detail.openReferenceRights')}</a>`
                : t('detail.notProvided');
            const evidence = openCandidate
                ? (language === 'zh' ? escapeHtml(item.source_claim_zh) : escapeHtml(item.source_claim))
                : t('detail.noEvidence');
            const training = openCandidate ? t('detail.openReferenceTraining') : t('detail.noTraining');
            const intro = openCandidate ? t('detail.openReferenceIntro') : t('detail.referenceIntro');
            const eyebrow = openCandidate ? t('detail.openReferenceTitle') : t('detail.reference');
            const credit = openCandidate ? `<div><b>${t('detail.credit')}</b> ${t('detail.openReferenceCredit')}</div>` : '';
            const warning = openCandidate ? t('detail.openReferenceWarning') : t('detail.referenceWarning');
            const duplicateNote = item.duplicate_media_of ? `<p class="fine-print">${t('detail.duplicateSourceMedia')}</p>` : '';
            $('#detail-content').innerHTML = `<div class="detail-layout"><img src="data/${escapeHtml(item.file)}" alt="${escapeHtml(caption)}"><div class="detail-copy"><div class="eyebrow"><span class="eyebrow-line"></span> ${eyebrow}</div><h2>${escapeHtml(caption)}</h2><p>${intro}</p><div class="detail-meta"><div><b>${language === 'en' ? 'Source page' : '来源页面'}</b> ${source}</div><div><b>${language === 'en' ? 'Original media' : '原始媒体'}</b> ${escapeHtml(item.source_asset)}</div><div><b>${t('detail.rights')}</b> ${rights}</div><div><b>${t('detail.evidence')}</b> ${evidence}</div>${credit}<div><b>${t('detail.training')}</b> ${training}</div></div>${duplicateNote}<p class="fine-print">${warning}</p></div></div>`;
            $('#detail-dialog').showModal();
        };
        card.addEventListener('click', open);
        card.addEventListener('keydown', (event) => { if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            open();
        } });
    });
}
function renderDrafts() {
    const panel = $('#draft-panel');
    panel.hidden = drafts.length === 0;
    if (!drafts.length) {
        panel.innerHTML = '';
        return;
    }
    panel.innerHTML = drafts.map((draft, index) => `<article class="draft-card"><img src="${draft.dataUrl}" alt="${language === 'en' ? 'New image preview' : '新图片预览'}"><div><h4>NEW-${String(index + 1).padStart(2, '0')} · ${escapeHtml(draft.name)}</h4><label>${t('curate.specimen')}<input data-field="individual_id" data-index="${index}" value="${escapeHtml(draft.individual_id)}" placeholder="${language === 'en' ? 'e.g. breeder-2026-001' : '例如 breeder-2026-001'}"></label><label>${t('curate.sourceUrl')}<input data-field="source_url" data-index="${index}" value="${escapeHtml(draft.source_url)}" placeholder="${language === 'en' ? 'Link to original page' : '来源页链接'}"></label><label>${t('curate.rights')}<select data-field="image_rights" data-index="${index}"><option value="unknown" ${draft.image_rights === 'unknown' ? 'selected' : ''}>${t('curate.unknownRights')}</option><option value="permission-granted" ${draft.image_rights === 'permission-granted' ? 'selected' : ''}>${t('curate.granted')}</option><option value="CC0">CC0</option><option value="CC-BY">CC BY</option><option value="CC-BY-SA">CC BY-SA</option><option value="restricted">${t('curate.restricted')}</option></select></label><label>${t('curate.evidence')}<input data-field="genotype_evidence" data-index="${index}" value="${escapeHtml(draft.genotype_evidence)}" placeholder="${language === 'en' ? 'Breeding records, genetic test, expert review…' : '繁育记录、遗传检测、专家复核等'}"></label><label>${t('curate.annotator')}<input data-field="annotator" data-index="${index}" value="${escapeHtml(draft.annotator)}" placeholder="${language === 'en' ? 'Name or team' : '姓名或团队'}"></label><label>${t('curate.reviewer')}<input data-field="reviewer" data-index="${index}" value="${escapeHtml(draft.reviewer)}" placeholder="${language === 'en' ? 'Leave blank if pending' : '未复核可留空'}"></label><label>${language === 'en' ? 'Review status' : '复核状态'}<select data-field="review_status" data-index="${index}"><option value="unverified" ${draft.review_status === 'unverified' ? 'selected' : ''}>${t('curate.unreviewed')}</option><option value="reviewed" ${draft.review_status === 'reviewed' ? 'selected' : ''}>${t('curate.reviewed')}</option></select></label><label>${t('curate.visibleTraits')}</label><div class="draft-tags">${catalog.labels.map((label) => `<label><input type="checkbox" data-tag="${label.id}" data-index="${index}" ${draft.labels.includes(label.id) ? 'checked' : ''}>${escapeHtml(labelName(label))}</label>`).join('')}</div><label><input type="checkbox" data-field="uncertain" data-index="${index}" ${draft.uncertain ? 'checked' : ''}> ${t('curate.uncertain')}</label></div></article>`).join('');
    panel.querySelectorAll('[data-field]').forEach((input) => input.addEventListener('change', () => {
        const draft = drafts[Number(input.dataset.index)];
        draft[input.dataset.field] = input.type === 'checkbox' ? input.checked : input.value;
    }));
    panel.querySelectorAll('[data-tag]').forEach((input) => input.addEventListener('change', () => {
        const draft = drafts[Number(input.dataset.index)];
        draft.labels = input.checked ? [...new Set([...draft.labels, input.dataset.tag])] : draft.labels.filter((id) => id !== input.dataset.tag);
    }));
}
$('#search').addEventListener('input', renderGallery);
$('#label-filter').addEventListener('change', renderGallery);
$('#review-filter').addEventListener('change', renderGallery);
$('#clear-filter').addEventListener('click', () => { $('#search').value = ''; $('#label-filter').value = ''; $('#review-filter').value = ''; renderGallery(); });
document.querySelectorAll('.view-button').forEach((button) => button.addEventListener('click', () => {
    view = button.dataset.view ?? 'grid';
    document.querySelectorAll('.view-button').forEach((item) => item.classList.toggle('active', item === button));
    renderGallery();
}));
$('.dialog-close').addEventListener('click', () => $('#detail-dialog').close());
$('#detail-dialog').addEventListener('click', (event) => { if (event.target === $('#detail-dialog'))
    $('#detail-dialog').close(); });
$('#file-input').addEventListener('change', async (event) => {
    const files = [...event.target.files];
    if (!files.length)
        return;
    for (const file of files) {
        if (!file.type.startsWith('image/'))
            continue;
        const dataUrl = await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => typeof reader.result === 'string' ? resolve(reader.result) : reject(new Error('Could not read image data URL')); reader.onerror = reject; reader.readAsDataURL(file); });
        drafts.push({ name: file.name, dataUrl, individual_id: '', source_url: '', image_rights: 'unknown', genotype_evidence: '', annotator: '', reviewer: '', review_status: 'unverified', labels: [], uncertain: true });
    }
    renderDrafts();
    event.target.value = '';
});
$('#export-button').addEventListener('click', () => {
    const incompleteReviews = drafts.filter((draft) => draft.review_status === 'reviewed' && (!draft.reviewer.trim() || !draft.genotype_evidence.trim() || draft.uncertain));
    const error = $('#export-error');
    if (incompleteReviews.length) {
        error.textContent = `${incompleteReviews.length}${t('curate.exportError')}`;
        error.hidden = false;
        return;
    }
    error.hidden = true;
    const payload = { title: 'HogMorph Studio contribution export', exported_at: new Date().toISOString(), note: 'Contributor records are not independently verified; do not treat visual labels as confirmed genotype.', images: drafts.map(({ dataUrl, ...draft }) => ({ ...draft, image_data_url: dataUrl })) };
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'hogmorph_contributions.json';
    anchor.click();
    URL.revokeObjectURL(url);
});
const preferredLanguage = new URLSearchParams(window.location.search).get('lang') === 'zh' ? 'zh' : 'en';
setLanguage(preferredLanguage);
init().catch((error) => {
    console.error(error);
    $('#result-summary').textContent = '数据加载失败';
    $('#empty-state').hidden = false;
    $('#empty-state').textContent = t('filter.failed');
});
export {};
