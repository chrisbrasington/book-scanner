import csv
import os
from openlibrary import fetch_open_library_data
from googlebooks import fetch_google_books_data
from classes import Book  # Import the Book class
from datetime import datetime

CSV_FILE = "books.csv"

def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except Exception:
        return False

def update_book_info(book: Book):
    print(f"[+] Processing '{book.title}' by {book.author}")

    # Determine if we need to fetch from Open Library or Google Books
    needs_openlibrary = not book.tags
    needs_google = (not is_valid_date(book.publish_date) or not book.description)

    openlib_data = None
    google_data = None

    # Fetch from Open Library only if needed
    if needs_openlibrary:
        openlib_data = fetch_open_library_data(book.isbn13) or fetch_open_library_data(book.isbn10)
        if openlib_data:
            print("  -> Open Library data fetched.")

    # Fetch from Google Books only if needed
    if needs_google:
        google_data = fetch_google_books_data(book.isbn13) or fetch_google_books_data(book.isbn10)
        if google_data:
            print("  -> Google Books data fetched.")

    # Try to update tags from Open Library first
    if not book.tags and openlib_data:
        key = f"ISBN:{book.isbn13 or book.isbn10}"
        subjects = openlib_data.get(key, {}).get("subjects", [])
        tags = ", ".join(subj["name"] for subj in subjects if "name" in subj)
        if tags:
            print(f"  -> Tags added from Open Library: {tags}")
            book.tags = tags

    # Fallback: get tags from Google Books if Open Library failed
    if not book.tags and google_data:
        categories = google_data.get("volumeInfo", {}).get("categories", [])
        if categories:
            tags = ", ".join(categories)
            print(f"  -> Tags added from Google Books: {tags}")
            book.tags = tags

    # Fix publish date if it's invalid using Google Books
    if not is_valid_date(book.publish_date) and google_data:
        publish_date = google_data.get("volumeInfo", {}).get("publishedDate", "")
        if is_valid_date(publish_date):
            print(f"  -> Publish date fixed: {book.publish_date} -> {publish_date}")
            book.publish_date = publish_date
        else:
            print("  -> Google Books had invalid or no publish date.")

    # Add description from Google Books if missing
    if not book.description and google_data:
        description = google_data.get("volumeInfo", {}).get("description", "")
        if description:
            print("  -> Description added from Google Books.")
            book.description = description

    # Add thumbnail from Google Books if missing
    if not book.thumbnail and google_data:
        thumbnail_url = google_data.get("volumeInfo", {}).get("imageLinks", {}).get("thumbnail", "")
        if thumbnail_url:
            print(f"  -> Thumbnail added from Google Books: {thumbnail_url}")
            book.thumbnail = thumbnail_url

    return book

def main():
    if not os.path.exists(CSV_FILE):
        print(f"{CSV_FILE} not found.")
        return

    books = []
    with open(CSV_FILE, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            book = Book(
                isbn13=row["ISBN-13"],
                isbn10=row["ISBN-10"],
                title=row["Title"],
                subtitle=row["Subtitle"],
                author=row["Author"],
                publish_date=row["Publish Date"],
                url=row["URL"],
                scanned_input=row["Scanned Input"],
                tags=row["Tags"],
                description=row.get("Description", ""),  # Support old CSVs
                thumbnail=row.get("Thumbnail", "")  # Read thumbnail from CSV if available
            )
            books.append(book)

    # Process books
    updated_books = []
    for book in books:
        updated_books.append(update_book_info(book))

    # Write updated books to CSV
    with open(CSV_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(Book.csv_headers())  # Assuming Book class has a method to return headers
        for book in updated_books:
            # Ensure `thumbnail` is written back to the CSV
            writer.writerow(book.to_csv_row())

if __name__ == "__main__":
    main()
