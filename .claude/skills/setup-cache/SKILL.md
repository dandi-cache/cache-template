---
name: setup-cache
description: First-time setup of a new DANDI cache repository generated from dandi-cache/cache-template. Use when asked to set up, initialize, or specialize this cache from the template — replacing placeholders, choosing an input mode, implementing update.py, and removing the template scaffolding.
---

# Setting up a new DANDI cache from the template

Work through all of these steps in a single setup PR. `<cache-name>` is the hyphenated
repository name (e.g., `my-cache`); `<cache_name>` is the underscored form used for file
and variable names (e.g., `my_cache`).

Before starting, read the README's **How it works** section — it explains the
`main` / `derivatives` / `dist` branch layout and the container-based provenance that
the pipeline relies on. (It is part of the scaffolding removed in step 4, so it only
exists before setup.)

## 1. Replace placeholders and resolve TODO markers

- Replace every `<cache-name>` / `<cache_name>` occurrence across the repository
  (README, `code/`, `containers/`, `.github/workflows/`).
- Resolve every `TODO` marker: the update schedule (cron in
  `.github/workflows/update.yml`), the input dataset, and the notification recipients.
- Fill in the placeholder fields in `dataset_description.json` (`Name`, `Authors`;
  `License` defaults to `CC-BY-4.0` — change it if this cache uses a different license).
- Write a short description of what the cache contains and how it is derived at the top
  of the README.

## 2. Choose the input mode

Select one of the three input modes in `code/update_pipeline.sh` (the
`INPUT_SUBDATASET_URL` TODO) and `code/update.py`:

1. **Upstream DataLad dataset.** Set `INPUT_SUBDATASET_URL` to register an upstream
   dataset as an input subdataset. It is cloned into the `derivatives` dataset and
   pinned via `--input` in the provenance of every run, so each result records the
   exact input commit it was computed from.
2. **Local `sourcedata` directory.** Inputs live under the dataset's own `sourcedata/`
   (e.g. committed fixtures). Leave `INPUT_SUBDATASET_URL` empty.
3. **First-in-chain / no input dataset.** The cache fetches its own inputs over the
   network at run time (e.g. it queries a remote API or archive). Leave
   `INPUT_SUBDATASET_URL` empty: there is no input dataset to pin, so no `--input`
   provenance is declared. Because the inputs are pulled at run time, the processing
   container requires outbound network access — the runtime environment must allow the
   container to reach the upstream source. If the inputs come from the public DANDI S3
   bucket, read the `dandi-s3-network-inputs` skill before writing that code.

## 3. Implement the cache logic

- Implement `_run` in `code/update.py`: read the inputs, compute the cache, and write the
  result into `derivatives/<cache_name>.jsonl` as JSON Lines.
- Decide whether to keep `--limit`: keep it for incremental, resumable runs; remove it
  (and its plumbing in `update_pipeline.sh` and `update.yml`) if the cache is recomputed
  in full on every run.
- Add the processing dependencies to `envs/pyproject.toml`.
- The container image is the authoritative runtime, but recreate the environment
  locally with [uv](https://docs.astral.sh/uv/) to debug and verify:
  `uv run --project envs python code/update.py`.

## 4. Remove the template scaffolding

These pieces document the template itself, not the generated cache — delete them in this
same setup PR:

- The README **How it works** section — the generated cache's README should describe
  only the cache itself and how to consume it.
- The README **Repository setup** section (including its **With Claude Code** and
  **Manually** subsections).
- `.claude/skills/setup-cache/` — this skill has no purpose once setup is done.
- `.claude/skills/dandi-s3-network-inputs/` — only if this cache does **not** fetch
  inputs from the DANDI S3 bucket; keep it when input mode 3 uses that bucket. If
  nothing remains under `.claude/`, remove the directory entirely.
