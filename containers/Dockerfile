# syntax=docker/dockerfile:1

# The pinned runtime environment for this cache.
#
# Everything shared comes from the base image: Debian, git-annex, the virtual environment, the
# `dandi_cache_utils` library that `code/update.py` imports, and the vendored `update_pipeline.sh`
# that CI extracts and runs on the runner. A cache's Dockerfile is therefore only the dependencies
# that are genuinely its own.
#
# The loose dependencies in `envs/pyproject.toml` are resolved fresh at build time and the resulting
# image (by digest) is the lock, so there is no lockfile in the repository to hold in sync. uv is
# intentionally not used inside the image; it stays an outside-the-container convenience for running
# locally while debugging.
#
# The image holds only the environment, not this cache's code. The code is mounted at run time, so
# a single image serves any revision of it.
#
# TODO: pin a release (`:0.1.0`) rather than `:latest` if this cache should hold its orchestration
# still, and use `:nwb` instead if it streams remote NWB files — that tag already carries h5py,
# zarr, pynwb, hdmf-zarr, remfile, s3fs and the NWB Inspector.
FROM ghcr.io/dandi-cache/dandi-cache-utils:latest

# The source label associates the image on the GitHub Container Registry with this repository.
LABEL org.opencontainers.image.source="https://github.com/dandi-cache/<cache-name>"
LABEL org.opencontainers.image.description="The pinned runtime environment for the DANDI Cache <cache-name> update pipeline."

# This cache's own processing dependencies. Delete these two lines if it has none beyond what the
# base image already provides.
COPY envs/pyproject.toml /tmp/build/pyproject.toml
RUN pip install /tmp/build && rm -rf /tmp/build

CMD ["python", "--version"]
