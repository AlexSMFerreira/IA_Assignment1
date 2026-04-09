from __future__ import annotations
import argparse
from angulus.agents import run_ai_self_play, run_random_self_play

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Angulus game")
    parser.add_argument("--random-games", type=int, default=0)
    parser.add_argument("--ai-games", type=int, default=0)
    parser.add_argument("--mode", choices=["human-vs-human", "human-vs-ai", "ai-vs-ai"], default="human-vs-human")
    parser.add_argument("--white-depth", type=int, default=1)
    parser.add_argument("--black-depth", type=int, default=1)
    return parser.parse_args()

def main() -> None:
    args = parse_args()

    if args.ai_games > 0:
        results = run_ai_self_play(games=args.ai_games, ai_depth=args.white_depth) 
        print(f"AI self-play results: {results}")
        return

    from angulus.ui import AngulusGame
    game = AngulusGame(mode=args.mode)
    game.white_depth = args.white_depth
    game.black_depth = args.black_depth
    game.run()

if __name__ == "__main__":
    main()


