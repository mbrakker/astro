# /opt/astro_bot/src/script_openai_report.py
# -*- coding: utf-8 -*-
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta
from service_notifier import notify_owner_async
import asyncio

# Загрузка переменных окружения
load_dotenv(dotenv_path="/opt/astro_bot/env/.env")

# Путь к лог-файлу OpenAI
OPENAI_USAGE_LOG_PATH = "/opt/astro_bot/logs/openai_usage.log"

# Тарифы
GPT4_PROMPT_COST_PER_1K = 0.003  # $ за 1000 входных токенов
GPT4_COMPLETION_COST_PER_1K = 0.009  # $ за 1000 выходных токенов
DALLE3_IMAGE_COST = 0.04  # $ за 1 изображение
AUDIO_COST_PER_SECOND = 0  # $ за 1 секунду аудио (пока бесплатно)

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def generate_openai_report():
    """
    Сбирает и отправляет в Telegram отчёт по расходам OpenAI за последние 24 часа.
    """
    now = datetime.now()
    window_start = now - timedelta(hours=24)

    text_generations = 0
    prompt_tokens_total = 0
    completion_tokens_total = 0
    text_cost_total = 0.0

    image_generations = 0
    image_cost_total = 0.0

    audio_generations = 0
    audio_cost_total = 0.0

    total_actions = 0

    try:
        with open(OPENAI_USAGE_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            # Парсим timestamp из начала строки
            parts = line.split("|")
            timestamp_str = parts[0].strip()  # "YYYY-MM-DD HH:MM:SS"
            try:
                ts = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue

            # Фильтруем только за последние 24 часа
            if not (window_start <= ts <= now):
                continue

            total_actions += 1

            # action_type
            action_type = parts[1].split(":", 1)[1].strip()
            # prompt_tokens
            prompt_tokens = int(parts[2].split(":", 1)[1].strip())
            # completion_tokens
            completion_tokens = int(parts[3].split(":", 1)[1].strip())
            # images_generated
            images_generated = int(parts[4].split(":", 1)[1].strip())
            # audio_seconds
            audio_seconds = int(parts[5].split(":", 1)[1].strip())
            # cost
            cost = float(parts[6].split(":", 1)[1].replace("$", "").strip())

            if action_type == "text_generation":
                text_generations += 1
                prompt_tokens_total += prompt_tokens
                completion_tokens_total += completion_tokens
                text_cost_total += cost

            elif action_type == "image_generation":
                image_generations += images_generated
                image_cost_total += cost

            elif action_type == "audio_generation":
                audio_generations += 1
                audio_cost_total += cost

        # Формируем текст отчёта
        report_text = (
            f"✨ Отчёт расходов на OpenAI за последние 24 часа:\n\n"
            f"Текстовые генерации: {text_generations} запросов\n"
            f"- Входные токены: {prompt_tokens_total}\n"
            f"- Выходные токены: {completion_tokens_total}\n"
            f"- Сумма расходов: ${text_cost_total:.4f}\n\n"
            f"Генерация изображений: {image_generations} изображений\n"
            f"- Сумма расходов: ${image_cost_total:.4f}\n\n"
            f"Озвучка: {audio_generations} файлов\n"
            f"- Сумма расходов: ${audio_cost_total:.4f}\n\n"
            f"Общее количество действий: {total_actions}\n"
            f"Общая сумма расходов: ${(text_cost_total + image_cost_total + audio_cost_total):.4f}"
        )

        await notify_owner_async(report_text)
        logger.info("✅ Отчёт расходов за последние 24 часа отправлен успешно.")

    except Exception as e:
        logger.exception(f"❌ Ошибка при формировании или отправке отчёта расходов: {e}")

if __name__ == "__main__":
    asyncio.run(generate_openai_report())
