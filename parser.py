import streamlit as st
import pandas as pd
from pandasql import sqldf
from bs4 import BeautifulSoup
from datetime import datetime

st.set_page_config(layout="wide")

def fmt_date(ts):
    try:
        ts = int(ts)
        if ts > 1e11: 
            ts //= 1000000
        return datetime.fromtimestamp(ts).strftime("%d.%m.%Y")
    except: 
        return "—"

st.sidebar.title("Инструменты")
app_mode = st.sidebar.radio("Меню", ["SQL Парсер", "Парсер закладок"])

if app_mode == "SQL Парсер":
    st.title("SQL Парсер баз данных")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        uploaded = st.file_uploader("Загрузите csv-файл", type=["csv"])
        
    if uploaded:
        df = pd.read_csv(uploaded)
        
        with col2:
            m1, m2, m3 = st.columns(3)
            m1.metric("Строки", len(df))
            m2.metric("Столбцы", len(df.columns))
            m3.metric("Размер", f"{uploaded.size/1024:.1f} KB")

        st.divider()
        
        cols = df.columns.tolist()
        selected_cols = st.sidebar.multiselect("Выберите столбцы", cols, default=cols)
        st.dataframe(df[selected_cols], use_container_width=True)

        st.header("SQL Запросы")
        st.info("Имя таблицы для запросов: df")
        query = st.text_area("SQL запрос", "")

        if st.button("Выполнить"):
            try:
                res = sqldf(query, {"df": df})
                st.dataframe(res, use_container_width=True)
                
                csv = res.to_csv(index=False).encode("utf-8")
                st.download_button("Скачать результат (CSV)", csv, "result.csv", "text/csv")
            except Exception as e:
                st.error(str(e))

elif app_mode == "Парсер закладок":
    st.title("Парсер закладок браузера")
    st.markdown("---")
    
    owner = st.sidebar.text_input("Пользователь", placeholder="Имя")
    file = st.file_uploader("Загрузите HTML файл", type="html")

    if file:
        soup = BeautifulSoup(file.read(), "html.parser")
        data = []
        stack = []

        for item in soup.find_all(["h3", "a"]):
            is_folder = item.name == "h3"
            depth = len(item.find_parents("dl"))
            
            if is_folder:
                stack = stack[:depth - 1] + [item.get_text(strip=True)]
                path = "/".join(stack[:-1]) if len(stack) > 1 else "Корень"
            else:
                path = "/".join(stack) if depth == len(stack) + 1 else "Корень"

            data.append({
                "Тип": "Папка" if is_folder else "Ссылка",
                "Название": item.get_text(strip=True),
                "Путь": path,
                "URL": item.get("href", "—"),
                "Дата": fmt_date(item.get("add_date")),
                "Владелец": owner or "Не указан"
            })

        df = pd.DataFrame(data)
        
        c1, c2 = st.columns(2)
        with c1:
            choice = st.selectbox("Фильтр по типу", ["Все", "Папка", "Ссылка"])
        with c2:
            search = st.text_input("Поиск по названию")

        if choice != "Все":
            df = df[df["Тип"] == choice]
        if search:
            df = df[df["Название"].str.contains(search, case=False, na=False)]

        st.dataframe(df, use_container_width=True)
        
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button("Скачать таблицу (CSV)", csv_data, "bookmarks.csv", "text/csv")
