# /opt/astro_bot/src/script_pipeline.py
# -*- coding: utf-8 -*-
import logging
import datetime
import asyncio
import argparse
from dotenv import load_dotenv

from gen_mystic import generate_mystic_post
from gen_horoscope_daily import generate_horoscope_post 
from gen_confession import generate_confession_post
from gen_astro_basics import generate_astro_basic_post
from gen_tarot_weekly import generate_tarot_weekly_post
from gen_energy_zodiac import generate_zodiac_energy_post
from gen_energy_day_main import generate_energy_day_post
from gen_alchemy_day_zodiac import generate_alchemy_day_post

from service_notifier import notify_owner, notify_owner_async
from service_history_logger import init_db, make_hash, is_already_published, log_post
from service_topic_loader import (get_all_scheduled_topics as get_topics_for_date, get_topic_by_id, update_topic_status)
from service_telegram_sender import post_to_telegram, post_generated_post


from script_openai_report import generate_openai_report


load_dotenv(dotenv_path="/opt/astro_bot/env/.env")

# Список всех типов, поддерживаемых pipeline
SUPPORTED_TYPES = [
    "horoscope", "mystic_news", "confession", "astro_basics",
    "energy_day", "zodiac_energy", "tarot_weekly", "alchemy_day" 
]

# Аргументы командной строки
parser = argparse.ArgumentParser()
parser.add_argument("--test_topic_id", type=int, help="ID темы для ручного теста")
parser.add_argument("--dry_run", action="store_true", help="Не публиковать и не логировать")
parser.add_argument("--list_types", action="store_true", help="Вывести список поддерживаемых типов")
args = parser.parse_args()

# Логирование
log_path = "/opt/astro_bot/logs/bot.log"
logging.basicConfig(
    filename=log_path,
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger()

class TelegramErrorHandler(logging.Handler):
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            try:
                msg = self.format(record)
                notify_owner(f"❌ [ЛОГ] {msg}")
            except Exception:
                pass

error_handler = TelegramErrorHandler(level=logging.ERROR)
error_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
logger.addHandler(error_handler)

ZODIAC_SIGNS = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
]

def run_pipeline(args):
    return asyncio.run(main(args))

# Поддержка --list_types
if args.list_types:
    for t in SUPPORTED_TYPES:
        print(t)
    exit(0)

