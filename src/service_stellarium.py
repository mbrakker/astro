# /opt/astro_bot/src/service_stellarium.py
import os
import time
import datetime
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

LAT = os.getenv("STELLARIUM_LAT", "55.75")
LNG = os.getenv("STELLARIUM_LNG", "37.62")
ELEV = os.getenv("STELLARIUM_ELEV", "0")
DEFAULT_TIME = "T01:00:00Z"
IMAGE_DIR = "/opt/astro_bot/images/energy"

PLANET_TRANSLATIONS = {
    "меркурий": "Mercury",
    "венера": "Venus",
    "марс": "Mars",
    "юпитер": "Jupiter",
    "сатурн": "Saturn",
    "уран": "Uranus",
    "нептун": "Neptune",
    "плутон": "Pluto",
    "луна": "Moon",
    "солнце": "Sun"
}

PLANET_FOV = {
    "меркурий": (0.0032810, 68.963),
    "венера": (0.013767, 68.963),
    "марс": (0.0043968, 68.963),
    "юпитер": (0.013767, 68.963),
    "сатурн": (0.011326, 68.963),
    "уран": (0.0017737, 68.963),
    "нептун": (0.0012005, 68.963),
    "плутон": (0.00027778, 68.963),
    "луна": (0.85424, 68.963),
    "солнце": (0.85424, 68.963)
}

def build_stellarium_url(body: str, fov: float, date: datetime.date) -> str:
    date_str = date.isoformat()
    full_date = f"{date_str}{DEFAULT_TIME}"
    return f"https://stellarium-web.org/skysource/{body}?fov={fov}&date={full_date}&lat={LAT}&lng={LNG}&elev={ELEV}"

def toggle_visual_settings(driver):
    try:
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.bottom-button')))
        buttons = driver.find_elements(By.CSS_SELECTOR, '.bottom-button')
        button_map = {}
        for btn in buttons:
            try:
                hint = btn.find_element(By.CLASS_NAME, 'hint').get_attribute("innerHTML").strip().lower()
                button_map[hint] = btn
            except:
                continue

        def toggle(label: str, should_enable: bool):
            btn = button_map.get(label)
            if not btn:
                return
            classes = btn.get_attribute('class').split()
            is_on = 'on' in classes
            if is_on != should_enable:
                try:
                    btn.find_element(By.TAG_NAME, "a").click()
                except:
                    pass

        toggle("constellations", True)
        toggle("atmosphere", False)
        toggle("landscape", False)
        toggle("deep sky objects", False)
    except Exception as e:
        logger.warning(f"❌ Ошибка при настройке Stellarium: {e}")

def take_screenshot(url: str, filename: str) -> str:
    os.makedirs(IMAGE_DIR, exist_ok=True)
    filepath = os.path.join(IMAGE_DIR, filename)
    if os.path.exists(filepath):
        logger.info(f"🖼 Уже существует: {filename}")
        return filepath

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)
        time.sleep(5)
        toggle_visual_settings(driver)

        driver.execute_script("""
            document.querySelectorAll('.sidebar, .top-bar, .location-box, .info-panel, .bottom-bar')
              .forEach(el => el.style.display = 'none');
        """)
        wait = WebDriverWait(driver, 15)
        canvas = wait.until(EC.presence_of_element_located((By.TAG_NAME, "canvas")))
        canvas.screenshot(filepath)
    except Exception as e:
        logger.warning(f"❌ Ошибка скриншота Stellarium: {e}")
        filepath = None
    finally:
        driver.quit()

    return filepath

def get_stellarium_images(date: datetime.date, planet: str) -> list:
    paths = []

    # Луна
    moon_close = build_stellarium_url("Moon", PLANET_FOV["луна"][0], date)
    moon_wide = build_stellarium_url("Moon", PLANET_FOV["луна"][1], date)
    paths.append(take_screenshot(moon_close, f"{date.isoformat()}_moon_close.png"))
    paths.append(take_screenshot(moon_wide, f"{date.isoformat()}_moon_wide.png"))

    planet = planet.lower()
    if planet != "луна":
        eng = PLANET_TRANSLATIONS.get(planet)
        if eng and planet in PLANET_FOV:
            fov_close, fov_wide = PLANET_FOV[planet]
            url_close = build_stellarium_url(eng, fov_close, date)
            url_wide = build_stellarium_url(eng, fov_wide, date)
            paths.append(take_screenshot(url_close, f"{date.isoformat()}_{planet}_close.png"))
            paths.append(take_screenshot(url_wide, f"{date.isoformat()}_{planet}_wide.png"))

    return [p for p in paths if p]
