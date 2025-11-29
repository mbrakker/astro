# /opt/astro_bot/src/dataclass_day_context.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class DayContext:
    date: str                            # YYYY-MM-DD
    moon_phase: str                      # Фаза Луны
    moon_illumination: float             # Освещённость Луны (0.0–100.0)
    moon_age: float                      # Возраст Луны (в днях)
    moon_sign: str                       # Знак Луны
    sun_sign: str                        # Знак Солнца
    mercury_sign: str                    # Знак Меркурия
    venus_sign: str                      # Знак Венеры
    mars_sign: str                       # Знак Марса
    jupiter_sign: str                    # Знак Юпитера
    saturn_sign: str                     # Знак Сатурна
    lunar_day: int                       # Лунный день
    is_new_moon_day: bool               # Новый день новолуния
    is_full_moon_day: bool              # День полнолуния
    next_new_moon: str                  # Дата следующего новолуния
    prev_full_moon: str                 # Дата предыдущего полнолуния
    next_full_moon: str                 # Дата следующего полнолуния
    planet_of_day: str                  # Планета дня
    moon_in_element: str                # Стихия Луны
    special_event: str                  # Специальное событие (Фаза в Знаке)
