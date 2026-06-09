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
    max_steps: int = 400
    target_laps: int = 3
    training_fps: int = 120
    profile_index: int = 0
    profile_name: str = ""
    # Advanced rewards
    speed_reward: float = 0.02
    wall_penalty: float = 2.0
    checkpoint_reward: float = 20.0
    lap_reward: float = 100.0
    stuck_penalty: float = 0.03
    finish_reward: float = 250.0


@dataclass
class WatchSettings:
    show_sensors: bool = True
    profile_index: int = 0


@dataclass
class EditTrackSettings:
    track_name: str = ""
    track_profile_index: int = 0
