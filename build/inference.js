"use strict";
// Live analysis uses the configured multimodal service. Research models are separate.
(() => {
    const q = (selector) => document.querySelector(selector);
    const zh = new URLSearchParams(location.search).get('lang') === 'zh';
    const tr = (en, cn) => zh ? cn : en;
    const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const copy = {
        'nav-analyze': tr('Analyze photo', '分析照片'), 'nav-model': tr('How it works', '识别原理'),
        'hero-method-link': tr('How this works →', '识别原理 →'),
        'analyzer-eyebrow': tr('MULTIMODAL PHOTO ANALYSIS', '多模态照片分析'),
        'analyzer-title': tr('Explore visible morph clues', '探索可见形态线索'),
        'analyzer-intro': tr('Upload a Western Hognose photo. The configured vision model observes its traits, then compares real reference photos.', '上传西部猪鼻蛇照片。视觉模型先观察性状，再与真实参考照片进行比较。'),
        'analyze-upload-text': tr('Choose a photo', '选择照片'),
        'analysis-result-eyebrow': tr('PHOTO EVIDENCE', '照片证据'),
        'analysis-result-title': tr('Phenotype candidates', '表型候选'),
        'analysis-method-link': tr('How the model reasons ↘', '模型如何判断 ↘'),
        'model-eyebrow': tr('UNDER THE HOOD', '识别原理'),
        'model-title': tr('A vision model, real references.', '视觉模型与真实参考图。'),
        'model-intro-text': tr('A pretrained vision model observes your photo and compares real references. The local demo uses Ollama qwen3-vl:4b-instruct; the hosted demo uses a configured OpenAI-compatible vision API.', '预训练视觉模型观察照片并比较真实参考图。本机版使用 Ollama qwen3-vl:4b-instruct，线上版使用配置的 OpenAI 兼容视觉 API。'),
        'model-step1-title': tr('Observe the photo', '观察照片'),
        'model-step1-text': tr('The vision model checks the subject and describes visible pattern and color evidence. Ambiguous or unsuitable images can receive no call.', '视觉模型检查主体，描述可见花纹与颜色依据；模糊或不适合的图片可以拒绝判断。'),
        'model-step2-title': tr('Compare real references', '比较真实参考图'),
        'model-step2-text': tr('The server selects up to three relevant photos from the packaged labeled photo library. A second model pass compares these images and revises the candidates.', '服务端从随项目提供的已标注实拍库中选择最多三张相关照片，再由模型比较并修正候选。'),
        'model-step3-title': tr('Resolve atomic traits', '拆解基础性状'),
        'model-step3-text': tr('The server validates seven supported traits and resolves trade names through the ontology: Sunburst = Albino + Sable. Evidence strength is not a probability; carrier states cannot be inferred from a photo.', '服务端校验七类支持性状，通过本体解析别名：Sunburst = Albino + Sable。证据强弱不代表概率；照片无法推断隐性携带状态。'),
        'model-next-title': tr('Separate research modules', '独立研究模块'),
        'model-next-text': tr('The historical CNN, FPPA denoiser, and MobileNetV3 trainer remain available for research. They do not produce these live results. The reference library has no established independent test set.', '历史 CNN、FPPA 降噪算法和 MobileNetV3 训练器保留用于研究，不承担实时判断。参考图库尚未建立独立测试集。'),
        'model-benchmark-title': tr('Archived architecture timing · random weights', '历史架构计时 · 随机权重'),
        'model-benchmark-note': tr('These archived CPU/MPS timings use randomly initialized research models. They do not measure the multimodal service or classification accuracy. Each live analysis reports its actual service time and configured model.', '这些历史 CPU/MPS 计时使用随机初始化研究模型，不代表多模态服务速度或分类准确率。每次实时分析均显示实际服务耗时与配置模型。'),
        'model-port-link': tr('MATLAB → Python research migration ↗', 'MATLAB → Python 研究迁移 ↗')
    };
    for (const [id, text] of Object.entries(copy))
        if (document.getElementById(id))
            document.getElementById(id).textContent = text;
    buttonCopy();
    function buttonCopy() { q('#analyze-submit').textContent = tr('Analyze photo', '分析照片'); q('#analyze-refresh').textContent = tr('Refresh model', '刷新模型'); }
    q('#hero-title').innerHTML = tr('Upload a hognose.<br><em>Explore its traits.</em>', '上传猪鼻蛇照片。<br><em>探索可见表型。</em>');
    q('.hero-copy > p').textContent = tr('Explore phenotype candidates, atomic traits, visible evidence, and real photo comparisons with a configured multimodal model.', '通过配置的多模态模型，查看表型候选、基础性状、可见依据与真实照片对照。');
    q('#analysis-caveat').textContent = tr('Photo-based assistance cannot establish genotype or recessive carrier status. Evidence levels are qualitative, not calibrated probabilities.', '照片辅助判断不能确认基因型或隐性携带状态。证据等级是定性描述，不是校准概率。');
    let selected = null;
    let previewUrl = null;
    let busy = false;
    let ready = false;
    const button = q('#analyze-submit');
    const statusNode = q('#analyzer-status');
    function message(text) { q('#analysis-summary').textContent = text; }
    function serviceMessage(code, fallback, model) {
        if (!zh)
            return textList(fallback) || 'The model service is unavailable.';
        const messages = {
            ready: '模型服务已就绪。',
            cloud_model_not_configured: '线上识别尚未连接模型服务，图库可以正常浏览。',
            invalid_image: '图片无法读取或上传格式无效，请选择一张不超过 20 MB 的有效图片。',
            references_unavailable: '演示参考图集无法读取，请按 README 检查完整安装。',
            model_not_configured: '模型配置无效，请按 README 设置 HOGMORPH_PROVIDER、HOGMORPH_MODEL 与 HOGMORPH_BASE_URL。',
            provider_error: '模型服务拒绝请求，请检查服务配置与访问权限。',
            model_timeout: '模型响应超时，请重试或调整服务端等待时间。',
            model_unavailable: '无法连接模型服务，请检查服务已启动且地址正确。',
            model_missing: model ? `尚未安装配置模型，请运行 ollama pull ${model}；云端模式请检查模型名称。` : '配置的模型未安装或不在服务模型列表中，请按 README 检查模型配置。',
            model_not_vision: '配置的模型不支持图片，请选择支持视觉输入的模型。',
            invalid_model_output: '模型返回的结果格式无效或包含不支持的性状，请重试。'
        };
        return messages[code] || '服务未能完成分析，请检查模型配置或稍后重试。';
    }
    async function checkStatus() {
        statusNode.textContent = tr('Checking model…', '正在检查模型…');
        try {
            const response = await fetch('/api/status');
            if (!response.ok)
                throw new Error('unavailable');
            const status = await response.json();
            ready = status.ready === true;
            statusNode.textContent = `${ready ? tr('Model ready', '模型就绪') : tr('Model unavailable', '模型不可用')} · ${status.model || '—'}${!ready && status.message ? ' · ' + serviceMessage(status.code, status.message, status.model) : ''}`;
            q('#analyzer-privacy').textContent = status.provider === 'ollama'
                ? tr('Analysis sends your photo to the local server and local Ollama. Uploads are released after processing.', '分析会将照片发送至本机服务与本机 Ollama，处理后释放上传数据。')
                : tr('Cloud mode: analysis sends your photo to the configured vision API. Uploads are released after processing.', '云端模式：分析会将照片发送至配置的视觉 API，处理后释放上传数据。');
        }
        catch {
            ready = false;
            statusNode.textContent = tr('Model unavailable. Start the demo server and configure the model.', '模型不可用。请启动演示服务并配置模型。');
            q('#analyzer-privacy').textContent = tr('Selecting a photo only previews it locally. Configure a model before analysis.', '选择照片仅在本地预览，配置模型后才可分析。');
        }
        button.disabled = !ready || !selected || busy;
        return ready;
    }
    q('#analyze-refresh').addEventListener('click', () => checkStatus());
    q('#analyze-file').addEventListener('change', async (event) => {
        const file = event.target.files?.[0];
        if (!file || busy)
            return;
        selected = null;
        button.disabled = true;
        q('#analysis-result').hidden = false;
        q('#analysis-candidates').replaceChildren();
        q('#analysis-evidence').textContent = tr('Preview', '预览');
        if (!file.type.startsWith('image/') || file.size > 20 * 1024 * 1024) {
            message(tr('Choose an image no larger than 20 MB.', '请选择不超过 20 MB 的图片。'));
            return;
        }
        if (previewUrl)
            URL.revokeObjectURL(previewUrl);
        previewUrl = URL.createObjectURL(file);
        try {
            const preview = q('#analysis-preview');
            preview.src = previewUrl;
            await preview.decode();
            selected = file;
            q('#analysis-file-name').textContent = file.name;
            message(tr('Preview ready. Select Analyze when the model is ready.', '预览就绪。模型就绪后点击分析。'));
            button.disabled = !ready;
        }
        catch {
            message(tr('This image could not be read. Try another file.', '无法读取图片，请尝试其他文件。'));
        }
    });
    function textList(value) { return Array.isArray(value) ? value.map(v => String(v)).join(' · ') : String(value ?? ''); }
    function traitName(trait) {
        const names = { 'anaconda': tr('Anaconda', '康达'), 'arctic': tr('Arctic', '北极'), 'albino': tr('Albino', '白化'), 'axanthic': tr('Axanthic', '缺黄'), 'sable': tr('Sable', '紫貂'), 'toffee_belly': tr('Toffee Belly', '太妃糖腹'), 'lavender': tr('Lavender', '薰衣草') };
        const base = names[trait.trait_id] || trait.trait_id;
        return /super|homozygous/.test(trait.state) && ['anaconda', 'arctic'].includes(trait.trait_id) ? (zh ? '超级' + base : 'Super ' + base) : base;
    }
    function render(result) {
        q('#analysis-candidates').replaceChildren();
        const statusNames = { candidates: tr('Candidate evidence', '候选证据'), non_target: tr('Non-target subject', '非目标主体'), insufficient_evidence: tr('Insufficient evidence', '证据不足') };
        q('#analysis-evidence').textContent = statusNames[result.status] || tr('No call', '暂不判断');
        message(`${textList(result.assessment?.reason) + ' ' + textList(result.assessment?.observations)} · ${result.model || '—'} · ${Number(result.elapsed_seconds || 0).toFixed(1)} ${tr('seconds', '秒')}`);
        if (result.limitations?.length)
            q('#analysis-caveat').textContent = textList(result.limitations) + ' ' + tr('Evidence levels are qualitative, not probabilities. A photo cannot confirm genotype or carrier status.', '证据等级是定性描述，不代表概率；照片不能确认基因型或携带状态。');
        for (const candidate of (result.candidates || []).slice(0, 3)) {
            const article = document.createElement('article');
            article.className = 'analysis-candidate';
            const support = { strong: tr('Strong evidence', '较强证据'), moderate: tr('Moderate evidence', '一般证据'), weak: tr('Weak evidence', '较弱证据') };
            const refs = (candidate.references || []).filter(ref => (candidate.reference_ids || []).includes(ref.id));
            article.innerHTML = `<div class="analysis-candidate-heading"><strong>${esc(candidate.rank)}. ${esc(zh ? candidate.name_zh : candidate.name_en)}</strong><span>${esc(support[candidate.support_level] || support.weak)}</span></div><div class="analysis-traits">${(candidate.traits || []).map(t => `<span class="label-chip positive">${esc(traitName(t))}</span>`).join('')}</div><p><b>${tr('Visible evidence', '可见依据')}:</b> ${esc(textList(candidate.visible_evidence))}</p><p><b>${tr('Uncertainties', '不确定项')}:</b> ${esc(textList(candidate.uncertainties))}</p><div class="analysis-reference-photos">${refs.map(ref => `<figure><img src="${esc(ref.image)}" alt="${esc(ref.id)}" loading="lazy"><figcaption>${esc(ref.id)} · ${esc(zh ? ref.name_zh : ref.name_en)}</figcaption></figure>`).join('')}</div>`;
            q('#analysis-candidates').append(article);
        }
    }
    button.addEventListener('click', async () => {
        if (busy || !selected)
            return;
        busy = true;
        button.disabled = true;
        q('#analyze-file').disabled = true;
        q('#analysis-candidates').replaceChildren();
        try {
            if (!await checkStatus()) {
                message(tr('Model unavailable. No analysis was performed.', '模型不可用，未进行分析。'));
                return;
            }
            q('#analysis-evidence').textContent = tr('Analyzing', '分析中');
            message(tr('Model working: observing your photo and comparing reference images. Waiting for the two-stage result…', '模型正在处理：观察照片并比较参考图，等待两阶段结果…'));
            const form = new FormData();
            form.append('image', selected);
            form.append('lang', zh ? 'zh' : 'en');
            const response = await fetch('/api/analyze', { method: 'POST', body: form });
            const result = await response.json();
            if (!response.ok)
                throw new Error(serviceMessage(result.detail?.code, result.detail?.message || result.detail || result.error));
            render(result);
        }
        catch (error) {
            q('#analysis-evidence').textContent = tr('Analysis unavailable', '分析不可用');
            message(error instanceof TypeError ? tr('Cannot connect to the analysis service. Check that the demo server is running.', '无法连接分析服务，请检查演示服务已启动。') : error instanceof Error ? error.message : tr('The service could not return a valid result.', '服务未能返回有效结果。'));
        }
        finally {
            busy = false;
            q('#analyze-file').disabled = false;
            button.disabled = !ready || !selected;
        }
    });
    checkStatus();
})();
