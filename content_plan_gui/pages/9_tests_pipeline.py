import streamlit as st
import sqlite3
import random
import sys, os
sys.path.append("/opt/astro_bot/src")
from test_runner import run_pipeline_test

# ✅ Кэширование для предотвращения повторных соединений
@st.cache_data(show_spinner=False)
def load_pending_topics():
    return get_random_pending_topics()

def get_random_pending_topics(limit_per_type=10):
    """Возвращает до N случайных тем со статусом pending по каждому type"""
    conn = sqlite3.connect("/opt/astro_bot/history/content_topics.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, type, theme, scheduled_for FROM topics WHERE status = 'pending'")
    rows = cur.fetchall()
    conn.close()

    grouped = {}
    for row in rows:
        t = dict(row)
        grouped.setdefault(t["type"], []).append({
            "label": f"{t['id']}: {t['type']} | {t['theme']} | {t['scheduled_for']}",
            "id": t["id"],
            "type": t["type"]
        })

    result = []
    for type_, items in grouped.items():
        result.extend(random.sample(items, min(len(items), limit_per_type)))
    return result

# --- GUI ---
st.header("🧪 Ручной тест публикации через pipeline.py")

all_topics = load_pending_topics()
available_types = sorted(set(t["type"] for t in all_topics))
selected_type = st.selectbox("Фильтр по типу публикации:", ["Все типы"] + available_types)

# Фильтрация
filtered_topics = [t for t in all_topics if t["type"] == selected_type] if selected_type != "Все типы" else all_topics

if not filtered_topics:
    st.info("Нет доступных тем для теста.")
else:
    topic_labels = [t["label"] for t in filtered_topics]
    selected_label = st.selectbox("Выберите тему для теста:", topic_labels)
    selected_id = next((t["id"] for t in filtered_topics if t["label"] == selected_label), None)

    send_flag = st.checkbox("Отправлять в Telegram?", value=False, key="send_checkbox_test_topic")
    run_button = st.button("▶️ Запустить тест")

    if run_button and selected_id:
        with st.spinner("Выполняется..."):
            result = run_pipeline_test(topic_id=selected_id, send_to_telegram=send_flag)

            # Сохраняем лог в файл
            try:
                with open("/opt/astro_bot/logs/last_test.log", "w") as f:
                    f.write(result["stdout"])
                    if result["stderr"]:
                        f.write("\n\n[stderr]\n" + result["stderr"])
            except Exception as e:
                st.warning(f"⚠️ Не удалось сохранить лог: {e}")

            # Вывод результатов
            if result["returncode"] == 0:
                st.success("✅ Тест выполнен успешно")
            else:
                st.error("❌ Ошибка во время выполнения")

            st.subheader("stdout (результат):")
            st.text_area("Результат pipeline", result["stdout"], height=400)

            if result["stderr"]:
                st.subheader("stderr (ошибки):")
                st.text_area("Ошибки выполнения", result["stderr"], height=200)

            # Вывод изображения, если найден путь
            if result.get("image_path") and os.path.exists(result["image_path"]):
                st.subheader("🖼 Сгенерированное изображение:")
                st.image(result["image_path"])
            else:
                st.warning("Изображение не найдено или не удалось прочитать файл.")

            st.info("Лог сохранён: `/opt/astro_bot/logs/last_test.log`")
