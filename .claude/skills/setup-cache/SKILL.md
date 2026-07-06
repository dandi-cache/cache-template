---
name: setup-cache
description: First-time setup of a new DANDI cache repository generated from dandi-cache/cache-template. Use when asked to set up, initialize, or specialize this cache from the template — replacing placeholders, choosing an input mode, implementing update.py, and removing the template scaffolding.
---

# Setting up a new DANDI cache from the template

Work through all of these steps in a single setup PR. `<cache-name>` is the hyphenated
repository name (e.g., `my-cache`); `<cache_name>` is the underscored form used for file
and variable names (e.g., `my_cache`).

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

1. **Upstream DataLad dataset** — set `INPUT_SUBDATASET_URL`; the dataset is pinned in
   the provenance of every run.
2. **Local `sourcedata` directory** — committed fixtures; leave `INPUT_SUBDATASET_URL`
   empty.
3. **First-in-chain / no input dataset** — `update.py` fetches its own inputs over the
   network at run time; leave `INPUT_SUBDATASET_URL` empty and remember the processing
   container needs outbound network access. If the inputs come from the public DANDI S3
   bucket, read the `dandi-s3-network-inputs` skill before writing that code.

## 3. Implement the cache logic

- Implement `_run` in `code/update.py`: read the inputs, compute the cache, and write the
  result into `derivatives/<cache_name>.jsonl` as JSON Lines.
- Decide whether to keep `--limit`: keep it for incremental, resumable runs; remove it
  (and its plumbing in `update_pipeline.sh` and `update.yml`) if the cache is recomputed
  in full on every run.
- Add the processing dependencies to `envs/pyproject.toml`.

## 4. Remove the template scaffolding

These pieces document the template itself, not the generated cache — delete them in this
same setup PR:

- The README **How it works** section (including its **Input modes** subsection, once the
  chosen input mode is wired up).
- The README **Repository setup** section (including the **Set up with Claude Code** and
  **Local development** subsections).
- `.claude/skills/setup-cache/` — this skill has no purpose once setup is done.
- `.claude/skills/dandi-s3-network-inputs/` — only if this cache does **not** fetch
  inputs from the DANDI S3 bucket; keep it when input mode 3 uses that bucket.
