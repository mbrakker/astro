# content_plan_gui/pages/7_publish_rules.py

import streamlit as st
import sqlite3
import sys
import os
import pandas as pd

# Добавляем путь к src
SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.append(SRC_PATH)

from core import rule_loader
from core import content_types
from core import settings_config


DB_PATH = "/opt/astro_bot/history/content_topics.db"

DAYS_FULL = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAYS_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

st.set_page_config(page_title="Правила публикации", layout="wide")

st.markdown(
    """
    <style>
        /* Применяем к таблицам визуализации */
        table {
            table-layout: fixed;
            width: 100%;
            font-size: 14px;
        }
        th, td {
            width: 17ch;
            max-width: 17ch;
            word-wrap: break-word;
            text-align: left;
            vertical-align: top;
            padding: 0.4rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

rules_data = rule_loader.load_rules_full()
rules = rules_data.get("rules", [])
all_types = content_types.CONTENT_TYPES

def get_rule_for_type(rules, topic_type):
    for r in rules:
        if isinstance(r, dict) and r.get("type") == topic_type:
            return r
    return None

def get_all_types():
    return content_types.CONTENT_TYPES

def get_cell_data(rule, row):
    if not rule:
        return "—"
    mode = rule.get("mode", "daily")
    value = rule.get("value")

    if row == "Target channel":
        return rule.get("scope", "—")
    elif row == "Mode":
        return mode
    elif row == "Mode value":
        if mode == "daily":
            return "—"
        elif mode == "interval":
            return f"Every {value} days"
        elif mode == "weekdays":
            return ", ".join([d[:3] for d in value]) if value else "—"
        else:
            return str(value)

col1, col2 = st.columns([7, 5])

with col1:
    st.subheader("📋 Все правила публикации")

    row_labels = ["Target channel", "Mode", "Mode value"]
    table_data = {label: [] for label in row_labels}


    def get_cell_data(rule, row):
        if not rule:
            return "Правило не задано" if row == "Mode value" else "—"

        mode = rule.get("mode", "daily")
        value = rule.get("value")

        if row == "Target channel":
            return rule.get("scope", "—")
        elif row == "Mode":
            return mode
        elif row == "Mode value":
            if mode == "daily":
                return "—"
            elif mode == "interval":
                return f"Every {value} days"
            elif mode == "weekdays":
                return ", ".join([d[:3] for d in value]) if value else "—"
            else:
                return str(value)

    for topic_type in all_types:
        rule = get_rule_for_type(rules, topic_type)
        for row in row_labels:
            table_data[row].append(get_cell_data(rule, row))

    df = pd.DataFrame(table_data, index=all_types)
    df.reset_index(inplace=True)
    df.rename(columns={"index": "Content type"}, inplace=True)
    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

    
with col2:
    st.subheader("✏️ Изменить или задать правило")

    selected_type = st.selectbox("Тип контента", all_types)
    existing = get_rule_for_type(rules, selected_type)

    scope = st.selectbox(
        "Scope",
        ["main", "zodiac", "all"],
        index=["main", "zodiac", "all"].index(existing.get("scope", "main")) if existing else 0
    )

    mode = st.radio(
        "Режим публикации",
        options=["daily", "interval", "weekdays"],
        index=["daily", "interval", "weekdays"].index(existing.get("mode", "daily")) if existing else 0,
        horizontal=True
    )

    value = None
    if mode == "interval":
        default_interval = existing.get("value", 3) if existing and existing.get("mode") == "interval" else 3
        value = st.number_input("Каждые N дней", min_value=1, value=default_interval)
    elif mode == "weekdays":
        default_days = existing.get("value", []) if existing and existing.get("mode") == "weekdays" else []
        value = st.multiselect("Дни недели", DAYS_FULL, default=default_days)

    if st.button("💾 Сохранить правило", key="save_rule_btn"):
        new_rule = {
            "type": selected_type,
            "scope": scope,
            "mode": mode,
            "value": value
        }
        rule_loader.save_rule(new_rule)
        st.success("✅ Правило обновлено")
        st.rerun()

# === БЛОК: Управление источниками тем ===
st.subheader("📚 Управление источниками тем")

source_options = {
    "external": "🔗 Внешний источник",
    "generated": "✨ Генерация по теме"
}

topic_sources = rules_data.get("topic_sources", {})
updated_sources = {}

cols = st.columns(3)
for i, content_type in enumerate(get_all_types()):
    with cols[i % 3]:
        current = topic_sources.get(content_type, "generated")
        updated_sources[content_type] = st.radio(
            content_type,
            options=list(source_options.keys()),
            format_func=lambda k: source_options[k],
            index=list(source_options.keys()).index(current),
            key=f"source_{content_type}",
            horizontal=True
        )

if st.button("💾 Сохранить источники тем", key="save_sources"):
    rules_data["topic_sources"] = updated_sources
    rule_loader.save_rules_full(rules_data)
    st.success("✅ Источники тем обновлены")
    st.rerun()


st.subheader("📏 Лимиты публикаций в день")

settings = settings_config.load_settings()

col1, col2 = st.columns([1, 1])

with col1:
    min_posts = st.number_input(
        "Минимум публикаций в день:",
        min_value=0,
        max_value=10,
        value=rules_data.get("min_posts_per_day", 1),
        key="limits_min_posts"
    )

with col2:
    max_posts = st.number_input(
        "Максимум публикаций в день:",
        min_value=1,
        max_value=20,
        value=rules_data.get("max_posts_per_day", 4),
        key="limits_max_posts"
    )

st.markdown("")  # небольшой отступ


if st.button("💾 Сохранить лимиты", key="save_limits"):
    rules_data["min_posts_per_day"] = min_posts
    rules_data["max_posts_per_day"] = max_posts
    rule_loader.save_rules_full(rules_data)
    st.success("✅ Лимиты обновлены")
    st.rerun()

from datetime import datetime, timedelta
import calendar
from collections import defaultdict

# === Визуализация публикаций по правилам ===
st.subheader("📆 План публикаций на 4 недели")

rules = rules_data.get("rules", [])

# Эмодзи по типу контента
EMOJI_MAP = {
    "horoscope": "♈",
    "energy_day": "🌕",
    "zodiac_energy": "♌",
    "mystic_news": "📰",
    "confession": "🔥",
    "astro_basics": "📘"
}

# Получаем ближайший понедельник
today = datetime.today()
start_date = today - timedelta(days=today.weekday())

# План по каналам и дням: plan["main"][date] = [список рубрик]
plan = {"main": defaultdict(list), "zodiac": defaultdict(list)}

# Возвращает список дат, когда правило применяется
def get_active_dates(rule):
    mode = rule.get("mode")
    value = rule.get("value")
    dates = []

    for i in range(28):  # 4 недели
        date = start_date + timedelta(days=i)
        weekday = calendar.day_name[date.weekday()]  # "Monday", ...
        if mode == "daily":
            dates.append(date)
        elif mode == "interval":
            interval = int(value)
            if (i % interval) == 0:
                dates.append(date)
        elif mode == "weekdays":
            if weekday in value:
                dates.append(date)
    return dates

# Собираем публикации по дням
for rule in rules:
    scope = rule.get("scope", "main")
    topic_type = rule.get("type")
    emoji = EMOJI_MAP.get(topic_type, "🌀")
    name = topic_type.replace("_", " ").title()
    label = f"{emoji} {name}"
    for d in get_active_dates(rule):
        plan[scope][d].append(label)

# Формирует таблицу строка=неделя, столбцы=дни
def make_week_table(scope):
    rows = []
    for w in range(4):
        week_start = start_date + timedelta(days=w * 7)
        row = {}
        for d in range(7):
            date = week_start + timedelta(days=d)
            labels = plan[scope].get(date, [])
            row[calendar.day_abbr[date.weekday()]] = "<br>".join(labels)
        row_label = f"{scope.capitalize()} (Week {w+1})"
        rows.append((row_label, row))
    return rows

# Канал: main
st.markdown("### 🔸 Канал: main")
main_rows = make_week_table("main")
main_df = pd.DataFrame([r[1] for r in main_rows], index=[r[0] for r in main_rows])
st.markdown(main_df.to_html(escape=False), unsafe_allow_html=True)

# Канал: zodiac
st.markdown("### 🔹 Канал: zodiac")
zodiac_rows = make_week_table("zodiac")
zodiac_df = pd.DataFrame([r[1] for r in zodiac_rows], index=[r[0] for r in zodiac_rows])
st.markdown(zodiac_df.to_html(escape=False), unsafe_allow_html=True)

