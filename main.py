from __future__ import annotations
import argparse
from angulus.agents import run_ai_self_play

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Angulus game")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--max-plies", type=int, default=500)
    parser.add_argument(
        "--ai-vs-ai",
        nargs="+",
        metavar="ARGS",
        help=(
            "Run AI simulation. Formats: "
            "--ai-vs-ai WHITE_AI BLACK_AI N "
            "or --ai-vs-ai WHITE_AI WHITE_DEPTH BLACK_AI BLACK_DEPTH N"
        ),
    )
    parser.add_argument("--mode", choices=["human-vs-human", "human-vs-ai", "ai-vs-ai"], default="human-vs-human")
    parser.add_argument("--white-depth", type=int, default=1)
    parser.add_argument("--black-depth", type=int, default=1)
    return parser.parse_args()

def main() -> None:
    args = parse_args()

    if args.ai_vs_ai is not None:
        ai_vs_ai_args = args.ai_vs_ai
        try:
            if len(ai_vs_ai_args) == 3:
                white_ai, black_ai, game_count_text = ai_vs_ai_args
                white_depth = 1
                black_depth = 1
            elif len(ai_vs_ai_args) == 5:
                white_ai, white_depth_text, black_ai, black_depth_text, game_count_text = ai_vs_ai_args
                white_depth = int(white_depth_text)
                black_depth = int(black_depth_text)
            else:
                print(
                    "Invalid --ai-vs-ai format. Use: "
                    "WHITE_AI BLACK_AI N or WHITE_AI WHITE_DEPTH BLACK_AI BLACK_DEPTH N"
                )
                return

            game_count = int(game_count_text)
            simulation = run_ai_self_play(
                games=game_count,
                white_ai=white_ai,
                white_depth=white_depth,
                black_ai=black_ai,
                black_depth=black_depth,
                seed=args.seed,
                max_plies=args.max_plies,
            )
        except ValueError as exc:
            print(f"Invalid arguments: {exc}")
            return
        print(
            f"AI vs AI report ({white_ai} vs {black_ai}): {simulation}"
        )
        return

    from angulus.ui import AngulusGame
    game = AngulusGame(mode=args.mode)
    game.white_depth = args.white_depth
    game.black_depth = args.black_depth
    game.run()

if __name__ == "__main__":
    main()


