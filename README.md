## Features
- Choose a **3×3 (default), 4×4 or 5×5** grid before loading an image
- Seven car pictures included in `images/`, plus **Random Image** and **Load Image** for any picture of your own
- OpenCV resizes the image to fit the screen, crops it so it divides evenly, splits it into tiles and merges them back for display
- On load, a random scramble is applied: **6, 12 or 20 transformations** (n × (n − 1)), always including at least one swap, one rotation and one flip
- Original image on the left (reference only), scrambled image on the right (clickable) with a faint grid
- A green tick on every tile that is in the correct position **and** orientation
- Live **move counter** and **incorrect-tile counter**
- **Hint** (max 3 per image): circles a wrong tile and its home cell; the circle clears on the next move
- **Solve**: undoes every transformation and clears the moves and score
- A message appears when the puzzle is complete, and the board locks until a new image is loaded

## Requirements
- Python 3.9 or newer (with Tkinter – included in the standard python.org installers)
- Packages in `requirements.txt` (OpenCV, NumPy, Pillow)

## How to run
```bash
pip install -r requirements.txt
python app.py
```
Pick a grid size, then click **Load Image** (opens the `images` folder) or **Random Image** for a random picture from it.
To play with your own pictures, drop `.jpg` / `.png` files into the `images` folder.

Run the logic tests with:
```bash
python test_puzzle.py
```

## Controls
| Action | Result |
|--------|--------|
| Left click a tile | Select it (coloured border) |
| Left click a second tile | Swap the two tiles |
| Left click the selected tile again | Deselect |
| Right click a tile | Rotate 90° clockwise |
| Shift + left click a tile | Flip horizontally |
| Hint button | Show one incorrect tile and its home position |
| Solve button | Restore the whole image |

Every swap, rotation and flip counts as one move.

> **Tip:** a tile only gets a tick when it is in the right place *and* upright. Tiles with
> similar content on both sides (sky, trees, road) can look right while still being mirrored or
> rotated, so go by the ticks. For an upside-down tile: Shift + click once, then right-click twice
> (a vertical flip equals a horizontal flip plus a 180° turn).

## Project structure
```
puzzle_game/
├── app.py            # Tkinter GUI (PuzzleApp)
├── puzzle.py         # Game logic and OpenCV code
├── test_puzzle.py    # Logic tests
├── images/           # Pictures to play with (add your own)
├── requirements.txt
├── .gitignore
├── github_link.txt   # Link to this repository
└── README.md
```

## Object-oriented design
| Class | File | Concept shown |
|-------|------|---------------|
| `ImageProcessor` | puzzle.py | OpenCV work: load, resize, crop, split, merge (static methods) |
| `Tile` | puzzle.py | **Encapsulation** – home index, rotation and flip are private and changed only through methods |
| `Transformation` | puzzle.py | **Base class** with `apply()` and `undo()` |
| `Swap`, `Rotate`, `Flip` | puzzle.py | **Inheritance and polymorphism** – each overrides `apply()` and `undo()` |
| `Board` | puzzle.py | **Class interaction** – owns the tiles, builds the scramble, runs and logs moves, gives hints |
| `PuzzleApp(tk.Tk)` | app.py | GUI; inherits from `tk.Tk` and uses `Board` and `ImageProcessor` |

**Constructors** (`__init__`) are used in every class. **Solve** works by calling `undo()` on the
logged transformations in reverse order, so it restores the exact original image.

### How tile orientation is tracked
Each tile stores `rotation` (0–3 quarter turns) and `flipped` (true/false). Rotating adds one
turn. Flipping toggles `flipped` and reverses the rotation, because a mirror reverses the
turning direction. A tile is correct when `position == home`, `rotation == 0` and `not flipped`.


