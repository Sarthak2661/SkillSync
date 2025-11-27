from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import psycopg2
import streamlit as st

# --- Make 'src' importable when running `streamlit run dashboard/app.py` ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.config.settings import settings  # type: ignore


# ---------- DB helpers ----------

def get_connection():
    if not settings.db_url:
        raise RuntimeError("WEBSCRAPER_DB_URL is not set in .env")
    return psycopg2.connect(settings.db_url)


@st.cache_data(ttl=300)
def load_books_df() -> pd.DataFrame:
    """Load all books from Postgres into a DataFrame."""
    with get_connection() as conn:
        df = pd.read_sql(
            """
            SELECT
                title,
                price,
                currency,
                rating,
                availability_text,
                in_stock,
                stock_count,
                product_url,
                scraped_at
            FROM books
            """,
            conn,
        )
    return df


# ---------- UI ----------

st.set_page_config(
    page_title="Books to Scrape – Analytics",
    layout="wide",
)

st.title("📚 Books to Scrape – Analytics Dashboard")
st.caption(
    "Data collected by your Python web scraper → cleaned with pandas → stored in PostgreSQL."
)

# Load data
df = load_books_df()

if df.empty:
    st.warning("No data in the `books` table yet. Run `web_scraper_etl.py` first.")
    st.stop()

# ---------- Sidebar filters ----------

st.sidebar.header("Filters")

min_rating: Optional[int] = st.sidebar.slider(
    "Minimum rating (stars)",
    min_value=1,
    max_value=5,
    value=1,
)

price_min = float(df["price"].min()) if df["price"].notna().any() else 0.0
price_max = float(df["price"].max()) if df["price"].notna().any() else 100.0

price_range = st.sidebar.slider(
    "Price range",
    min_value=round(price_min, 2),
    max_value=round(price_max, 2),
    value=(round(price_min, 2), round(price_max, 2)),
)

search_text = st.sidebar.text_input(
    "Search in title",
    value="",
    placeholder="e.g. history, love, python...",
)

# Apply filters
filtered = df.copy()

if min_rating:
    filtered = filtered[filtered["rating"].fillna(0) >= min_rating]

filtered = filtered[
    (filtered["price"].fillna(0) >= price_range[0])
    & (filtered["price"].fillna(0) <= price_range[1])
]

if search_text.strip():
    filtered = filtered[filtered["title"].str.contains(search_text, case=False, na=False)]

st.sidebar.markdown(f"**Books after filters:** {len(filtered)}")

# ---------- Top metrics row ----------

total_books = len(df)
priced_books = df["price"].notna().sum()
avg_price = df["price"].mean()
min_price = df["price"].min()
max_price = df["price"].max()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total books", total_books)
col2.metric("Books with price", int(priced_books))
col3.metric("Avg price (£)", f"{avg_price:.2f}" if pd.notna(avg_price) else "N/A")
col4.metric("Min price (£)", f"{min_price:.2f}" if pd.notna(min_price) else "N/A")
col5.metric("Max price (£)", f"{max_price:.2f}" if pd.notna(max_price) else "N/A")

st.markdown("---")

# ---------- Charts ----------

left, right = st.columns(2)

with left:
    st.subheader("📊 Rating distribution")
    rating_counts = (
        filtered["rating"]
        .value_counts()
        .sort_index()
        .rename_axis("rating")
        .reset_index(name="count")
    )
    st.bar_chart(rating_counts.set_index("rating")["count"])

with right:
    st.subheader("💰 Price distribution")
    st.caption("Approximate histogram of book prices after filters.")

    price_series = filtered["price"].dropna()

    if not price_series.empty:
        bin_count = 15  # 10–20 is usually nice

        # Create numeric bins
        bins = pd.cut(price_series, bins=bin_count)

        # Count how many books fall into each bin
        hist = (
            bins.value_counts()
            .sort_index()
            .rename_axis("interval")
            .reset_index(name="count")
        )

        # Pretty string labels like "£10–£15"
        def format_bin(iv):
            return f"£{iv.left:.0f}–£{iv.right:.0f}"

        hist["price_range"] = hist["interval"].apply(format_bin)

        # Use price_range as index for the chart
        hist = hist[["price_range", "count"]].set_index("price_range")

        st.bar_chart(hist["count"])
    else:
        st.info("No price data available for the current filters.")

st.markdown("---")

st.subheader("📈 Price vs Rating")

scatter_df = filtered[["rating", "price"]].dropna()

if scatter_df.empty:
    st.info("Not enough data with both price and rating to show this chart.")
else:
    st.caption("Each point is a book. Helps see whether higher-rated books are more expensive.")
    # Rating on X-axis, Price on Y-axis
    st.scatter_chart(scatter_df, x="rating", y="price")


st.subheader("🏆 Top 10 books by price")

col_expensive, col_cheap = st.columns(2)

base_price_df = filtered.dropna(subset=["price"])

with col_expensive:
    st.markdown("**Most expensive books**")
    if base_price_df.empty:
        st.info("No price data available.")
    else:
        top_expensive = (
            base_price_df
            .sort_values("price", ascending=False)
            .head(10)
        )
        st.bar_chart(
            top_expensive.set_index("title")["price"],
        )

with col_cheap:
    st.markdown("**Cheapest books**")
    if base_price_df.empty:
        st.info("No price data available.")
    else:
        top_cheapest = (
            base_price_df
            .sort_values("price", ascending=True)
            .head(10)
        )
        st.bar_chart(
            top_cheapest.set_index("title")["price"],
        )

# ---------- Time-based view (if multiple scrapes) ----------

st.subheader("⏱ Average price over time (per scrape run)")
if "scraped_at" in df.columns:
    tmp = (
        df.dropna(subset=["price"])
        .assign(scrape_time=lambda x: x["scraped_at"].dt.floor("min"))
        .groupby("scrape_time")["price"]
        .mean()
        .reset_index()
    )
    if not tmp.empty:
        tmp = tmp.set_index("scrape_time")
        st.line_chart(tmp["price"])
    else:
        st.info("Not enough price data to show a time series yet.")
else:
    st.info("No `scraped_at` column available.")

st.markdown("---")

# ---------- Table of results ----------

st.subheader("📄 Filtered books")
st.dataframe(
    filtered[["title", "price", "rating", "in_stock", "stock_count", "product_url"]],
    use_container_width=True,
)

st.caption("Tip: click the column headers to sort by price, rating, etc.")
