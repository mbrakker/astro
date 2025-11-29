# /opt/astro_bot/src/dataclass_tarot.py
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Optional

@dataclass
class TarotCardDraw:
    id: str                         # ID карты (например, "T12")
    name: str                       # Название карты
    arcana: str                     # major / minor
    suit: Optional[str] = None     # Масть (если есть)
    number: Optional[int] = None   # Номер карты (если есть)
    reversed: bool = False         # Перевёрнута ли карта
    upright_text: Optional[str] = None      # Прямая трактовка
    reversed_text: Optional[str] = None     # Перевёрнутая трактовка
    suit_archetype: Optional[str] = None    # Архетип масти
    number_archetype: Optional[str] = None  # Архетип числа
    position: Optional[str] = None          # Позиция (Прошлое/Настоящее/Будущее)
    image_path: Optional[str] = None        # Путь к изображению

    def get_interpretation(self) -> str:
        """
        Возвращает трактовку карты в зависимости от положения.
        """
        if self.reversed and self.reversed_text:
            return self.reversed_text.strip()
        elif not self.reversed and self.upright_text:
            return self.upright_text.strip()
        else:
            return "🔮 Карта скрывает свою тайну…"
