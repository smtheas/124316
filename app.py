import json
import requests
import pandas as pd

from dash import Dash, html, dcc, dash_table, Input, Output, State
import plotly.express as px


# =========================
# 1) НАСТРОЙКИ
# =========================
NOCODB_URL = "http://localhost:8080"
NOCODB_TOKEN = "ACmEJK3iMNyOH5ZCWCQo8RuzWp4lztVj5rQ_1VLQ"

# Таблица тем
THEMES_TABLE_ID = "mwfefucaxriw1rv"

# Таблицы-справочники
USERS_TABLE_ID = "mujcde4hjzjik8w"
MASTERS_TABLE_ID = "moys5sghfftwx4p"
STUDENTS_TABLE_ID = "mhs0t5v9vcqtwyc"

VIEW_ID = ""

# =========================
# 2) NocoDB helpers
# =========================
def nocodb_get_records(table_id: str, limit=1000, offset=0, where=None, view_id=None):
    url = f"{NOCODB_URL.rstrip('/')}/api/v2/tables/{table_id}/records"
    headers = {"xc-token": NOCODB_TOKEN}
    params = {"limit": limit, "offset": offset}
    if where:
        params["where"] = where
    if view_id:
        params["viewId"] = view_id

    r = requests.get(url, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    payload = r.json()
    return payload.get("list") or payload.get("data") or payload


def extract_id(x):
    if x is None:
        return None
    if isinstance(x, dict):
        return x.get("Id") if "Id" in x else x.get("id")
    if isinstance(x, (int, float)):
        return int(x)
    try:
        return int(str(x))
    except Exception:
        return None


def load_users_map():
    rows = nocodb_get_records(USERS_TABLE_ID, limit=2000)
    m = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        uid = extract_id(row.get("Id") if "Id" in row else row.get("id"))
        name = row.get("name")
        if uid is not None and name is not None:
            m[int(uid)] = str(name)
    return m


def load_master_to_name(users_map):
    rows = nocodb_get_records(MASTERS_TABLE_ID, limit=2000)
    m = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        master_id = extract_id(row.get("Id") if "Id" in row else row.get("id"))
        user_id = extract_id(row.get("user_id"))
        if master_id is None or user_id is None:
            continue
        m[int(master_id)] = users_map.get(int(user_id), f"User {user_id}")
    return m


def load_student_to_name(users_map):
    rows = nocodb_get_records(STUDENTS_TABLE_ID, limit=2000)
    m = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        student_id = extract_id(row.get("Id") if "Id" in row else row.get("id"))
        user_id = extract_id(row.get("user_id"))
        if student_id is None or user_id is None:
            continue
        m[int(student_id)] = users_map.get(int(user_id), f"User {user_id}")
    return m


def to_cell(v, master_to_name, student_to_name, users_map):
    if isinstance(v, dict):
        vid = extract_id(v)

        # master object?
        if "dept" in v or (vid is not None and vid in master_to_name):
            if vid is not None and vid in master_to_name:
                return master_to_name[vid]
            return v.get("dept") or json.dumps(v, ensure_ascii=False)

        # student object?
        if "spec" in v or "course" in v or (vid is not None and vid in student_to_name):
            if vid is not None and vid in student_to_name:
                return student_to_name[vid]
            return v.get("spec") or json.dumps(v, ensure_ascii=False)

        # user link?
        if vid is not None and vid in users_map:
            return users_map[vid]

        if "name" in v and v["name"] is not None:
            return v["name"]

        return json.dumps(v, ensure_ascii=False)

    if isinstance(v, list):
        parts = [to_cell(item, master_to_name, student_to_name, users_map) for item in v]
        parts = [str(p) for p in parts if p is not None and str(p).strip() != ""]
        return ", ".join(parts)

    return v


# =========================
# 3) СКРЫТЬ СЛУЖЕБНЫЕ СТОЛБЦЫ
# =========================
HIDE_EXACT = {"Id", "CreatedAt", "UpdatedAt"}
HIDE_PREFIXES = ("nc_", "_nc_", "nc_ipg3__", "nc_m2m_", "__nc_")


def filter_columns(df: pd.DataFrame) -> pd.DataFrame:
    keep = []
    for c in df.columns:
        if c in HIDE_EXACT:
            continue
        cl = str(c)
        if any(cl.startswith(p) for p in HIDE_PREFIXES):
            continue
        keep.append(c)
    return df[keep]


# =========================
# 4) Графики
# =========================
def pick_type_column(df: pd.DataFrame):
    candidates = ["type", "work_type", "workType", "Тип", "тип", "Тип работы", "тип работы"]
    for c in candidates:
        if c in df.columns:
            return c
    return None


def pick_teacher_column(df: pd.DataFrame):
    candidates = ["masters", "master", "преподаватель", "Преподаватель", "руководитель", "Руководитель"]
    for c in candidates:
        if c in df.columns:
            return c
    return None


def make_fig_type_counts(df: pd.DataFrame):
    col = pick_type_column(df)
    if col is None:
        return px.bar(title="Не найдена колонка типа работы (type/work_type/Тип...)")

    tmp = df.copy()
    tmp[col] = tmp[col].fillna("").astype(str).str.strip()
    tmp = tmp[tmp[col] != ""]
    counts = tmp[col].value_counts().reset_index()
    counts.columns = ["Тип работы", "Количество"]
    return px.bar(counts, x="Тип работы", y="Количество", title="Сколько работ каждого типа")


def make_fig_teacher_counts(df: pd.DataFrame):
    col = pick_teacher_column(df)
    if col is None:
        return px.bar(title="Не найдена колонка преподавателя (masters/Преподаватель...)")

    s = df[col].fillna("").astype(str)

    # если несколько преподавателей через запятую
    s = s.apply(lambda x: [p.strip() for p in x.split(",")] if x.strip() else [])
    teachers = s.explode()
    teachers = teachers[teachers.notna() & (teachers != "")]
    counts = teachers.value_counts().reset_index()
    counts.columns = ["Преподаватель", "Количество тем"]
    return px.bar(counts, x="Преподаватель", y="Количество тем", title="Сколько тем у каждого преподавателя")


# =========================
# 5) DASH APP
# =========================
app = Dash(__name__)
app.layout = html.Div(
    style={"maxWidth": "1200px", "margin": "24px auto", "fontFamily": "Arial"},
    children=[
        html.H2("Dash ↔ NocoDB (таблица + графики)"),

        html.Div(
            style={"display": "flex", "gap": "8px", "alignItems": "center"},
            children=[
                dcc.Input(id="where", placeholder="where (опционально)", style={"flex": "1"}),
                html.Button("Обновить", id="refresh"),
            ],
        ),

        html.Div(id="err", style={"color": "crimson", "marginTop": "8px"}),

        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "14px", "marginTop": "12px"},
            children=[
                dcc.Graph(id="fig_types"),
                dcc.Graph(id="fig_teachers"),
            ],
        ),

        dash_table.DataTable(
            id="table",
            page_size=15,
            style_table={"overflowX": "auto", "marginTop": "12px"},
            style_cell={"textAlign": "left", "padding": "8px"},
            filter_action="native",
            sort_action="native",
            page_action="native",
        ),
    ],
)


