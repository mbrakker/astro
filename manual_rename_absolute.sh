#!/bin/bash

echo '##############################################################'
echo 'Переименование файла: topic_seeder.py --> service_topic_seeder.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/topic_seeder.py src/service_topic_seeder.py'
echo '2. Замени все импорты:'
echo '   from topic_seeder import ...   →   from service_topic_seeder import ...'
echo '3. Эти файлы содержат topic_seeder:'
grep -rl ' topic_seeder ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: topic_loader.py --> service_topic_loader.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/topic_loader.py src/service_topic_loader.py'
echo '2. Замени все импорты:'
echo '   from topic_loader import ...   →   from service_topic_loader import ...'
echo '3. Эти файлы содержат topic_loader:'
grep -rl ' topic_loader ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: text_service.py --> service_text.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/text_service.py src/service_text.py'
echo '2. Замени все импорты:'
echo '   from text_service import ...   →   from service_text import ...'
echo '3. Эти файлы содержат text_service:'
grep -rl ' text_service ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: telegram_sender.py --> service_telegram_sender.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/telegram_sender.py src/service_telegram_sender.py'
echo '2. Замени все импорты:'
echo '   from telegram_sender import ...   →   from service_telegram_sender import ...'
echo '3. Эти файлы содержат telegram_sender:'
grep -rl ' telegram_sender ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: tarot_weekly_gen.py --> gen_tarot_weekly.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/tarot_weekly_gen.py src/gen_tarot_weekly.py'
echo '2. Замени все импорты:'
echo '   from tarot_weekly_gen import ...   →   from gen_tarot_weekly import ...'
echo '3. Эти файлы содержат tarot_weekly_gen:'
grep -rl ' tarot_weekly_gen ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: tarot_service.py --> service_tarot.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/tarot_service.py src/service_tarot.py'
echo '2. Замени все импорты:'
echo '   from tarot_service import ...   →   from service_tarot import ...'
echo '3. Эти файлы содержат tarot_service:'
grep -rl ' tarot_service ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: stellarium_service.py --> service_stellarium.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/stellarium_service.py src/service_stellarium.py'
echo '2. Замени все импорты:'
echo '   from stellarium_service import ...   →   from service_stellarium import ...'
echo '3. Эти файлы содержат stellarium_service:'
grep -rl ' stellarium_service ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: scarlet_confession_gen.py --> gen_confession.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/scarlet_confession_gen.py src/gen_confession.py'
echo '2. Замени все импорты:'
echo '   from scarlet_confession_gen import ...   →   from gen_confession import ...'
echo '3. Эти файлы содержат scarlet_confession_gen:'
grep -rl ' scarlet_confession_gen ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: prompt_loader.py --> service_prompt_loader.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/prompt_loader.py src/service_prompt_loader.py'
echo '2. Замени все импорты:'
echo '   from prompt_loader import ...   →   from service_prompt_loader import ...'
echo '3. Эти файлы содержат prompt_loader:'
grep -rl ' prompt_loader ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: preload_stellarium.py --> script_preload_stellarium.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/preload_stellarium.py src/script_preload_stellarium.py'
echo '2. Замени все импорты:'
echo '   from preload_stellarium import ...   →   from script_preload_stellarium import ...'
echo '3. Эти файлы содержат preload_stellarium:'
grep -rl ' preload_stellarium ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: pipeline.py --> script_pipeline.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/pipeline.py src/script_pipeline.py'
echo '2. Замени все импорты:'
echo '   from pipeline import ...   →   from script_pipeline import ...'
echo '3. Эти файлы содержат pipeline:'
grep -rl ' pipeline ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: openai_logger.py --> service_openai_logger.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/openai_logger.py src/service_openai_logger.py'
echo '2. Замени все импорты:'
echo '   from openai_logger import ...   →   from service_openai_logger import ...'
echo '3. Эти файлы содержат openai_logger:'
grep -rl ' openai_logger ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: notifier.py --> service_notifier.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/notifier.py src/service_notifier.py'
echo '2. Замени все импорты:'
echo '   from notifier import ...   →   from service_notifier import ...'
echo '3. Эти файлы содержат notifier:'
grep -rl ' notifier ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: mystic_gen.py --> gen_mystic.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/mystic_gen.py src/gen_mystic.py'
echo '2. Замени все импорты:'
echo '   from mystic_gen import ...   →   from gen_mystic import ...'
echo '3. Эти файлы содержат mystic_gen:'
grep -rl ' mystic_gen ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: image_service.py --> service_image.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/image_service.py src/service_image.py'
echo '2. Замени все импорты:'
echo '   from image_service import ...   →   from service_image import ...'
echo '3. Эти файлы содержат image_service:'
grep -rl ' image_service ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: horoscope_gen.py --> gen_horoscope_daily.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/horoscope_gen.py src/gen_horoscope_daily.py'
echo '2. Замени все импорты:'
echo '   from horoscope_gen import ...   →   from gen_horoscope_daily import ...'
echo '3. Эти файлы содержат horoscope_gen:'
grep -rl ' horoscope_gen ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: history_logger.py --> service_history_logger.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/history_logger.py src/service_history_logger.py'
echo '2. Замени все импорты:'
echo '   from history_logger import ...   →   from service_history_logger import ...'
echo '3. Эти файлы содержат history_logger:'
grep -rl ' history_logger ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: energy_zodiac_gen.py --> gen_energy_zodiac.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/energy_zodiac_gen.py src/gen_energy_zodiac.py'
echo '2. Замени все импорты:'
echo '   from energy_zodiac_gen import ...   →   from gen_energy_zodiac import ...'
echo '3. Эти файлы содержат energy_zodiac_gen:'
grep -rl ' energy_zodiac_gen ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: energy_personalization_service.py --> service_energy_personalization.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/energy_personalization_service.py src/service_energy_personalization.py'
echo '2. Замени все импорты:'
echo '   from energy_personalization_service import ...   →   from service_energy_personalization import ...'
echo '3. Эти файлы содержат energy_personalization_service:'
grep -rl ' energy_personalization_service ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: energy_day_gen.py --> gen_energy_main.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/energy_day_gen.py src/gen_energy_main.py'
echo '2. Замени все импорты:'
echo '   from energy_day_gen import ...   →   from gen_energy_main import ...'
echo '3. Эти файлы содержат energy_day_gen:'
grep -rl ' energy_day_gen ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: day_context_service.py --> service_day_context.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/day_context_service.py src/service_day_context.py'
echo '2. Замени все импорты:'
echo '   from day_context_service import ...   →   from service_day_context import ...'
echo '3. Эти файлы содержат day_context_service:'
grep -rl ' day_context_service ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: daily_openai_report.py --> script_openai_report.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/daily_openai_report.py src/script_openai_report.py'
echo '2. Замени все импорты:'
echo '   from daily_openai_report import ...   →   from script_openai_report import ...'
echo '3. Эти файлы содержат daily_openai_report:'
grep -rl ' daily_openai_report ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: generated_post.py --> dataclass_generated_post.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/generated_post.py src/dataclass_generated_post.py'
echo '2. Замени все импорты:'
echo '   from generated_post import ...   →   from dataclass_generated_post import ...'
echo '3. Эти файлы содержат generated_post:'
grep -rl ' generated_post ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: channels.py --> service_channels.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/channels.py src/service_channels.py'
echo '2. Замени все импорты:'
echo '   from channels import ...   →   from service_channels import ...'
echo '3. Эти файлы содержат channels:'
grep -rl ' channels ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt
echo '##############################################################'
echo 'Переименование файла: astro_basics_gen.py --> gen_astro_lesson.py'
echo '1. Переименуй файл вручную:'
echo '   mv src/astro_basics_gen.py src/gen_astro_lesson.py'
echo '2. Замени все импорты:'
echo '   from astro_basics_gen import ...   →   from gen_astro_lesson import ...'
echo '3. Эти файлы содержат astro_basics_gen:'
grep -rl ' astro_basics_gen ' /opt/astro_bot/ > tmp_matches.txt
cat tmp_matches.txt
echo ''
read -p 'Сделал переименование и замену? [Y/n]: ' confirm
if [[ $confirm != "Y" && $confirm != "y" ]]; then
  echo 'Операция прервана пользователем.'
  exit 1
fi
rm tmp_matches.txt