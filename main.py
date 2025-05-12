import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from simplex import simplex

class SimplexGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Симплекс метод")
        self.root.geometry("800x600")

        # Создаем фреймы
        self.input_frame = ttk.LabelFrame(root, text="Ввод данных", padding=10)
        self.input_frame.pack(fill="x", padx=5, pady=5)

        self.result_frame = ttk.LabelFrame(root, text="Результаты", padding=10)
        self.result_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Элементы ввода размерности
        ttk.Label(self.input_frame, text="Количество переменных:").grid(row=0, column=0, padx=5, pady=5)
        self.vars_entry = ttk.Entry(self.input_frame, width=10)
        self.vars_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.input_frame, text="Количество ограничений:").grid(row=0, column=2, padx=5, pady=5)
        self.constraints_entry = ttk.Entry(self.input_frame, width=10)
        self.constraints_entry.grid(row=0, column=3, padx=5, pady=5)

        self.create_table_btn = ttk.Button(self.input_frame, text="Создать таблицу", command=self.create_table)
        self.create_table_btn.grid(row=0, column=4, padx=5, pady=5)

        # Фрейм для таблицы
        self.table_frame = ttk.Frame(self.input_frame)
        self.table_frame.grid(row=1, column=0, columnspan=5, padx=5, pady=5)

        # Текстовое поле для вывода результатов
        self.result_text = scrolledtext.ScrolledText(self.result_frame, height=10)
        self.result_text.pack(fill="both", expand=True)

    def create_table(self):
        try:
            n = int(self.vars_entry.get())
            m = int(self.constraints_entry.get())

            # Очищаем предыдущую таблицу
            for widget in self.table_frame.winfo_children():
                widget.destroy()

            # Создаем заголовки
            for j in range(n):
                ttk.Label(self.table_frame, text=f"x{j+1}").grid(row=0, column=j+1)
            ttk.Label(self.table_frame, text="b").grid(row=0, column=n+1)

            # Создаем ячейки для ввода
            self.cells = []
            # Сначала создаем строки ограничений
            for i in range(m):
                row = []
                for j in range(n + 1):  # включая столбец b
                    entry = ttk.Entry(self.table_frame, width=8)
                    entry.grid(row=i+1, column=j+1, padx=2, pady=2)
                    row.append(entry)
                self.cells.append(row)
                ttk.Label(self.table_frame, text=f"Огр. {i+1}").grid(row=i+1, column=0)

            # Создаем строку целевой функции
            row = []
            for j in range(n):
                entry = ttk.Entry(self.table_frame, width=8)
                entry.grid(row=m+1, column=j+1, padx=2, pady=2)
                row.append(entry)
            self.cells.append(row)
            ttk.Label(self.table_frame, text="Z(max)").grid(row=m+1, column=0)

            # Кнопка решения
            self.solve_btn = ttk.Button(self.table_frame, text="Решить", command=self.solve)
            self.solve_btn.grid(row=m+2, column=0, columnspan=n+2, pady=10)

        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числа")

    def solve(self):
        try:
            n = int(self.vars_entry.get())
            m = int(self.constraints_entry.get())

            # Собираем данные из таблицы
            tableau = []
            # Собираем строки ограничений
            for i in range(m):
                row = []
                for j in range(n + 1):
                    value = float(self.cells[i][j].get().replace(',', '.'))
                    row.append(value)
                tableau.append(row)
            
            # Собираем коэффициенты целевой функции
            objective_coeffs = []
            for j in range(n):
                value = float(self.cells[m][j].get().replace(',', '.'))
                objective_coeffs.append(value)
            
            # Вычисляем начальное значение целевой функции
            initial_z = 0
            tableau.append(objective_coeffs + [initial_z])

            # Начальный базис (предполагаем, что базисные переменные - последние m переменных)
            basis = list(range(n - m, n))

            # Решаем задачу
            result = simplex(tableau, basis)

            # Выводим результаты
            self.result_text.delete(1.0, tk.END)
            
            # Выводим начальную таблицу
            self.result_text.insert(tk.END, "Начальная симплекс-таблица:\n")
            self._print_tableau(result['tableau_history'][0])
            self.result_text.insert(tk.END, "\n")

            # Выводим промежуточные итерации
            if len(result['tableau_history']) > 2:
                self.result_text.insert(tk.END, "Промежуточные итерации:\n")
                for i, tab in enumerate(result['tableau_history'][1:-1], 1):
                    self.result_text.insert(tk.END, f"\nИтерация {i}:\n")
                    self._print_tableau(tab)

            # Выводим финальную таблицу
            self.result_text.insert(tk.END, "\nФинальная симплекс-таблица:\n")
            self._print_tableau(result['tableau'])
            self.result_text.insert(tk.END, "\n")

            # При выводе таблиц добавляем текущее значение Z
            self.result_text.insert(tk.END, "\nТекущее значение целевой функции:\n")
            current_solution = [0.0] * n
            for i in range(m):
                if basis[i] < n:  # проверяем, что это не вспомогательная переменная
                    current_solution[basis[i]] = tableau[i][-1]
            
            z_value = sum(coef * val for coef, val in zip(objective_coeffs, current_solution))
            self.result_text.insert(tk.END, f"Z = {z_value:.4f}\n")

            # Выводим результат
            if result['status'] == 'optimal':
                self.result_text.insert(tk.END, "Найдено оптимальное решение:\n")
                for i, val in enumerate(result['solution']):
                    if abs(val) > 1e-8:  # Выводим только ненулевые значения
                        self.result_text.insert(tk.END, f"x{i+1} = {val:.4f}\n")
                self.result_text.insert(tk.END, f"\nОптимальное значение целевой функции: {result['optimal_value']:.4f}\n")
                if result['multiple_solutions']:
                    self.result_text.insert(tk.END, "\nЕсть множество оптимальных решений")
            else:
                self.result_text.insert(tk.END, f"Статус: {result['message']}")

        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте правильность введенных данных")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _print_tableau(self, tableau):
        """Вспомогательный метод для форматированного вывода таблицы"""
        for row in tableau:
            line = " | ".join(f"{x:8.4f}" for x in row)
            self.result_text.insert(tk.END, line + "\n")

def run():
    root = tk.Tk()
    app = SimplexGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run()
