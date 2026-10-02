"""Quick logic tests: python test_puzzle.py"""
import itertools
import numpy as np
from puzzle import Board, ImageProcessor, Tile, Rotate, Flip


def test_scramble_and_solve():
    raw = ImageProcessor.load("images/car-compact-hatch.jpg")
    for grid in (3, 4, 5):
        for _ in range(50):
            img = ImageProcessor.prepare(raw, grid, 500)
            assert img.shape[0] % grid == 0 and img.shape[0] == img.shape[1]
            b = Board(img, grid)
            assert len(b.history) == grid * (grid - 1)
            assert {t.name for t in b.history} == {"swap", "rotate", "flip"}
            assert not b.is_solved()
            b.solve()
            assert b.is_solved() and b.moves == 0
            assert np.array_equal(b.image(), img)       # pixel-perfect restore


def test_player_controls_can_solve_every_tile_state():
    # Using only rotate-90 and horizontal flip, every orientation can be reached back to upright.
    px = np.arange(16).reshape(4, 4)
    for ops in itertools.product(["r", "h", "v"], repeat=4):
        t = Tile(0, px)
        for o in ops:
            {"r": t.rotate, "h": t.flip_h, "v": t.flip_v}[o]()
        seen, frontier = set(), [t]
        # BFS is overkill; just try all sequences up to length 4 of the two player moves
        ok = False
        for seq in itertools.product("rh", repeat=4):
            import copy
            c = copy.deepcopy(t)
            for o in seq:
                c.rotate() if o == "r" else c.flip_h()
            if c.upright():
                ok = True
                break
        assert ok, ops


def test_orientation_matches_pixels():
    px = np.arange(16).reshape(4, 4)
    t = Tile(0, px)
    t.flip_v()
    assert np.array_equal(t.image(), np.flipud(px))
    t = Tile(0, px); t.rotate(); t.flip_h()
    assert np.array_equal(t.image(), np.fliplr(np.rot90(px, -1)))
    t = Tile(0, px); t.rotate(); t.flip_h(); t.flip_h(); t.rotate(3)
    assert t.upright()


if __name__ == "__main__":
    test_scramble_and_solve(); test_player_controls_can_solve_every_tile_state(); test_orientation_matches_pixels()
    print("All tests passed")
