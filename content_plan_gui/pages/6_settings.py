# content_plan_gui/pages/6_settings.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import streamlit as st
from core.settings_config import load_settings, save_settings, load_env_vars, save_env_vars

st.set_page_config(page_title="Настройки", layout="centered")
st.title("⚙️ Глобальные настройки")

settings = load_settings()

st.subheader("🔮 Модель и генерация")
default_model = st.text_input("Модель по умолчанию", settings.get("global", {}).get("default_model", "gpt-4o"))
temperature = st.slider("Temperature", 0.0, 1.5, float(settings.get("global", {}).get("default_temperature", 0.8)), 0.05)
max_tokens = st.number_input("Максимум токенов", 100, 4000, int(settings.get("global", {}).get("max_tokens", 700)))

st.subheader("🌐 Временная зона")
timezone = st.text_input("Часовой пояс", settings.get("global", {}).get("timezone", "Europe/Paris"))

if st.button("💾 Сохранить"):
    settings["global"] = {
        "default_model": default_model,
        "default_temperature": temperature,
        "max_tokens": max_tokens,
        "timezone": timezone

    }
    save_settings(settings)
    st.success("✅ Настройки сохранены")

st.subheader("🔐 Переменные .env")

env_vars = load_env_vars()
edited_env = {}

for key, value in env_vars.items():
    edited_env[key] = st.text_input(f"{key}", value)

if st.button("💾 Обновить .env"):
    save_env_vars(edited_env)
    st.success("✅ .env сохранён")


