import tkinter as tk
from tkinter import ttk
from collections import deque

BOARD_SIZE = 5
CENTER = (2, 2)  # 0-based (row, col)

EMPTY = 0
GREEN = 1
BLUE = 2
BARRIER = 3
HOLE = 4

COLORS = {
    EMPTY: "white",
    GREEN: "green",
    BLUE: "blue",
    BARRIER: "grey",
    HOLE: "black",
}

ARROWS = {
    (-1, 0): "↑",
    (1, 0):  "↓",
    (0, -1): "←",
    (0, 1):  "→",
}

class TiltPuzzleSolver:
    def __init__(self, board):
        self.start_board = board
        self.states_tried = 0  # for stats

    @staticmethod
    def serialize(greens, blues):
        return (tuple(sorted(greens)), tuple(sorted(blues)))

    def move(self, greens, blues, direction, barriers):
        """Tilt once in `direction` with 'slide until stop' physics.
        Returns (new_greens, new_blues) or None if a blue falls in the hole."""
        dx, dy = direction
        all_pins = list(greens) + list(blues)
        moved_greens, moved_blues = set(), set()

        occupied = set(barriers)  # only barriers & settled tokens matter

        # Order ensures correct blocking behavior
        if dx == 1:      # down
            order = sorted(all_pins, key=lambda rc: -rc[0])
        elif dx == -1:   # up
            order = sorted(all_pins, key=lambda rc: rc[0])
        elif dy == 1:    # right
            order = sorted(all_pins, key=lambda rc: -rc[1])
        else:            # left
            order = sorted(all_pins, key=lambda rc: rc[1])

        for (r, c) in order:
            color = GREEN if (r, c) in greens else BLUE
            nr, nc = r, c
            while True:
                tr, tc = nr + dx, nc + dy

                # off board?
                if not (0 <= tr < BOARD_SIZE and 0 <= tc < BOARD_SIZE):
                    break

                # HOLE check must happen first
                if (tr, tc) == CENTER:
                    nr, nc = tr, tc
                    break

                # obstacle (barrier or already-settled pin)?
                if (tr, tc) in occupied:
                    break

                # free to slide
                nr, nc = tr, tc

            if (nr, nc) == CENTER:
                if color == BLUE:
                    return None  # invalid: blue fell in
                continue  # green sunk, remove
            else:
                occupied.add((nr, nc))
                if color == GREEN:
                    moved_greens.add((nr, nc))
                else:
                    moved_blues.add((nr, nc))

        return moved_greens, moved_blues

    def solve(self):
        greens = {(i, j) for i in range(BOARD_SIZE) for j in range(BOARD_SIZE) if self.start_board[i][j] == GREEN}
        blues  = {(i, j) for i in range(BOARD_SIZE) for j in range(BOARD_SIZE) if self.start_board[i][j] == BLUE}
        barriers = {(i, j) for i in range(BOARD_SIZE) for j in range(BOARD_SIZE) if self.start_board[i][j] == BARRIER}

        start = self.serialize(greens, blues)
        q = deque([(greens, blues, "")])
        visited = {start}

        directions = [(-1,0), (1,0), (0,-1), (0,1)]  # up, down, left, right

        while q:
            g, b, path = q.popleft()
            self.states_tried += 1
            if not g:  # all greens sunk
                return path
            for d in directions:
                moved = self.move(g, b, d, barriers)
                if moved is None:
                    continue
                ng, nb = moved
                state = self.serialize(ng, nb)
                if state not in visited:
                    visited.add(state)
                    q.append((ng, nb, path + ARROWS[d]))
        return None

class TiltPuzzleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tilty Tokens Solver")
        self.root.attributes("-topmost", True)

        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.board[CENTER[0]][CENTER[1]] = HOLE

        self.canvas_size = 420
        self.canvas = tk.Canvas(root, width=self.canvas_size, height=self.canvas_size, bg="white")
        self.canvas.grid(row=0, column=0, columnspan=5)
        self.canvas.bind("<Button-1>", self.place_token)
        self.canvas.bind("<Button-3>", self.erase_token)

        self.mode = tk.StringVar(value="GREEN")
        tk.Radiobutton(root, text="Green pin (1)",  variable=self.mode, value="GREEN").grid(row=1, column=0, sticky="w")
        tk.Radiobutton(root, text="Blue pin (2)",   variable=self.mode, value="BLUE").grid(row=1, column=1, sticky="w")
        tk.Radiobutton(root, text="Barrier (3)", variable=self.mode, value="BARRIER").grid(row=1, column=2, sticky="w")
        tk.Button(root, text="Solve", command=self.solve).grid(row=1, column=3, sticky="e")
        
        # New "Clear board" button
        self.clear_button = tk.Button(root, text="Clear board (c)", command=self.clear_board)
        self.clear_button.grid(row=1, column=4, sticky="e")
        
        self.status = tk.StringVar(value="Left-click to place; right-click to erase. Center hole is fixed.")
        tk.Label(root, textvariable=self.status).grid(row=2, column=0, columnspan=5, sticky="w")

        self.draw_board()

        # New key bindings
        self.root.bind('<Key-1>', lambda event: self.set_mode("GREEN"))
        self.root.bind('<Key-2>', lambda event: self.set_mode("BLUE"))
        self.root.bind('<Key-3>', lambda event: self.set_mode("BARRIER"))
        self.root.bind('<Key-c>', lambda event: self.clear_board())

    def set_mode(self, new_mode):
        self.mode.set(new_mode)

    def draw_board(self):
        self.canvas.delete("all")
        cell = self.canvas_size // BOARD_SIZE
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                x1, y1 = j * cell, i * cell
                x2, y2 = x1 + cell, y1 + cell
                color = COLORS[self.board[i][j]]
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")
                # barrier X
                if self.board[i][j] == BARRIER:
                    self.canvas.create_line(x1+4, y1+4, x2-4, y2-4, width=2)
                    self.canvas.create_line(x1+4, y2-4, x2-4, y1+4, width=2)
                # 1-based coordinate overlay
                self.canvas.create_text(x1+10, y1+10, text=f"{i+1},{j+1}", anchor="nw", font=("TkDefaultFont", 8))
        # draw center hole on top
        i, j = CENTER
        x1, y1 = j * cell, i * cell
        x2, y2 = x1 + cell, y1 + cell
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLORS[HOLE], outline="black")

    def place_token(self, event):
        cell = self.canvas_size // BOARD_SIZE
        j, i = event.x // cell, event.y // cell
        if (i, j) == CENTER:
            return
        mode = self.mode.get()
        self.board[i][j] = {"GREEN": GREEN, "BLUE": BLUE, "BARRIER": BARRIER}[mode]
        self.draw_board()

    def erase_token(self, event):
        cell = self.canvas_size // BOARD_SIZE
        j, i = event.x // cell, event.y // cell
        if (i, j) == CENTER:
            return
        self.board[i][j] = EMPTY
        self.draw_board()

    def clear_board(self):
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                self.board[i][j] = EMPTY
        self.board[CENTER[0]][CENTER[1]] = HOLE
        self.draw_board()

    def popup_result(self, seq, states_tried):
        win = tk.Toplevel(self.root)
        win.title("Solution")
        win.attributes("-topmost", True)
        win.grab_set()

        if seq is None:
            ttk.Label(win, text="No solution found.").pack(padx=10, pady=10)
        else:
            ttk.Label(win, text=f"Shortest Solution: {seq}", font=("TkDefaultFont", 12, "bold")).pack(padx=10, pady=5)
            ttk.Label(win, text=f"Length: {len(seq)} moves").pack(padx=10, pady=2)
        ttk.Label(win, text=f"States tried: {states_tried}").pack(padx=10, pady=5)

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)

    def solve(self):
        solver = TiltPuzzleSolver(self.board)
        seq = solver.solve()
        self.popup_result(seq, solver.states_tried)

if __name__ == "__main__":
    root = tk.Tk()
    app = TiltPuzzleGUI(root)
    root.mainloop()
