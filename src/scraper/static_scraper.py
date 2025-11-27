# src/scraper/static_scraper.py
from __future__ import annotations
from typing import List, Dict
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from src.config.settings import settings

def fetch_page(url: str) -> str:
    """Download a single page and return HTML text."""
    headers = {"User-Agent": settings.user_agent}
    resp = requests.get(url, headers=headers, timeout=10)

    # 👇 Force correct encoding to avoid Â£ etc.
    if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
        resp.encoding = "utf-8"

    resp.raise_for_status()
    return resp.text

def parse_book_list(html: str) -> List[Dict]:
    """Parse the books on a category/listing page."""
    soup = BeautifulSoup(html, "lxml")
    books: List[Dict] = []

    for article in soup.select("article.product_pod"):
        title = article.h3.a["title"].strip()

        price_text = article.select_one(".price_color").get_text(strip=True)
        # Rating is encoded in a CSS class like "star-rating Three"
        rating_classes = article.p.get("class", [])
        rating_raw = rating_classes[1] if len(rating_classes) > 1 else None

        availability_text = (
            article.select_one(".availability").get_text(strip=True)
        )

        relative_url = article.h3.a["href"]
        product_url = urljoin(settings.base_url, relative_url)

        books.append(
            {
                "title": title,
                "price_raw": price_text,
                "rating_raw": rating_raw,
                "availability_raw": availability_text,
                "product_url": product_url,
            }
        )

    return books


def scrape_books(num_pages: int = 1) -> List[Dict]:
    """
    Scrape N pages starting from the home page.
    For now we just follow the 'next' button on BooksToScrape.
    """
    from bs4 import BeautifulSoup  # local import to reuse

    all_books: List[Dict] = []
    next_url = settings.base_url

    for _ in range(num_pages):
        html = fetch_page(next_url)
        books = parse_book_list(html)
        all_books.extend(books)

        soup = BeautifulSoup(html, "lxml")
        next_link = soup.select_one("li.next > a")
        if not next_link:
            break

        next_url = urljoin(next_url, next_link["href"])

    return all_books
