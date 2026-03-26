from pathlib import Path

BOARD_COLS = 9
BOARD_ROWS = 8
SQUARE_SIZE = 80
BOARD_TOP_PADDING = 50
SIDEBAR_WIDTH = 340
WINDOW_WIDTH = BOARD_COLS * SQUARE_SIZE + SIDEBAR_WIDTH
WINDOW_HEIGHT = BOARD_TOP_PADDING + BOARD_ROWS * SQUARE_SIZE
FPS = 60

LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
SELECTED_OVERLAY = (90, 160, 255, 120)
MOVE_OVERLAY = (85, 170, 110, 130)
CAPTURE_OVERLAY = (210, 70, 70, 160)
PANEL_BG = (28, 32, 40)
PANEL_HEADER = (45, 52, 64)
TEXT_LIGHT = (236, 240, 247)
TEXT_DIM = (165, 173, 186)

PIECES_STYLE = "3d_wood"
PIECES_DIR = Path("chess.com-boards-and-pieces-master") / "pieces" / PIECES_STYLE
PIECE_SCALE = 0.7
PIECE_IMAGE_FILES = {
    ("white", "pawn"): "wp.png",
    ("white", "piece"): "wb.png",
    ("white", "king"): "wk.png",
    ("black", "pawn"): "bp.png",
    ("black", "piece"): "bb.png",
    ("black", "king"): "bk.png",
}

# Used by UI evaluation display (king excluded from score view, like chess tools).
POSITION_SCORE_VALUES = {
    "pawn": 1,
    "piece": 3,
    "king": 0,
}

PIECE_VERTICAL_OFFSETS = {
    "pawn": 0,
    "piece": -12,
    "king": -18,
}

DIRECTIONS = [
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
]

# Symbols: P/A/K = white pawn/piece/king, p/a/k = black pawn/piece/king, . = empty
INITIAL_LAYOUT = [
    "p.p.k.p.p",
    ".a.a.a.a.",
    "p.p.p.p.p",
    ".........",
    ".........",
    "P.P.P.P.P",
    ".A.A.A.A.",
    "P.P.K.P.P",
]
