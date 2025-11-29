# content_plan_gui/pages/8_tests.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import streamlit as st
import subprocess

# --- 🧠 Логика тестов через subprocess ---
def run_test_command(test_name, to_telegram):
    SCRIPT_PATH = "/opt/astro_bot/src/test_publications.py"
    cmd = ["python3", SCRIPT_PATH, test_name, "--streamlit"]
    if to_telegram:
        cmd.append("--telegram")

    try:
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1) as proc:
            for line in proc.stdout:
                st.write(line.strip())
            proc.wait(timeout=300)
    except subprocess.TimeoutExpired:
        st.error("⏱ Timeout: генерация заняла более 5 минут")
    except Exception as e:
        st.error(f"[EXCEPTION] {type(e).__name__}: {e}")

# --- 🧩 Список тестов ---
TESTS = {
    "horoscope": "🔮 Гороскоп",
    "energy_day": "🌕 Энергия дня",
    "zodiac_energy": "🌘 Энергия по знакам",
    "mystic_news": "🌌 Мистические новости",
    "confession": "🔥 Откровения",
    "astro_basics": "📘 Азы астрологии",
}

# --- 🎛️ Интерфейс ---
st.set_page_config(page_title="Тест генераторов", layout="wide")
st.title("🧪 Ручной тест генераторов")

selected = st.radio("Выбери генератор", list(TESTS.keys()), format_func=lambda k: TESTS[k])
mode = st.radio("Куда отправлять результат?", ["🖥️ Только на экран", "📤 Telegram"])
send_to_telegram = (mode == "📤 Telegram")

if st.button("🚀 Запустить тест"):
    with st.spinner("Генерация..."):
        run_test_command(selected, to_telegram=send_to_telegram)
        st.success("✅ Тест завершён")