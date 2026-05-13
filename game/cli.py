import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ML-WHEELS.")
    parser.add_argument(
        "mode",
        choices=("play", "train", "watch"),
        default="play",
        nargs="?",
        help="Run mode. Defaults to play.",
    )
    parser.add_argument(
        "generations",
        default=50,
        nargs="?",
        type=int,
        help="Number of NEAT generations for train mode.",
    )
    args = parser.parse_args()

    if args.mode == "play":
        from game.modes.human import run_human_game

        run_human_game()
    elif args.mode == "train":
        from game.ai.training import run_training

        run_training(args.generations)
    elif args.mode == "watch":
        from game.ai.training import watch_winner

        watch_winner()
