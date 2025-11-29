# /opt/astro_bot/src/service_text.py

import os
import logging
import yaml
from jinja2 import Template, UndefinedError
from service_openai_logger import call_openai_and_log
from service_prompt_loader import get_prompt
from service_notifier import notify_owner
from dotenv import load_dotenv

# Загрузка .env
load_dotenv(dotenv_path="/opt/astro_bot/env/.env")

# Настройка логирования
logger = logging.getLogger("service_text")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("/opt/astro_bot/logs/bot.log")
handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
if not logger.handlers:
    logger.addHandler(handler)


def render_jinja(text: str, context: dict) -> str:
    try:
        tmpl = Template(text)
        return tmpl.render(**context)
    except UndefinedError as e:
        logger.error(f"❌ Ошибка Jinja2 при шаблонизации: {e}")
        raise


def _serialize_context(ctx: dict) -> str:
    """
    Безопасно сериализует произвольный контекст в YAML для логов.
    Поддерживает вложенные структуры и нестандартные объекты.
    """
    def _to_primitive(obj):
        if isinstance(obj, dict):
            return {str(k): _to_primitive(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [_to_primitive(v) for v in obj]
        # dataclass / объекты
        if hasattr(obj, "__dict__"):
            try:
                return _to_primitive(vars(obj))
            except Exception:
                return str(obj)
        # простые типы и всё остальное как строка
        try:
            return obj if isinstance(obj, (str, int, float, bool)) or obj is None else str(obj)
        except Exception:
            return repr(obj)

    try:
        prim = _to_primitive(ctx or {})
        return yaml.safe_dump(
            prim,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
    except Exception as e:
        # Последний резерв — строковое представление
        return f"<<unserializable context: {e}>> " + str(ctx)


def generate_text(
    topic_type: str,
    topic_subtype: str = None,
    theme: str = "",
    context: dict = None,
    **kwargs
) -> str:
    """
    Универсальная функция генерации текста через OpenAI GPT-4o.
    Использует шаблоны Jinja2. Все параметры берутся из prompts.yaml.
    """
    try:
        context = context or {}
        context["theme"] = theme  # гарантируем, что theme доступен

        # 🔎 Логируем весь контекст (включая вложенные значения)
        logger.info(
            f"🧩 Контекст генерации для {topic_type}/{topic_subtype}:\n{_serialize_context(context)}"
        )

        # 1. Получаем промпты и параметры генерации из service_prompt_loader (парсит prompts.yaml)
        system_prompt, user_prompt, params = get_prompt(
            topic_type, topic_subtype, theme, context
        )
        max_tokens = params.get("max_tokens", 900)
        temperature = params.get("temperature", 1.0)
        presence_penalty = params.get("presence_penalty", 0)
        frequency_penalty = params.get("frequency_penalty", 0)
        top_p = params.get("top_p", 1.0)

        # 2. Генерируем Jinja2-промпты
        system_prompt_fmt = render_jinja(system_prompt, context)
        user_prompt_fmt = render_jinja(user_prompt, context)

        if not system_prompt_fmt.strip() and not user_prompt_fmt.strip():
            logger.error(f"❌ Оба промпта пустые для {topic_type}/{topic_subtype}")
            notify_owner(f"❌ Оба промпта пустые для {topic_type}/{topic_subtype}")
            return "⚡ Ошибка генерации текста: пустые промпты."

        response = call_openai_and_log(
            system_prompt=system_prompt_fmt,
            user_prompt=user_prompt_fmt,
            max_tokens=max_tokens,
            temperature=temperature,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            top_p=top_p,
            model="gpt-4o",
            extra_params=context
        )

        text = response.choices[0].message.content.strip()

        if len(text) < 100:
            logger.warning(f"⚠️ Короткий текст ({topic_type}), повторная генерация...")
            response = call_openai_and_log(
                system_prompt=system_prompt_fmt,
                user_prompt=user_prompt_fmt,
                max_tokens=max_tokens,
                temperature=temperature + 0.2,
                presence_penalty=presence_penalty,
                frequency_penalty=frequency_penalty,
                top_p=top_p,
                model="gpt-4o",
                extra_params=context
            )
            text = response.choices[0].message.content.strip()

        return text

    except Exception as e:
        logger.error(f"❌ Ошибка генерации текста ({topic_type}): {str(e)}")
        notify_owner(f"❌ Ошибка генерации текста ({topic_type}): {str(e)}")
        return "⚡ Ошибка генерации текста. Попробуй позже!"
