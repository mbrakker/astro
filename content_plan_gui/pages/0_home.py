# content_plan_gui/home.py

import sys
import os
sys.path.append("/opt/astro_bot/src")

import streamlit as st
from core.content_service import get_summary_by_type, get_today_schedule
from core.analyzer import find_missing_days, find_channel_overload

st.set_page_config(page_title="Дашборд Скарлет Луны", layout="wide")
st.title("🔮 Дашборд: статус контент-системы")

# 📊 Сводка по статусам
st.markdown("## ✨ Обзор контент-плана")
summary = get_summary_by_type()
st.dataframe(summary, use_container_width=True)
st.markdown("✅ Темы со статусом `pending`, `scheduled`, `published` по типам контента")

# 📅 Публикации на сегодня
st.markdown("---")
today_df = get_today_schedule()
st.markdown(f"## 📅 Публикации на сегодня ({len(today_df)})")

if today_df.empty:
    st.info("🕒 Сегодня публикаций нет.")
else:
    st.dataframe(today_df, use_container_width=True)

# ⚠️ Быстрый аудит
st.markdown("---")
st.markdown("## ⚠️ Потенциальные проблемы")

col1, col2 = st.columns(2)
with col1:
    missing = find_missing_days(days_ahead=7)
    if missing.empty:
        st.success("✅ Все каналы покрыты на 7 дней")
    else:
        st.warning(f"📉 Пропусков: {len(missing)} записей")

with col2:
    overload = find_channel_overload(limit=3)
    if overload.empty:
        st.success("✅ Перегрузов нет")
    else:
        st.error(f"📈 Перегрузов: {len(overload)} дней")

# 🔗 Быстрый переход в анализ
st.page_link("pages/4_problems.py", label="🔍 Открыть детальный анализ проблем", icon="🚨")

# Подпись
st.markdown("---")
st.caption("🧠 ScarletBot Admin v3.1 · Привет, Скарлет ✨ · Всё под контролем 🌕")
