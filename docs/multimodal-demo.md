# Multimodal demo / 多模态辅助判断

The photo analyzer uses a pretrained vision-language model. The archived CNN and MobileNet training modules are separate research tools. English is the default UI language; use `?lang=zh` for Chinese.

## Start

```bash
python3 -m venv .venv-demo
source .venv-demo/bin/activate
python -m pip install -r requirements-demo.txt
npm ci
ollama pull qwen3-vl:4b
npm run demo
```

Open http://127.0.0.1:8000/. Ollama must be running. The FastAPI server serves the compiled interface and packaged photographs from the same origin; no path to the original course directory is needed. Demo dependencies do not include PyTorch.

## Provider configuration

Copy `.env.example` to `.env` and configure the server. Do not commit `.env`.

Default local configuration:

```dotenv
HOGMORPH_PROVIDER=ollama
HOGMORPH_MODEL=qwen3-vl:4b
HOGMORPH_BASE_URL=http://127.0.0.1:11434
```

The local provider sends image content to the configured local Ollama service. Keep its address local when expecting local processing.

OpenAI-compatible configuration:

```dotenv
HOGMORPH_PROVIDER=openai
HOGMORPH_MODEL=your-vision-model-id
HOGMORPH_BASE_URL=https://your-provider.example/v1
HOGMORPH_API_KEY=your-server-side-key
```

Use a provider that supports image inputs and the chat-completions interface. The key is read only by the server. Selecting this route sends the uploaded photo and selected reference images to that provider; the UI communicates that processing destination. Actual cloud inference is only claimed when an actual configured service has been exercised. Mock adapter checks establish request formatting and error handling, not model quality.

## Analysis contract

- `GET /api/status`: provider/model readiness and configuration status.
- `GET /api/references`: real reference records from `data/demo_references.json`.
- `POST /api/analyze`: uploaded image and language; returns at most three candidates, component traits and states, qualitative evidence strength, visible observations, limitations, reference IDs, model, and elapsed time.

The first pass observes the uploaded image. The server selects at most three relevant references using validated candidate components. The second pass compares those photos. Names are derived by the server from supported ontology entries, including Superconda, Super Arctic, Snow, and Sunburst. Novel names, conflicting states for a locus, hidden carrier claims, and nonexistent reference IDs are rejected.

模型先观察，再做参考图比较。证据强弱为定性结果；不会转换成基因概率。模型未就绪时直接显示原因，不回退到旧颜色相似度，也不返回缓存或预制的推理结果。上传图片只为当前请求处理，处理后释放，不作为上传档案保存。

## References and limitations

18 owner-authorized, user-confirmed friend-provided course photographs are included. Figure12 (Lucy), figure14 (Chocolate), and figure15 (Skull Face) remain outside the supported demo set. The original 21-photo material is not a supervised training or independent test dataset.

Only seven loci enter candidate output: Anaconda, Arctic, Albino, Axanthic, Sable, Toffee Belly, and Lavender. Anaconda and Arctic retain heterozygous/homozygous phenotype states; recessive visible traits use `expressed`. Carrier inference is excluded. Unresolved historical labels and Extreme Red are omitted from components; their omission does not establish their absence in the photographed animal. White Wall is not a gene. `labels_complete=false` means unlisted traits are unknown, never explicit negatives.

207 incoming candidates were removed at the owner's request. 16 uncertain images remain quarantined privately and have no role in analysis. No raw uploads, API keys, or private runtime logs should enter the repository.

## Acceptance evidence

Albino (figure06), Snow (figure16), Sunburst (figure18), and Superconda (figure04) are demonstration consistency cases. Since these are also reference images, outputs cannot establish independent accuracy. Record model name, raw outputs, candidate components, selected references, and duration for actual runs; keep any private image payloads out of logs.

Also exercise: non-snake input, blank image, corrupt file, unavailable model, timeout, invalid structured output, conflicting states, invalid reference IDs, and English/Chinese rendering. A successful adapter mock is reported separately from actual local inference. Request latency belongs to this full VLM chain; random-weight CNN/MobileNet timings must not be substituted for it.
