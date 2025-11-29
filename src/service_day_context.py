# /opt/astro_bot/src/service_day_context.py

import sqlite3
from datetime import datetime
from typing import Optional
from dataclass_day_context import DayContext

DB_PATH = "/opt/astro_bot/config/day_context.db"

def from_row(row: tuple) -> DayContext:
    return DayContext(
        date=row[0],
        moon_phase=row[1],
        moon_illumination=row[2],
        moon_age=row[3],
        moon_sign=row[4],
        sun_sign=row[5],
        mercury_sign=row[6],
        venus_sign=row[7],
        mars_sign=row[8],
        jupiter_sign=row[9],
        saturn_sign=row[10],
        lunar_day=row[11],
        is_new_moon_day=bool(row[12]),
        is_full_moon_day=bool(row[13]),
        next_new_moon=row[14],
        prev_full_moon=row[15],
        next_full_moon=row[16],
        planet_of_day=row[17],
        moon_in_element=row[18],
        special_event=row[19],
    )

def load_day_context(date: datetime) -> DayContext:
    date_str = date.strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM day_context WHERE date = ?", (date_str,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return from_row(row)
    else:
        raise ValueError(f"No context found for date: {date_str}")
