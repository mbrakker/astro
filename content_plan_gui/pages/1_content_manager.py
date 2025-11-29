# content_plan_gui/content_manager.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from core.rule_loader import load_rules_full
from core.content_types import CONTENT_TYPES
import streamlit as st
import pandas as pd
from core.content_service import (
    get_all_topics, update_topics, add_new_topic
)

st.set_page_config(page_title="Управление контентом", layout="wide")
st.title("📋 Управление контентом")

with st.expander("🔍 Фильтры"):
    selected_type = st.selectbox("Тип контента", options=["Все"] + get_all_topics("types"), index=0)
    selected_status = st.selectbox("Статус", options=["Все"] + get_all_topics("statuses"), index=0)

# Загрузка и фильтрация данных
df = get_all_topics("dataframe")

if selected_type != "Все":
    df = df[df["type"] == selected_type]
if selected_status != "Все":
    df = df[df["status"] == selected_status]

st.markdown(f"### ✨ Темы ({len(df)} шт.)")
edited_df = st.data_editor(
    df,
    use_container_width=True,
    num_rows="dynamic",
    disabled=["id", "created_at", "published_at"]
)

# Обновление тем
if st.button("💾 Сохранить изменения"):
    result = update_topics(edited_df)
    st.success(f"Обновлено строк: {result}")

# Добавление новых тем
st.markdown("---")
st.subheader("➕ Добавить новые темы в канал **main**")

# 🔎 Определяем допустимые типы контента (scope = main)

# Загружаем правила публикации
rules_data = load_rules_full()
rules = rules_data.get("rules", [])

# Оставляем только типы, у которых scope = main
main_types = sorted({
    rule["type"] for rule in rules if rule.get("scope") == "main"
})

selected_type = st.selectbox("Тип контента", main_types)
count = st.slider("Количество тем", 10, 100, 20)

if st.button("🛠 Добавить темы"):
    import sqlite3
    from datetime import datetime

    DB_PATH = "/opt/astro_bot/history/content_topics.db"
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.now().isoformat()

    for _ in range(count):
        cur.execute("""
            INSERT INTO topics (type, theme, status, channel_scope, created_at)
            VALUES (?, 'Автодобавление', 'pending', 'main', ?)
        """, (selected_type, now))

    conn.commit()
    conn.close()
    st.success(f"✅ Добавлено {count} тем с типом {selected_type} в канал main")

st.markdown("---")
st.subheader("➕ Добавить новые темы в канал **zodiac**")

from core.rule_loader import load_rules_full

# Загрузка правил
rules_data = load_rules_full()
rules = rules_data.get("rules", [])

# Фильтрация типов с scope = zodiac
zodiac_types = sorted({
    rule["type"] for rule in rules if rule.get("scope") == "zodiac"
})

# ✅ Выбор типа контента
selected_z_type = st.selectbox("Тип контента", zodiac_types, key="zodiac_type")

# ✅ Мультивыбор знаков зодиака с опцией "все"
ZODIAC_SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"
]
ALL_SIGNS_LABEL = "🌌 Все знаки зодиака"

sign_options = [ALL_SIGNS_LABEL] + ZODIAC_SIGNS
raw_selection = st.multiselect("Выбери знаки зодиака", sign_options, default=[])

# Обработка выбора
if ALL_SIGNS_LABEL in raw_selection:
    selected_signs = ZODIAC_SIGNS
else:
    selected_signs = raw_selection

# ✅ Количество тем (на каждый знак)
z_count = st.slider("Количество тем на каждый знак", 1, 20, 1)

# ✅ Кнопка добавления
if st.button("🛠 Добавить темы для канала zodiac"):
    import sqlite3
    from datetime import datetime

    if not selected_signs:
        st.warning("⚠️ Выбери хотя бы один знак")
    else:
        DB_PATH = "/opt/astro_bot/history/content_topics.db"
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        now = datetime.now().isoformat()

        for sign in selected_signs:
            for _ in range(z_count):
                cur.execute("""
                    INSERT INTO topics (type, theme, status, channel_scope, target_sign, created_at)
                    VALUES (?, 'Автодобавление', 'pending', 'zodiac', ?, ?)
                """, (selected_z_type, sign, now))

        conn.commit()
        conn.close()
        st.success(f"✅ Добавлено {len(selected_signs) * z_count} тем в канал zodiac по типу {selected_z_type}")
