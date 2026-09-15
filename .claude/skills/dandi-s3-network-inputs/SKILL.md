---
name: dandi-s3-network-inputs
description: How to read the public DANDI S3 bucket from a cache's update code, and the hard-won lessons behind the shared dandi_cache.s3 module. Use when implementing, debugging, or speeding up code in update.py that lists or downloads objects from the DANDI archive bucket — especially with boto3/botocore, a ThreadPoolExecutor, or manifest parsing.
---

# Fetching inputs from the public DANDI S3 bucket

Lessons earned while debugging and speeding up [dandi-cache/content-id-to-dandiset-paths](https://github.com/dandi-cache/content-id-to-dandiset-paths) (its PRs #9 and #10), for any first-in-chain cache whose `update.py` pulls its own inputs from the public DANDI S3 bucket at run time.

**They are already implemented.** `dandi_cache.s3` is the shared module every such cache uses, and it is where these lessons live now.
Reach for it before writing any boto3 of your own; the rest of this skill explains what it is doing on your behalf, so that you can tell when you are about to step outside it.

```python
import dandi_cache_utils as dandi_cache

client = dandi_cache.s3.anonymous_client(max_pool_connections=16)

metadata = dandi_cache.s3.dandiset_metadata(client, "000003")          # draft dandiset.jsonld
raw = dandi_cache.s3.get_object_bytes(client, dandi_cache.s3.blob_key(content_id))
exists = dandi_cache.s3.object_exists(client, dandi_cache.s3.blob_key(content_id))
results = dandi_cache.s3.concurrent_map(fetch_one, dandiset_ids, max_workers=16)
```

## Listed does not mean readable

Objects that appear in a bucket listing can still deny an anonymous `GetObject`:

- Embargoed Dandisets list their manifests publicly but return `AccessDenied`.
- An object can be deleted between listing and fetching, returning `NoSuchKey`.

`get_object_bytes`, `get_json` and `object_exists` return `None` / `False` for exactly the codes in `s3.ABSENT_ERROR_CODES` and re-raise anything else, so an expected upstream state never fails the whole run and a genuine fault still does.
If you catch `botocore.exceptions.ClientError` yourself, match that behaviour — do not swallow everything.

## Size the connection pool to the worker count

botocore's default connection pool of 10 makes surplus threads redo the TCP/TLS handshake on every request.
`anonymous_client(max_pool_connections=N)` sets the pool, unsigned requests and standard retries in one place; pass the same `N` to `concurrent_map`'s `max_workers`.
A pool smaller than the pool of workers is the single most common reason one of these caches is slow.

## Prefer JSON inputs over YAML

Parsing large YAML in pure Python is GIL-bound, orders of magnitude slower than `json.loads`, and threads do not parallelize it — it can dominate the entire run time.
Wherever the source offers both formats, take the JSON: the DANDI archive publishes `assets.jsonld` next to every `assets.yaml`, which is why `DANDISET_MANIFEST_KEY` and `ASSETS_MANIFEST_KEY` point at the `.jsonld` form.

## If you need something the module does not have

Add it to `dandi_cache.s3` in [`dandi-cache-utils`](https://github.com/dandi-cache/dandi-cache-utils) rather than to this cache.
Every cache that reads the archive hits the same three problems above, and a private copy here is the duplication the shared library exists to end.
