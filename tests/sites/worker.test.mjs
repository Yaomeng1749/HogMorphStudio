import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { createWorker, loadCatalog, validateResult, selectReferences } from '../../scripts/sites-worker.mjs';

const ontology = JSON.parse(await fs.readFile(new URL('../../data/ontology.json', import.meta.url)));
const manifest = JSON.parse(await fs.readFile(new URL('../../data/demo_references.json', import.meta.url)));
const image = await fs.readFile(new URL('../../data/demo_references/figure01.jpg', import.meta.url));
const assets = { async fetch(request) {
  const path = new URL(request.url).pathname;
  if (path === '/data/ontology.json') return Response.json(ontology);
  if (path === '/data/demo_references.json') return Response.json(manifest);
  if (manifest.images.some(r => '/' + r.image === path)) return new Response(image);
  return new Response('static', { status: 200 });
} };
const env = { ASSETS: assets, HOGMORPH_MODEL: 'mock-vision', HOGMORPH_BASE_URL: 'https://vision.example/v1', HOGMORPH_API_KEY: 'private-server-secret' };
const catalog = await loadCatalog(env, 'https://demo.example');
const trait = (id = 'albino', state = 'expressed') => ({ trait_id: id, state });
const candidate = (traits = [trait()], reference_ids = []) => ({ traits, support_level: 'weak', visible_evidence: ['Visible reduced pigment'], uncertainties: ['Lighting'], reference_ids });
const result = (candidates = [candidate()]) => ({ assessment: { species: 'western_hognose', animal_count: 1, usable: true, observations: ['Upturned snout'], reason: 'Visible anatomy' }, candidates, limitations: ['Visual estimate'] });
const upload = (bytes = image, lang = 'en') => {
  const form = new FormData(); form.set('image', new Blob([bytes], { type: 'image/jpeg' }), 'snake.jpg'); form.set('lang', lang);
  return new Request('https://demo.example/api/analyze', { method: 'POST', body: form });
};
const expectError = async (worker, request, code, status = 502, config = env) => {
  const response = await worker.fetch(request, config); assert.equal(response.status, status); const body = await response.json();
  assert.equal(body.detail.code, code); assert.ok(!JSON.stringify(body).includes(env.HOGMORPH_API_KEY)); return body;
};
function mockProvider(responseFactory = () => result()) {
  const calls = [];
  const worker = createWorker(async (url, options) => {
    calls.push({ url, options });
    assert.equal(options.redirect, 'error');
    if (url.endsWith('/models')) return Response.json({ data: [{ id: env.HOGMORPH_MODEL }] });
    const body = JSON.parse(options.body);
    return Response.json({ choices: [{ message: { content: JSON.stringify(responseFactory(body, calls)) } }] });
  });
  return { worker, calls };
}

