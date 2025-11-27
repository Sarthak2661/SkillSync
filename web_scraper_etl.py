# web_scraper_etl.py

from src.scraper.static_scraper import scrape_books
from src.etl.io import save_raw_records
from src.etl.transform import normalize_records, save_processed_df
from src.etl.db import init_db, insert_books


def main() -> None:
    # 1) Scrape
    raw_books = scrape_books(num_pages=5)
    print(f"Scraped {len(raw_books)} books")

    # 2) Save raw
    raw_path = save_raw_records(raw_books, name="books")
    print(f"Saved raw data to: {raw_path}")

    # 3) Transform + save processed CSV
    df = normalize_records(raw_books)
    processed_path = save_processed_df(df, name="books_clean")
    print(f"Saved processed data to: {processed_path}")

    # 4) Init DB + load
    init_db()
    insert_books(df)


if __name__ == "__main__":
    main()
