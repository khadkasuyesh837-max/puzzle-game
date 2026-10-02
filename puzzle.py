"""Game logic: OpenCV image handling, tiles, transformations and the board."""
import random

import cv2
import numpy as np


class ImageProcessor:
    """All OpenCV work lives here (load, resize, crop, split, merge)."""

    @staticmethod
    def load(path):
        data = np.fromfile(path, dtype=np.uint8)          # works with any file path
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not read that image file.")
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)       # OpenCV is BGR, Tk needs RGB

    @staticmethod
    def prepare(img, grid, max_size):
        """Resize to fit the screen, then centre-crop to a square that divides by grid."""
        h, w = img.shape[:2]
        scale = min(max_size / w, max_size / h)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
        h, w = img.shape[:2]
        side = min(h, w) // grid * grid
        top, left = (h - side) // 2, (w - side) // 2
        return img[top:top + side, left:left + side].copy()

    @staticmethod
    def split(img, grid):
        t = img.shape[0] // grid
        return [img[r * t:(r + 1) * t, c * t:(c + 1) * t] for r in range(grid) for c in range(grid)]

    @staticmethod
    def merge(tiles, grid):
        rows = [np.hstack(tiles[r * grid:(r + 1) * grid]) for r in range(grid)]
        return np.vstack(rows)


class Tile:
    """One puzzle piece. Its state is private and only changed through methods."""

    def __init__(self, home, pixels):
        self.__home = home            # index where this piece belongs
        self.__pixels = pixels        # original, untouched pixels
        self.__rot = 0                # clockwise quarter turns (0-3)
        self.__flipped = False        # mirrored horizontally?

    @property
    def home(self):
        return self.__home

    def rotate(self, quarter_turns=1):
        self.__rot = (self.__rot + quarter_turns) % 4

    def flip_h(self):
        # Mirroring reverses the direction of any existing rotation.
        self.__flipped = not self.__flipped
        self.__rot = (-self.__rot) % 4

    def flip_v(self):
        # A vertical flip is a horizontal flip plus a 180 degree turn.
        self.flip_h()
        self.rotate(2)

    def upright(self):
        return self.__rot == 0 and not self.__flipped

    def image(self):
        img = np.fliplr(self.__pixels) if self.__flipped else self.__pixels
        return np.rot90(img, -self.__rot)                 # negative = clockwise


class Transformation:
    """Base class. Every transformation can be applied and undone."""

    name = "transformation"

    def apply(self, board):
        raise NotImplementedError

    def undo(self, board):
        raise NotImplementedError


class Swap(Transformation):
    name = "swap"

    def __init__(self, a, b):
        self.a, self.b = a, b

    def apply(self, board):
        t = board.tiles
        t[self.a], t[self.b] = t[self.b], t[self.a]

    def undo(self, board):
        self.apply(board)                                 # a swap undoes itself


class Rotate(Transformation):
    name = "rotate"

    def __init__(self, pos, quarter_turns=1):
        self.pos, self.turns = pos, quarter_turns

    def apply(self, board):
        board.tiles[self.pos].rotate(self.turns)

    def undo(self, board):
        board.tiles[self.pos].rotate(-self.turns)


class Flip(Transformation):
    name = "flip"

    def __init__(self, pos, vertical=False):
        self.pos, self.vertical = pos, vertical

    def apply(self, board):
        tile = board.tiles[self.pos]
        tile.flip_v() if self.vertical else tile.flip_h()

    def undo(self, board):
        self.apply(board)                                 # a flip undoes itself


class Board:
    """Holds the tiles, scrambles them, and applies/undoes moves."""

    MAX_HINTS = 3

    def __init__(self, image, grid):
        self.grid = grid
        self.tiles = [Tile(i, p) for i, p in enumerate(ImageProcessor.split(image, grid))]
        self.history = []             # every transformation applied, in order
        self.moves = 0
        self.hints_left = self.MAX_HINTS
        self.scramble()

    def do(self, transformation):
        transformation.apply(self)
        self.history.append(transformation)

    def play(self, transformation):
        """A move made by the player."""
        self.do(transformation)
        self.moves += 1

    def scramble(self):
        count = self.grid * (self.grid - 1)               # 6, 12, 20 for 3x3, 4x4, 5x5
        kinds = [0, 1, 2] + random.choices([0, 1, 2], k=count - 3)   # all 3 types appear
        random.shuffle(kinds)
        while True:
            for kind in kinds:
                a, b = random.sample(range(len(self.tiles)), 2)
                if kind == 0:
                    self.do(Swap(a, b))
                elif kind == 1:
                    self.do(Rotate(a, random.randint(1, 3)))
                else:
                    self.do(Flip(a, vertical=random.random() < 0.5))
            if not self.is_solved():
                return
            self.solve()                                  # unlucky: scramble cancelled out

    def solve(self):
        while self.history:
            self.history.pop().undo(self)
        self.moves = 0

    def is_correct(self, pos):
        return self.tiles[pos].home == pos and self.tiles[pos].upright()

    def wrong_positions(self):
        return [p for p in range(len(self.tiles)) if not self.is_correct(p)]

    def is_solved(self):
        return not self.wrong_positions()

    def hint(self):
        """Position of a random incorrect tile, or None if no hints are left."""
        if self.hints_left == 0 or self.is_solved():
            return None
        self.hints_left -= 1
        return random.choice(self.wrong_positions())

    def image(self):
        return ImageProcessor.merge([t.image() for t in self.tiles], self.grid)
