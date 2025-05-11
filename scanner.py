import csv
import os
import requests
from dataclasses import dataclass, asdict, field

BOOKS_CSV = "books.csv"

@dataclass
class Book:
    isbn13: str
    title: str
    subtitle: str = ""
    author: str = ""
    publish_date: str = ""
    url: str = ""

    @classmethod
    def from_api(cls, isbn: str, data: dict):
        key = f"ISBN:{isbn}"
        book_data = data.get(key, {})
        return cls(
            isbn13=isbn,
            title=book_data.get("title", ""),
            subtitle=book_data.get("subtitle", ""),
            author=", ".join(a["name"] for a in book_data.get("authors", [])),
            publish_date=book_data.get("publish_date", ""),
            url=book_data.get("url", "")
        )

    def to_csv_row(self):
        return [self.isbn13, self.title, self.subtitle, self.author, self.publish_date, self.url]

    @staticmethod
    def csv_headers():
        return ["ISBN-13", "Title", "Subtitle", "Author", "Publish Date", "URL"]

def load_books() -> dict:
    books = {}
    try:
        with open(BOOKS_CSV, newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                books[row["ISBN-13"]] = Book(
                    isbn13=row["ISBN-13"],
                    title=row["Title"],
                    subtitle=row["Subtitle"],
                    author=row["Author"],
                    publish_date=row["Publish Date"],
                    url=row["URL"]
                )
    except FileNotFoundError:
        pass
    return books

def save_books(books: dict):
    sorted_books = sorted(
        books.values(),
        key=lambda b: (b.author.lower(), b.publish_date)
    )
    with open(BOOKS_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(Book.csv_headers())
        for book in sorted_books:
            writer.writerow(book.to_csv_row())

def fetch_book_data(isbn: str) -> dict:
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {}

def main():
    books = load_books()

    while True:
        isbn = input("Enter ISBN-13 (or 'q' to quit): ").strip().replace('-','')
        os.system('clear')
        if isbn.lower() == 'q':
            break
        if len(isbn) != 13 or not isbn.isdigit():
            print("Invalid ISBN-13. Try again.\n")
            continue
        if isbn in books:
            book = books[isbn]
            print(f"Book already in database:\n\n\tTitle: {book.title}\n\tAuthor: {book.author}\n\tPublished: {book.publish_date}\n")
            continue

        data = fetch_book_data(isbn)
        if not data or f"ISBN:{isbn}" not in data:
            print("Book not found.\n")
            continue

        book = Book.from_api(isbn, data)
        books[isbn] = book
        save_books(books)
        print(f"Added: {book.title} by {book.author}\n")

if __name__ == "__main__":
    main()
