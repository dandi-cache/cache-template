# Source data

This directory holds the input data used to generate the cache derivatives.

If this cache derives from an upstream DataLad dataset, it is registered here as an **input subdataset** of the `derivatives` branch dataset, cloned and pinned by `code/update_pipeline.sh` so that every run records exactly which input commit it processed. Set `INPUT_SUBDATASET_URL` / `INPUT_SUBDATASET_PATH` in that script to enable it.
