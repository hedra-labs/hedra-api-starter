# Hedra v3 API starter

A small Python example for Hedra's managed image, video, and audio inference API.
It estimates a request, submits it once, waits for completion, and downloads its
first file output. Use Python 3.12 or later.

## Setup

Create a v3 API key in the [developer console](https://www.hedra.com/develop/api-keys)
and fund your [API wallet](https://www.hedra.com/develop/billing). The API wallet
is separate from Studio subscription credits.

```bash
uv sync
cp .env.example .env
```

Set `HEDRA_API_KEY=<key_id>:<secret>` in `.env` or your environment. Keep the
credential server-side. If you do not use uv, create a virtual environment and
install `requests` and `python-dotenv` with pip.

## Estimate, then submit

The input file contains the model's input object, **without** an `input` wrapper.
Review `examples/image.json` before running:

```bash
uv run main.py --estimate
uv run main.py --output image.png
```

The second command submits a billable GPT Image 2 job. It prints an idempotency
key before submission and a job ID after acceptance. Existing output files are
not overwritten. Download failures can leave a partial file; choose a new output
path or remove that partial file before resuming.

For another modality, use its model and input schema:

```bash
uv run main.py --model veo-3 --input examples/video.json --estimate
uv run main.py --model veo-3 --input examples/video.json --output video.mp4
```

For speech, replace the placeholder in `examples/audio.json` with a voice ID from
`GET /v3/models/elevenlabs-v3/voices`, then use `--model elevenlabs-v3` and
`--input examples/audio.json`. Inspect the model's output format before choosing
an output extension. Model inputs are not interchangeable.

## Resume and troubleshoot

Polling stops after 600 seconds by default. A local timeout does not cancel work:

```bash
uv run main.py --job-id job_REPLACE_WITH_YOUR_ID --output recovered.png --wait 1200
```

This command does not submit a new job. The script uses 30-second API request
timeouts and a 60-second download socket timeout; an in-flight request can extend
past the polling deadline. It stops on HTTP errors, failed jobs, and unavailable
outputs. It does not automatically retry submissions or rate-limited requests.

If submission failed before returning an ID, keep the printed idempotency key.
Check the job list in the API or console before retrying. If you retry the same
model and unchanged input, pass `--idempotency-key` with the original key. Never
reuse that key for different work. Respect `Retry-After` on a rate-limit response.

The download uses a separate HTTP request so the API credential is not forwarded
to the storage host. Save files you need to retain; output URLs can expire.

## More resources

- [v3 documentation](https://www.hedra.com/docs/pages/developer/v3/quickstart)
- [Model catalog](https://www.hedra.com/docs/pages/developer/v3/model-catalog)
- [Python SDK](https://github.com/hedra-labs/hedra-python) (`pip install hedra-sdk`)
- [TypeScript SDK](https://github.com/hedra-labs/hedra-node) (`npm install @hedra/sdk`)

This starter demonstrates direct HTTP requests. For SDK-managed models and
helpers, use the official SDKs above. Training and GPU Sandbox preview APIs are
outside this example's scope.

## Existing v2 users

The previous avatar starter is preserved in [legacy/](legacy/README.md) for
existing integrations. Its flags and credentials are different. New integrations
should use v3. See the [migration guide](https://www.hedra.com/docs/pages/developer/v3/migrate-from-v2).

## Offline checks

```bash
uv run python -m unittest discover -s tests -v
```

The tests mock all HTTP calls; they do not create paid jobs.