@app.callback(
    Output("table", "data"),
    Output("table", "columns"),
    Output("fig_types", "figure"),
    Output("fig_teachers", "figure"),
    Output("err", "children"),
    Input("refresh", "n_clicks"),
    State("where", "value"),
)
def refresh_all(_, where_value):
    try:
        users_map = load_users_map()
        master_to_name = load_master_to_name(users_map)
        student_to_name = load_student_to_name(users_map)

        rows = nocodb_get_records(
            THEMES_TABLE_ID,
            limit=2000,
            offset=0,
            where=where_value or None,
            view_id=VIEW_ID or None
        )
        df = pd.DataFrame(rows)

        if df.empty:
            fig1 = px.bar(title="Нет данных")
            fig2 = px.bar(title="Нет данных")
            return [], [], fig1, fig2, "Нет данных (или фильтр ничего не нашёл)."

        # 1) делаем значения красивыми (имена вместо json)
        df = df.map(lambda x: to_cell(x, master_to_name, student_to_name, users_map))

        # 2) убираем служебные колонки
        df = filter_columns(df)

        # 3) графики
        fig1 = make_fig_type_counts(df)
        fig2 = make_fig_teacher_counts(df)

        # 4) DataTable
        cols = [{"name": c, "id": c} for c in df.columns]
        return df.to_dict("records"), cols, fig1, fig2, ""

    except Exception as e:
        fig1 = px.bar(title="Ошибка")
        fig2 = px.bar(title="Ошибка")
        return [], [], fig1, fig2, f"Ошибка: {e}"


if __name__ == "__main__":
    app.run(debug=True)