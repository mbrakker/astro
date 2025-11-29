# /opt/astro_bot/src/test_gen_tarot_weekly.py
# -*- coding: utf-8 -*-
"""
Интеграционный тест генератора недельного расклада:
- вызывает gen_tarot_weekly.generate_tarot_weekly_post()
- проверяет, что вернулся GeneratedPost
- убеждается, что список изображений не пуст и содержит общий кадр «на столе»
- печатает диагностическую информацию и возвращает код выхода 0/1

Запуск:
    python3 /opt/astro_bot/src/test_gen_tarot_weekly.py
"""
import os
import sys
import traceback

try:
    from gen_tarot_weekly import generate_tarot_weekly_post
    from dataclass_generated_post import GeneratedPost
except Exception:
    print("❌ Импорт не удался. Убедитесь, что PYTHONPATH включает /opt/astro_bot/src")
    traceback.print_exc()
    sys.exit(1)


def main() -> int:
    try:
        print("🧪 Тест генератора: generate_tarot_weekly_post()")
        post = generate_tarot_weekly_post()

        # Поддержка случая, если вдруг вернули (text, images)
        if isinstance(post, tuple):
            text, images = post
            print("⚠️ Получен кортеж (text, images), не GeneratedPost — продолжаем проверку в упрощённом режиме.")
        elif isinstance(post, GeneratedPost):
            text = post.text
            images = post.media_types.get("image", [])
        else:
            print(f"❌ Неожиданный тип результата: {type(post)}")
            return 1

        # Проверка текста
        if not isinstance(text, str) or not text.strip():
            print("❌ Пустой текст поста.")
            return 1
        print(f"📝 Длина текста: {len(text)} символов")

        # Проверка изображений
        if not images:
            print("❌ Список изображений пуст — ожидались 3 карты + общий кадр стола.")
            return 1

        print(f"📸 Количество изображений: {len(images)}")
        for i, p in enumerate(images, start=1):
            print(f"  {i}. {p}")
            if not isinstance(p, str) or not p.strip():
                print(f"❌ Пустой путь к изображению на позиции {i}")
                return 1
            if not os.path.exists(p):
                print(f"❌ Файл не найден на диске: {p}")
                return 1

        # Проверяем, что последний кадр — общий «стол» (по расположению и расширению)
        table_candidate = images[-1]
        # Неформальный хинт: общий кадр сохраняется в /opt/astro_bot/images/tarot и .jpg
        looks_like_table = table_candidate.startswith("/opt/astro_bot/images/tarot/") and table_candidate.lower().endswith(".jpg")
        if not looks_like_table:
            print("❌ Похоже, последний элемент не является общим изображением «стола».")
            return 1

        size = os.path.getsize(table_candidate)
        if size <= 0:
            print("❌ Общий кадр «стола» имеет нулевой размер файла.")
            return 1

        print(f"✅ Успех: генератор вернул корректный пост. Общий «стол»: {table_candidate} | size={size} bytes")
        return 0

    except Exception:
        print("❌ Неожиданная ошибка при тестировании генератора:")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
