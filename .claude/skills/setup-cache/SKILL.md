---
name: setup-cache
description: First-time setup of a new DANDI cache repository generated from dandi-cache/cache-template. Use when asked to set up, initialize, or specialize this cache from the template — filling in cache.toml, implementing the per-item operation in update.py against dandi-cache-utils, and removing the template scaffolding.
---

# Setting up a new DANDI cache from the template

Work through all of these steps in a single setup PR.
`<cache-name>` is the hyphenated repository name (e.g., `my-cache`); `<cache_name>` is the underscored form used for file and variable names (e.g., `my_cache`).

## What you are and are not writing

Every cache in the organization is the same pipeline around a different operation: read one or more upstream caches, work out what is not yet recorded, do something per item, and publish JSON Lines with full provenance.
All of that except the operation lives in [`dandi-cache-utils`](https://github.com/dandi-cache/dandi-cache-utils), reaching this repository through the base container image it is built `FROM`, and in [`dandi-cache-action`](https://github.com/dandi-cache/dandi-cache-action), which is the CI that runs it.

So this repository holds **four things**, and nothing else:

| File | What it is |
|---|---|
| `cache.toml` | What this cache is: its inputs, its outputs, its entry points, its batch size, its metadata. |
| `code/update.py` | What this cache *does*, per item. Usually a few dozen lines. |
| `envs/pyproject.toml` | This cache's own processing dependencies, if any. |
| `.github/workflows/update.yml` | When it runs. |

Do **not** write, copy in, or restore any of the following.
They are the shared pipeline, and a copy here is a copy that drifts:

- an orchestration script (`code/update_pipeline.sh`) — it ships inside the `dandi_cache_utils` package, is vendored into the image with it, and the shared action extracts and runs it (`dandi-cache pipeline --path` says where any installation keeps it);
- a compression step (`code/compress.py`) — `dandi-cache compress` does it;
- a hand-written `dataset_description.json` — the repository's copy is generated from `cache.toml`'s `[description]` (`dandi-cache dataset-description --declared --output dataset_description.json`) and the build workflow fails when the two disagree, so edit the declaration and regenerate, never the file;
- argument parsing, logging setup, the incremental frontier, batch limits, testing mode, output paths, or error-log handling in `code/update.py` — all of it is in the library.

If something the pipeline does is wrong or missing for this cache, fix it in `dandi-cache-utils` so every cache gets the fix.
That is the whole point of it being there.

## 1. Fill in `cache.toml` and replace the remaining placeholders

- `cache.name` — the repository name.
  The output file, the image and the file stem are all derived from it, so most caches set nothing else under `[cache]`.
- `[[inputs]]` — one entry per upstream cache this one reads (see step 2).
  Only `name` is required unless the upstream publishes on a branch other than `derivatives` or under a file name that is not the underscored form of its own name.
- `format` on each input — `lookup` if the file is one single-key object per line to be merged into one mapping (the usual shape), `records` if each line is an independent JSON value, `ids` if the lines are bare scalars.
- `[description]` — `title` and `authors`.
  This is what the published branches describe the repository with: the pipeline renders it to a BIDS study `dataset_description.json` (`DatasetType: "study"`) on every run.
  Every key has a default, so filling in the authors is usually the whole job; `dandi-cache dataset-description cache.toml` prints the result.
  Regenerate the repository's copy once this section is filled in, since the template's still names `<cache-name>`:
  `dandi-cache dataset-description --declared --output dataset_description.json`.
- Replace every remaining `<cache-name>` / `<cache_name>` occurrence (README, `code/`, `containers/`, `envs/`), and resolve every `TODO`: the schedule in `.github/workflows/update.yml`, and the notification recipients if they should differ from the default.
- Write a short description of what the cache contains and how it is derived at the top of the README.

## 2. Choose the input mode

1. **Upstream caches.** The usual case: one or more `[[inputs]]` entries.
   Each is cloned into the `derivatives` dataset as a DataLad subdataset and pinned via `--input` in every run's provenance, so each result records the exact input commit it came from.
   Read them with `dataset.read_input()` (one input) or `dataset.read_input("<name>")` (several).
2. **Local `sourcedata` directory.** Inputs live under the dataset's own `sourcedata/` (e.g. committed fixtures).
   Declare no `[[inputs]]` and read from `dataset.sourcedata_directory`.
3. **First-in-chain / no input dataset.** The cache fetches its own inputs over the network at run time.
   Declare no `[[inputs]]`: there is no input dataset to pin, so no `--input` provenance is declared, and the container must be able to reach the upstream source at run time.
   If those inputs come from the public DANDI S3 bucket, use `dandi_cache.s3` and read the `dandi-s3-network-inputs` skill before writing anything of your own.

## 3. Implement the operation

`code/update.py` arrives with the shape already written; fill in `process` and the candidate list.

- `process(key, item)` computes this cache's value for one item.
  Raise to fail the item; return `dandi_cache.NOTHING` to record nothing for it without counting a failure.
  Set `item.stage` before each phase so a failure is routed to the right error log.
- **Choose the failure policy deliberately.** `on_failure=dandi_cache.SKIP` leaves a failure unrecorded so a later run retries it — right when the work is known to be possible and failures are transient (a network read).
  `on_failure=dandi_cache.RECORD` writes `failure_value` so the item is never retried — right when the failure *is* the answer (a file that does not validate).
  Choosing the wrong one is a real bug, which is why the runner makes you say which.
- **Use the library's DANDI operations rather than writing your own**: `dandi_cache.s3` (unsigned client, content-addressed blob keys, Dandiset manifests, `concurrent_map`), `dandi_cache.api` (tokenless asset resolution), and `dandi_cache.nwb` (remote HDF5 and Zarr readers, the structural walk, the NWB Inspector).
  Tab-completion on those modules lists exactly what they offer.
- **A cache that rebuilds from scratch** — a pure filter or reshaping of its input, with no per-item work — uses `dandi_cache.run_full_rebuild` instead of `run_incremental_update`.
  Do not reimplement incrementality it does not need.
- **A second entry point** (e.g. a `refresh` that re-assesses what is already recorded) gets its own script and an `[operations.<name>]` entry in `cache.toml`, plus a job in `update.yml` whose step passes `operation: <name>`.
- Add this cache's processing dependencies to `envs/pyproject.toml`.
  Leave `datalad` and `datalad-container` out: they run on the runner, from the pipeline's own pinned requirements, never inside the image.
- `--testing` and `--limit` come from the shared command line; do not add your own.
  Testing mode writes `testing_`-prefixed files and can never touch the real cache, because only the outputs declared in `cache.toml` are published.

## 4. Verify before merging

- Locally, against the library from git: `uv run --project envs --extra local python code/update.py --testing`.
  Run with `--testing` first — it is fast and never touches the real cache — before a full local run.
- Then through the real pipeline: manually dispatch the `Update` workflow with `testing: true` and confirm it completes, writes `derivatives/testing_<cache_name>.jsonl`, and leaves `derivatives/<cache_name>.jsonl` untouched.
- When triaging a failed `Update` run that died at a push, check `git ls-remote origin derivatives dist` first: if `derivatives` already holds the run's commit, nothing was lost and the next scheduled run republishes `dist`.
  The shared pipeline retries transient push and `docker pull` failures on its own; that is pipeline infrastructure, not this cache's concern.

## 5. Remove the template scaffolding

These pieces document the template itself, not the generated cache — delete them in this same setup PR:

- The README **How it works** section — the generated cache's README should describe only the cache itself and how to consume it.
- The README **Repository setup** section (including its **With Claude Code** subsection).
- `.claude/skills/setup-cache/` — this skill has no purpose once setup is done.
- `.claude/skills/dandi-s3-network-inputs/` — only if this cache does **not** fetch inputs from the DANDI S3 bucket; keep it when input mode 3 uses that bucket.
  If nothing remains under `.claude/`, remove the directory entirely.
- The `if:` line on the `Update` and `BuildAndPush` jobs, which reads `github.repository != 'dandi-cache/cache-template'`.
  It exists so the template does not run a cache's schedule or publish a cache's image, and this repository is not the template, so the condition is already true and every trigger runs.
  Deleting it is tidiness rather than a fix, and leaving it costs this cache nothing.
