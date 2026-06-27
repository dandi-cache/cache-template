# DANDI Cache: `<cache-name>`

`<A short description of what this cache contains and how it is derived.>`

Updated frequently.

Primarily for use by developers.

> **Note:** Throughout this template, `<cache-name>` refers to the hyphenated repository name (e.g., `my-cache`) and `<cache_name>` refers to the underscored form used for file and variable names (e.g., `my_cache`).



## One-time use

If you only plan to use this cache infrequently or from disparate locations, you can directly download the latest version of the cache as a minified and compressed JSON file from the `dist` branch:

### Python API (recommended)

```python
import gzip
import json

import requests

url = "https://raw.githubusercontent.com/dandi-cache/<cache-name>/refs/heads/dist/derivatives/<cache_name>.min.json.gz"
response = requests.get(url)
<cache_name> = json.loads(gzip.decompress(data=response.content))
```

### Save to file

```bash
curl https://raw.githubusercontent.com/dandi-cache/<cache-name>/refs/heads/dist/derivatives/<cache_name>.min.json.gz -o <cache_name>.min.json.gz
```



## Repeated use

If you plan on using this cache regularly, clone the `dist` branch of this repository:

```bash
git clone --branch dist https://github.com/dandi-cache/<cache-name>.git
```

Then set up a CRON on your system to pull the latest version of the cache at your desired frequency.

For example, through `crontab -e`, add:

```bash
0 0 * * * git -C /path/to/<cache-name> pull
```

This will minimize data overhead by only loading the most recent changes.



## How it works

This cache keeps the generated results off the code branch and records every update with full provenance. It uses three branches:

- **`main`** holds only the code (this branch): the update logic, the runtime container definition, and the CI workflows.
- **`derivatives`** is a persistent [DataLad](https://www.datalad.org/) dataset on its own branch. Each update is recorded there with `datalad containers-run`, so every revision carries full provenance — the exact command, the input subdataset commit, the output diff, and the runtime container image digest — and the history is retained.
- **`dist`** is the lightweight, force-recreated publication artifact consumed by downstream users (the minified, compressed file linked above).

The processing runs inside a published container image (`ghcr.io/dandi-cache/<cache-name>:latest`) that holds only the pinned runtime environment. The code and the dataset are bind-mounted in at run time, so a single image serves any revision of the code, and only the image digest is stored in the dataset (a small text file) — the registry holds the image bytes.

The orchestration lives in [`code/update_pipeline.sh`](code/update_pipeline.sh); the actual cache logic lives in [`code/update.py`](code/update.py) (full output) and [`code/minify.py`](code/minify.py) (consumer artifact), both of which run in any environment.



## Repository setup

After generating a repository from this template:

1. Replace every `<cache-name>` / `<cache_name>` placeholder and resolve the `TODO` markers (the update schedule, the cache logic, the input dataset, the notification recipients).
2. Add this cache's processing dependencies to [`envs/pyproject.toml`](envs/pyproject.toml). That file is the single source of truth for both the local environment and the published container image.
3. Configure the repository secrets used by the workflows: `_GITHUB_API_KEY` (a token allowed to push to this repository and to push/pull packages), `MAIL_USERNAME`, and `MAIL_PASSWORD`.
4. Push to `main`. The **Build and Upload Container** workflow publishes the runtime image, and the **Update** workflow runs the pipeline on its schedule (or via *Run workflow*), creating the `derivatives` and `dist` branches on the first run.

### Local development

The container image is the authoritative runtime, but you can recreate the environment locally with [uv](https://docs.astral.sh/uv/) for debugging:

```bash
uv run --project envs python code/update.py
```
