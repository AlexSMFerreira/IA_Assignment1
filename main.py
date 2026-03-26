from __future__ import annotations

import argparse

from angulus.agents import run_random_self_play


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Angulus game")
    parser.add_argument(
        "--random-games",
        type=int,
        default=0,
        help="Run N headless random-vs-random games instead of opening the UI",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for reproducible random games",
    )
    parser.add_argument(
        "--max-plies",
        type=int,
        default=500,
        help="Maximum half-moves per random game before declaring draw",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.random_games > 0:
        results = run_random_self_play(
            games=args.random_games,
            seed=args.seed,
            max_plies=args.max_plies,
        )
        print(
            f"Random self-play over {args.random_games} games: "
            f"white={results['white']}, black={results['black']}, draw={results['draw']}"
        )
        return

    from angulus.ui import AngulusGame

    AngulusGame().run()

if __name__ == "__main__":
    main()
