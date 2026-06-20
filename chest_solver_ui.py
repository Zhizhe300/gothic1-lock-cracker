import tkinter as tk
from collections import deque
from tkinter import messagebox, ttk


MIN_POS = -3
MAX_POS = 3

NONE = "none"
RIGHT = "right"
LEFT = "left"

TEXT = {
    "ru": {
        "title": "Решатель сундуков",
        "bolt_count": "Количество задвижек:",
        "start_positions": "Стартовые позиции:",
        "load_sample": "Загрузить пример",
        "clear_effects": "Очистить связи",
        "solve": "Решить",
        "help": (
            "Позиции: -3..+3, где 0 - центр. Например: +3 -1 -2 +2 -2 +2\n"
            "В таблице указывается, что делает задвижка-строка с задвижкой-столбцом, "
            "когда строка двигается вправо. При движении влево эффект автоматически обратный."
        ),
        "table_title": "Связи при движении задвижки вправо",
        "result_title": "Результат",
        "moves": "двигает ->",
        "row_right": "{num} вправо",
        "self": "сама",
        "input_error": "Ошибка ввода",
        "need_positions": "Нужно указать ровно {count} позиций.",
        "bad_position": "Не могу прочитать позицию: {value}",
        "range_error": "Все позиции должны быть в диапазоне от -3 до +3.",
        "start": "Старт",
        "already_open": "Уже открыто: все пины стоят по центру.",
        "no_solution": "Решение не найдено. Проверь связи или стартовые позиции.",
        "solution_found": "Решение найдено за {steps} ходов.",
        "bolt": "Задвижка",
        "none_label": "-",
        "right_label": "вправо",
        "left_label": "влево",
    },
    "en": {
        "title": "Chest Lock Solver",
        "bolt_count": "Bolt count:",
        "start_positions": "Start positions:",
        "load_sample": "Load sample",
        "clear_effects": "Clear links",
        "solve": "Solve",
        "help": (
            "Positions: -3..+3, where 0 is the center. Example: +3 -1 -2 +2 -2 +2\n"
            "The table describes what each row bolt does to each column bolt when the row bolt moves right. "
            "When the row bolt moves left, every linked effect is automatically reversed."
        ),
        "table_title": "Links when a bolt moves right",
        "result_title": "Result",
        "moves": "moves ->",
        "row_right": "{num} right",
        "self": "self",
        "input_error": "Input error",
        "need_positions": "Enter exactly {count} positions.",
        "bad_position": "Cannot parse position: {value}",
        "range_error": "All positions must be in the -3..+3 range.",
        "start": "Start",
        "already_open": "Already open: all pins are centered.",
        "no_solution": "No solution found. Check the links or start positions.",
        "solution_found": "Solution found in {steps} moves.",
        "bolt": "Bolt",
        "none_label": "-",
        "right_label": "right",
        "left_label": "left",
    },
}


class ChestSolverApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.minsize(920, 640)

        self.language = tk.StringVar(value="ru")
        self.bolt_count = tk.IntVar(value=6)
        self.start_positions = tk.StringVar(value="+3 -1 -2 +2 -2 +2")
        self.effects = []
        self.effect_boxes = []

        self._build_ui()
        self._reset_effects()
        self.load_sample()
        self._refresh_language()

    def _build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)

        top = ttk.Frame(root)
        top.pack(fill=tk.X)

        self.bolt_count_label = ttk.Label(top)
        self.bolt_count_label.pack(side=tk.LEFT)

        count_box = ttk.Spinbox(
            top,
            from_=4,
            to=7,
            width=5,
            textvariable=self.bolt_count,
            command=self._on_count_changed,
            state="readonly",
        )
        count_box.pack(side=tk.LEFT, padx=(6, 18))

        self.start_positions_label = ttk.Label(top)
        self.start_positions_label.pack(side=tk.LEFT)
        ttk.Entry(top, textvariable=self.start_positions, width=32).pack(side=tk.LEFT, padx=6)

        self.load_sample_button = ttk.Button(top, command=self.load_sample)
        self.load_sample_button.pack(side=tk.LEFT, padx=4)

        self.clear_effects_button = ttk.Button(top, command=self.clear_effects)
        self.clear_effects_button.pack(side=tk.LEFT, padx=4)

        self.solve_button = ttk.Button(top, command=self.solve)
        self.solve_button.pack(side=tk.LEFT, padx=(16, 0))

        ttk.Label(top, text="Language:").pack(side=tk.LEFT, padx=(18, 4))
        language_box = ttk.Combobox(
            top,
            textvariable=self.language,
            values=("ru", "en"),
            width=4,
            state="readonly",
        )
        language_box.pack(side=tk.LEFT)
        language_box.bind("<<ComboboxSelected>>", lambda _event: self._refresh_language())

        self.help_label = ttk.Label(root, justify=tk.LEFT)
        self.help_label.pack(fill=tk.X, pady=(10, 8))

        self.table_outer = ttk.LabelFrame(root)
        self.table_outer.pack(fill=tk.X, pady=(0, 10))

        self.table_frame = ttk.Frame(self.table_outer, padding=8)
        self.table_frame.pack(fill=tk.X)

        self.result_frame = ttk.LabelFrame(root)
        self.result_frame.pack(fill=tk.BOTH, expand=True)

        self.result = tk.Text(self.result_frame, wrap=tk.NONE, height=18)
        self.result.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        y_scroll = ttk.Scrollbar(self.result_frame, orient=tk.VERTICAL, command=self.result.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.result.configure(yscrollcommand=y_scroll.set)

    def _text(self, key, **kwargs):
        value = TEXT[self.language.get()][key]
        return value.format(**kwargs) if kwargs else value

    def _display_to_effect(self, value):
        labels = TEXT[self.language.get()]
        if value == labels["right_label"]:
            return RIGHT
        if value == labels["left_label"]:
            return LEFT
        return NONE

    def _effect_to_display(self, value):
        labels = TEXT[self.language.get()]
        if value == RIGHT:
            return labels["right_label"]
        if value == LEFT:
            return labels["left_label"]
        return labels["none_label"]

    def _refresh_language(self):
        self.title(self._text("title"))
        self.bolt_count_label.configure(text=self._text("bolt_count"))
        self.start_positions_label.configure(text=self._text("start_positions"))
        self.load_sample_button.configure(text=self._text("load_sample"))
        self.clear_effects_button.configure(text=self._text("clear_effects"))
        self.solve_button.configure(text=self._text("solve"))
        self.help_label.configure(text=self._text("help"))
        self.table_outer.configure(text=self._text("table_title"))
        self.result_frame.configure(text=self._text("result_title"))
        self._rebuild_effect_table()

    def _on_count_changed(self):
        self._reset_effects()
        self._rebuild_effect_table()

    def _reset_effects(self):
        n = self._safe_bolt_count()
        self.effects = [[NONE for _ in range(n)] for _ in range(n)]

    def _rebuild_effect_table(self):
        if not hasattr(self, "table_frame"):
            return

        for child in self.table_frame.winfo_children():
            child.destroy()

        n = self._safe_bolt_count()
        self.effect_boxes = []

        ttk.Label(self.table_frame, text=self._text("moves")).grid(row=0, column=0, padx=3, pady=3)
        for col in range(n):
            ttk.Label(self.table_frame, text=f"{col + 1}").grid(row=0, column=col + 1, padx=3, pady=3)

        values = (
            self._text("none_label"),
            self._text("left_label"),
            self._text("right_label"),
        )
        for row in range(n):
            ttk.Label(self.table_frame, text=self._text("row_right", num=row + 1)).grid(
                row=row + 1,
                column=0,
                sticky="e",
                padx=3,
                pady=3,
            )
            box_row = []
            for col in range(n):
                if row == col:
                    ttk.Label(self.table_frame, text=self._text("self")).grid(row=row + 1, column=col + 1, padx=3, pady=3)
                    box_row.append(None)
                    continue
                var = tk.StringVar(value=self._effect_to_display(self.effects[row][col]))
                box = ttk.Combobox(self.table_frame, textvariable=var, values=values, width=8, state="readonly")
                box.grid(row=row + 1, column=col + 1, padx=3, pady=3)
                box.bind("<<ComboboxSelected>>", self._make_effect_handler(row, col, var))
                box_row.append((box, var))
            self.effect_boxes.append(box_row)

    def _make_effect_handler(self, row, col, var):
        def handler(_event):
            self.effects[row][col] = self._display_to_effect(var.get())

        return handler

    def _safe_bolt_count(self):
        try:
            return max(4, min(7, int(self.bolt_count.get())))
        except (tk.TclError, ValueError):
            return 4

    def clear_effects(self):
        self._reset_effects()
        self._rebuild_effect_table()

    def load_sample(self):
        self.bolt_count.set(6)
        self.start_positions.set("+3 -1 -2 +2 -2 +2")
        self._reset_effects()

        self.effects[0][1] = LEFT
        self.effects[0][2] = LEFT
        self.effects[0][4] = LEFT
        self.effects[2][5] = LEFT
        self.effects[3][4] = RIGHT
        self.effects[3][5] = LEFT
        self.effects[4][3] = RIGHT
        self.effects[5][3] = LEFT
        self._rebuild_effect_table()

    def solve(self):
        try:
            start = self._parse_start_positions()
            effects = self._read_effects()
        except ValueError as exc:
            messagebox.showerror(self._text("input_error"), str(exc))
            return

        solution = find_solution(start, effects)
        self._show_solution(start, effects, solution)

    def _parse_start_positions(self):
        n = self._safe_bolt_count()
        raw_parts = self.start_positions.get().replace(",", " ").split()
        if len(raw_parts) != n:
            raise ValueError(self._text("need_positions", count=n))

        positions = []
        for part in raw_parts:
            try:
                value = int(part)
            except ValueError as exc:
                raise ValueError(self._text("bad_position", value=part)) from exc
            if value < MIN_POS or value > MAX_POS:
                raise ValueError(self._text("range_error"))
            positions.append(value)

        return tuple(positions)

    def _read_effects(self):
        n = self._safe_bolt_count()
        values = [[0 for _ in range(n)] for _ in range(n)]
        for driver in range(n):
            for target in range(n):
                if driver == target:
                    continue
                if self.effects[driver][target] == RIGHT:
                    values[driver][target] = 1
                elif self.effects[driver][target] == LEFT:
                    values[driver][target] = -1
        return values

    def _show_solution(self, start, effects, solution):
        self.result.delete("1.0", tk.END)
        self.result.insert(tk.END, f"{self._text('start')}: {format_state(start)}\n")

        if start == tuple(0 for _ in start):
            self.result.insert(tk.END, self._text("already_open") + "\n")
            return

        if solution is None:
            self.result.insert(tk.END, self._text("no_solution") + "\n")
            return

        self.result.insert(tk.END, self._text("solution_found", steps=len(solution)) + "\n\n")
        state = start
        for step, action in enumerate(solution, start=1):
            driver, direction = action
            state = apply_action(state, effects, driver, direction)
            self.result.insert(
                tk.END,
                f"{step:02d}. {self._text('bolt')} {driver + 1} {direction_name(direction, self.language.get()):6s} -> {format_state(state)}\n",
            )


def find_solution(start, effects):
    goal = tuple(0 for _ in start)
    if start == goal:
        return []

    queue = deque([start])
    parents = {start: (None, None)}

    while queue:
        state = queue.popleft()
        for driver in range(len(state)):
            for direction in (1, -1):
                next_state = apply_action(state, effects, driver, direction)
                if next_state is None or next_state in parents:
                    continue
                parents[next_state] = (state, (driver, direction))
                if next_state == goal:
                    return restore_path(parents, next_state)
                queue.append(next_state)

    return None


def apply_action(state, effects, driver, direction):
    next_state = list(state)

    # A pin shifts opposite to the physical movement of its bolt.
    next_state[driver] -= direction

    for target, effect_when_right in enumerate(effects[driver]):
        if target == driver or effect_when_right == 0:
            continue
        physical_direction = effect_when_right * direction
        next_state[target] -= physical_direction

    if any(value < MIN_POS or value > MAX_POS for value in next_state):
        return None
    return tuple(next_state)


def restore_path(parents, state):
    path = []
    while True:
        previous, action = parents[state]
        if previous is None:
            break
        path.append(action)
        state = previous
    path.reverse()
    return path


def direction_name(direction, language="ru"):
    key = "right_label" if direction == 1 else "left_label"
    return TEXT[language][key]


def format_state(state):
    return " ".join(f"{value:+d}" if value else " 0" for value in state)


if __name__ == "__main__":
    app = ChestSolverApp()
    app.mainloop()
