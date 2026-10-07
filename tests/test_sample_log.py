from blobs_project.backend.regulation import SampleLog


def test_sample_log_keeps_only_the_newest_samples() -> None:
    log = SampleLog(limit=2)

    log.append(1.0, 20.0, 18.0)
    log.append(2.0, 20.0, 19.0)
    log.append(3.0, 20.0, 20.0)

    assert len(log) == 2
    assert [sample.time_s for sample in log.samples] == [2.0, 3.0]


def test_sample_log_clear_removes_every_sample() -> None:
    log = SampleLog(limit=5)
    log.append(1.0, 20.0, 18.0)

    log.clear()

    assert len(log) == 0
    assert log.trend_points() == []
