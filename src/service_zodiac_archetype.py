# /opt/astro_bot/src/zodiac_archetype_service.py

import sqlite3
from dataclass_zodiac_archetype import ZodiacArchetype

DB_PATH = "/opt/astro_bot/config/zodiac_archetypes.db"

def get_zodiac_archetype(sign: str) -> ZodiacArchetype:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.execute("""
        SELECT * FROM zodiac_archetypes WHERE sign = ?
    """, (sign.capitalize(),))

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"Знак зодиака '{sign}' не найден в базе.")

    return ZodiacArchetype(
        sign=row["sign"],
        element=row["element"],
        tempo=row["tempo"],
        polarity=row["polarity"],
        archetype=row["archetype"],
        light=row["light"],
        shadow=row["shadow"],
        growth_strategy=row["growth_strategy"],
        tension_control=row["tension_control"],
        tension_order=row["tension_order"],
        tension_speed=row["tension_speed"]
    )
