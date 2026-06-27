import argparse
import pathlib

import yaml


def _run(base_directory: pathlib.Path, limit: int | None) -> None:
    # TODO: implement the update logic for this cache.
    # Read the input data (e.g. from `base_directory / "sourcedata"`), compute the cache,
    # and write the result into `base_directory / "derivatives"`.
    #
    # `limit` is an optional batch size for incremental, resumable runs: process at most
    # `limit` new items per invocation and skip those already recorded in the derivatives.
    # Remove it (and the `--limit` plumbing in update_pipeline.sh and update.yml) if this
    # cache is recomputed in full on every run.

    cache: dict = dict()

    output_file_path = base_directory / "derivatives" / "<cache_name>.yaml"
    with output_file_path.open(mode="w") as file_stream:
        yaml.safe_dump(data=cache, stream=file_stream)


if __name__ == "__main__":
    default_base_directory = pathlib.Path(__file__).parent.parent

    parser = argparse.ArgumentParser(description="Update the <cache-name> DANDI cache.")
    parser.add_argument(
        "--base-directory",
        type=pathlib.Path,
        default=default_base_directory,
        help=(
            "The directory containing the `sourcedata` and `derivatives` directories. "
            "Set to the mounted dataset path when run inside the pipeline container; "
            "defaults to the repository root."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap on the number of new items to process in this run.",
    )
    args = parser.parse_args()

    _run(base_directory=args.base_directory, limit=args.limit)
