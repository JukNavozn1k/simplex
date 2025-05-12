import streamlit as st

from simplex import simplex

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
    # st.set_page_config(layout="wide")
    
    tabs = st.tabs(["Калькулятор", "Инструкция"])
    
    with tabs[0]:
        st.title("Симплекс метод")
        
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
        constraints = []
        for i in range(n_constraints):
            st.write(f"Ограничение {i+1}")
            row = []
            cols = st.columns(n_vars + 1)
            
            # Coefficients
            for j in range(n_vars):
                with cols[j]:
                    coef = st.number_input(f"x{j+1}", key=f"cons_{i}_{j}")
                    row.append(coef)
            
            # RHS
            with cols[-1]:
                rhs = st.number_input("≤", key=f"rhs_{i}")
                row.append(rhs)
            
            constraints.append(row)
        
        if st.button("Решить"):
            # Prepare tableau
            tableau = constraints.copy()
            tableau.append(obj_coeffs + [0])  # Add objective function row
            
            # Initial basis (assuming last m variables are basic)
            basis = list(range(n_vars - n_constraints, n_vars))
            
            # Solve
            result = simplex(tableau, basis)
            
            # Display results
            st.subheader("Результаты")
            
            if result['status'] == 'optimal':
                st.success("Найдено оптимальное решение!")
                
                # Display solution
                st.write("Значения переменных:")
                for i, val in enumerate(result['solution']):
                    if abs(val) > 1e-8:  # Show only non-zero values
                        st.write(f"x{i+1} = {val:.4f}")
                
                st.write(f"Оптимальное значение целевой функции: {result['optimal_value']:.4f}")
                
                if result['multiple_solutions']:
                    st.info("Существует множество оптимальных решений")
                    
                # Display iteration history
                st.subheader("История итераций")
                for i, tab in enumerate(result['tableau_history']):
                    with st.expander(f"Итерация {i}"):
                        # Create headers for variables and slack variables
                        headers = [f"x{j+1}" for j in range(n_vars)]
                        headers.append("b")  # Add RHS column header
                        
                        # Create row indices
                        index = [f"Огр. {i+1}" for i in range(n_constraints)]
                        index.append("Z")  # Add objective function row label
                        
                        # Format data with labels
                        formatted_tab = [[f"{x:.4f}" for x in row] for row in tab]
                        
                        # Create a dictionary for the table with labels
                        table_data = {
                            "": index,  # Empty string for index column header
                            **{headers[j]: [row[j] for row in formatted_tab] 
                               for j in range(len(headers))}
                        }
                        
                        st.dataframe(table_data)
            else:
                st.error(result['message'])
    
    with tabs[1]:
        show_instructions()
    

if __name__ == "__main__":
    main()