async def main(args):
    print("▶️ Вошли в main()")
    logger.info("🚀 Пайплайн запущен")
    init_db()

    today = datetime.date.today().strftime("%Y-%m-%d")

    # Если указан конкретный topic_id для теста
    if args.test_topic_id:
        topic = get_topic_by_id(args.test_topic_id)
        if not topic:
            logger.error(f"❌ Тема с id={args.test_topic_id} не найдена.")
            return

        logger.info(f"🧪 Тестовая тема: {topic['type']} [{topic['id']}] — {topic.get('theme', '')}")
        topic["scheduled_for"] = today  # подменяем дату
        topics = [topic]
    else:
        topics = get_topics_for_date(today)

    for topic in topics:
        channel_scope = topic.get("channel_scope", "main")
        target_sign = topic.get("target_sign")
        topic_type = topic["type"]

        try:
            if topic_type == "horoscope":
                success_signs = []

                for sign in ZODIAC_SIGNS:
                    key = f"{sign}:{today}"
                    source_hash = make_hash(key)
                    title_hash = make_hash(key)

                    if is_already_published(source_hash, title_hash, None):
                        logger.info(f"🔁 Гороскоп {sign} уже опубликован, пропускаем.")
                        continue

                    logger.info(f"🔮 Генерация гороскопа для {sign}")
                    try:
                        post = generate_horoscope_post(sign, today)
                    except Exception as e:
                        logger.warning(f"❌ Ошибка генерации гороскопа {sign}: {e}")
                        continue

                    text_hash = make_hash(post.text)

                    if not args.dry_run:
                        await post_generated_post(post, scope=channel_scope, target_sign=sign)
                        log_post(post.type, source_hash, title_hash, text_hash)
                    else:
                        logger.info(f"[dry_run] Гороскоп {sign}:\n{post.text[:400]}")
                        print(f"🪐SIGN={sign.upper()}")
                        print(post.text)
                        print(f"🖼 {post.main_image() or '—'}\n")
                    success_signs.append(sign)

                if len(success_signs) >= 10:
                    if not args.dry_run:
                        update_topic_status(topic["id"], "published")
                else:
                    logger.warning("⚠️ Не все гороскопы сгенерированы — статус темы не обновлён")

            elif topic_type == "mystic_news":
                logger.info("🌌 Публикация мистических новостей")
                posts = generate_mystic_post(limit=3)

                published_any = False

                for post in posts:
                    theme = post.metadata.get("title") or "Мистическая новость"
                    source_hash = make_hash(post.metadata.get("source_url") or theme)
                    title_hash = make_hash(theme)
                    text_hash = make_hash(post.text)

                    if is_already_published(source_hash, title_hash, text_hash):
                        logger.info(f"🔁 Мистика: «{theme}» уже публиковалась, пропускаем.")
                        continue

                    if not args.dry_run:
                        await post_generated_post(post, scope=channel_scope)
                        log_post(post.type, source_hash, title_hash, text_hash)
                        published_any = True
                    else:
                        logger.info(f"[dry_run] Мистика: {theme}\n{post.text[:500]}")
                        print(f"\n🌌 {theme}\n{post.text}\n🖼 {post.main_image() or '—'}\n🔗 {post.metadata.get('source_url')}")

                if published_any and not args.dry_run:
                    update_topic_status(topic["id"], "published")

            elif topic_type == "confession":
                theme = topic["theme"]
                logger.info(f"🔥 Откровение: {theme}")

                source_hash = make_hash(theme)
                post = generate_confession_post(theme)
                text_hash = make_hash(post.text)

                if not args.dry_run:
                    await post_generated_post(post, scope=channel_scope)
                    log_post(post.type, source_hash, make_hash(theme), text_hash)
                    update_topic_status(topic["id"], "published")
                else:
                    logger.info(f"[dry_run] Откровение: {theme}\n{post.text[:500]}")
                    print(f"\n🔥 {theme}\n{post.text}\n🖼 {post.main_image()}\n")

            elif topic_type == "astro_basics":
                theme = topic["theme"]
                logger.info(f"🔰 Азы астрологии: {theme}")

                post = generate_astro_basic_post(theme)                
                source_hash = make_hash(theme)
                text_hash = make_hash(post.text)

                if not args.dry_run:
                    await post_generated_post(post, scope=channel_scope)
                    log_post("astro_basics", source_hash, make_hash(theme), text_hash)
                    update_topic_status(topic["id"], "published")
                else:
                    logger.info(f"[dry_run] Азы: {theme}\n{post.text[:500]}")
                    print("🪐TYPE=astro_basics")
                    print(f"📘 {theme}")
                    print(post.text)
                    print(f"🖼 {post.main_image() or '—'}\n")

            elif topic_type == "energy_day":
                logger.info("⚡️ Энергия дня — генерация")

                try:
                    from gen_energy_day_main import generate_energy_day_post
                    post = await generate_energy_day_post()
                except Exception as e:
                    logger.error(f"❌ Ошибка генерации энергии дня: {e}")
                    update_topic_status(topic["id"], "error")
                    return

                theme = f"{post.metadata.get('moon_phase', '?')} / {post.metadata.get('planet_of_day', '?')}"
                source_hash = make_hash(post.metadata.get("moon_phase", ""))
                text_hash = make_hash(post.text)

                if not args.dry_run:
                    await post_generated_post(post, scope=channel_scope)
                    log_post(post.type, source_hash, make_hash(theme), text_hash)
                    update_topic_status(topic["id"], "published")
                else:
                    logger.info(f"[dry_run] Энергия дня: {theme}\n{post.text[:500]}")
                    print(f"\n⚡️ {theme}\n{post.text}\n🖼 {post.main_image() or '—'}")

            elif topic_type == "alchemy_day":
                sign = topic.get("target_sign")
                if not sign:
                    logger.error("❌ Нет target_sign для alchemy_day")
                    update_topic_status(topic["id"], "error")
                    return

                logger.info(f"🧪 Астрологическая алхимия дня для знака {sign}")

                try:
                    post = generate_alchemy_day_post(sign, datetime.date.fromisoformat(today))
                except Exception as e:
                    logger.error(f"❌ Ошибка генерации alchemy_day для {sign}: {e}")
                    update_topic_status(topic["id"], "error")
                    return

                source_hash = make_hash(f"alchemy_day:{sign}:{today}")
                title_hash = make_hash(post.metadata.get("theme", ""))
                text_hash = make_hash(post.text)

                if not args.dry_run:
                    await post_generated_post(post, scope=channel_scope, target_sign=sign)
                    log_post(post.type, source_hash, title_hash, text_hash)
                    update_topic_status(topic["id"], "published")
                else:
                    logger.info(f"[dry_run] alchemy_day для {sign}\n{post.text[:500]}")
                    print(f"\n🧪 {sign.upper()} — {post.metadata.get('theme')}\n{post.text}\n🖼 {post.main_image() or '—'}")


            elif topic_type == "tarot_weekly":
                logger.info("🃏 Таро недели — универсальный прогноз")

                try:
                    post = generate_tarot_weekly_post()
                except Exception as e:
                    logger.exception(f"❌ Ошибка генерации tarot_weekly: {e}")
                    if not args.dry_run:
                        update_topic_status(topic["id"], "error")
                    post = None

                if not post:
                    continue


                # ✅ Берём изображения из media_types["image"], иначе fallback на all_images()
                if hasattr(post, "media_types"):
                    images = list(post.media_types.get("image", []))
                else:
                    images = post.all_images() if hasattr(post, "all_images") else []

                if not images:
                    logger.warning("❌ Не сгенерировано изображение для Таро недели (пустой список images)")
                    if not args.dry_run:
                        update_topic_status(topic["id"], "error")
                    continue

                text = post.text
                source_hash = make_hash("tarot_weekly:" + today)
                title_hash = make_hash("tarot")
                text_hash = make_hash(text)

                if not args.dry_run:
                    await post_generated_post(post, scope=channel_scope)
                    log_post(post.type, source_hash, title_hash, text_hash)
                    update_topic_status(topic["id"], "published")
                else:
                    logger.info(f"[dry_run] Таро недели:\n{post.text[:500]}")
                    print(f"\n🃏 Таро недели\n{post.text}\n📸 Картинки:\n" + "\n".join(post.all_images()))

            elif topic_type == "zodiac_energy":

                sign = topic.get("target_sign")
                if not sign:
                    logger.error("❌ Нет target_sign для zodiac_energy")
                    update_topic_status(topic["id"], "error")
                    return

                logger.info(f"💫 Энергия дня для знака {sign}")

                try:
                    post = await generate_zodiac_energy_post(sign)
                except Exception as e:
                    logger.error(f"❌ Ошибка генерации zodiac_energy для {sign}: {e}")
                    update_topic_status(topic["id"], "error")
                    return

                theme = f"{post.metadata.get('moon_phase', '?')} + {post.metadata.get('planet', '?')}"
                source_hash = make_hash(post.metadata.get("moon_phase", ""))
                text_hash = make_hash(post.text)

                if not args.dry_run:
                    await post_generated_post(post, scope=channel_scope, target_sign=sign)
                    log_post(post.type, source_hash, make_hash(theme), text_hash)
                    update_topic_status(topic["id"], "published")
                else:
                    logger.info(f"[dry_run] zodiac_energy для {sign}\n{post.text[:500]}")
                    print(f"\n💫 {sign.upper()} — {theme}\n{post.text}\n🖼 {post.main_image() or '—'}")

        except Exception as e:
            logger.exception(f"❌ Ошибка обработки темы: {e}")

    # Отчёт по OpenAI
    if not args.dry_run:
        try:
            await generate_openai_report()
        except Exception as e:
            logger.exception(f"❌ Ошибка отчёта расходов: {e}")

    logger.info("🏁 Пайплайн завершён")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_topic_id", type=int, help="ID темы для ручного теста")
    parser.add_argument("--dry_run", action="store_true", help="Не публиковать и не логировать")
    parser.add_argument("--list_types", action="store_true", help="Вывести список поддерживаемых типов")
    cli_args = parser.parse_args()

    if cli_args.list_types:
        for t in SUPPORTED_TYPES:
            print(t)
        exit(0)

    run_pipeline(cli_args)

