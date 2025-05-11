import os
import csv
import requests
from dataclasses import dataclass
from datetime import datetime

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

    @classmethod
    def from_google_books(cls, isbn: str, data: dict):
        volume_info = data.get("volumeInfo", {})
        return cls(
            isbn13=isbn,
            title=volume_info.get("title", ""),
            subtitle=volume_info.get("subtitle", ""),
            author=", ".join(volume_info.get("authors", [])),
            publish_date=volume_info.get("publishedDate", ""),
            url=volume_info.get("infoLink", "")
        )

    def to_csv_row(self):
        return [self.isbn13, self.title, self.subtitle, self.author, self.publish_date, self.url]

    @staticmethod
    def csv_headers():
        return ["ISBN-13", "Title", "Subtitle", "Author", "Publish Date", "URL"]

    def sortable_date(self):
        try:
            return datetime.strptime(self.publish_date, "%b %d, %Y")
        except ValueError:
            try:
                return datetime.strptime(self.publish_date, "%Y")
            except ValueError:
                return datetime.min

    def __str__(self):
        lines = [
            f"Title: {self.title}",
            f"Subtitle: {self.subtitle}" if self.subtitle else None,
            f"Author: {self.author}",
            f"Published: {self.publish_date}",
            f"URL: {self.url}\n" if self.url else None
        ]
        return "\n".join(filter(None, lines))

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
        key=lambda b: (b.author.lower(), b.sortable_date())
    )
    with open(BOOKS_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(Book.csv_headers())
        for book in sorted_books:
            writer.writerow(book.to_csv_row())

def fetch_book_data_from_open_library(isbn: str) -> dict:
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {}

def fetch_book_data_from_google_books(isbn: str) -> dict:
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {}

def search_books_by_title_and_author(books: dict, title: str, author: str) -> list:
    return [book for book in books.values() if title.lower() in book.title.lower() and author.lower() in book.author.lower()]

def main():
    books = load_books()
    os.system('clear')

    while True:
        user_input = input("Enter ISBN-13 or Title (or 'q' to quit): ").strip()
        os.system('clear')

        if user_input.lower() == 'q':
            break
        
        # If the input is numeric (ISBN)
        if user_input.isdigit():
            isbn = user_input
            if len(isbn) != 13:
                print("Invalid ISBN-13. Try again.\n")
                continue

            if isbn in books:
                book = books[isbn]
                print("Book already in database:")
                print(book)
                continue

            data = fetch_book_data_from_open_library(isbn)
            if not data or f"ISBN:{isbn}" not in data:
                print(f"Book not found in Open Library. Trying Google Books...\n")
                data = fetch_book_data_from_google_books(isbn)

                if not data or "items" not in data:
                    print(f"Book not found in Google Books either. ISBN: {isbn}\n")
                    continue

                book = Book.from_google_books(isbn, data["items"][0])
                books[isbn] = book
                save_books(books)
                print("\nAdded from Google Books:")
                print(book)
            else:
                book = Book.from_api(isbn, data)
                books[isbn] = book
                save_books(books)
                print("\nAdded from Open Library:")
                print(book)
        
        # If the input is not numeric (Title search)
        else:
            title = user_input
            author = input("Enter author name: ").strip()

            matching_books = search_books_by_title_and_author(books, title, author)
            if not matching_books:
                print(f"No books found with title '{title}' and author '{author}'.\n")
                continue
            
            print(f"Found books with title '{title}' and author '{author}':")
            for idx, book in enumerate(matching_books, 1):
                print(f"{idx}. {book.title} by {book.author}")

            selection = input(f"Enter the number to select a book or 'q' to quit: ").strip()

            if selection.lower() == 'q':
                break
            elif selection.isdigit() and 1 <= int(selection) <= len(matching_books):
                selected_book = matching_books[int(selection) - 1]
                print(f"\nSelected Book:\n{selected_book}")
                continue
            else:
                print("Invalid selection. Try again.\n")
                continue

if __name__ == "__main__":
    main()
