# api/main.py
from __future__ import annotations
from src.etl.db import fetch_books, fetch_price_stats, search_books
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, Query
from pydantic import BaseModel
from src.etl.db import fetch_books, fetch_price_stats
from pydantic_settings import BaseSettings



class Book(BaseModel):
    title: str
    price: Optional[float] = None
    currency: Optional[str] = None
    rating: Optional[int] = None
    availability_text: Optional[str] = None
    in_stock: Optional[bool] = None
    stock_count: Optional[int] = None
    product_url: Optional[str] = None
    scraped_at: datetime


app = FastAPI(
    title="Book Price API",
    description="API over the scraped 'Books to Scrape' dataset.",
    version="0.1.0",
)
@app.get("/")
def root():
    return {
        "message": "Web Scraper ETL API is running",
        "docs": "/docs",
        "endpoints": ["/books", "/books/cheapest", "/stats/prices"],
    }

@app.get("/books", response_model=List[Book])
def list_books(
    limit: int = Query(20, ge=1, le=200),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
):
    """
    List books from the database.
    - limit: max number of books
    - min_rating: filter by minimum star rating
    """
    rows = fetch_books(limit=limit, min_rating=min_rating)
    return [Book(**row) for row in rows]


@app.get("/books/cheapest", response_model=List[Book])
def cheapest_books(limit: int = Query(10, ge=1, le=200)):
    """
    Return the cheapest N books (by price).
    """
    rows = fetch_books(limit=limit, min_rating=None)
    return [Book(**row) for row in rows]


@app.get("/stats/prices")
def price_stats():
    """
    Simple aggregated stats about prices.
    """
    return fetch_price_stats()

@app.get("/books/search", response_model=List[Book])
def search_books_endpoint(
    q: str = Query(..., min_length=1, description="Search term in book title"),
    limit: int = Query(20, ge=1, le=200),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
):
    """
    Search books by title substring (case-insensitive).
    Example: /books/search?q=history&min_rating=4
    """
    rows = search_books(query=q, limit=limit, min_rating=min_rating)
    return [Book(**row) for row in rows]