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
            for i in range(m + 1):
                row = []
                for j in range(n + 1):
                    entry = ttk.Entry(self.table_frame, width=8)
                    entry.grid(row=i+1, column=j+1, padx=2, pady=2)
                    row.append(entry)
                self.cells.append(row)
                if i < m:
                    ttk.Label(self.table_frame, text=f"Огр. {i+1}").grid(row=i+1, column=0)
                else:
                    ttk.Label(self.table_frame, text="Z(max)").grid(row=i+1, column=0)

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
            for i in range(m + 1):
                row = []
                for j in range(n + 1):
                    value = float(self.cells[i][j].get().replace(',', '.'))
                    row.append(value)
                tableau.append(row)

            # Начальный базис (предполагаем, что базисные переменные - последние m переменных)
            basis = list(range(n - m, n))

            # Решаем задачу
            result = simplex(tableau, basis)

            # Выводим результаты
            self.result_text.delete(1.0, tk.END)
            
            if result['status'] == 'optimal':
                self.result_text.insert(tk.END, "Найдено оптимальное решение:\n\n")
                for i, val in enumerate(result['solution']):
                    self.result_text.insert(tk.END, f"x{i+1} = {val:.4f}\n")
                self.result_text.insert(tk.END, f"\nОптимальное значение: {result['optimal_value']:.4f}\n")
                if result['multiple_solutions']:
                    self.result_text.insert(tk.END, "\nЕсть множество оптимальных решений")
            else:
                self.result_text.insert(tk.END, f"Статус: {result['message']}")

        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте правильность введенных данных")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

def run():
    root = tk.Tk()
    app = SimplexGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run()
