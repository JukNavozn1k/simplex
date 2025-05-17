import streamlit as st

from simplex import simplex, solve_integer

def show_instructions():
    st.title("Инструкция по применению")
    st.markdown("""
    ### Как задать задачу

    1. **Выберите тип задачи:**  
       * Максимум — коэффициенты целевой функции используются как есть  
       * Минимум — коэффициенты целевой функции автоматически домножаются на -1

    2. **Ввод ограничений:**  
       * Для каждого ограничения выберите знак: ≤, ≥ или =  
       * Введите коэффициенты и правую часть для каждого ограничения

    3. **Формат:**  
       * Все переменные по умолчанию считаются неотрицательными (x₁ ≥ 0, x₂ ≥ 0, ...)

    4. **Пример:**  
       ```
       min Z = 2x₁ + 3x₂
       x₁ + x₂ ≥ 4
       2x₁ + x₂ ≤ 10
       ```
       В интерфейсе выберите "Минимум", задайте коэффициенты целевой функции,  
       для первого ограничения выберите знак ≥, для второго — ≤.

    5. **Результаты:**  
       * Для задачи на минимум итоговое значение целевой функции автоматически пересчитывается обратно.
       * История итераций симплекс-метода доступна для просмотра.

    """)


def main():
    st.set_page_config(
        page_title="Симплекс калькулятор",
        page_icon="🧮",
    )
    tabs = st.tabs(["Калькулятор", "Инструкция"])

    with tabs[0]:
        st.title("Симплекс метод")

        method = st.selectbox("Метод решения", ["Симплекс", "Ветвление и границы (BnB)"])

        # Новый выбор: максимум/минимум
        opt_type = st.radio("Тип задачи", ["Максимум", "Минимум"], horizontal=True)

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

        # Преобразование коэффициентов для минимума
        if opt_type == "Минимум":
            obj_coeffs = [-c for c in obj_coeffs]

        # Input for constraints
        st.subheader("Ограничения")
        A = []
        b = []
        senses = []
        for i in range(n_constraints):
            st.write(f"Ограничение {i+1}")
            row = []
            cols = st.columns(n_vars + 2)
            for j in range(n_vars):
                with cols[j]:
                    coef = st.number_input(f"x{j+1}", key=f"cons_{i}_{j}")
                    row.append(coef)
            with cols[-2]:
                # Используем символы ≤, ≥, =
                sense = st.selectbox("Тип", options=["≤", "≥", "="], key=f"sense_{i}")
                # Преобразуем к формату для simplex
                sense_map = {"≤": "<=", "≥": ">=", "=": "=="}
                sense_std = sense_map[sense]
            with cols[-1]:
                rhs = st.number_input("Правая часть", key=f"rhs_{i}")
            A.append(row)
            b.append(rhs)
            senses.append(sense_std)

        if st.button("Решить"):
            if method == "Симплекс":
                result = simplex(obj_coeffs, A, b, senses)
            else:
                result, x_int = solve_integer(obj_coeffs, A, b, senses)

            st.subheader("Результаты")

            if result.status == 'optimal':
                st.success("Найдено оптимальное решение!")
                st.write("Значения переменных:")
                if method == "Симплекс":
                    for i, val in enumerate(result.x):
                        if abs(val) > 1e-8:
                            st.write(f"x{i+1} = {val:.4f}")
                    # Для минимума меняем знак обратно
                    if opt_type == "Минимум":
                        st.write(f"Оптимальное значение целевой функции: {-result.objective:.4f}")
                    else:
                        st.write(f"Оптимальное значение целевой функции: {result.objective:.4f}")
                    if getattr(result, "alternative", False):
                        st.info("Существует множество оптимальных решений")
                else:
                    for i, val in enumerate(result.x):
                        st.write(f"x{i+1} = {val}")
                    if opt_type == "Минимум":
                        st.write(f"Оптимальное значение целевой функции: {-result.objective:.4f}")
                    else:
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
