# Sites deployment

The hosted build preserves the bilingual interface, all 886 packaged reference photos, and the research sections. Sites runs a JavaScript Worker for the cloud vision adapter; the local Python/FastAPI and Ollama workflow remains available.

## Build

```sh
npm ci
npm run build:sites
```

The build produces `dist/client` static assets and `dist/server/index.js`. Create or open the Site and publish with the Sites workflow. Keep its project identity in the Site checkout `.openai/hosting.json`. Do not publish private photos, uploads, local runtime state, or model credentials.

## Configure online analysis

Set the following **server-side** environment values in Sites:

- `HOGMORPH_BASE_URL`: HTTPS OpenAI-compatible vision API base URL, normally ending in `/v1`.
- `HOGMORPH_MODEL`: the installed vision model name.
- `HOGMORPH_API_KEY`: a secret, never a browser configuration or committed file.

The hosted service cannot reach a visitor's local Ollama. Without online model configuration it explicitly disables analysis while leaving the photo library available. It does not substitute fabricated results or a color classifier.

The Worker observes the uploaded photo, chooses up to three real references, compares them in a second model call, and validates traits and reference IDs before generating combination names. Uploads remain transient. Cloud-adapter checks use mocked responses; a real cloud service must be configured before claiming live cloud inference.
