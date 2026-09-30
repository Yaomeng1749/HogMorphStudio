const STORE = "hogmorph.incoming-review.v1:";
const Identity = window.HogMorphReviewIdentity;
let rows = [], excludedRows = [], ontology = null, selected = null, english = true;
const $ = (id) => document.getElementById(id);
const text = (en, zh) => english ? en : zh;
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function read(sha) { try { return JSON.parse(localStorage.getItem(STORE + sha) || "{}"); } catch { return {}; } }
function save(data) { localStorage.setItem(STORE + selected.sha256, JSON.stringify(data)); }
function triageName(v) { return v === "candidate_western_hognose" ? text("Candidate", "候选") : text("Uncertain", "待确认"); }
function reviewState(data) {
  if (data.review_status === "reviewed") return text("Reviewed", "已复核");
  const editableFields=["species_review","source_scope","individual_id","source_url","evidence_type","evidence_url","claim_scope","image_rights","rights_evidence_url","rights_reviewed_by","attribution","reviewer","review_status","notes"];
  const hasText=editableFields.some(key=>typeof data[key]==="string"&&Boolean(data[key].trim()));
  const hasLabels=Array.isArray(data.morph_labels)&&data.morph_labels.length>0;
  const hasAliases=Array.isArray(data.aliases)&&data.aliases.length>0;
  const hasRights=Boolean(data.rights_scopes)&&Object.values(data.rights_scopes).some(value=>typeof value==="boolean");
  if (hasText||hasLabels||hasAliases||hasRights) return text("In progress", "进行中");
  return text("Not reviewed", "未复核");
}
function renderProgress() {
  const total=rows.length;
  const records=rows.map(r=>read(r.sha256));
  const count=predicate=>records.filter(predicate).length;
  const hasText=value=>typeof value==="string"&&Boolean(value.trim());
  const labelEvidence=d=>d.review_status==="reviewed"&&((Array.isArray(d.morph_labels)&&d.morph_labels.some(x=>x&&x.state!=="not_recorded"))||(Array.isArray(d.aliases)&&d.aliases.length>0))&&hasText(d.evidence_type)&&hasText(d.evidence_url);
  const rightsRecorded=d=>hasText(d.image_rights)&&hasText(d.rights_evidence_url)&&hasText(d.rights_reviewed_by)&&
    d.rights_scopes&&["training","evaluation","hackathon_demo","public_web"].every(scope=>typeof d.rights_scopes[scope]==="boolean");
  $("progress-species").textContent=`${count(d=>d.species_review==="western_hognose")}/${total}`;
  $("progress-individual").textContent=`${count(d=>typeof d.individual_id==="string"&&Boolean(d.individual_id.trim()))}/${total}`;
  $("progress-labels").textContent=`${count(labelEvidence)}/${total}`;
  $("progress-rights").textContent=`${count(rightsRecorded)}/${total}`;
}
function renderList() {
  const mode = $("filter").value;
  if (mode === "excluded") {
    $("next-unreviewed").hidden=true;
    $("count").textContent = text(`${excludedRows.length} excluded photos · previews blocked`, `${excludedRows.length} 张已排除照片 · 预览已禁用`);
    $("items").innerHTML = excludedRows.map(r => `<button class="item" data-index="${r.index}" data-sha="${r.sha256}"><span class="hash">#${r.index}</span><span><b>${text("Excluded · restore","已排除 · 可恢复")}</b><br><span class="meta">${r.sha256.slice(0,16)}…</span></span></button>`).join("");
    document.querySelectorAll(".item").forEach(b => b.onclick = () => openExcluded(Identity.find(excludedRows, b.dataset.index, b.dataset.sha)));
    return;
  }
  $("next-unreviewed").hidden=false;
  const list = rows.filter(r => r.visual_triage === mode);
  $("count").textContent = text(`${list.length} staged review photos`, `${list.length} 张待审预览图`);
  $("items").innerHTML = list.map(r => {const state=reviewState(read(r.sha256));return `<button class="item ${selected?.index === r.index && selected?.sha256 === r.sha256 ? "active" : ""}" data-index="${r.index}" data-sha="${r.sha256}"><img src="${r.preview_url}" loading="lazy"><span><b>#${r.index} · ${triageName(r.visual_triage)}</b><br><span class="item-state">${state}</span><br><span class="meta">${r.sha256.slice(0,16)}…</span></span></button>`;}).join("");
  document.querySelectorAll(".item").forEach(b => b.onclick = () => openRecord(Identity.find(rows, b.dataset.index, b.dataset.sha)));
}
function openNextUnreviewed() {
  collect();
  const queue=rows.filter(r=>r.visual_triage===$("filter").value);
  if(!queue.length)return;
  const current=selected?queue.findIndex(r=>r.index===selected.index&&r.sha256===selected.sha256):-1;
  for(let offset=1;offset<=queue.length;offset++){
    const candidate=queue[(current+offset+queue.length)%queue.length];
    if(read(candidate.sha256).review_status!=="reviewed"){
      $("queue-message").textContent="";
      openRecord(candidate);
      return;
    }
  }
  $("queue-message").textContent=text("Every photo in this queue is marked reviewed. Check evidence and rights before export.","此队列中的照片均已标记复核。导出前仍需检查证据和使用权。");
}
async function refreshQueues() {
  const [active, excluded] = await Promise.all([fetch("/api/inventory"), fetch("/api/excluded")]);
  if (!active.ok || !excluded.ok) throw new Error("Unable to refresh the local review queue");
  rows = await active.json(); excludedRows = await excluded.json();
}
async function mutateExclusion(action, row) {
  const response = await fetch(`/api/${action}`, {method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify({index:row.index,sha256:row.sha256})});
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}
function field(label, key, value, opts, wide=false) {
  return `<div class="field ${wide ? "wide" : ""}"><label for="f-${key}">${label}</label><select id="f-${key}">${opts.map(([v,l]) => `<option value="${esc(v)}" ${String(value ?? "")===String(v) ? "selected" : ""}>${esc(l)}</option>`).join("")}</select></div>`;
}
function input(label,key,value,type="text",wide=false) {
  return `<div class="field ${wide ? "wide" : ""}"><label for="f-${key}">${label}</label><input id="f-${key}" type="${type}" value="${esc(value)}" autocomplete="off"></div>`;
}
function traitOptions() { return ontology.traits.map(t => [t.id, `${english?t.name_en:t.name_zh} · ${t.id}`]); }
function stateOptions(traitId) {
  const trait=ontology.traits.find(t=>t.id===traitId);
  return (trait?.states || []).map(s=>[s, text(s.replaceAll("_"," "), stateZh(s))]);
}
function stateZh(s) { return ({not_recorded:"未记录",carrier:"携带",expressed:"表现型",heterozygous:"杂合",homozygous:"纯合",line_trait:"品系性状",reported:"有报告"})[s] || s; }
function aliasDescription(alias) {
  const name=english?alias.name_en:alias.name_zh;
  const components=alias.components.map(part=>{
    const trait=ontology.traits.find(t=>t.id===part.trait_id);
    const traitName=trait?(english?trait.name_en:trait.name_zh):part.trait_id;
    return `${traitName} (${text(part.state.replaceAll("_"," "),stateZh(part.state))})`;
  }).join(" + ");
  return `${name} = ${components}`;
}
function renderSelectedAliases() {
  const holder=$("selected-aliases"), hidden=$("f-aliases");
  if(!holder||!hidden)return;
  let ids=[];try{ids=JSON.parse(hidden.value||"[]");}catch{ids=[];}
  if(!Array.isArray(ids))ids=[];
  holder.innerHTML=ids.map(id=>{
    const alias=ontology.aliases.find(a=>a.id===id);
    const label=alias?aliasDescription(alias):`${text("Unknown alias","未知别名")}: ${id}`;
    return `<span class="selected-alias">${esc(label)}<button type="button" class="remove-alias" data-alias="${esc(id)}" aria-label="${esc(text("Remove alias","移除此别名"))}">×</button></span>`;
  }).join("")||`<span class="hint">${text("No combination aliases selected.","尚未选择组合别名。")}</span>`;
  holder.querySelectorAll(".remove-alias").forEach(button=>button.onclick=()=>{
    ids=ids.filter(id=>id!==button.dataset.alias);hidden.value=JSON.stringify(ids);renderSelectedAliases();collect();
  });
}
function traitRows(labels, aliases=[]) {
  const arr = Array.isArray(labels) ? labels : [];
  return `<div class="field wide"><span class="label">${text("Canonical trait/state labels", "标准性状／状态标签")}</span><div class="hint">${text("Leave blank when unknown. Carrier requires documented pedigree/genetic evidence; never infer it from an image.", "未知时留空。携带状态须有系谱／遗传证据，绝不能从照片推断。")}</div><div id="trait-rows">${arr.map((v,i)=>traitRow(v,i)).join("")}</div><input id="f-aliases" type="hidden" value="${esc(JSON.stringify(Array.isArray(aliases)?aliases:[]))}"><div class="label">${text("Recorded combination aliases","已记录的组合别名")}</div><div id="selected-aliases" class="selected-aliases"></div><div class="actions"><button type="button" class="secondary" id="add-trait">${text("Add trait", "添加性状")}</button><div class="alias-bar">${ontology.aliases.map(a=>`<button type="button" class="secondary alias" data-alias="${a.id}">${english?a.name_en:a.name_zh} → +${a.components.length}</button>`).join("")}</div></div></div>`;
}
function traitRow(value={}, i=0) {
  const trait=value.trait_id || ontology.traits[0].id;
  return `<div class="trait-row"><select class="trait-id" aria-label="Trait">${traitOptions().map(([v,l])=>`<option value="${esc(v)}" ${v===trait?"selected":""}>${esc(l)}</option>`).join("")}</select><select class="trait-state" aria-label="State">${stateOptions(trait).map(([v,l])=>`<option value="${esc(v)}" ${v===value.state?"selected":""}>${esc(l)}</option>`).join("")}</select><button type="button" class="secondary remove-trait" aria-label="Remove">×</button></div>`;
}
function bindTraitRows(labels) {
  const holder=$("trait-rows");
  const refresh=()=>holder.querySelectorAll(".trait-row").forEach(row=>{
    row.querySelector(".trait-id").onchange=()=>{ row.querySelector(".trait-state").innerHTML=stateOptions(row.querySelector(".trait-id").value).map(([v,l])=>`<option value="${esc(v)}">${esc(l)}</option>`).join(""); collect(); };
    row.querySelector(".remove-trait").onclick=()=>{row.remove();collect();};
  });
  refresh();
  renderSelectedAliases();
  $("add-trait").onclick=()=>{holder.insertAdjacentHTML("beforeend",traitRow());refresh();collect();};
  document.querySelectorAll(".alias").forEach(b=>b.onclick=()=>{
    const hidden=$("f-aliases");let ids=[];try{ids=JSON.parse(hidden.value||"[]");}catch{ids=[];}
    if(!Array.isArray(ids))ids=[];
    if(!ids.includes(b.dataset.alias))ids.push(b.dataset.alias);
    hidden.value=JSON.stringify(ids);renderSelectedAliases();collect();
  });
}
function openRecord(row) {
  selected=row; renderList();
  const d=read(row.sha256), boolOpts=[["",text("Unknown / not reviewed","未知／未复核")],["true",text("Yes","是")],["false",text("No","否")]];
  const evidenceOpts=[["",text("Unknown","未知")],["breeder_record","Breeder record / 系谱记录"],["genetic_test","Genetic test / 遗传检测"],["expert_phenotype_review","Expert phenotype review / 专家表型复核"]];
  const rightOpts=[["",text("Unknown","未知")],["owner_permission","Owner permission / 权利人许可"],["cc0","CC0"],["cc_by_4_0","CC BY 4.0"],["public_domain","Public domain / 公有领域"],["other","Other / 其他"]];
  const scopeOpts=[["",text("Unknown","未知")],["captive_morph","Captive morph / 圈养形态"],["captive_pet","Captive pet / 圈养宠物"],["wild","Wild / 野外"],["other","Other / 其他"]];
  const speciesOpts=[["",text("Not reviewed","未复核")],["western_hognose","Western hognose confirmed / 已确认西部猪鼻蛇"],["uncertain","Uncertain / 不确定"],["non_western_hognose","Confirmed not Western hognose · hide from queue / 已确认非西部猪鼻蛇 · 从队列隐藏"]];
  const boolField=(key,label)=>field(label,key,d[key]===true?"true":d[key]===false?"false":"",boolOpts);
  $("editor").className="editor";
  $("editor").innerHTML=`<div class="photo-title"><h2>${text("Photo", "照片")} #${row.index} <span class="muted">${triageName(row.visual_triage)}</span></h2><span class="status" id="save-status">${text("Saved locally", "已保存在本地")}</span></div>
  <div class="layout"><div><img class="preview" src="${row.preview_url}" alt="Metadata-stripped preview"><div class="hash">SHA-256 · ${row.sha256}</div><p class="hint">${text("Preview only. Original filenames, paths, and metadata are never displayed or served.","仅展示预览图。不会显示或提供原文件名、路径或元数据。")}</p></div>
  <div><div class="fields">${field(text("Manual species review","人工物种复核"),"species_review",d.species_review,speciesOpts,true)}${field(text("Source scope","来源范围"),"source_scope",d.source_scope,scopeOpts)}${input(text("Snake individual ID","蛇个体编号"),"individual_id",d.individual_id||"")}
  ${input(text("Source URL / provenance","来源网址／来源记录"),"source_url",d.source_url||"","url",true)}${traitRows(d.morph_labels,d.aliases)}${field(text("Evidence type","证据类型"),"evidence_type",d.evidence_type,evidenceOpts)}${input(text("Evidence URL","证据网址"),"evidence_url",d.evidence_url||"","url")}${field(text("Claim scope","主张范围"),"claim_scope",d.claim_scope,[["",text("Unknown","未知")],["phenotype","Phenotype only / 仅表型"],["genotype","Genotype / 基因型"]])}
  ${field(text("Rights status","权利状态"),"image_rights",d.image_rights,rightOpts)}${input(text("Rights evidence URL","权利证据网址"),"rights_evidence_url",d.rights_evidence_url||"","url")}${input(text("Rights reviewed by","权利复核人"),"rights_reviewed_by",d.rights_reviewed_by||"")}
  ${boolField("training",text("Training permission","训练许可"))}${boolField("evaluation",text("Evaluation permission","评估许可"))}${boolField("hackathon_demo",text("Hackathon demo permission","黑客松演示许可"))}${boolField("public_web",text("Public web permission","公开网站许可"))}
  ${input(text("Attribution","署名要求"),"attribution",d.attribution||"")}${input(text("Reviewer","复核人"),"reviewer",d.reviewer||"")}${field(text("Review status","复核状态"),"review_status",d.review_status,[["",text("Not reviewed","未复核")],["reviewed","Reviewed / 已复核"],["needs_followup","Needs follow-up / 需跟进"]])}
  <div class="field wide"><label for="f-notes">${text("Notes","备注")}</label><textarea id="f-notes">${esc(d.notes||"")}</textarea></div></div>
  <div class="actions"><button type="button" id="export">${text("Download JSON review export","下载 JSON 复核导出")}</button><button type="button" class="secondary" id="clear">${text("Clear this photo's review","清除此照片复核")}</button></div></div></div>`;
  bindTraitRows(d.morph_labels);
  $("editor").querySelectorAll("input,textarea").forEach(el=>el.addEventListener("input",collect));
  $("editor").querySelectorAll("select").forEach(el=>el.addEventListener("change",collect));
  $("export").onclick=exportJson;
  $("clear").onclick=()=>{localStorage.removeItem(STORE+selected.sha256);openRecord(selected);};
  $("f-species_review").addEventListener("change", async () => {
    if ($("f-species_review").value !== "non_western_hognose") return;
    const row = selected;
    collect();
    try {
      await mutateExclusion("exclude", row);
      await refreshQueues();
      renderProgress();
      $("filter").value = "excluded";
      renderList();
      openExcluded(Identity.find(excludedRows, row.index, row.sha256));
    } catch (error) {
      const draft = read(row.sha256); draft.species_review = ""; saveFor(row.sha256, draft);
      alert(`${text("Could not exclude this photo","无法排除此照片")}: ${error.message}`);
      openRecord(row);
    }
  });
}
function saveFor(sha, data) { localStorage.setItem(STORE + sha, JSON.stringify(data)); }
function openExcluded(row) {
  if (!row) return;
  selected = null;
  $("editor").className = "editor";
  $("editor").innerHTML = `<div class="photo-title"><h2>${text("Excluded photo","已排除照片")} #${row.index}</h2></div><div class="hash">SHA-256 · ${row.sha256}</div><p>${text("The server has removed this photo from the active inventory and blocks its preview. Restore it to return it to its original candidate or uncertain queue.","服务器已将照片从活动清单移除并阻止预览。恢复后会回到原候选或待确认队列。")}</p><button type="button" id="restore">${text("Restore to review queue","恢复到复核队列")}</button>`;
  $("restore").onclick = async () => {
    try {
      await mutateExclusion("restore", row);
      const draft = read(row.sha256); draft.species_review = ""; saveFor(row.sha256, draft);
      await refreshQueues(); renderProgress(); $("filter").value = row.visual_triage; renderList();
      const restored = Identity.find(rows, row.index, row.sha256); if (restored) openRecord(restored);
    } catch (error) { alert(`${text("Could not restore this photo","无法恢复此照片")}: ${error.message}`); }
  };
}
function collect() {
  if (!selected) return;
  const get=(key)=>$("f-"+key)?.value ?? "";
  const nonPhotoEvidence=["breeder_record","genetic_test"].includes(get("evidence_type"));
  const labels=[...document.querySelectorAll(".trait-row")].map(row=>({trait_id:row.querySelector(".trait-id").value,state:row.querySelector(".trait-state").value})).filter(x=>x.state && (x.state!=="carrier" || nonPhotoEvidence));
  let aliases=[];try{aliases=JSON.parse(get("aliases")||"[]");}catch{aliases=[];}
  const data={source_index:selected.index,source_sha256:selected.sha256,visual_triage:selected.visual_triage,species_review:get("species_review"),source_scope:get("source_scope"),source_url:get("source_url"),individual_id:get("individual_id"),morph_labels:labels,aliases:Array.isArray(aliases)?aliases:[],evidence_type:get("evidence_type"),evidence_url:get("evidence_url"),claim_scope:get("claim_scope"),image_rights:get("image_rights"),rights_evidence_url:get("rights_evidence_url"),rights_reviewed_by:get("rights_reviewed_by"),rights_scopes:{training:nullable(get("training")),evaluation:nullable(get("evaluation")),hackathon_demo:nullable(get("hackathon_demo")),public_web:nullable(get("public_web"))},attribution:get("attribution"),reviewer:get("reviewer"),review_status:get("review_status"),notes:get("notes")};
  save(data); const status=$("save-status"); if(status)status.textContent=text("Saved in this browser only","仅保存在此浏览器");
  renderProgress();
}
function nullable(value){return value==="true"?true:value==="false"?false:null;}
function exportJson() {
  collect();
  const records=[];
  for(const r of rows){const d=read(r.sha256);if(Object.keys(d).length && d.species_review!=="non_western_hognose") records.push(Identity.forExport(r,d));}
  const blob=new Blob([JSON.stringify({schema_version:"incoming-review-v1",exported_at:new Date().toISOString(),records},null,2)],{type:"application/json"});
  const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="hogmorph-incoming-review.json";a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
}
async function init(){
  try{const or=await fetch("/api/ontology");if(!or.ok)throw new Error("Private inventory unavailable");ontology=await or.json();await refreshQueues();
    // The server omits rows screened as excluded/non-target; this UI handles candidates and uncertain images only.
    rows=rows.filter(r=>["candidate_western_hognose","uncertain"].includes(r.visual_triage));
    const legacyExcluded=rows.filter(r=>read(r.sha256).species_review==="non_western_hognose");
    for(const row of legacyExcluded) await mutateExclusion("exclude",row);
    if(legacyExcluded.length) await refreshQueues();
    rows=rows.filter(r=>["candidate_western_hognose","uncertain"].includes(r.visual_triage));
    $("filter").onchange=()=>{renderList();if($("filter").value==="excluded"){selected=null;if(excludedRows[0])openExcluded(excludedRows[0]);else{$("editor").className="editor empty";$("editor").innerHTML=`<p>${text("No excluded photos.","没有已排除照片。")}</p>`;}}else{const first=rows.find(r=>r.visual_triage===$("filter").value);if(first)openRecord(first);}};
    $("language").onclick=()=>{english=!english;document.documentElement.lang=english?"en":"zh-CN";document.querySelectorAll("[data-en]").forEach(e=>e.textContent=e.dataset[english?"en":"zh"]);$("language").textContent=english?"中文":"English";[...$("filter").options].forEach((o,i)=>o.text=english?["Candidate","Uncertain","Excluded · restore"][i]:["候选","待确认","已排除 · 恢复"][i]);renderList();if(selected)openRecord(selected);else if($("filter").value==="excluded"&&excludedRows[0])openExcluded(excludedRows[0]);};
    renderProgress();
    $("next-unreviewed").onclick=openNextUnreviewed;
    renderList();const first=rows.find(r=>r.visual_triage==="candidate_western_hognose");if(first)openRecord(first);else $("editor").innerHTML=`<p>${text("No candidate images are available in the fixed local inventory.","固定本地清单中没有候选照片。")}</p>`;
  }catch(e){$("editor").innerHTML=`<p>${esc(e.message)}. ${text("Run scripts/serve_incoming_review.py after staging previews.","完成预处理后运行 scripts/serve_incoming_review.py。")}</p>`;}
}
init();
