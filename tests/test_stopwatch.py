from blobs_project.backend.timekeeping import Stopwatch


def test_start_resets_the_clock_and_the_mark() -> None:
    clock = Stopwatch(1.0)
    clock.advance(2.5)
    clock.mark()

    clock.start()

    assert clock.elapsed_s == 0.0
    assert clock.seconds_since_mark == 0.0
    assert not clock.sample_due


def test_sample_is_due_after_the_interval() -> None:
    clock = Stopwatch(1.0)

    clock.advance(0.5)
    assert not clock.sample_due

    clock.advance(0.5)
    assert clock.sample_due


def test_mark_restarts_the_interval() -> None:
    clock = Stopwatch(1.0)
    clock.advance(1.0)
    assert clock.sample_due

    clock.mark()

    assert not clock.sample_due
    assert clock.seconds_since_mark == 0.0

    clock.advance(1.0)
    assert clock.sample_due
