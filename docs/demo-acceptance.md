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
