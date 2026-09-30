# Actual local demo runs · 2026-09-30

## Environment and scope

- Code: `1eb4d42ab3a31d0c602987c6015c07f3a2fdf729`.
- Ollama 0.34.4, `qwen3-vl:4b-instruct` (`ee4b975b58c1`), Apple M5, 24 GB RAM, GPU inference, 16,384 context tokens.
- Temperature 0, 1,800 maximum output tokens per pass, default 180-second timeout per provider request.
- Inputs are already members of the 18-photo reference set. These are **demo consistency checks, not independent recognition accuracy**.
- Uploaded photos are not saved. Opt-in acceptance tracing records model response text and timing; it is disabled by default and remains private under `.aris/runtime/acceptance/final-traces/`.

## Final four-case run

| Expected phenotype | Returned candidates | Component check | End-to-end time |
|---|---|---|---|
| Albino | Albino, Lavender, Coral | expected component set present | 49.97 s |
| Snow | Albino, Lavender, Coral | not supported in this run | 59.00 s |
| Sunburst | Albino | not supported in this run | 42.24 s |
| Superconda | insufficient_evidence | not supported in this run | 12.16 s |

**Current model limitations:** Snow lost the Axanthic component, Sunburst returned only Albino, and Superconda received no call. Earlier prompt iterations sometimes returned Snow, so these results are not stable enough to claim reliable recognition. Albino also has incorrect competing alternatives (Lavender/Coral). Candidate ranking and evidence wording come from the model and require human review.

中文：最终运行仅 Albino 的预期拆解进入候选。Snow 漏掉 Axanthic，Sunburst 漏掉 Sable，Superconda 拒绝判断；较早版本曾给出 Snow，但结果不稳定。候选中的错误备选也应人工复核。

## Rework performed

The ambiguous `qwen3-vl:4b` tag resolved to the Thinking variant and exhausted the bounded generation budget without structured content. The explicit Instruct tag produced valid JSON. General breeder-sourced visual rules then corrected red-eye/color-based species rejection; later prompts required actual visible features, minimal trait sets, partial-label semantics, and explicit provisional hypotheses. The final failed component checks above are retained rather than replaced with prepared answers.

