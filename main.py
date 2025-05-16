import streamlit as st

from simplex import simplex, solve_integer

def show_instructions():
    st.title("Инструкция по применению")
    st.markdown("""
    ### Подготовка задачи к решению

    1. **Для задачи минимизации:**
       * Необходимо домножить целевую функцию на -1
       * Пример: min Z = 2x₁ + 3x₂ → max Z = -2x₁ - 3x₂

    2. **Для ограничений типа ≤ (стандартная форма):**
       * Симплекс метод работает с ограничениями вида ≤
       * Если у вас ограничение вида ≥, домножьте его на -1
       * Пример: x₁ + x₂ ≥ 4 → -x₁ - x₂ ≤ -4
    
    ### Пример преобразования задачи:
    ```
    min Z = 2x₁ + 3x₂
    x₁ + x₂ ≥ 4      | × (-1)
    2x₁ + x₂ ≤ 10    | оставляем как есть
    ```
    
    Преобразуется в:
    ```
    max Z = -2x₁ - 3x₂
    -x₁ - x₂ ≤ -4
    2x₁ + x₂ ≤ 10
    ```
    """)


def main():
    st.set_page_config(
        page_title="Симплекс калькулятор",
        page_icon="🧮",
    )
    tabs = st.tabs(["Калькулятор", "Инструкция"])

    with tabs[0]:
        st.title("Симплекс метод")

        # Метод решения — в самом начале
        method = st.selectbox("Метод решения", ["Симплекс", "Ветвление и границы (BnB)"])

        # Input dimensions
        col1, col2 = st.columns(2)
        with col1:
            n_vars = st.number_input("Количество переменных", min_value=1, max_value=8, value=3)
        with col2:
            n_constraints = st.number_input("Количество ограничений", min_value=1, max_value=6, value=2)

        # Input for objective function
        st.subheader("Целевая функция")
        obj_coeffs = []
        cols = st.columns(int(n_vars))
        for i in range(n_vars):
            with cols[i]:
                coef = st.number_input(f"x{i+1}", key=f"obj_{i}")
                obj_coeffs.append(coef)

        # Input for constraints
        st.subheader("Ограничения")
        A = []
        b = []
        for i in range(n_constraints):
            st.write(f"Ограничение {i+1}")
            row = []
            cols = st.columns(n_vars + 1)
            for j in range(n_vars):
                with cols[j]:
                    coef = st.number_input(f"x{j+1}", key=f"cons_{i}_{j}")
                    row.append(coef)
            with cols[-1]:
                rhs = st.number_input("≤", key=f"rhs_{i}")
            A.append(row)
            b.append(rhs)

        if st.button("Решить"):
            if method == "Симплекс":
                result = simplex(obj_coeffs, A, b)
            else:
                result, x_int = solve_integer(obj_coeffs, A, b)

            st.subheader("Результаты")

            if result.status == 'optimal':
                st.success("Найдено оптимальное решение!")
                st.write("Значения переменных:")
                if method == "Симплекс":
                    for i, val in enumerate(result.x):
                        if abs(val) > 1e-8:
                            st.write(f"x{i+1} = {val:.4f}")
                    st.write(f"Оптимальное значение целевой функции: {result.objective:.4f}")
                    if getattr(result, "alternative", False):
                        st.info("Существует множество оптимальных решений")
                else:
                    for i, val in enumerate(result.x):
                        st.write(f"x{i+1} = {val}")
                    st.write(f"Оптимальное значение целевой функции: {result.objective:.4f}")
            else:
                st.error({
                    'infeasible': "Задача несовместна (нет решений)",
                    'unbounded': "Задача неограничена (целевую функцию можно увеличивать неограниченно)",
                }.get(result.status, "Не удалось найти решение"))

            # История итераций — в самом конце
            if hasattr(result, "history") and result.history:
                st.subheader("История итераций")
                for i, tab in enumerate(result.history):
                    with st.expander(f"Итерация {i}"):
                        # Формируем заголовки: переменные + "b"
                        headers = [f"x{j+1}" for j in range(n_vars)]
                        headers += [f"s{j+1}" for j in range(len(tab[0]) - n_vars - 1)]
                        headers.append("b")
                        # Индексы строк: ограничения и Z
                        index = [f"Огр. {j+1}" for j in range(len(tab)-1)]
                        index.append("Z")
                        # Форматируем значения
                        formatted_tab = [[f"{x:.4f}" for x in row] for row in tab]
                        # Собираем таблицу для отображения
                        table_data = {
                            "": index,
                            **{headers[j]: [row[j] for row in formatted_tab]
                               for j in range(len(headers))}
                        }
                        st.dataframe(table_data)

    with tabs[1]:
        show_instructions()

if __name__ == "__main__":
    main()
