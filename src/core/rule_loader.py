import yaml
import os

RULES_PATH = "/opt/astro_bot/config/publish_rules.yaml"

def load_rules_full():
    if not os.path.exists(RULES_PATH):
        return {"min_posts_per_day": 1, "max_posts_per_day": 4, "rules": []}
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def save_rules_full(data):
    with open(RULES_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

def load_rules():
    return load_rules_full().get("rules", [])

def save_rule(rule):
    data = load_rules_full()
    rules = data.get("rules", [])
    rules = [r for r in rules if r.get("type") != rule["type"]]
    rules.append(rule)
    data["rules"] = rules
    save_rules_full(data)
