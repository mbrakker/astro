# /opt/astro_bot/src/service_openai_logger.py
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Загрузка переменных окружения
load_dotenv(dotenv_path="/opt/astro_bot/env/.env")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

OPENAI_USAGE_LOG_PATH = "/opt/astro_bot/logs/openai_usage.log"

# Тарифы OpenAI (на 27 апреля 2025)
GPT4_PROMPT_COST_PER_1K = 0.003
GPT4_COMPLETION_COST_PER_1K = 0.009
DALLE3_IMAGE_COST = 0.04
AUDIO_COST_PER_SECOND = 0

def log_openai_usage(action_type: str,
                     prompt_tokens: int = 0,
                     completion_tokens: int = 0,
                     images_generated: int = 0,
                     audio_seconds: int = 0) -> None:
    """
    Логирует использование OpenAI API с расчётом стоимости.
    """
    try:
        if action_type == "text_generation":
            cost = ((prompt_tokens * GPT4_PROMPT_COST_PER_1K) + (completion_tokens * GPT4_COMPLETION_COST_PER_1K)) / 1000
        elif action_type == "image_generation":
            cost = images_generated * DALLE3_IMAGE_COST
        elif action_type == "audio_generation":
            cost = audio_seconds * AUDIO_COST_PER_SECOND
        else:
            cost = 0.0

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = (
            f"{now} | action: {action_type} | "
            f"prompt_tokens: {prompt_tokens} | completion_tokens: {completion_tokens} | "
            f"images_generated: {images_generated} | audio_seconds: {audio_seconds} | "
            f"cost: ${cost:.4f}"
        )

        with open(OPENAI_USAGE_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

        logger.info(f"✅ Запись в openai_usage.log: {log_entry}")

    except Exception as e:
        logger.error(f"❌ Ошибка при логировании использования OpenAI: {e}")

# === ДОБАВЛЯЕМ ОБЁРТКУ ДЛЯ ГЕНЕРАЦИИ ТЕКСТА С ЛОГИРОВАНИЕМ ===

def call_openai_and_log(system_prompt=None, user_prompt=None,
                        max_tokens=900, temperature=1.0,
                        presence_penalty=0, frequency_penalty=0, top_p=1.0,
                        model="gpt-4o", extra_params=None):
    import os
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
        top_p=top_p
    )

    usage = getattr(response, "usage", None)
    prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
    completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

    log_openai_usage(
        action_type="text_generation",
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens
    )
    return response