Visual rules are descriptive clues, not genetic proof: [Albino](https://www.reptifit.nl/en/collection/western-hognose-snake-albino), [Axanthic](https://www.reptifit.nl/en/collection/western-hognose-snake-axanthic), [Anaconda](https://www.reptifit.nl/en/collection/western-hognose-snake-anaconda), [Superconda](https://www.reptifit.nl/en/collection/western-hognose-snake-superconda), [Arctic](https://www.reptifit.nl/en/collection/western-hognose-snake-arctic), [Sable](https://www.reptifit.nl/en/collection/western-hognose-snake-sable), [Lavender](https://www.reptifit.nl/en/collection/western-hognose-snake-lavender).

## Boundaries and reproducibility

- Clean clone at `1eb4d42`: demo-only dependencies, no torch installed/imported, TypeScript typecheck/build, 15 unit tests at that clone; 16 after response normalization, unified startup, 18 reference images loading, private paths rejected.
- Actual non-snake illustration: `non_target`; blank image: `insufficient_evidence`; corrupted file: HTTP 400 `invalid_image`. These results were repeated successfully on the final prompt (8.51 s, 4.45 s, 0.05 s respectively).
- Missing model, timeout, malformed provider output, conflicting trait states, invented reference IDs, text-only Ollama models, oversized/chunked multipart uploads, and OpenAI-compatible image payloads are covered by deterministic tests. Cloud service inference has **not** been exercised.
- An independent fresh-context Codex code review was used. A separate Claude route was unavailable due to OAuth 401; no cross-family review is claimed.

## Response evidence hashes

Raw responses are private opt-in verification artifacts, not uploaded archives or public telemetry. SHA-256 identifiers for the final model response traces:

| Stage | Response artifact SHA-256 |
|---|---|
| observe | `64429a9095c432361ff1f2e2e3c84fc63509927b969a3d395a422f627861f573` |
| compare | `5adf712561e886ef897634a8f61707dbcbd4ea0367990ef8761b8b1e11c98b7f` |
| observe | `21977a9d6f6fdf0ee54cba4b90f7c11896b11bac5cce756f176443789d41a3ce` |
| compare | `99f6867a9925d27835be6e2d17310918452c087b9ae3f90c3560c412f213d33c` |
| observe | `e115b4fddef70a1307d2ea85913e43d8c8bf7ee5724833b701d05cd2ddd61c73` |
| compare | `3829bf43673e6a3301e7138c66ef79f1189f8a96dc7e0df8b3160b2ae63760ab` |
| observe | `b49e7ac033fe7829567ad5e9f71e6fa0259436cf5afa3ccdc713956a6a9eaeb4` |
| observe | `4087a653d4c2625ee6041113831f723928dfaaecc7f03b431d32092f59e4d662` |
| compare | `a98e48786f58b661d99958d3dd6a9cccccf489844c75ec21377330d8a796e9e6` |

## Chinese response normalization

An actual Chinese request produced repeated valid hypotheses. After validating every original trait/state/reference, the server now stably removes repeated hypotheses and citations without inventing or merging evidence. Conflicts and invented references remain errors. The phenotype prompt is unchanged from the four-case run; this narrow normalization change has separate regression coverage.

The repeated real Chinese request after normalization returned HTTP 200, candidates 白化 / 薰衣草, Chinese observations, and 48.362 seconds end-to-end latency. See [Chinese result screenshot](assets/multimodal-result-zh.png). A real missing-model check used the actual local Ollama model list, returned `ready=false/model_missing`, rejected analysis with HTTP 503, and performed zero image inference calls.

## Expanded archive

The user subsequently supplied 868 labelled photographs and withdrew the recording requirement. The public reference archive now contains 886 photographs. Initial results above describe the original 18-photo archive; expanded-library runs are recorded separately.

## Expanded-library actual runs

Runtime code: `af89679e17f222469fdd1852fa5c6ecf7d5804be` (the subsequent public-summary route and compound display-name updates do not change inference prompts). Same Ollama Instruct model and hardware as above; 886 reference photographs. These inputs belong to the reference library, so this remains **within-reference consistency, never independent accuracy**.

| Input | Returned candidates | Expected complete component set | Time |
|---|---|---|---|
| Albino (`figure06`) | Albino, Lavender, Coral | present | 66.11 s |
| Snow (`figure16`) | Coral, Albino, Lavender | not present | 74.34 s |
| Sunburst (`figure18`) | Albino | not present | 47.36 s |
| Superconda (`figure04`) | Superconda, Albino, Axanthic | present | 53.00 s |
| Albino (`genes-0587fa4e86889ea4`) | Albino, Lavender, Snow | present | 57.55 s |
| Snow (`genes-02175d671bcf97ac`) | Lavender | not present | 34.75 s |
| Super Arctic (`genes-022a377a3bf5d84e`) | insufficient_evidence | not present | 42.36 s |
| Super Yeti (`genes-05b2027b905a091a`) | Albino, Axanthic, Superconda | not present | 61.64 s |

Albino and Superconda course cases returned the expected components. The new Albino input also did so. Snow, Sunburst, Super Arctic and Super Yeti checks did not return their complete expected components; the model sometimes lists component traits as competing single-trait candidates. These cases remain unsupported by this tested configuration. Incorrect alternatives remain visible rather than replaced with folder labels.

中文：新参考库已实际参与比较。白化及课程图 Superconda 的预期成分进入候选，但 Snow、Sunburst、Super Arctic、Super Yeti 仍有遗漏或拒绝判断；模型有时把本应组合的成分列成独立备选。当前结果不能用作高准确率或独立泛化能力声明。

Lightweight HSV/texture features select comparison photographs only. They do not assign candidate genes, evidence levels or percentages. Positive labels determine coverage; missing annotations remain unknown. Usable single Western Hognose photos can be compared even when the first pass has no phenotype candidate; non-target, ambiguous-species, multiple-animal and unusable inputs still stop early.

### Expanded archive gates

- Independent clean clone at `af89679`: 19 demo tests, 4 importer tests, typecheck/build, no torch, 886 reference photographs fetched with matching SHA-256, private routes rejected.
- Web UI: 886 records, 60 initial cards, 120 after loading more, search finds the last record in the full library; Superconda filter covers 231 records. English and Chinese render without browser errors or broken loaded thumbnails.
- Import and code received an independent fresh-context Codex review at `1eed3e7`; no cross-family review is claimed.

### Expanded run response evidence

Model responses and timing are kept in opt-in private runtime traces, disabled during ordinary use. The original ZIP and upload payloads are not public artifacts.

| Stage | Response artifact SHA-256 |
|---|---|
| observe | `047e123791c2802a481aedfb4b0a122cac3cb6c79ba7df03ea00622645f3db84` |
| compare | `0449f7c73072f024a4b52456226575ded5f9065b9f157cd89e6d4741f8c15370` |
| observe | `874a3f712179a747edf9984991c99f7aadb7d9d7cf9c415ae1ee3d7e06c238b4` |
| compare | `988b8e4fd9d9bd2fb20b0b2865f6e72723618b93fa5f229f2131616efa6af265` |
| observe | `fdfc6dd12a85aa56659666a9bd5446292d4ca3bf8a4318cfa859e94a2f001787` |
| compare | `afe7389b71bb66e99a5997664d1923159cf4795060df213e2870fa2a530479c9` |
| observe | `8f73ec6ac4cf4faa1172b80a5db0ca73644b3f104c51841440e5a63dd224cd48` |
| compare | `f56f866448b8ec9ee306f410355583f66eafd6759938e4cccea90a693c1053fd` |
| observe | `1963800b8f4b139961cbf8af72127928850a8433ec98223a33b394c6c2d76cc8` |
| compare | `18d8ef4ba297af57f1feff3a0113073cf9fb0fd663610d38f920a183af3a2957` |
| observe | `0e3b306e70edf0d48d679efb669a2dd24db61cd4d795ca8c007e298b6d91620e` |
| compare | `63ffc050d115e475e6f780a435d90a95721ba73277b1d54f53149346291470e0` |
| observe | `7d17ec97ec292159493478374ae24f844a4ad2668a18025007f484faba614d0f` |
| compare | `136e68769daf144cf04298a3bdecd5bd1bf49bdf9822e2db94c3627ff886dbfe` |
| observe | `0c052d41528d79d16f1be28b858fd68d1f3fc4d703141adce5a85eba488a1269` |
| compare | `e835e9a8275480ee3fce111d9a36829efe8764c15c5519901ecb443a7a3b8a58` |
