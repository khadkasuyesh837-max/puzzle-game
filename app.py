"""Tkinter GUI for the image puzzle game."""
import glob
import os
import random
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk

from puzzle import Board, Flip, ImageProcessor, Rotate, Swap

IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")


class PuzzleApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Puzzle Game")
        self.board = None
        self.selected = None          
        self.hint = None              
        self.locked = True
        self.tile = 0                
        self.max_size = min((self.winfo_screenwidth() - 120) // 2,
                            self.winfo_screenheight() - 260, 520)

        bar = tk.Frame(self)
        bar.pack(pady=6)
        tk.Label(bar, text="Grid size:").pack(side="left")
        self.grid_var = tk.IntVar(value=3)
        for n in (3, 4, 5):
            tk.Radiobutton(bar, text=f"{n}x{n}", variable=self.grid_var, value=n).pack(side="left")
        tk.Button(bar, text="Load Image", command=self.load_image).pack(side="left", padx=8)
        tk.Button(bar, text="Random Image", command=self.random_image).pack(side="left")
        self.hint_btn = tk.Button(bar, text="Hint", command=self.show_hint, state="disabled")
        self.hint_btn.pack(side="left")
        self.solve_btn = tk.Button(bar, text="Solve", command=self.solve, state="disabled")
        self.solve_btn.pack(side="left", padx=8)

        views = tk.Frame(self)
        views.pack(padx=10)
        tk.Label(views, text="Original (reference)").grid(row=0, column=0)
        tk.Label(views, text="Puzzle (click here)").grid(row=0, column=1)
        self.left = tk.Canvas(views, bg="#eeeeee", highlightthickness=0)
        self.right = tk.Canvas(views, bg="#eeeeee", highlightthickness=0)
        self.left.grid(row=1, column=0, padx=8, pady=4)
        self.right.grid(row=1, column=1, padx=8, pady=4)
        self.status = tk.Label(self, text="Choose a grid size, then load an image.")
        self.status.pack(pady=6)

        self.right.bind("<Button-1>", self.on_left_click)
        self.right.bind("<Shift-Button-1>", self.on_shift_click)
        self.right.bind("<Button-3>", self.on_right_click)
        self.right.bind("<Button-2>", self.on_right_click)      

    # ---------- loading ----------
    def load_image(self):
        path = filedialog.askopenfilename(
            initialdir=IMAGE_DIR if os.path.isdir(IMAGE_DIR) else None,
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")])
        if path:
            self.load_path(path)

    def random_image(self):
        files = glob.glob(os.path.join(IMAGE_DIR, "*.[jp][pn]g"))
        if files:
            self.load_path(random.choice(files))
        else:
            messagebox.showinfo("No images", "Put some pictures in the 'images' folder.")

    def load_path(self, path):
        try:
            img = ImageProcessor.load(path)
        except ValueError as error:
            messagebox.showerror("Error", str(error))
            return
        grid = self.grid_var.get()
        img = ImageProcessor.prepare(img, grid, self.max_size)
        self.board = Board(img, grid)
        self.tile = img.shape[0] // grid
        size = img.shape[0]
        self.left.config(width=size, height=size)
        self.right.config(width=size, height=size)
        self.left_photo = ImageTk.PhotoImage(Image.fromarray(img))
        self.left.delete("all")
        self.left.create_image(0, 0, anchor="nw", image=self.left_photo)
        self.selected = self.hint = None
        self.locked = False
        self.solve_btn.config(state="normal")
        self.draw()

    # ---------- drawing ----------
    def cell(self, pos):
        n = self.board.grid
        return (pos % n) * self.tile, (pos // n) * self.tile

    def circle(self, canvas, pos):
        x, y = self.cell(pos)
        m = self.tile * 0.15
        canvas.create_oval(x + m, y + m, x + self.tile - m, y + self.tile - m,
                           outline="blue", width=4, tags="hint")

    def draw(self):
        b, t = self.board, self.tile
        self.right_photo = ImageTk.PhotoImage(Image.fromarray(b.image()))
        self.right.delete("all")
        self.right.create_image(0, 0, anchor="nw", image=self.right_photo)
        for i in range(1, b.grid):                                  
            self.right.create_line(i * t, 0, i * t, t * b.grid, fill="#dddddd")
            self.right.create_line(0, i * t, t * b.grid, i * t, fill="#dddddd")
        s = max(8, t // 8)
        for pos in range(len(b.tiles)):                             
            if b.is_correct(pos):
                x, y = self.cell(pos)
                x, y = x + t - 4 * s // 3, y + s // 2
                self.right.create_line(x - 2 * s, y + s, x - s, y + 2 * s, x, y,
                                       fill="green", width=4)
        if self.selected is not None:
            x, y = self.cell(self.selected)
            self.right.create_rectangle(x + 2, y + 2, x + t - 2, y + t - 2,
                                        outline="orange", width=4)
        self.left.delete("hint")
        if self.hint is not None:
            self.circle(self.right, self.hint)
            self.circle(self.left, b.tiles[self.hint].home)
        self.status.config(text=f"Moves: {b.moves}   |   Incorrect tiles: "
                                f"{len(b.wrong_positions())}   |   Hints left: {b.hints_left}")
        self.hint_btn.config(state="disabled" if self.locked or b.hints_left == 0 else "normal")
        self.solve_btn.config(state="disabled" if self.locked else "normal")

    # ---------- interaction ----------
    def tile_at(self, event):
        if self.locked:
            return None
        col, row = event.x // self.tile, event.y // self.tile
        n = self.board.grid
        return row * n + col if 0 <= col < n and 0 <= row < n else None

    def on_left_click(self, event):
        pos = self.tile_at(event)
        if pos is None:
            return
        if self.selected is None:
            self.selected = pos
            self.draw()
        elif self.selected == pos:
            self.selected = None
            self.draw()
        else:
            first, self.selected = self.selected, None
            self.play(Swap(first, pos))

    def on_right_click(self, event):
        pos = self.tile_at(event)
        if pos is not None:
            self.selected = None
            self.play(Rotate(pos))                                   

    def on_shift_click(self, event):
        pos = self.tile_at(event)
        if pos is not None:
            self.selected = None
            self.play(Flip(pos))                                      

    def play(self, transformation):
        self.board.play(transformation)
        self.hint = None                                            
        if self.board.is_solved():
            self.locked = True
            self.draw()
            messagebox.showinfo("Well done!", f"Puzzle solved in {self.board.moves} moves!")
        else:
            self.draw()

    def show_hint(self):
        pos = self.board.hint()
        if pos is not None:
            self.hint = pos
            self.draw()

    def solve(self):
        self.board.solve()
        self.selected = self.hint = None
        self.locked = True
        self.draw()


if __name__ == "__main__":
    PuzzleApp().mainloop()
