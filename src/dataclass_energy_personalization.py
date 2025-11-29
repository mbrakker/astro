# /opt/astro_bot/src/dataclass_energy_personalization.py
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Optional

@dataclass
class PersonalizationBlock:
    influence_type: str      # Тип воздействия: "фаза Луны", "знак Луны", "планета дня"
    influence_value: str     # Конкретное значение (например, "Полнолуние", "Овен", "Марс")
    tone: Optional[str]      # "похвала" или "вызов", может быть None
    message: Optional[str]   # Персонализированное сообщение, может быть None

@dataclass
class EnergyPersonalization:
    sign: str                            # Знак зодиака, например "Лев"
    moon_phase: PersonalizationBlock     # Блок: влияние фазы Луны
    moon_sign: PersonalizationBlock      # Блок: влияние знака Луны
    planet: PersonalizationBlock         # Блок: влияние планеты дня
