import argparse
import datetime
import itertools
import json
import logging
import pathlib
import resource
import sys
import time

# Testing mode processes only this many items and writes to its own designated file
# (`derivatives/testing.jsonl`), leaving the real cache untouched.
_TESTING_LIMIT = 10
_CACHE_FILE_NAME = "<cache_name>.jsonl"
_TESTING_FILE_NAME = "testing.jsonl"

# Each run writes its log to `logs/` next to `derivatives/`. In the pipeline that directory is
# an output of the recorded run, so the log of every completed update is committed to the
# `derivatives` branch alongside the results it produced.
_LOG_DIRECTORY_NAME = "logs"

logger = logging.getLogger("update")


def _configure_logging(log_directory: pathlib.Path, testing: bool) -> pathlib.Path:
    """Send the log to stdout and to a new timestamped file under `log_directory`; return the file.

    Stdout is the live view in the CI job log, and is flushed per record so that a run killed
    mid-batch still shows how far it got. The file is the persistent copy, kept with the
    results. A testing run gets its own file name prefix so it is never mistaken for an update
    of the real cache.
    """
    log_directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(tz=datetime.UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    log_file_path = log_directory / f"{'testing' if testing else 'update'}_{timestamp}.log"

    formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ")
    formatter.converter = time.gmtime  # UTC timestamps, matching the file name and the CI log.

    logger.setLevel(logging.INFO)
    for handler in (logging.StreamHandler(stream=sys.stdout), logging.FileHandler(filename=log_file_path)):
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return log_file_path


def _peak_memory_mib() -> float:
    """Peak resident set size of this process so far, in MiB (Linux reports `ru_maxrss` in KiB)."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def _run(base_directory: pathlib.Path, testing: bool) -> None:
    log_file_path = _configure_logging(log_directory=base_directory / _LOG_DIRECTORY_NAME, testing=testing)
    logger.info("Logging to %s.", log_file_path)
    start_time = time.monotonic()

    # TODO: implement the update logic for this cache.
    # Read the inputs, compute the cache, and write the result into
    # `base_directory / "derivatives"` as JSON Lines (one JSON value per line).
    #
    # Log through `logger` (never `print`): one `logger.info` line per processed item with
    # what it was, its size, how long it took, and `_peak_memory_mib()`, so a run that is
    # killed mid-batch shows in the CI job log which item it was on and how much memory it
    # had reached, and every completed run leaves its log under `logs/` on the `derivatives`
    # branch. Use `logger.warning` for items that are skipped.
    #
    # The setup checklist — input modes, whether to keep `--testing`, and lessons for
    # fetching inputs from the public DANDI S3 bucket — lives in the plain-Markdown
    # skills .claude/skills/setup-cache/SKILL.md and
    # .claude/skills/dandi-s3-network-inputs/SKILL.md.

    records: list = []

    if testing:
        # Testing run: keep only the first few items, so the run is fast but still
        # exercises the real processing logic end to end.
        records = list(itertools.islice(records, _TESTING_LIMIT))

    derivatives_directory = base_directory / "derivatives"
    derivatives_directory.mkdir(parents=True, exist_ok=True)

    # Testing runs write to their own designated file, so the real cache is never touched.
    output_file_path = derivatives_directory / (_TESTING_FILE_NAME if testing else _CACHE_FILE_NAME)
    with output_file_path.open(mode="w") as file_stream:
        file_stream.writelines(f"{json.dumps(record)}\n" for record in records)

    logger.info(
        "Wrote %d records to %s in %.1f min (peak memory %.0f MiB).",
        len(records),
        output_file_path,
        (time.monotonic() - start_time) / 60,
        _peak_memory_mib(),
    )


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
        "--testing",
        action="store_true",
        help=(
            f"Run in testing mode: process only the first {_TESTING_LIMIT} items and write "
            f"`derivatives/{_TESTING_FILE_NAME}` instead of the real cache, leaving it "
            "untouched. Omit for a complete update."
        ),
    )
    args = parser.parse_args()

    _run(base_directory=args.base_directory, testing=args.testing)
