import streamlit as st

from simplex import gomory_integer, solve_integer
from simplex.dual import dual_simplex

def show_instructions():
    st.title("Инструкция по применению")
    st.markdown("""
    ### Как задать задачу

    1. **Выберите тип задачи:**  
       * Максимум — коэффициенты целевой функции используются как есть  
       * Минимум — коэффициенты целевой функции автоматически домножаются на -1

     2. **Выберите метод решения:**  
         * Симплекс — классический симплекс-метод  
         * Гомори — метод разрезов Гомори для поиска целочисленного решения
         * Ветвей и границ — метод ветвей и границ для целочисленного программирования

    3. **Ввод ограничений:**  
       * Для каждого ограничения выберите знак: ≤, ≥ или =  
       * Введите коэффициенты и правую часть для каждого ограничения  
       * Шаг изменения коэффициентов и правых частей — 1

    4. **Формат:**  
       * Все переменные по умолчанию считаются неотрицательными (x₁ ≥ 0, x₂ ≥ 0, ...)

    5. **Пример:**  
       ```
       min Z = 2x₁ + 3x₂
       x₁ + x₂ ≥ 4
       2x₁ + x₂ ≤ 10
       ```
       В интерфейсе выберите "Минимум", задайте коэффициенты целевой функции,  
       для первого ограничения выберите знак ≥, для второго — ≤.

    6. **Результаты:**  
       * Для задачи на минимум итоговое значение целевой функции автоматически пересчитывается обратно.
       * История итераций симплекс-метода доступна для просмотра.
       * Для целочисленных методов (Гомори, Ветвей и границ) переменные в решении будут целыми числами.
    """)


def main():
    st.set_page_config(
        page_title="Симплекс калькулятор",
        page_icon="🧮",
    )
    tabs = st.tabs(["Калькулятор", "Инструкция"])

    with tabs[0]:
        st.title("Симплекс метод")

        method = st.selectbox(
            "Метод решения",
            ["Симплекс", "Гомори", "Ветвей и границ"]
        )

        opt_type = st.radio("Тип задачи", ["Максимум", "Минимум"], horizontal=True)

        col1, col2 = st.columns(2)
        with col1:
            n_vars = st.number_input("Количество переменных", min_value=1, max_value=8, value=3, step=1)
        with col2:
            n_constraints = st.number_input("Количество ограничений", min_value=1, max_value=6, value=2, step=1)

        st.subheader("Целевая функция")
        obj_coeffs = []
        cols = st.columns(int(n_vars))
        for i in range(n_vars):
            with cols[i]:
                coef = st.number_input(f"x{i+1}", key=f"obj_{i}", step=1.0, format="%.6g")
                obj_coeffs.append(coef)

        if opt_type == "Минимум":
            obj_coeffs = [-c for c in obj_coeffs]

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
                    coef = st.number_input(f"x{j+1}", key=f"cons_{i}_{j}", step=1.0, format="%.6g")
                    row.append(coef)
            with cols[-2]:
                sense = st.selectbox("Тип", options=["≤", "≥", "="], key=f"sense_{i}")
                sense_map = {"≤": "<=", "≥": ">=", "=": "=="}
                sense_std = sense_map[sense]
            with cols[-1]:
                rhs = st.number_input("Правая часть", key=f"rhs_{i}", step=1.0, format="%.6g")
            A.append(row)
            b.append(rhs)
            senses.append(sense_std)

        if st.button("Решить"):
            if method == "Симплекс":
                # use dual simplex implementation
                result = dual_simplex(obj_coeffs, A, b, senses)
            elif method == "Гомори":
                result = gomory_integer(obj_coeffs, A, b, senses)
            elif method == "Ветвей и границ":
                result, _ = solve_integer(obj_coeffs, A, b, senses)
            else:
                result = None

            st.subheader("Результаты")

            if result is not None and result.status == 'optimal':
                st.success("Найдено оптимальное решение!")
                st.write("Значения переменных:")
                for i, val in enumerate(result.x):
                    if abs(val) > 1e-8:
                        st.write(f"x{i+1} = {val:.4f}")
                if opt_type == "Минимум":
                    st.write(f"Оптимальное значение целевой функции: {-result.objective:.4f}")
                else:
                    st.write(f"Оптимальное значение целевой функции: {result.objective:.4f}")
                if getattr(result, "alternative", False):
                    st.info("Существует множество оптимальных решений")
            else:
                st.error({
                    'infeasible': "Задача несовместна (нет решений)",
                    'unbounded': "Задача неограничена (целевую функцию можно увеличивать неограниченно)",
                }.get(getattr(result, "status", None), "Не удалось найти решение"))

            if hasattr(result, "history") and result.history:
                st.subheader("История итераций")
                for i, tab in enumerate(result.history):
                    with st.expander(f"Итерация {i}"):
                        headers = [f"x{j+1}" for j in range(n_vars)]
                        headers += [f"s{j+1}" for j in range(len(tab[0]) - n_vars - 1)]
                        headers.append("b")
                        index = [f"Огр. {j+1}" for j in range(len(tab)-1)]
                        index.append("Z")
                        formatted_tab = [[f"{x:.4f}" for x in row] for row in tab]
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
