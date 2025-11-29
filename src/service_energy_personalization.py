# /opt/astro_bot/src/service_energy_personalization.py
# -*- coding: utf-8 -*-
import sqlite3
from dataclass_energy_personalization import EnergyPersonalization, PersonalizationBlock

DB_PATH = "/opt/astro_bot/config/energy_personalization.db"

def fetch_personalization(sign: str, influence_type: str, influence_value: str) -> PersonalizationBlock:
    query = """
        SELECT tone, message
        FROM personalizations
        WHERE sign = ? AND influence_type = ? AND influence_value = ?
        LIMIT 1
    """

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (sign, influence_type, influence_value))
        result = cursor.fetchone()

    tone, message = result if result else (None, None)
    return PersonalizationBlock(
        influence_type=influence_type,
        influence_value=influence_value,
        tone=tone,
        message=message
    )


def get_energy_personalization(sign: str, moon_phase: str, moon_sign: str, planet: str) -> EnergyPersonalization:
    sign = sign.capitalize()
    moon_phase = moon_phase.capitalize()
    moon_sign = moon_sign.capitalize()
    planet = planet.capitalize()

    return EnergyPersonalization(
        sign=sign,
        moon_phase=fetch_personalization(sign, "фаза Луны", moon_phase),
        moon_sign=fetch_personalization(sign, "знак Луны", moon_sign),
        planet=fetch_personalization(sign, "планета дня", planet)
    )