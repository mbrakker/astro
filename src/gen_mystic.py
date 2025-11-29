# /opt/astro_bot/src/gen_mystic.py
# -*- coding: utf-8 -*-
import os
import requests
import re
import io
import feedparser
from PIL import Image
from bs4 import BeautifulSoup
from service_text import generate_text
from service_image import generate_image_for_topic
from dataclass_generated_post import GeneratedPost

# Настройки RSS и ключевых слов
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (ScarletLunaBot)"
}

RSS_CATEGORIES = {
    "news_all": os.getenv("RSS_NEWS_ALL", "").split(","),
    "news_astro": os.getenv("RSS_NEWS_ASTRO", "").split(","),
    "news_horoscope": os.getenv("RSS_NEWS_HOROSCOPES", "").split(","),
    "mystic": os.getenv("RSS_MYSTIC", "").split(","),
    "education": os.getenv("RSS_EDUCATION", "").split(","),
    "open_slot": os.getenv("RSS_OPEN_SLOT", "").split(","),
}

KEYWORDS_CATEGORIES = {
    "news_astro": [kw.strip().lower() for kw in os.getenv("KEYWORDS_NEWS_ASTRO", "").split(",") if kw.strip()],
    "news_horoscope": [kw.strip().lower() for kw in os.getenv("KEYWORDS_HOROSCOPES", "").split(",") if kw.strip()],
    "mystic": [kw.strip().lower() for kw in os.getenv("KEYWORDS_MYSTIC", "").split(",") if kw.strip()],
    "education": [kw.strip().lower() for kw in os.getenv("KEYWORDS_EDUCATION", "").split(",") if kw.strip()],
    "open_slot": [kw.strip().lower() for kw in os.getenv("KEYWORDS_OPEN_SLOT", "").split(",") if kw.strip()],
}

def clean_html(html_text: str) -> str:
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text(separator=' ', strip=True)

def fetch_rss_entries(rss_urls: list, keywords: list = None, category: str = "news_all", limit: int = 5) -> list:
    news_list = []
    for url in rss_urls:
        if not url.strip():
            continue
        try:
            response = requests.get(url, timeout=10, headers=REQUEST_HEADERS)
            feed = feedparser.parse(response.content)
        except Exception as e:
            print(f"Ошибка при загрузке RSS {url}: {e}")
            continue

        for entry in feed.entries:
            title = entry.title.strip()
            raw_description = getattr(entry, 'summary', '') or ''
            description = clean_html(raw_description)
            if not description:
                description = title

            image_urls = []
            if hasattr(entry, 'media_content'):
                image_urls.extend([m['url'] for m in entry.media_content if 'url' in m])
            if hasattr(entry, 'enclosures'):
                image_urls.extend([e['href'] for e in entry.enclosures if 'href' in e])
            if hasattr(entry, 'content'):
                for c in entry.content:
                    html = c.get('value', '')
                    image_urls.extend(re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html))
            if not image_urls:
                image_urls.extend(re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', raw_description))

            # Уникализируем ссылки на изображения
            image_urls = list(set(image_urls))

            text_to_search = (title + " " + description).lower()
            if keywords and not any(kw in text_to_search for kw in keywords):
                continue

            news_list.append({
                "type": category,
                "title": title,
                "description": description,
                "image_urls": image_urls,
                "source_url": getattr(entry, 'link', '')
            })

            if len(news_list) >= limit:
                break
        if len(news_list) >= limit:
            break
    return news_list

def transform_news(title: str, description: str, category: str) -> str:
    """
    Стилизует новость в стиле Скарлет Луны через централизованный service_text.
    """
    section = f"mystic_news.{category}"
    return generate_text(
        topic_type=section,
        theme=title,
        context={"title": title, "summary": description}
    )

def download_image(urls: list, prefix: str) -> str:
    for i, url in enumerate(urls):
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            img = Image.open(io.BytesIO(r.content))
            if img.width < 700 or img.height < 700:
                continue
            ext = url.split('?')[0].split('.')[-1]
            filename = f"{prefix}_{i}.{ext}"
            path = f"/opt/astro_bot/images/mystic/{filename}"
            with open(path, "wb") as f:
                f.write(r.content)
            return path
        except Exception:
            continue
    return ""

def build_mystic_posts(limit_per_category: int = 5, only_category: str = None) -> list:
    posts = []
    categories = [only_category] if only_category else RSS_CATEGORIES.keys()

    for cat in categories:
        urls = RSS_CATEGORIES.get(cat, [])
        kws = None if cat == "news_all" else KEYWORDS_CATEGORIES.get(cat, [])
        news_list = fetch_rss_entries(urls, keywords=kws, category=cat, limit=limit_per_category)

        for idx, news in enumerate(news_list, start=1):
            title = news["title"]
            desc = news["description"]
            text = transform_news(title, desc, cat)

            image = download_image(news["image_urls"], f"mystic_{cat}_{idx}")
            if not image:
                topic = {
                    "type": cat,  # ⚠️ важно! не "mystic", а real subtype: news_astro, etc.
                    "theme": title,
                    "context": {
                        "category": cat,
                        "news_title": title,
                        "summary": desc
                    }
                }
                image = generate_image_for_topic(topic)

            posts.append({
                "type": cat,
                "title": title,
                "description": desc,
                "text": text,
                "images": [image] if image else [],
                "source_url": news["source_url"]
            })

    return posts



def generate_mystic_post(limit: int = 3) -> list[GeneratedPost]:
    """
    Возвращает список GeneratedPost на основе мистических новостей.
    """
    raw_posts = build_mystic_posts(limit_per_category=limit, only_category="mystic")
    result = []

    for item in raw_posts:
        title = item["title"]
        text = item["text"]
        images = item.get("images", [])
        source = item.get("source_url", "")
        summary = item.get("description", "")

        post = GeneratedPost(
            type="mystic",
            text=text,
            media_types={"image": images} if images else {},
            metadata={
                "title": title,
                "summary": summary,
                "source_url": source,
                "category": "mystic"
            }
        )
        result.append(post)

    return result