from pathlib import Path

from game.config import AI_PROFILES

ROOT_DIR = Path(__file__).resolve().parent.parent
NEAT_CONFIG_PATH = ROOT_DIR / "neat_config.txt"
TRACK_LAYOUT_PATH = ROOT_DIR / "track_layout.json"


def get_winner_path(profile_index: int) -> Path:
    if not (0 <= profile_index < AI_PROFILES):
        raise ValueError(f"Invalid AI profile index: {profile_index}")
    return ROOT_DIR / f"winner{profile_index + 1}.pkl"

def get_winner_name_path(profile_index: int) -> Path:
    if not (0 <= profile_index < AI_PROFILES):
        raise ValueError(f"Invalid AI profile index: {profile_index}")
    return ROOT_DIR / f"winner{profile_index + 1}_name.txt"
