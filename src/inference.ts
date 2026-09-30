// Live analysis uses the configured multimodal service. Research models are separate.
(() => {
  const q = (selector: string): any => document.querySelector(selector);
  const zh = new URLSearchParams(location.search).get('lang') === 'zh';
  const tr = (en: string, cn: string) => zh ? cn : en;
  const esc = (v: unknown) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const copy: Record<string,string> = {
    'nav-analyze':tr('Analyze photo','分析照片'),'nav-model':tr('How it works','识别原理'),
    'hero-method-link':tr('How this works →','识别原理 →'),
    'analyzer-eyebrow':tr('MULTIMODAL PHOTO ANALYSIS','多模态照片分析'),
    'analyzer-title':tr('Explore visible morph clues','探索可见形态线索'),
    'analyzer-intro':tr('Upload a Western Hognose photo. The configured vision model observes its traits, then compares real reference photos.','上传西部猪鼻蛇照片。视觉模型先观察性状，再与真实参考照片进行比较。'),
    'analyze-upload-text':tr('Choose a photo','选择照片'),
    'analysis-result-eyebrow':tr('PHOTO EVIDENCE','照片证据'),
    'analysis-result-title':tr('Phenotype candidates','表型候选'),
    'analysis-method-link':tr('How the model reasons ↘','模型如何判断 ↘'),
    'model-eyebrow':tr('UNDER THE HOOD','识别原理'),
    'model-title':tr('A vision model, real references.','视觉模型与真实参考图。'),
    'model-intro-text':tr('The live demo uses a pretrained multimodal model through Python/FastAPI. Ollama qwen3-vl:4b-instruct is the default; an OpenAI-compatible vision endpoint can also be configured. No morph classifier is trained by this demo.','实时演示通过 Python/FastAPI 调用预训练多模态模型，默认使用 Ollama qwen3-vl:4b-instruct，也支持配置 OpenAI 兼容视觉接口。本演示没有训练专用形态分类器。'),
    'model-step1-title':tr('Observe the photo','观察照片'),
    'model-step1-text':tr('The vision model checks the subject and describes visible pattern and color evidence. Ambiguous or unsuitable images can receive no call.','视觉模型检查主体，描述可见花纹与颜色依据；模糊或不适合的图片可以拒绝判断。'),
    'model-step2-title':tr('Compare real references','比较真实参考图'),
    'model-step2-text':tr('The server selects up to three relevant photos from 18 approved course references. A second model pass compares these images and revises the candidates.','服务端从 18 张已确认可用的课程参考图中选择最多三张相关照片，再由模型比较并修正候选。'),
    'model-step3-title':tr('Resolve atomic traits','拆解基础性状'),
    'model-step3-text':tr('The server validates seven supported traits and resolves trade names through the ontology: Sunburst = Albino + Sable. Evidence strength is not a probability; carrier states cannot be inferred from a photo.','服务端校验七类支持性状，通过本体解析别名：Sunburst = Albino + Sable。证据强弱不代表概率；照片无法推断隐性携带状态。'),
    'model-next-title':tr('Separate research modules','独立研究模块'),
    'model-next-text':tr('The historical CNN, FPPA denoiser, and MobileNetV3 trainer remain available for research. They do not produce these live results. The small reference set cannot establish independent classification accuracy.','历史 CNN、FPPA 降噪算法和 MobileNetV3 训练器保留用于研究，不承担实时判断。小规模参考集不能证明独立分类准确率。'),
    'model-benchmark-title':tr('Archived architecture timing · random weights','历史架构计时 · 随机权重'),
    'model-benchmark-note':tr('These archived CPU/MPS timings use randomly initialized research models. They do not measure the multimodal service or classification accuracy. Each live analysis reports its actual service time and configured model.','这些历史 CPU/MPS 计时使用随机初始化研究模型，不代表多模态服务速度或分类准确率。每次实时分析均显示实际服务耗时与配置模型。'),
    'model-port-link':tr('MATLAB → Python research migration ↗','MATLAB → Python 研究迁移 ↗')
  };
  for (const [id,text] of Object.entries(copy)) if(document.getElementById(id)) document.getElementById(id).textContent = text;
  buttonCopy();
  function buttonCopy(){q('#analyze-submit').textContent=tr('Analyze photo','分析照片');q('#analyze-refresh').textContent=tr('Refresh model','刷新模型');}
  q('#hero-title').innerHTML=tr('Upload a hognose.<br><em>Explore its traits.</em>','上传猪鼻蛇照片。<br><em>探索可见表型。</em>');
  q('.hero-copy > p').textContent=tr('Explore phenotype candidates, atomic traits, visible evidence, and real photo comparisons with a configured multimodal model.','通过配置的多模态模型，查看表型候选、基础性状、可见依据与真实照片对照。');
  q('#analysis-caveat').textContent=tr('Photo-based assistance cannot establish genotype or recessive carrier status. Evidence levels are qualitative, not calibrated probabilities. Reference comparisons are not an independent accuracy test.','照片辅助判断不能确认基因型或隐性携带状态。证据等级是定性描述，不是校准概率；参考图对照不是独立准确率测试。');
  let selected: File | null = null;
  let previewUrl: string | null = null;
  let busy=false;
  let ready=false;
  const button: HTMLButtonElement=q('#analyze-submit');
  const statusNode=q('#analyzer-status');
  function message(text:string) {q('#analysis-summary').textContent=text;}
  async function checkStatus() {
    statusNode.textContent=tr('Checking model…','正在检查模型…');
    try {
      const response=await fetch('/api/status');
      if(!response.ok) throw new Error('unavailable');
      const status=await response.json();
      ready=status.ready===true;
      statusNode.textContent=`${ready ? tr('Model ready','模型就绪') : tr('Model unavailable','模型不可用')} · ${status.model || '—'}${!ready && status.message ? ' · '+status.message : ''}`;
      q('#analyzer-privacy').textContent=status.provider==='ollama'
        ? tr('Analysis sends your photo to the local server and local Ollama. Uploads are released after processing.','分析会将照片发送至本机服务与本机 Ollama，处理后释放上传数据。')
        : tr('Cloud mode: analysis sends your photo to the configured vision API. Uploads are released after processing.','云端模式：分析会将照片发送至配置的视觉 API，处理后释放上传数据。');
    } catch {
      ready=false;
      statusNode.textContent=tr('Model unavailable. Start the demo server and configure the model.','模型不可用。请启动演示服务并配置模型。');
      q('#analyzer-privacy').textContent=tr('Selecting a photo only previews it locally. Configure a model before analysis.','选择照片仅在本地预览，配置模型后才可分析。');
    }
    button.disabled=!ready || !selected || busy;
    return ready;
  }
  q('#analyze-refresh').addEventListener('click',()=>checkStatus());
  q('#analyze-file').addEventListener('change',async(event)=>{
    const file=event.target.files?.[0];
    if(!file || busy) return;
    selected=null; button.disabled=true;
    q('#analysis-result').hidden=false;
    q('#analysis-candidates').replaceChildren();
    q('#analysis-evidence').textContent=tr('Preview','预览');
    if(!file.type.startsWith('image/') || file.size>20*1024*1024) {message(tr('Choose an image no larger than 20 MB.','请选择不超过 20 MB 的图片。'));return;}
    if(previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl=URL.createObjectURL(file);
    try {
      const preview:HTMLImageElement=q('#analysis-preview');
      preview.src=previewUrl;
      await preview.decode();
      selected=file;
      q('#analysis-file-name').textContent=file.name;
      message(tr('Preview ready. Select Analyze when the model is ready.','预览就绪。模型就绪后点击分析。'));
      button.disabled=!ready;
    } catch {message(tr('This image could not be read. Try another file.','无法读取图片，请尝试其他文件。'));}
  });
  function textList(value:unknown):string {return Array.isArray(value)?value.map(v=>String(v)).join(' · '):String(value??'');}
  function traitName(trait:any):string {
    const names={'anaconda':tr('Anaconda','康达'),'arctic':tr('Arctic','北极'),'albino':tr('Albino','白化'),'axanthic':tr('Axanthic','缺黄'),'sable':tr('Sable','紫貂'),'toffee_belly':tr('Toffee Belly','太妃糖腹'),'lavender':tr('Lavender','薰衣草')};
    const base=names[trait.trait_id]||trait.trait_id;
    return /super|homozygous/.test(trait.state) && ['anaconda','arctic'].includes(trait.trait_id) ? (zh?'超级'+base:'Super '+base) : base;
  }
  function render(result:any) {
    q('#analysis-candidates').replaceChildren();
    const statusNames={candidates:tr('Candidate evidence','候选证据'),non_target:tr('Non-target subject','非目标主体'),insufficient_evidence:tr('Insufficient evidence','证据不足')};
    q('#analysis-evidence').textContent=statusNames[result.status]||tr('No call','暂不判断');
    message(`${textList(result.assessment?.reason)+' '+textList(result.assessment?.observations)} · ${result.model || '—'} · ${Number(result.elapsed_seconds || 0).toFixed(1)} ${tr('seconds','秒')}`);
    if(result.limitations?.length) q('#analysis-caveat').textContent=textList(result.limitations)+' '+tr('Evidence levels are qualitative, not probabilities. A photo cannot confirm genotype or carrier status.','证据等级是定性描述，不代表概率；照片不能确认基因型或携带状态。');
    for(const candidate of (result.candidates||[]).slice(0,3)) {
      const article=document.createElement('article'); article.className='analysis-candidate';
      const support={strong:tr('Strong evidence','较强证据'),moderate:tr('Moderate evidence','一般证据'),weak:tr('Weak evidence','较弱证据')};
      const refs=(candidate.references||[]).filter(ref=>(candidate.reference_ids||[]).includes(ref.id));
      article.innerHTML=`<div class="analysis-candidate-heading"><strong>${esc(candidate.rank)}. ${esc(zh?candidate.name_zh:candidate.name_en)}</strong><span>${esc(support[candidate.support_level]||support.weak)}</span></div><div class="analysis-traits">${(candidate.traits||[]).map(t=>`<span class="label-chip positive">${esc(traitName(t))}</span>`).join('')}</div><p><b>${tr('Visible evidence','可见依据')}:</b> ${esc(textList(candidate.visible_evidence))}</p><p><b>${tr('Uncertainties','不确定项')}:</b> ${esc(textList(candidate.uncertainties))}</p><div class="analysis-reference-photos">${refs.map(ref=>`<figure><img src="${esc(ref.image)}" alt="${esc(ref.id)}" loading="lazy"><figcaption>${esc(ref.id)} · ${esc(zh?ref.name_zh:ref.name_en)}</figcaption></figure>`).join('')}</div>`;
      q('#analysis-candidates').append(article);
    }
  }
  button.addEventListener('click',async()=>{
    if(busy||!selected) return;
    busy=true; button.disabled=true; q('#analyze-file').disabled=true;
    q('#analysis-candidates').replaceChildren();
    try {
      if(!await checkStatus()) {message(tr('Model unavailable. No analysis was performed.','模型不可用，未进行分析。'));return;}
      q('#analysis-evidence').textContent=tr('Analyzing','分析中');
      message(tr('Model working: observing your photo and comparing reference images. Waiting for the two-stage result…','模型正在处理：观察照片并比较参考图，等待两阶段结果…'));
      const form=new FormData();form.append('image',selected);form.append('lang',zh?'zh':'en');
      const response=await fetch('/api/analyze',{method:'POST',body:form});
      const result=await response.json();
      if(!response.ok) throw new Error(textList(result.detail?.message||result.detail||result.error)||tr('Analysis failed.','分析失败。'));
      render(result);
    } catch(error) {
      q('#analysis-evidence').textContent=tr('Analysis unavailable','分析不可用');
      message(error instanceof Error?error.message:tr('The service could not return a valid result.','服务未能返回有效结果。'));
    } finally {busy=false; q('#analyze-file').disabled=false;button.disabled=!ready||!selected;}
  });
  checkStatus();
})();
