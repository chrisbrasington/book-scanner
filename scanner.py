import os
import csv
import requests
from dataclasses import dataclass
from datetime import datetime

BOOKS_CSV = "books.csv"
SOUND_ON = True  # Optional, hardcoded

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

def isbn13_to_isbn10(isbn13: str) -> str:
    if not isbn13.startswith("978") or len(isbn13) != 13:
        return ""
    core = isbn13[3:-1]
    total = 0
    for i, digit in enumerate(core):
        total += int(digit) * (10 - i)
    check = 11 - (total % 11)
    if check == 10:
        check_char = 'X'
    elif check == 11:
        check_char = '0'
    else:
        check_char = str(check)
    return core + check_char

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

def play_sound(sound_type: str):
    if SOUND_ON:
        if sound_type == "success":
            os.system("mpv sounds/success.ogg > /dev/null 2>&1")
        elif sound_type == "error":
            os.system("mpv sounds/error.wav > /dev/null 2>&1")

def main():
    books = load_books()
    os.system('clear')

    while True:
        user_input = input("Enter ISBN-13 or Title (or 'q' to quit): ").strip()
        os.system('clear')
        print(user_input)

        if user_input.lower() == 'q':
            break

        # ISBN numeric input
        if user_input.isdigit():
            isbn = user_input
            if len(isbn) != 13:
                print("Invalid ISBN-13. Try again.\n")
                play_sound("error")
                continue

            if isbn in books:
                print("Book already in database:")
                print(books[isbn])
                play_sound("success")
                continue

            isbn10 = isbn13_to_isbn10(isbn)

            # Open Library - ISBN-13
            data = fetch_book_data_from_open_library(isbn)
            if data and f"ISBN:{isbn}" in data:
                book = Book.from_api(isbn, data)
                books[isbn] = book
                save_books(books)
                print("\nAdded from Open Library (ISBN-13):")
                print(book)
                play_sound("success")
                continue

            # Open Library - ISBN-10 fallback
            if isbn10:
                data = fetch_book_data_from_open_library(isbn10)
                if data and f"ISBN:{isbn10}" in data:
                    book = Book.from_api(isbn, data)
                    books[isbn] = book
                    save_books(books)
                    print("\nAdded from Open Library (ISBN-10 fallback):")
                    print(book)
                    play_sound("success")
                    continue

            # Google Books - ISBN-13
            data = fetch_book_data_from_google_books(isbn)
            if data and "items" in data:
                book = Book.from_google_books(isbn, data["items"][0])
                books[isbn] = book
                save_books(books)
                print("\nAdded from Google Books (ISBN-13):")
                print(book)
                play_sound("success")
                continue

            # Google Books - ISBN-10 fallback
            if isbn10:
                data = fetch_book_data_from_google_books(isbn10)
                if data and "items" in data:
                    book = Book.from_google_books(isbn, data["items"][0])
                    books[isbn] = book
                    save_books(books)
                    print("\nAdded from Google Books (ISBN-10 fallback):")
                    print(book)
                    play_sound("success")
                    continue

            print(f"Book not found using ISBN-13 or ISBN-10 in either source. ISBN: {isbn}\n")
            play_sound("error")

        # Title search if alphabetic characters present
        elif any(c.isalpha() for c in user_input):
            title = user_input
            author = input("Enter author name: ").strip()

            matching_books = search_books_by_title_and_author(books, title, author)
            if not matching_books:
                print(f"No books found with title '{title}' and author '{author}'.\n")
                play_sound("error")
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
                play_sound("success")
                continue
            else:
                print("Invalid selection. Try again.\n")
                play_sound("error")
                continue

if __name__ == "__main__":
    main()
