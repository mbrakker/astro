# /opt/astro_bot/src/dataclass_zodiac_archetype.py

from dataclasses import dataclass

@dataclass
class ZodiacArchetype:
    sign: str                # Название знака зодиака (Овен, Телец...)
    element: str             # Стихия (Огонь, Земля, Воздух, Вода)
    tempo: str               # Темп (Быстрый, Средний, Медленный)
    polarity: str            # Полярность (Активный, Пассивный)
    archetype: str           # Основной архетип (Воин, Хранитель, и т.д.)
    light: str               # Свет (сильные стороны)
    shadow: str              # Тень (слабости, страхи)
    growth_strategy: str     # Стратегия роста (направление развития)
    tension_control: str     # Архетипическое напряжение: Контроль vs Поток
    tension_order: str       # Архетипическое напряжение: Порядок vs Хаос
    tension_speed: str       # Архетипическое напряжение: Скорость vs Внимательность
