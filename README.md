# DANDI Cache: `<cache-name>`

`<A short description of what this cache contains and how it is derived.>`

Updated frequently.

Primarily for use by developers.

> **Note:** Throughout this template, `<cache-name>` refers to the hyphenated repository name (e.g., `my-cache`) and `<cache_name>` refers to the underscored form used for file and variable names (e.g., `my_cache`).



## One-time use

If you only plan to use this cache infrequently or from disparate locations, you can directly download the latest version of the cache as a compressed [JSON Lines](https://jsonlines.org/) file from the `dist` branch.
Each line is a single-key object, `{"<key>": <value>}`, and each key appears once.

### Python API (recommended)

```python
import gzip
import json
import urllib.request

url = "https://raw.githubusercontent.com/dandi-cache/<cache-name>/refs/heads/dist/derivatives/<cache_name>.jsonl.gz"
with urllib.request.urlopen(url) as response:
    lines = gzip.decompress(response.read()).decode("utf-8").splitlines()
<cache_name> = {key: value for line in lines if line for key, value in json.loads(line).items()}
```

### Save to file

```bash
curl https://raw.githubusercontent.com/dandi-cache/<cache-name>/refs/heads/dist/derivatives/<cache_name>.jsonl.gz -o <cache_name>.jsonl.gz
```

### Outputs past 50 MiB

An output whose compressed file would pass 50 MiB, GitHub's warning size for one file, is published instead as a [Zarr](https://zarr.dev/) store, `derivatives/<cache_name>.zarr/`.
Its chunk files are gzip-compressed pieces of the same JSON Lines, each holding whole lines, so list them and read them in order.
[`valid-nwb-file-to-array-sizes`](https://github.com/dandi-cache/valid-nwb-file-to-array-sizes) is a cache published this way.

```python
import gzip, json, urllib.request

chunks = "https://api.github.com/repos/dandi-cache/<cache-name>/contents/derivatives/<cache_name>.zarr/stream/c?ref=dist"
files = sorted((entry["download_url"] for entry in json.load(urllib.request.urlopen(chunks))), key=lambda url: int(url.rsplit("/", 1)[1]))
<cache_name> = {key: value for url in files for line in gzip.decompress(urllib.request.urlopen(url).read()).decode().splitlines() if line for key, value in json.loads(line).items()}
```

Any Zarr library can also open the store over HTTP and fetch only the chunks it needs.

```python
import zarr  # pip install "zarr>=3" fsspec aiohttp

url = "https://raw.githubusercontent.com/dandi-cache/<cache-name>/refs/heads/dist/derivatives/<cache_name>.zarr"
stream = zarr.open_group(url, mode="r")["stream"]
first_chunk = stream[: stream.chunks[0]].tobytes().decode("utf-8")
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

Each output is a store on the `derivatives` branch, where it is the whole log, uncompacted, and plain text:

```python
import json, pathlib

chunks = sorted(pathlib.Path("<cache-name>/derivatives/<cache_name>.zarr/stream/c").iterdir(), key=lambda path: int(path.name))
<cache_name> = {key: value for chunk in chunks for line in chunk.read_text().splitlines() if line for key, value in json.loads(line).items()}
```


## Reading the `derivatives` branch

Each output is kept on the `derivatives` branch as a [Zarr](https://zarr.dev/) v3 store of JSON Lines: a one-dimensional `uint8` array whose bytes are the lines, padded with newlines to the end of its last chunk.
A key recorded more than once keeps its last line, which the dictionary below does by itself.

```python
import json

import zarr  # zarr>=3, with fsspec and aiohttp to read over HTTP

url = "https://raw.githubusercontent.com/dandi-cache/<cache-name>/derivatives/derivatives/<cache_name>.zarr"
stream = zarr.open_group(url, mode="r")["stream"]
lines = stream[:].tobytes().decode("utf-8").splitlines()
<cache_name> = {key: value for line in lines if line for key, value in json.loads(line).items()}
```

Without Zarr, each chunk is a plain file of whole lines at `derivatives/<cache_name>.zarr/stream/c/<n>`, read in order of `n`.


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
