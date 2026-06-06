from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TrainingSettings:
    generations: int = 50
    max_steps: int = 1800
    target_laps: int = 3
    profile_index: int = 0


@dataclass
class WatchSettings:
    show_sensors: bool = True
    profile_index: int = 0
