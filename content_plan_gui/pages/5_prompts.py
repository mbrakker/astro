# content_plan_gui/pages/5_prompts.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from core.content_types import CONTENT_SUBTYPES
import streamlit as st
from core.prompt_config_editor import load_prompt_config, save_prompt_config
from core.content_types import CONTENT_TYPES

PROMPTS_PATH = "/opt/astro_bot/config/prompts.yaml"

st.set_page_config(page_title="Промпты", layout="wide")
st.title("🧠 Редактирование промптов")

cfg = load_prompt_config(PROMPTS_PATH)
content_type = st.selectbox("Тип контента", CONTENT_TYPES)

prompt_mode = st.radio("Тип промпта", ["GPT", "DALL·E"], horizontal=True)
is_dalle = (prompt_mode == "DALL·E")

DALLE_PROMPT_MAP = {
    "horoscope": "horoscope_prompt_templates",
    "confession": "confession_prompt_templates",
    "mystic_news": "mystic_prompt_templates",
    "astro_basics": "astro_basics_prompt_templates",
    "alchemy_day": "alchemy_day_prompt_templates",
    "zodiac_energy": "zodiac_energy_prompt_templates",
    "open_slot": "open_slot_prompt_templates",
    "education": "education_prompt_templates",
    "news_all": "news_all_prompt_templates",
    "news_astro": "news_astro_prompt_templates",
    "news_horoscope": "news_horoscope_prompt_templates",
}

# ===== DALL·E PROMPTS =====
if is_dalle:
    dalle_section = cfg.get("dalle", {})
    prompt_key = DALLE_PROMPT_MAP.get(content_type)
    if not prompt_key:
        st.warning(f"❌ Для типа {content_type} не найден DALL·E-шаблон")
        st.stop()

    prompt_list = dalle_section.get(prompt_key)
    if not isinstance(prompt_list, list):
        prompt_list = [""]


    st.markdown(f"🎨 Шаблоны DALL·E: `{prompt_key}`")

    if not prompt_list:
        prompt_list = [""]

    new_dalle_prompts = []
    for i, prompt in enumerate(prompt_list):
        new_prompt = st.text_area(f"{prompt_key} #{i+1}", prompt, key=f"dalle_prompt_{i}", height=140)
        new_dalle_prompts.append(new_prompt)

    if st.button("💾 Сохранить изменения"):
        cfg["dalle"][prompt_key] = new_dalle_prompts
        save_prompt_config(PROMPTS_PATH, cfg)
        st.success("✅ DALL·E шаблоны сохранены")

# ===== GPT PROMPTS =====
else:
    # Определяем подтипы через централизованную карту
    if content_type in CONTENT_SUBTYPES:
        subtype = st.selectbox("Подтип", CONTENT_SUBTYPES[content_type])
        section = cfg.get(content_type, {}).get(subtype, {})
    else:
        subtype = None
        section_raw = cfg.get(content_type)
        section = section_raw if isinstance(section_raw, dict) else {}

    st.markdown("### 🧾 System Prompt")
    system_prompt = st.text_area("🧠 System", section.get("system_prompt", ""), height=200)

    st.markdown("### 👤 User Prompt Templates")

    # Ключ для сессии
    prompt_key_base = f"{content_type}_{subtype}_user_prompts" if subtype else f"{content_type}_user_prompts"

    # Начальные шаблоны
    default_user_prompts = section.get("user_prompt_templates", [])
    if not isinstance(default_user_prompts, list):
        default_user_prompts = [""]

    if prompt_key_base not in st.session_state:
        st.session_state[prompt_key_base] = default_user_prompts

    # Кнопка добавления поля
    if st.button("➕ Добавить user prompt"):
        st.session_state[prompt_key_base].append("")

    # Отображение всех полей
    new_user_prompts = []
    for i, prompt in enumerate(st.session_state[prompt_key_base]):
        new_prompt = st.text_area(f"User Prompt #{i+1}", prompt, key=f"user_prompt_{prompt_key_base}_{i}", height=120)
        new_user_prompts.append(new_prompt)

    # Сохранение
    if st.button("💾 Сохранить изменения"):
        section["system_prompt"] = system_prompt
        section["user_prompt_templates"] = new_user_prompts

        if subtype:
            cfg.setdefault(content_type, {})[subtype] = section
        else:
            cfg[content_type] = section

        save_prompt_config(PROMPTS_PATH, cfg)
        st.success("✅ Промпты сохранены")
