from src import Application


def test_application_runs_successfully() -> None:
    assert Application.run() is True
