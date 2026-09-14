# DANDI Cache: `<cache-name>`

`<A short description of what this cache contains and how it is derived.>`

Updated frequently.

Primarily for use by developers.

> **Note:** Throughout this template, `<cache-name>` refers to the hyphenated repository name (e.g., `my-cache`) and `<cache_name>` refers to the underscored form used for file and variable names (e.g., `my_cache`).



## One-time use

If you only plan to use this cache infrequently or from disparate locations, you can directly download the latest version of the cache as a compressed [JSON Lines](https://jsonlines.org/) file from the `dist` branch:

### Python API (recommended)

```python
import gzip
import json

import requests

url = "https://raw.githubusercontent.com/dandi-cache/<cache-name>/refs/heads/dist/derivatives/<cache_name>.jsonl.gz"
response = requests.get(url)
lines = gzip.decompress(data=response.content).decode("utf-8").splitlines()
<cache_name> = [json.loads(line) for line in lines]
```

### Save to file

```bash
curl https://raw.githubusercontent.com/dandi-cache/<cache-name>/refs/heads/dist/derivatives/<cache_name>.jsonl.gz -o <cache_name>.jsonl.gz
```



## Repeated use

If you plan on using this cache regularly, clone the `derivatives` branch of this repository:

```bash
git clone --branch derivatives https://github.com/dandi-cache/<cache-name>.git
```

Or, if you prefer [DataLad](https://www.datalad.org/):

```bash
datalad clone https://github.com/dandi-cache/<cache-name>.git --branch derivatives
```

The `derivatives` branch also keeps the log of every update under `logs/`, next to the results it produced.

Then set up a CRON on your system to pull the latest version of the cache at your desired frequency.

For example, through `crontab -e`, add:

```bash
0 0 * * * git -C /path/to/<cache-name> pull
```

This will minimize data overhead by only loading the most recent changes.



## How it works

This cache is one operation; everything around it is shared.
The pipeline, the library its update code is written against and the container base image come from [`dandi-cache-utils`](https://github.com/dandi-cache/dandi-cache-utils); the CI that runs them comes from [`dandi-cache-action`](https://github.com/dandi-cache/dandi-cache-action).
So this repository holds only what makes this cache different from its siblings: `cache.toml` (what it is), `code/update.py` (what it does, per item), `envs/pyproject.toml` (its own dependencies) and a schedule.

It uses three branches:

- **`main`** holds only that: the declaration, the update logic, the runtime container definition, and the two workflows that call the shared actions.
- [**`derivatives`**](https://github.com/dandi-cache/cache-template/tree/derivatives) is a persistent [DataLad](https://www.datalad.org/) dataset on its own branch.
  Each update is recorded there with `datalad containers-run`, so every revision carries full provenance of the exact command, the input subdataset commit, the output diff, the runtime container image digest, and the run's own log under `logs/`.
- **`dist`** is the lightweight publication artifact consumed by downstream users and preferred for one-time downloads.
  Only the outputs declared in `cache.toml` are published to it.

The processing runs inside a published container image (`ghcr.io/dandi-cache/<cache-name>:latest`) built `FROM` the shared base image.
That base carries the `dandi_cache_utils` library *and* the orchestration script, which CI extracts from the image and runs on the runner — so the image digest recorded in each run's provenance pins the orchestration and the runtime together, and a recorded run can be reproduced from the digest alone.

The repository is described as a [BIDS study dataset](https://bids-specification.readthedocs.io/en/stable/common-principles.html#study-dataset) via a `dataset_description.json` that the pipeline renders from `cache.toml` onto the published branches (`DatasetType: "study"`).
Future enhancements may improve the provenance tracking through this mechanism in line with BEP028.



## Repository setup

After generating a repository from this template, the full setup checklist lives in [`.claude/skills/setup-cache/SKILL.md`](.claude/skills/setup-cache/SKILL.md): filling in `cache.toml`, choosing an input mode, implementing the per-item operation against `dandi_cache_utils`, and removing the template scaffolding (this section and the **How it works** section above included).

Setting up a cache is filling in a declaration and writing one function.
If you find yourself writing a pipeline, a logging setup, an argument parser, or a compression step, stop: it already exists in the shared library, and the skill says where.

### With Claude Code

Open a [Claude Code](https://claude.com/claude-code) session in the freshly generated repository and start from a prompt like:

> Set up this new DANDI cache using the setup-cache skill. The cache should `<describe what this cache computes, where its inputs come from, and how often it should update>`. Open the result as a single setup PR.
