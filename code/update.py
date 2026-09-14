"""Update the <cache-name> DANDI cache.

Everything shared with the other caches -- the argument parsing, the logging, the incremental
frontier, the batch cap, the failure handling, the output paths, and testing mode -- comes from
`dandi_cache_utils`, which the runtime image carries. What remains in this file is only what makes
this cache different from its siblings.
"""

import dandi_cache_utils as dandi_cache


def process(content_id: str, item) -> object:
    """Compute this cache's value for one item.

    Raise to record a failure; the `on_failure` policy below decides what that means. Set
    `item.stage` before each phase of the work so a failure is routed to the right error log.
    Return `dandi_cache.NOTHING` to record nothing for this item without counting it as a failure.
    """
    item.stage = "doing the work"
    raise NotImplementedError("TODO: implement this cache's per-item operation.")


def main() -> None:
    dataset, arguments = dandi_cache.open_dataset()

    # The universe of items this cache could record. Usually the keys of its upstream cache, often
    # filtered by something that upstream already determined.
    upstream = dataset.read_input()
    candidates = list(upstream)

    dandi_cache.run_incremental_update(
        dataset,
        candidates=candidates,
        process=process,
        limit=dandi_cache.effective_limit(testing=dataset.testing, limit=arguments.limit),
        # `SKIP` leaves a failure unrecorded so a later run retries it -- right when the work is
        # known to be possible and a failure is almost always transient. `RECORD` writes
        # `failure_value` so the item is never retried -- right when the failure is the answer.
        on_failure=dandi_cache.SKIP,
        # Named error logs per phase of the work, so a week of failures stays triageable.
        stages={"doing the work": "processing_errors.txt"},
        # Write the partial result every N items, so a run killed mid-batch keeps what it did.
        checkpoint_every=50,
    )


if __name__ == "__main__":
    main()
