from __future__ import annotations

from dataclasses import dataclass

PLAYER_TYPE_EMPTY = "empty"
PLAYER_TYPE_HUMAN_1 = "human_1"
PLAYER_TYPE_HUMAN_2 = "human_2"
PLAYER_TYPE_AI = "ai"


@dataclass
class PlaySettings:
    player_one_type: str = PLAYER_TYPE_HUMAN_1
    player_two_type: str = PLAYER_TYPE_HUMAN_2
    player_one_ai_profile: int | None = None
    player_two_ai_profile: int | None = None
    collisions_enabled: bool = True


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
