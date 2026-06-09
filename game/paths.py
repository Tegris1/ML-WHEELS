from pathlib import Path

from game.config import AI_PROFILES, TRACK_PROFILES

ROOT_DIR = Path(__file__).resolve().parent.parent
NEAT_CONFIG_PATH = ROOT_DIR / "neat_config.txt"
MODEL_DIR = ROOT_DIR / "model"
TRACK_DIR = ROOT_DIR / "track"

MODEL_DIR.mkdir(exist_ok=True)
TRACK_DIR.mkdir(exist_ok=True)


def get_winner_path(profile_index: int) -> Path:
    if not (0 <= profile_index < AI_PROFILES):
        raise ValueError(f"Invalid AI profile index: {profile_index}")
    return MODEL_DIR / f"winner{profile_index + 1}.pkl"


def get_winner_name_path(profile_index: int) -> Path:
    if not (0 <= profile_index < AI_PROFILES):
        raise ValueError(f"Invalid AI profile index: {profile_index}")
    return MODEL_DIR / f"winner{profile_index + 1}_name.txt"


def get_track_layout_path(profile_index: int) -> Path:
    if not (0 <= profile_index < TRACK_PROFILES):
        raise ValueError(f"Invalid track profile index: {profile_index}")
    return TRACK_DIR / f"track_layout_{profile_index + 1}.json"


def get_track_name_path(profile_index: int) -> Path:
    if not (0 <= profile_index < TRACK_PROFILES):
        raise ValueError(f"Invalid track profile index: {profile_index}")
    return TRACK_DIR / f"track_layout_{profile_index + 1}_name.txt"
