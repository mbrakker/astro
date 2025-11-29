# /opt/astro_bot/src/service_prompt_loader.py
# -*- coding: utf-8 -*-
import os
import yaml
import random
import logging
from jinja2 import Template

logger = logging.getLogger(__name__)

_CONFIG = None

def _load_config():
    global _CONFIG
    if _CONFIG is None:
        path = "/opt/astro_bot/config/prompts.yaml"
        with open(path, encoding="utf-8") as f:
            _CONFIG = yaml.safe_load(f)
    return _CONFIG

def pick_template(sec, key, theme, context):
    logger.info(f"pick_template called with key={key}, sec keys={list(sec.keys()) if isinstance(sec, dict) else 'N/A'}")

    raw_value = sec.get(key)
    if isinstance(raw_value, list):
        tmpl = random.choice(raw_value) if raw_value else ""
        logger.info(f"Chosen random template from list: {tmpl[:100]}")
    else:
        tmpl = raw_value or ""

    fmt_vars = {"theme": theme}
    if context:
        fmt_vars.update(context)

    try:
        prompt = Template(tmpl).render(**fmt_vars)
    except Exception as e:
        logger.warning(f"⚠️ Ошибка Jinja-шаблона key={key}: {e}")
        prompt = tmpl

    logger.info(f"[pick_template] key={key} -> prompt snippet: {prompt[:100]}")
    return prompt

def get_prompt(
    topic_type: str,
    topic_subtype: str = None,
    theme: str = "",
    context: dict = None
):
    """
    Универсальный загрузчик промптов:
    — Поддерживает оба вида: get_prompt("mystic_news", "news_all", ...) и get_prompt("mystic_news.news_all", ...)
    — Возвращает (system_prompt, user_prompt, params)
    """

    # 0) Обработка старого стиля "mystic_news.news_all"
    if not topic_subtype and "." in topic_type:
        topic_type, topic_subtype = topic_type.split(".", 1)

    cfg = _load_config()

    if topic_type not in cfg:
        logger.error(f"❌ prompts.yaml: отсутствует ключ '{topic_type}'")
        return "", "", {}

    section = cfg[topic_type]

    # 1) Вложенная секция
    if topic_subtype and isinstance(section, dict) and topic_subtype in section:
        sec = section[topic_subtype]
    else:
        sec = section

    if not isinstance(sec, dict):
        logger.warning(f"⚠️ get_prompt: секция {topic_type}/{topic_subtype} не является словарём.")
        sec = {}

    logger.info(f"get_prompt: resolved section = {topic_type}/{topic_subtype}, keys = {sec.keys()}")

    system_prompt = pick_template(sec, "system_prompt", theme, context)
    user_prompt   = pick_template(sec, "user_prompt_templates", theme, context)

    params = {
        "max_tokens": sec.get("max_tokens", 900),
        "temperature": sec.get("temperature", 1.0),
        "presence_penalty": sec.get("presence_penalty", 0),
        "frequency_penalty": sec.get("frequency_penalty", 0),
        "top_p": sec.get("top_p", 1.0),
    }

    return system_prompt, user_prompt, params
