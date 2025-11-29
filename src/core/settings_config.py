import yaml
import os

SETTINGS_PATH = "/opt/astro_bot/config/settings.yaml"
ENV_PATH = "/opt/astro_bot/env/.env"

def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        return {}
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_settings(data):
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)


def load_env_vars():
    if not os.path.exists(ENV_PATH):
        return {}
    env = {}
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() and "=" in line:
                k, v = line.strip().split("=", 1)
                env[k] = v
    return env

def save_env_vars(env_dict):
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        for k, v in env_dict.items():
            f.write(f"{k}={v}\n")
