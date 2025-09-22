import streamlit as st

from simplex import gomory_integer, solve_integer
from simplex.dual import dual_simplex


def main():
    st.set_page_config(
        page_title="Симплекс калькулятор",
        page_icon="🧮",
    )
  


    st.title("🧮 Симплекс калькулятор")

    method = st.selectbox(
        "Метод решения",
        ["Симплекс", "Ветвей и границ", "Гомори"]
    )

    opt_type = st.radio("Тип задачи", ["Максимум", "Минимум"], horizontal=True)

    col1, col2 = st.columns(2)
    with col1:
        n_vars = st.number_input("Количество переменных", min_value=1, max_value=8, value=2, step=1)
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

    # Дополнительные параметры метода
    gomory_max_cuts = None
    if method == "Гомори":
        gomory_max_cuts = st.number_input(
            "Макс. число срезов (итераций Гомори)", min_value=1, max_value=500, value=50, step=1,
            help="Ограничивает количество добавляемых резок Гомори."
        )

    if st.button("Решить"):
        # Сбрасываем сохранённое дерево BnB перед каждым новым запуском решения,
        # чтобы не показывать граф от предыдущей задачи
        if "bnb_tree" in st.session_state:
            st.session_state.pop("bnb_tree", None)
        st.session_state["bnb_tree_present"] = False
        if method == "Симплекс":
            # use dual simplex implementation
            result = dual_simplex(obj_coeffs, A, b, senses)
        elif method == "Гомори":
            # Передаем max_cuts для нового Гомори
            result = gomory_integer(obj_coeffs, A, b, senses, max_cuts=int(gomory_max_cuts) if gomory_max_cuts else 50)
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
            status = getattr(result, "status", None)
            msg = {
                'infeasible': "Задача несовместна (нет решений)",
                'unbounded': "Задача неограничена (целевую функцию можно увеличивать неограниченно)",
                'max_iter_exceeded': "Достигнут предел числа срезов Гомори до нахождения целочисленного решения",
            }.get(status, "Не удалось найти решение")
            if status == 'max_iter_exceeded':
                st.warning(msg)
            else:
                st.error(msg)

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

        # Сохраняем только дерево BnB в сессию (объект простого словаря), чтобы UI не пропадал при любом ререндере
        if method == "Ветвей и границ" and hasattr(result, "bnb_tree") and result.bnb_tree:
            st.session_state["bnb_tree"] = result.bnb_tree
            st.session_state["bnb_tree_present"] = True
        else:
            # Если дерево не получено (другая методика или нет решения) — сбрасываем флаг,
            # чтобы не отображать дерево от предыдущей задачи
            st.session_state["bnb_tree_present"] = False

        # (удалено) В методе ветвей и границ не показываем финальные ограничения и финальную симплекс-таблицу

        # Дерево ветвей и границ (визуализация графом + панель деталей узла)
        # Берём дерево из текущего результата или из сессии
        tree_to_show = None
        if method == "Ветвей и границ":
            if 'result' in locals() and result is not None and hasattr(result, "bnb_tree") and result.bnb_tree:
                tree_to_show = result.bnb_tree
            elif st.session_state.get("bnb_tree_present"):
                tree_to_show = st.session_state.get("bnb_tree")
        if tree_to_show:
            st.subheader("Дерево ветвей и границ")

            # Явно показываем целевую функцию задачи
            def format_obj(coefs):
                terms = []
                for j, c in enumerate(coefs):
                    if abs(c) < 1e-12:
                        continue
                    sign = "+" if c >= 0 else "-"
                    val = abs(c)
                    if len(terms) == 0:
                        terms.append(("- " if c < 0 else "") + (f"{val:.4g}·x{j+1}" if val != 1 else f"x{j+1}"))
                    else:
                        terms.append(f" {sign} " + (f"{val:.4g}·x{j+1}" if val != 1 else f"x{j+1}"))
                return "".join(terms) if terms else "0"

            if opt_type == "Минимум":
                shown_type = "Минимизация"
                shown_coefs = [-c for c in obj_coeffs]
            else:
                shown_type = "Максимизация"
                shown_coefs = obj_coeffs
            st.info(f"{shown_type}: Z = {format_obj(shown_coefs)}")

            # Построение индекса узлов и дуг (используем путь как ID)
            def node_label(node):
                node_type = node.get('type') or 'root'
                var = node.get('var')
                bound = node.get('bound')
                obj = node.get('lp_objective')
                vtxt = (f"x{var+1}" if var is not None else '-')
                btxt = (f"{bound}" if bound is not None else '-')
                ztxt = (f"{obj:.4f}" if isinstance(obj, (int, float)) else '-')
                return f"{node_type}\n{vtxt} @ {btxt}\nz={ztxt}"

            nodes = []  # list of dicts: {id, label, tableau, basis}
            edges = []  # list of (parent_id, child_id, branch_label)

            def traverse(node, path="root"):
                if not node:
                    return
                nodes.append({
                    'id': path,
                    'label': node_label(node),
                    'tableau': node.get('tableau'),
                    'basis': node.get('basis'),
                })
                if node.get('left'):
                    edges.append((path, path+"_L", "<="))
                    traverse(node['left'], path+"_L")
                if node.get('right'):
                    edges.append((path, path+"_R", ">="))
                    traverse(node['right'], path+"_R")

            # Функции для вычисления значений переменных из таблицы и базиса
            def basis_labels_from_tableau(tab):
                if not tab:
                    return []
                total_cols = len(tab[0]) - 1
                labels = [f"x{j+1}" for j in range(n_vars)]
                slack_count = max(0, total_cols - n_vars)
                labels += [f"s{j+1}" for j in range(slack_count)]
                return labels

            def variable_values_from_node(node):
                tab = node.get('tableau')
                basis = node.get('basis')
                if not tab or not basis:
                    return []
                labels = basis_labels_from_tableau(tab)
                values = [0.0] * len(labels)
                for i, col in enumerate(basis):
                    if col is None:
                        continue
                    if 0 <= col < len(labels):
                        try:
                            values[col] = float(tab[i][-1])
                        except Exception:
                            values[col] = 0.0
                return list(zip(labels, values))

            def node_label(node):
                node_type = node.get('type') or 'root'
                var = node.get('var')
                bound = node.get('bound')
                obj = node.get('lp_objective')
                # Текст ветвления: для LE — x_k ≤ bound; для GE — x_k ≥ bound; для root — '-'
                if node_type == 'LE' and var is not None and bound is not None:
                    branch_txt = f"x{var+1} ≤ {bound}"
                elif node_type == 'GE' and var is not None and bound is not None:
                    branch_txt = f"x{var+1} ≥ {bound}"
                else:
                    branch_txt = "-"
                ztxt = (f"{obj:.4f}" if isinstance(obj, (int, float)) else '-')
                # Формируем строку значений переменных (x и slack) и помечаем переменную ветвления символом '*'
                pairs = variable_values_from_node(node)
                if pairs:
                    def fmt_pair(name, val):
                        mark = '*' if (var is not None and name == f"x{var+1}") else ''
                        return f"{name}{mark}={val:.3g}"
                    # показываем максимум 12 значений, чтобы не перегружать узел
                    vals_str = ", ".join(fmt_pair(nm, v) for nm, v in pairs[:12])
                else:
                    vals_str = ""
                # Многострочная подпись узла
                return f"{node_type}\n{branch_txt}\nz={ztxt}\n{vals_str}"

            nodes = []  # list of dicts: {id, label, tableau, basis}
            edges = []  # list of (parent_id, child_id, branch_label)

            def traverse(node, path="root"):
                if not node:
                    return
                nodes.append({
                    'id': path,
                    'label': node_label(node),
                    'tableau': node.get('tableau'),
                    'basis': node.get('basis'),
                })
                if node.get('left'):
                    edges.append((path, path+"_L", "≤"))
                    traverse(node['left'], path+"_L")
                if node.get('right'):
                    edges.append((path, path+"_R", "≥"))
                    traverse(node['right'], path+"_R")

            traverse(tree_to_show, "root")

            # Рисуем граф DOT
            dot_lines = [
                'digraph G {',
                '  rankdir=TB;',
                '  node [shape=box, fontname="Helvetica", fontsize=10];',
            ]
            for n in nodes:
                safe_label = n['label'].replace('"', '\"')
                dot_lines.append(f'  "{n["id"]}" [label="{safe_label}"];')
            for a, b, lab in edges:
                dot_lines.append(f'  "{a}" -> "{b}" [label="{lab}"];')
            dot_lines.append('}')
            # Отцентрируем граф: используем 3 колонки и помещаем диаграмму в центральную
            cols_graph = st.columns([1, 2, 1])
            with cols_graph[1]:
                st.graphviz_chart("\n".join(dot_lines))

            # Вспомогательные функции для отображения таблицы и базиса
            def render_tableau(tab, caption=None):
                if not tab:
                    return
                if caption:
                    st.caption(caption)
                headers_local = [f"x{j+1}" for j in range(n_vars)]
                headers_local += [f"s{j+1}" for j in range(len(tab[0]) - n_vars - 1)]
                headers_local.append("b")
                index_local = [f"Огр. {j+1}" for j in range(len(tab)-1)]
                index_local.append("Z")
                formatted_tab_local = [[f"{float(x):.4f}" for x in row] for row in tab]
                table_data_local = {
                    "": index_local,
                    **{headers_local[j]: [row[j] for row in formatted_tab_local]
                       for j in range(len(headers_local))}
                }
                st.dataframe(table_data_local)

            def render_basis(basis, tab):
                if not basis or not tab:
                    return
                labels = basis_labels_from_tableau(tab)
                rows = []
                for i, col in enumerate(basis):
                    if col is None or col < 0 or col >= len(labels):
                        rows.append(f"Огр.{i+1} -> -")
                    else:
                        rows.append(f"Огр.{i+1} -> {labels[col]}")
                st.write("Базис:")
                st.code("\n".join(rows))

            # (удалено) Панель деталей узла для метода ветвей и границ

   

if __name__ == "__main__":
    main()