test('unconfigured online status is localized, exposes no credential and never calls provider', async () => {
  const worker = createWorker(() => { throw new Error('must not call'); });
  const response = await worker.fetch(new Request('https://demo.example/api/status?lang=zh'), { ASSETS: assets });
  const body = await response.json(); assert.equal(response.status, 200); assert.equal(body.ready, false);
  assert.equal(body.code, 'cloud_model_not_configured'); assert.match(body.message, /在线识别/);
  await expectError(worker, upload(), 'cloud_model_not_configured', 503, { ASSETS: assets });
});
test('status checks actual model discovery and references remain available without model', async () => {
  const { worker, calls } = mockProvider();
  const body = await (await worker.fetch(new Request('https://demo.example/api/status'), env)).json();
  assert.equal(body.ready, true); assert.equal(body.provider, 'openai'); assert.equal(calls.length, 1);
  const references = await (await worker.fetch(new Request('https://demo.example/api/references'), { ASSETS: assets })).json();
  assert.equal(references.images.length, 886);
});
test('unsafe server URLs do not cause outbound requests', async () => {
  const worker = createWorker(() => { throw new Error('must not call'); });
  for (const base of ['http://vision.example', 'https://user:password@vision.example', 'https://localhost', 'https://127.0.0.1', 'https://vision.example?q=secret', 'https://vision.example/#secret']) {
    await expectError(worker, upload(), 'cloud_model_not_configured', 503, { ...env, HOGMORPH_BASE_URL: base });
  }
});
test('valid two-stage analysis cites real selected images and server names Sunburst', async () => {
  let stages = 0;
  const { worker, calls } = mockProvider(body => {
    stages++;
    const text = body.messages[0].content[0].text;
    assert.equal(body.model, env.HOGMORPH_MODEL); assert.equal(body.response_format.type, 'json_object');
    assert.match(text, /All descriptive strings in Chinese/);
    if (stages === 1) { assert.equal(body.messages[0].content.length, 2); return result([candidate([trait('albino'), trait('sable')])]); }
    assert.equal(body.messages[0].content.length, 5);
    const selected = selectReferences([candidate([trait('albino'), trait('sable')])], manifest.images);
    assert.ok(text.includes(selected[0].id));
    return result([candidate([trait('albino'), trait('sable')], [selected[0].id])]);
  });
  const response = await worker.fetch(upload(image, 'zh'), env); const body = await response.json();
  assert.equal(response.status, 200); assert.equal(stages, 2); assert.equal(calls.length, 3);
  assert.equal(body.candidates[0].name_en, 'Sunburst'); assert.equal(body.candidates[0].traits.length, 2);
  assert.equal(body.candidates[0].references[0].id, body.candidates[0].reference_ids[0]);
  assert.ok(body.elapsed_seconds >= 0); assert.ok(!JSON.stringify(body).includes(env.HOGMORPH_API_KEY));
});
test('valid target without candidates still receives real-photo comparison', async () => {
  let stages = 0;
  const { worker } = mockProvider(() => { stages++; return result([]); });
  const body = await (await worker.fetch(upload(), env)).json();
  assert.equal(stages, 2); assert.equal(body.status, 'insufficient_evidence');
});
test('non-target and multiple subject stop after observation without inventing candidates', async () => {
  for (const mode of ['non_target', 'multiple']) {
    let stages = 0;
    const { worker } = mockProvider(() => { stages++; const value = result([]); if (mode === 'multiple') value.assessment.animal_count = 2; else value.assessment.species = 'non_target'; return value; });
    const body = await (await worker.fetch(upload(), env)).json(); assert.equal(stages, 1);
    assert.equal(body.status, mode === 'non_target' ? 'non_target' : 'insufficient_evidence'); assert.deepEqual(body.candidates, []);
  }
});
test('strict schema rejects unknown loci, conflicts, carriers, unsupported state and invented references', () => {
  for (const c of [candidate([trait('new_gene')]), candidate([trait('albino'), trait('albino')]),
    candidate([trait('albino', 'carrier')]), candidate([trait('anaconda')]), candidate([trait()], ['fiction']),
    { ...candidate(), probability: 0.9 }]) {
    assert.throws(() => validateResult(result([c]), catalog), /invalid_model_output/);
  }
  const value = result(); value.assessment.animal_count = 1.2; assert.throws(() => validateResult(value, catalog));
  assert.throws(() => validateResult({ ...result(), invented: true }, catalog));
});
test('duplicate normalization validates every original candidate and retains original evidence', () => {
  const original = candidate(); const other = { ...candidate(), visible_evidence: ['Different'] };
  assert.deepEqual(validateResult(result([original, other]), catalog).candidates, [original]);
  assert.throws(() => validateResult(result([original, { ...other, reference_ids: ['fiction'] }]), catalog));
});
test('malformed model JSON, unknown reference and upstream failure fail closed', async () => {
  await expectError(mockProvider(() => result([candidate([trait()], ['invented'])])).worker, upload(), 'invalid_model_output');
  const malformed = createWorker(async url => url.endsWith('/models') ? Response.json({ data: [{ id: env.HOGMORPH_MODEL }] }) : Response.json({ choices: [{ message: { content: 'not JSON' } }] }));
  await expectError(malformed, upload(), 'invalid_model_output');
  await expectError(createWorker(async () => new Response('sensitive provider error', { status: 401 })), upload(), 'provider_error', 503);
});
test('provider timeout returns typed error, timer cancelled and secrets absent', async () => {
  const worker = createWorker(async (_url, options) => new Promise((_resolve, reject) => {
    options.signal.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')), { once: true });
  }));
  await expectError(worker, upload(), 'model_timeout', 504, { ...env, HOGMORPH_TIMEOUT: '0.005' });
});
test('missing model is a discovery failure rather than mock inference', async () => {
  await expectError(createWorker(async () => Response.json({ data: [] })), upload(), 'model_missing', 503);
});
test('corrupted upload, duplicate fields and invalid language rejected before provider', async () => {
  const worker = createWorker(() => { throw new Error('must not call'); });
  await expectError(worker, upload(new Uint8Array(50)), 'invalid_image', 400);
  await expectError(worker, upload(image.subarray(0, 100)), 'invalid_image', 400);
  await expectError(worker, upload(image, 'fr'), 'invalid_image', 400);
  const form = new FormData(); form.append('image', new Blob([image]), 'a.jpg'); form.append('image', new Blob([image]), 'b.jpg');
  await expectError(worker, new Request('https://demo.example/api/analyze', { method: 'POST', body: form }), 'invalid_image', 400);
});
test('actual streamed multipart bytes bounded even without content-length', async () => {
  const worker = createWorker(() => { throw new Error('must not call'); });
  let chunks = 0;
  const stream = new ReadableStream({ pull(controller) { chunks++; controller.enqueue(new Uint8Array(1024 * 1024)); } });
  const request = new Request('https://demo.example/api/analyze', { method: 'POST', body: stream, duplex: 'half', headers: { 'content-type': 'multipart/form-data; boundary=bad' } });
  await expectError(worker, request, 'invalid_image', 413); assert.ok(chunks <= 23);
});
test('static assets fall through and unsupported API never falls through', async () => {
  const worker = createWorker();
  assert.equal(await (await worker.fetch(new Request('https://demo.example/styles.css'), env)).text(), 'static');
  assert.equal((await worker.fetch(new Request('https://demo.example/api/unknown'), env)).status, 404);
});
test('invalid catalog fails safely and reference selection covers diverse positive states', async () => {
  const bad = { ASSETS: { fetch: async () => Response.json({ images: [] }) } };
  await expectError(createWorker(), new Request('https://demo.example/api/references'), 'references_unavailable', 503, bad);
  const refs = selectReferences([candidate([trait('albino'), trait('anaconda', 'homozygous')])], manifest.images);
  assert.equal(refs.length, 3); assert.equal(new Set(refs.map(r => r.traits.map(t => `${t.trait_id}:${t.state}`).sort().join('|'))).size, 3);
  assert.ok(refs.some(r => r.traits.some(t => t.trait_id === 'anaconda' && t.state === 'homozygous')));
});
