import yaml
import os

RULES_PATH = "/opt/astro_bot/config/publish_rules.yaml"

def load_publish_rules():
    if not os.path.exists(RULES_PATH):
        return []
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []

def save_publish_rules(rules: list):
    with open(RULES_PATH, "w", encoding="utf-8") as f:
        yaml.dump(rules, f, allow_unicode=True)
