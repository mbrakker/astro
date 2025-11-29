# /opt/astro_bot/src/dataclass_generated_post.py

from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class GeneratedPost:
    type: str                                                           # Тип контента: 'horoscope', 'tarot', 'energy_day' и т.д.
    text: str                                                           # Основной текст поста
    media: List[str] = field(default_factory=list)                      # Все медиафайлы
    media_types: Dict[str, List[str]] = field(default_factory=dict)     # {"image": [...], "video": [...], ...}
    metadata: Dict = field(default_factory=dict)                        # Дополнительные параметры: theme, sign и т.д.

    def __post_init__(self):
        # Безопасность: убедимся, что поля корректны
        if self.media is None:
            self.media = []
        if self.media_types is None:
            self.media_types = {}
        if self.metadata is None:
            self.metadata = {}

    def is_ready_for_publish(self) -> bool:
        return bool(self.text)

    def main_image(self) -> Optional[str]:
        return self._get_media("image")

    def main_video(self) -> Optional[str]:
        return self._get_media("video")

    def main_audio(self) -> Optional[str]:
        return self._get_media("audio")

    def all_images(self) -> List[str]:
        return self.media_types.get("image", [])

    def all_audio(self) -> List[str]:
        return self.media_types.get("audio", [])

    def all_video(self) -> List[str]:
        return self.media_types.get("video", [])

    def _get_media(self, media_type: str) -> Optional[str]:
        return self.media_types.get(media_type, [None])[0]

    def __str__(self):
        return f"<GeneratedPost type={self.type}, media={len(self.media)} items, metadata={list(self.metadata.keys())}>"
