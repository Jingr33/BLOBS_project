from __future__ import annotations

from blobs_project import config

from .csv_profile import CsvProfile


class ProfileSchedule:
    """Imported profile of desired levels and how long each one is held."""

    def __init__(self) -> None:
        self._profile: CsvProfile | None = None
        self._step_s = config.PROFILE_STEP_S

    @property
    def profile(self) -> CsvProfile | None:
        return self._profile

    @property
    def step_s(self) -> float:
        """Return how long each level is held [s]."""
        return self._step_s

    def set_profile(self, profile: CsvProfile | None) -> None:
        self._profile = None if profile is None else profile.with_step(self._step_s)

    def set_step_s(self, step_s: float) -> None:
        self._step_s = step_s
        if self._profile is not None:
            self._profile = self._profile.with_step(step_s)

    def step_at(self, elapsed_s: float) -> int | None:
        """Return the 0-based step at ``elapsed_s``, or ``None`` without a profile."""
        return None if self._profile is None else self._profile.step_at(elapsed_s)

    def desired_at(self, elapsed_s: float) -> float | None:
        return None if self._profile is None else self._profile.desired_at(elapsed_s)

    def remaining_s(self, elapsed_s: float) -> float | None:
        if self._profile is None:
            return None
        return max(0.0, self._profile.duration_s - elapsed_s)

    def finished(self, elapsed_s: float) -> bool:
        return self._profile is None or elapsed_s >= self._profile.duration_s

    def points(self) -> list[tuple[float, float]]:
        """Return the desired level over the whole profile as chart points."""
        return [] if self._profile is None else self._profile.points()
