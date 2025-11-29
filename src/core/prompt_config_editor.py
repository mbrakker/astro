# src/core/prompt_config_editor.py

import yaml

def load_prompt_config(path: str) -> dict:
    """Загружает prompts.yaml как словарь"""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_prompt_config(path: str, data: dict):
    """Сохраняет изменённый конфиг обратно в YAML"""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)
