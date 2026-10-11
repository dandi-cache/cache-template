# DANDI Cache: `<cache-name>`

`<A short description of what this cache contains and how it is derived.>`

Updated frequently.

Primarily for use by developers.

> **Note:** Throughout this template, `<cache-name>` refers to the hyphenated repository name (e.g., `my-cache`) and `<cache_name>` refers to the underscored form used for file and variable names (e.g., `my_cache`).



## One-time use

`dist` publishes each output as a [Zarr](https://zarr.dev/) store: the cache itself is `derivatives/<cache_name>.zarr/`.
A store is one array of [JSON Lines](https://jsonlines.org/) text cut into chunk files, each holding whole lines and gzip-compressed.
Where a key appears more than once, the last line is its current entry, and the published copy has no repeats.
It can be read with the standard library alone, or opened remotely with any Zarr library.

### Python API (recommended)

The chunk files are gzip-compressed [JSON Lines](https://jsonlines.org/): list them, then read them in order as you would any JSONL files.

```python
import gzip, json, urllib.request

chunks = "https://api.github.com/repos/dandi-cache/<cache-name>/contents/derivatives/<cache_name>.zarr/stream/c?ref=dist"
files = sorted((entry["download_url"] for entry in json.load(urllib.request.urlopen(chunks))), key=lambda url: int(url.rsplit("/", 1)[1]))
<cache_name> = {key: value for url in files for line in gzip.decompress(urllib.request.urlopen(url).read()).decode().splitlines() if line for key, value in json.loads(line).items()}
```

An entry is not filed under its key: the chunks hold the entries in the order they were recorded, so looking up one means reading through them.
To look up many, read it once as above, or clone the `derivatives` branch.

### Remote Zarr store

Anything that opens Zarr can open the store over HTTP, reading only the chunks it needs.
The group's `zarr.json` carries the array's metadata, so opening it takes one request:

```bash
pip install "zarr>=3" fsspec aiohttp
```

```python
import json

import zarr

url = "https://raw.githubusercontent.com/dandi-cache/<cache-name>/refs/heads/dist/derivatives/<cache_name>.zarr"
stream = zarr.open_group(url, mode="r")["stream"]
print(stream.shape, stream.chunks)  # Bytes in all, and bytes per chunk.

# The first chunk, fetched and decompressed on its own: whole lines, each `{"<key>": <value>}`.
first_chunk = stream[: stream.chunks[0]].tobytes().decode("utf-8")
for line in first_chunk.splitlines():
    if line.strip():
        print(json.loads(line))
        break
```

Reading `stream[:]` returns the whole text; to read it in pieces, step through it by `stream.chunks[0]`, as each chunk is fetched whole.

### Save to file

A raw URL cannot be listed, so to fetch every chunk at once clone the `dist` branch, which holds nothing else:

```bash
git clone --branch dist --depth 1 https://github.com/dandi-cache/<cache-name>.git
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
