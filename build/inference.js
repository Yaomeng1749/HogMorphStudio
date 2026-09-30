// Local visual screening only. The archived labels are unreviewed course records.
// No output from this file is a calibrated probability or a genotype call.
(() => {
    'use strict';
    const $ = (selector) => document.querySelector(selector);
    const zh = new URLSearchParams(location.search).get('lang') === 'zh';
    const words = zh ? {
        nav: '分析照片', navModel: '识别原理', method: '识别原理 →',
        headline: '上传猪鼻蛇照片。<br><em>探索可见表型。</em>',
        hero: '在浏览器里将照片与课程档案比对，查看相似的可见特征和证据量。遗传组成需要繁育记录或检测支持。',
        eyebrow: '照片分析 · 本地演示', title: '探索可见形态线索',
        intro: '请只使用已确认是西部猪鼻蛇的照片；本工具不核验物种。结果是图像相似度与样本支持数，不是基因型概率。',
        choose: '选择照片开始分析', privacy: '在浏览器本地处理。照片不会上传或保存。',
        resultEyebrow: '本地视觉筛查', resultTitle: '档案图像相似度', limited: '证据不足 · 暂不分类',
        processing: '正在比较图像，请稍候…', invalid: '请选择有效图片文件（不超过 20 MB）。',
        loadError: '当前版本没有可授权的形态参考图集，因此不返回相似度；照片仅在本地处理。', imageError: '无法读取这张图片，请尝试其他文件。',
        summary: (count, elapsed) => `与 ${count} 张可读取的课程照片完成比对，用时 ${elapsed} 秒（当前设备实测）。`,
        candidate: '档案中的基础形态标签', nearest: '最近参考照片', support: '条正例',
        score: '颜色/布局相似度', noScores: '暂无可比较的基础形态标签。',
        caveat: '本工具不会确认上传的是蛇或西部猪鼻蛇；其他图片也可能得到相似度。所有课程标签尚未独立复核，且每种形态的样本都很少。下方百分比仅表示与最近一张带标签照片在颜色和粗略布局上的相似程度；背景、光线和裁剪会影响结果。系统保留“不确定”，不能据此判断基因型或隐性携带状态。',
        scoreMethod: '分数计算方式 ↘',
        modelEyebrow: '识别原理', modelTitle: '目前是谁在分析照片？',
        modelIntro: '实时照片筛查由浏览器中的 TypeScript 完成。独立的 Python 3/PyTorch 研究流程已复现旧 CNN 和论文定义的 FPPA 降噪算法；它尚未用基因标签训练。',
        step1Title: '本地图像特征', step1Text: '照片在内存中缩小，通过颜色分布与小型空间色块网格形成视觉描述。',
        step2Title: '寻找最近的档案照片', step2Text: '描述向量与目前可用的 21 张课程照片比较。每个百分比表示与最近一张带对应标签照片的相似度，不是 softmax 概率。',
        step3Title: '基础性状与拒绝判断', step3Text: '组合名会拆解为基础性状。“白墙”作为可见外观描述单独记录，不作为基因或模型输出；当前照片匹配器只比较历史档案中可映射的性状标签。',
        nextTitle: '已实现 · Python / PyTorch 训练流程', nextText: '旧 CNN 为 16/32/64 通道卷积块、128 单元全连接层和 0.5 dropout。训练器使用 ImageNet 预训练 MobileNetV3-Small 主干，替换为独立 sigmoid 性状输出，并用 masked BCE 忽略未知标签；评估按蛇只分组。训练门槛因缺少核实过的形态标签、蛇只 ID 与训练/评估授权而未满足。21 张课程照片的合成噪声实验只衡量图像重建。', benchmarkTitle: '本机推理基准 · Apple M5', benchmarkModel: '架构 / 输出层', benchmarkParams: '参数量', benchmarkSize: '权重状态大小', benchmarkCpu: 'CPU 中位数 / p95', benchmarkMps: 'MPS 中位数 / p95', benchmarkNote: '批量 1 · 224×224 RGB · 预热 10 次 · 计时 50 次 · PyTorch 2.14.0 / torchvision 0.29.0。权重为随机初始化；大小为未压缩 state_dict 序列化字节数。此设备上 MobileNet 参数更少、但速度更慢；此处使用默认 1,000 输出，训练器会替换为受支持的性状数。该基准不衡量分类准确度，也不是已训练模型的成绩。', portLink: '查看 MATLAB → Python 迁移说明 ↗',
        readyTitle: '先补齐数据，<br><em>再验证模型。</em>', speciesStat: '仅物种级参考照片'
    } : {
        nav: 'Analyze photo', navModel: 'How it works', method: 'How this works →',
        headline: 'Upload a hognose.<br><em>Explore its traits.</em>',
        hero: 'Compare a photo with the course archive in your browser. Explore visible clues and supporting examples while keeping genetic claims tied to evidence.',
        eyebrow: 'PHOTO ANALYSIS · LOCAL DEMO', title: 'Explore visible morph clues',
        intro: 'Use only a photo you know is a Western Hognose. This tool does not verify species. It compares image similarity and sample support, not genetic probabilities.',
        choose: 'Choose a photo to analyze', privacy: 'Runs in your browser. Your photo is not uploaded or saved.',
        resultEyebrow: 'LOCAL VISUAL SCREENING', resultTitle: 'Archive similarity', limited: 'Insufficient evidence · no call',
        processing: 'Comparing images…', invalid: 'Choose an image file no larger than 20 MB.',
        loadError: 'No rights-cleared morph reference archive is installed, so no similarity score is returned. Your photo stays local.', imageError: 'This image could not be read. Try another file.',
        summary: (count, elapsed) => `Compared with ${count} readable course photos in ${elapsed} s on this device.`,
        candidate: 'Base trait tag in archive', nearest: 'Nearest reference photo', support: 'positive example(s)',
        score: 'color/layout overlap', noScores: 'No base trait tags can be compared yet.',
        caveat: 'This tool cannot verify that the uploaded image is a snake or Western Hognose; other images can also receive similarity scores. All course labels remain independently unverified, and each trait has few examples. A percentage below measures color and coarse-layout similarity to the nearest tagged photo. Background, lighting, and crop affect the score. This uncertain visual screen cannot identify genotype or recessive carrier status.',
        scoreMethod: 'How scores are calculated ↘',
        modelEyebrow: 'UNDER THE HOOD', modelTitle: 'What is analyzing your photo?',
        modelIntro: 'The live photo screen is a TypeScript visual matcher running in your browser. A separate Python 3/PyTorch research pipeline reproduces the legacy CNN and paper-defined FPPA denoiser; it has not been trained on morph labels.',
        step1Title: 'Local image features', step1Text: 'Your photo is resized in memory. Color distribution and a small spatial color grid form its visual descriptor.',
        step2Title: 'Nearest archive photos', step2Text: 'The descriptor is compared with the 21 available course photos. Each percentage is similarity to the nearest photo carrying that tag, not a softmax probability.',
        step3Title: 'Base traits and abstention', step3Text: 'Combination names resolve to base traits. “White Wall” is kept as a visible-appearance descriptor, not a gene or model output; the photo matcher compares only historical tags that map to a genetic trait.',
        nextTitle: 'Implemented · Python / PyTorch training pipeline', nextText: 'The legacy CNN uses 16/32/64-channel convolution blocks, a 128-unit dense layer, and 0.5 dropout. The trainer uses an ImageNet-pretrained MobileNetV3-Small backbone with independent sigmoid trait outputs, masked BCE for unknown labels, and snake-grouped evaluation. Training has not run because reviewed morph labels, snake IDs, and training/evaluation rights are unavailable. The 21-image noise experiment measures reconstruction only.', benchmarkTitle: 'Local inference benchmark · Apple M5', benchmarkModel: 'Architecture / output head', benchmarkParams: 'Parameters', benchmarkSize: 'State size', benchmarkCpu: 'CPU median / p95', benchmarkMps: 'MPS median / p95', benchmarkNote: 'Batch 1 · 224×224 RGB · 10 warmups · 50 timed runs · PyTorch 2.14.0 / torchvision 0.29.0. Weights were random; size is uncompressed serialized state_dict bytes. MobileNet is smaller but slower on this setup. This benchmark uses its default 1,000-output head; the trainer replaces that head with the supported trait count. These timings do not measure accuracy or a trained classifier.', portLink: 'Read the MATLAB → Python migration ↗',
        readyTitle: 'Data first.<br><em>Validate models later.</em>', speciesStat: 'species-only reference photos'
    };
    const copyIds = {
        'nav-analyze': words.nav, 'nav-model': words.navModel, 'hero-method-link': words.method,
        'analyzer-eyebrow': words.eyebrow, 'analyzer-title': words.title,
        'analyzer-intro': words.intro, 'analyze-upload-text': words.choose,
        'analyzer-privacy': words.privacy, 'analysis-result-eyebrow': words.resultEyebrow,
        'analysis-result-title': words.resultTitle, 'analysis-method-link': words.scoreMethod,
        'model-eyebrow': words.modelEyebrow, 'model-title': words.modelTitle,
        'model-intro-text': words.modelIntro, 'model-step1-title': words.step1Title,
        'model-step1-text': words.step1Text, 'model-step2-title': words.step2Title,
        'model-step2-text': words.step2Text, 'model-step3-title': words.step3Title,
        'model-step3-text': words.step3Text, 'model-next-title': words.nextTitle,
        'model-next-text': words.nextText, 'model-benchmark-title': words.benchmarkTitle,
        'benchmark-model': words.benchmarkModel, 'benchmark-params': words.benchmarkParams,
        'benchmark-size': words.benchmarkSize, 'benchmark-cpu': words.benchmarkCpu,
        'benchmark-mps': words.benchmarkMps, 'model-benchmark-note': words.benchmarkNote,
        'model-port-link': words.portLink
    };
    $('#model-port-link').href = 'docs/matlab-to-python.md';
    Object.entries(copyIds).forEach(([id, value]) => { document.getElementById(id).textContent = value; });
    $('#hero-title').innerHTML = words.headline;
    $('.hero-copy > p').textContent = words.hero;
    $('.readiness-intro h2').innerHTML = words.readyTitle;
    $('#analyze-file').setAttribute('aria-label', words.choose);
    $('#stat-species-label').textContent = words.speciesStat;
    fetch('data/species_manifest.json').then((response) => response.ok ? response.json() : null).then((manifest) => {
        if (!manifest || manifest.scope !== 'species_only' || manifest.morph_training_eligible !== false)
            return;
        const count = Number(manifest.downloaded_photos);
        if (!Number.isInteger(count) || count < 1)
            return;
        $('#stat-species').textContent = String(count);
        $('#species-stat').hidden = false;
    }).catch(() => { });
    fetch('data/catalog.json').then((response) => response.ok ? response.json() : null).then((catalog) => {
        if (catalog?.images?.some((item) => item.available))
            return;
        const fallback = zh
            ? {
                hero: '此副本没有随附经授权的形态参考集。你仍可在本地整理照片与来源；在加入经过授权和复核的参考图之前，不显示相似度或基因判断。',
                intro: '当前没有可授权的形态参考图集。你选择的照片会保留在浏览器，不会上传；在参考集就绪前不返回相似度或基因判断。',
                method: '此副本没有安装形态参考集。只有加入经授权、可追溯且经过复核的图片后，才会启用视觉相似度筛查。',
                eyebrow: '本地整理 · 尚无形态参考集',
                stamp: '无形态<br>参考图'
            }
            : {
                hero: 'This copy does not include a rights-cleared morph reference set. You can still curate photos and sources locally; no similarity or gene result appears until authorized, reviewed references are added.',
                intro: 'No rights-cleared morph reference archive is installed. Your selected photo stays in the browser and is not uploaded; no similarity or gene result is returned until the reference set is ready.',
                method: 'No morph reference archive is installed in this copy. Visual similarity screening stays unavailable until authorized, traceable, reviewed images are added.',
                eyebrow: 'LOCAL REVIEW · NO MORPH ARCHIVE',
                stamp: 'NO MORPH<br>ARCHIVE'
            };
        $('.hero-copy > p').textContent = fallback.hero;
        $('#analyzer-intro').textContent = fallback.intro;
        $('#model-step2-text').textContent = fallback.method;
        $('#analyzer-eyebrow').textContent = fallback.eyebrow;
        $('#hero-stamp-count').textContent = '0';
        $('.hero-stamp span').innerHTML = fallback.stamp;
    }).catch(() => { });
    fetch('data/catalog.json').then((response) => response.ok ? response.json() : null).then((catalog) => {
        const hasArchive = catalog?.images?.some((item) => item.available) === true;
        if (hasArchive)
            return;
        const text = zh
            ? {
                hero: '可授权的猪鼻蛇形态图集未随此副本发布。你仍可在本地整理图片与来源；在加入经过授权和复核的参考集前，不显示相似度或基因判断。',
                intro: '当前副本没有可授权的形态参考图集。选择照片后会保留在浏览器本地，不会上传；在参考集就绪前不返回相似度或基因判断。',
                method: '此副本没有安装形态参考集。加入经授权、可追溯且复核过的图片后，才会启用视觉相似度筛查。'
            }
            : {
                hero: 'A rights-cleared morph photo archive is not bundled with this copy. You can still curate photos and provenance locally; no similarity or gene result appears until reviewed, authorized references are added.',
                intro: 'This copy has no rights-cleared morph reference archive. Your selected photo stays in the browser and is not uploaded; no similarity or gene result is returned until the reference set is ready.',
                method: 'No morph reference archive is installed in this copy. Visual similarity screening stays unavailable until authorized, traceable, reviewed images are added.'
            };
        $('.hero-copy > p').textContent = text.hero;
        $('#analyzer-intro').textContent = text.intro;
        $('#model-step2-text').textContent = text.method;
        $('#analyzer-eyebrow').textContent = zh ? '本地整理 · 尚无形态参考集' : 'LOCAL REVIEW · NO MORPH ARCHIVE';
    }).catch(() => { });
    let previewUrl;
    let archivePromise;
    let requestId = 0;
    async function readImage(source) {
        const image = new Image();
        image.decoding = 'async';
        image.src = source;
        await image.decode();
        return image;
    }
    function descriptor(image) {
        const canvas = document.createElement('canvas');
        canvas.width = 48;
        canvas.height = 48;
        const context = canvas.getContext('2d', { willReadFrequently: true });
        context.fillStyle = '#f5f3eb';
        context.fillRect(0, 0, 48, 48);
        const scale = Math.min(48 / image.naturalWidth, 48 / image.naturalHeight);
        const width = image.naturalWidth * scale;
        const height = image.naturalHeight * scale;
        context.drawImage(image, (48 - width) / 2, (48 - height) / 2, width, height);
        const rgba = context.getImageData(0, 0, 48, 48).data;
        const histogram = new Float32Array(24);
        const grid = new Float32Array(4 * 4 * 3);
        for (let y = 0; y < 48; y += 1) {
            for (let x = 0; x < 48; x += 1) {
                const pixel = (y * 48 + x) * 4;
                const cell = (Math.floor(y / 12) * 4 + Math.floor(x / 12)) * 3;
                for (let channel = 0; channel < 3; channel += 1) {
                    const value = rgba[pixel + channel];
                    histogram[channel * 8 + Math.min(7, Math.floor(value / 32))] += 1 / 2304;
                    grid[cell + channel] += value / (255 * 144);
                }
            }
        }
        return { histogram, grid };
    }
    function similarity(a, b) {
        let histDistance = 0;
        let gridDistance = 0;
        for (let i = 0; i < a.histogram.length; i += 1)
            histDistance += Math.abs(a.histogram[i] - b.histogram[i]);
        for (let i = 0; i < a.grid.length; i += 1)
            gridDistance += Math.abs(a.grid[i] - b.grid[i]);
        // Both distances are normalized to [0, 1]. This is a descriptor overlap, not a probability.
        const distance = .65 * (histDistance / 6) + .35 * (gridDistance / 48);
        return Math.max(0, Math.min(100, 100 * (1 - distance)));
    }
    async function loadArchive() {
        const [catalog, ontology] = await Promise.all([
            fetch('data/catalog.json').then((response) => {
                if (!response.ok)
                    throw new Error('catalog unavailable');
                return response.json();
            }),
            fetch('data/ontology.json').then((response) => response.ok ? response.json() : null).catch(() => null)
        ]);
        const records = await Promise.all(catalog.images.filter((item) => item.available).map(async (item) => {
            try {
                return { item, feature: descriptor(await readImage(item.image)) };
            }
            catch (error) {
                console.warn('Archive image unavailable:', item.id, error);
                return null;
            }
        }));
        return { catalog, ontology, records: records.filter(Boolean) };
    }
    const fallbackMap = { b: 'anaconda', c: 'arctic', d: 'arctic', e: 'anaconda', g: 'albino', h: 'toffee-belly', i: 'lavender', k: 'axanthic', m: 'sable', p: 'extreme-red' };
    function baseTrait(label, ontology) {
        const mapped = ontology?.legacy_label_map?.[label.id];
        const traitId = mapped?.trait_id || fallbackMap[label.id];
        if (!traitId)
            return null;
        const trait = ontology?.traits?.find((item) => item.id === traitId);
        if (trait && (trait.photo_inferable === false || trait.photo_inferable === 'unverified'))
            return null;
        const fallbackName = label.id === 'd' ? (zh ? '北极' : 'Arctic') : label.id === 'e' ? (zh ? '康达' : 'Anaconda') : null;
        return { id: traitId, name: (zh ? trait?.name_zh : trait?.name_en) || fallbackName || (zh ? label.name_zh : label.name_en) };
    }
    function renderCandidates(feature, archive) {
        const byId = new Map();
        for (const label of archive.catalog.labels) {
            const trait = baseTrait(label, archive.ontology);
            if (!trait)
                continue;
            const examples = archive.records.filter(({ item }) => item.labels[label.id] === 1);
            if (!examples.length)
                continue;
            const existing = byId.get(trait.id) || { ...trait, examples: new Map() };
            for (const example of examples)
                existing.examples.set(example.item.id, example);
            byId.set(trait.id, existing);
        }
        const ranked = [...byId.values()].map((trait) => {
            const neighbors = [...trait.examples.values()].map((entry) => ({ entry, score: similarity(feature, entry.feature) }));
            neighbors.sort((a, b) => b.score - a.score);
            return { ...trait, support: neighbors.length, best: neighbors[0] };
        }).sort((a, b) => b.best.score - a.best.score).slice(0, 4);
        const host = $('#analysis-candidates');
        host.replaceChildren();
        if (!ranked.length) {
            host.textContent = words.noScores;
            return;
        }
        for (const trait of ranked) {
            const row = document.createElement('article');
            row.className = 'analysis-candidate';
            const heading = document.createElement('div');
            heading.className = 'analysis-candidate-heading';
            const name = document.createElement('strong');
            name.textContent = `${words.candidate}: ${trait.name}`;
            const percent = document.createElement('span');
            percent.textContent = `${Math.round(trait.best.score)}% ${words.score}`;
            heading.append(name, percent);
            const track = document.createElement('div');
            track.className = 'analysis-track';
            const fill = document.createElement('i');
            fill.style.width = `${trait.best.score}%`;
            track.append(fill);
            const detail = document.createElement('p');
            detail.textContent = `${words.nearest}: ${trait.best.entry.item.id} · ${trait.support} ${words.support}`;
            row.append(heading, track, detail);
            host.append(row);
        }
    }
    const input = $('#analyze-file');
    input.addEventListener('change', async () => {
        const file = input.files?.[0];
        if (!file)
            return;
        const currentRequest = ++requestId;
        const result = $('#analysis-result');
        result.hidden = false;
        result.scrollIntoView({ behavior: 'smooth', block: 'start' });
        $('#analysis-evidence').textContent = words.limited;
        $('#analysis-candidates').replaceChildren();
        $('#analysis-caveat').textContent = '';
        if (!file.type.startsWith('image/') || file.size > 20 * 1024 * 1024) {
            $('#analysis-summary').textContent = words.invalid;
            $('#analysis-preview').removeAttribute('src');
            $('#analysis-file-name').textContent = '';
            input.value = '';
            return;
        }
        if (previewUrl)
            URL.revokeObjectURL(previewUrl);
        previewUrl = URL.createObjectURL(file);
        $('#analysis-preview').src = previewUrl;
        $('#analysis-preview').alt = zh ? '所选照片预览' : 'Selected photo preview';
        $('#analysis-file-name').textContent = file.name;
        $('#analysis-summary').textContent = words.processing;
        const start = performance.now();
        try {
            const image = await readImage(previewUrl);
            const feature = descriptor(image);
            archivePromise ||= loadArchive();
            const archive = await archivePromise;
            if (currentRequest !== requestId)
                return;
            if (!archive.records.length)
                throw new Error('no readable archive images');
            renderCandidates(feature, archive);
            $('#analysis-summary').textContent = words.summary(archive.records.length, ((performance.now() - start) / 1000).toFixed(2));
            $('#analysis-caveat').textContent = words.caveat;
        }
        catch (error) {
            if (currentRequest !== requestId)
                return;
            console.error('Visual screening failed:', error);
            $('#analysis-summary').textContent = error.message === 'no readable archive images' || error.message === 'catalog unavailable' ? words.loadError : words.imageError;
            archivePromise = null;
        }
        input.value = '';
    });
})();
export {};
