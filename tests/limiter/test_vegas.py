from aioadaptive.limiter._vegas import VegasLimiter


def test_vegas_on_update_increases_limit() -> None:
    # GIVEN
    limiter = VegasLimiter(
        limit=10,
        alpha=2,
        beta=4,
    )

    # WHEN
    limiter.update(10)
    limiter.update(10)

    # THEN
    assert limiter.limit == 11


def test_vegas_on_update_decreases_limit() -> None:
    # GIVEN
    limiter = VegasLimiter(
        limit=10,
        alpha=2,
        beta=4,
    )

    # WHEN
    limiter.update(10)
    limiter.update(100)

    # THEN
    assert limiter.limit == 9
