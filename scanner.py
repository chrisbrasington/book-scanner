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
    isbn10: str
    title: str
    subtitle: str = ""
    author: str = ""
    publish_date: str = ""
    url: str = ""
    scanned_input: str = ""

    @classmethod
    def from_open_library(cls, isbn: str, data: dict):
        key = f"ISBN:{isbn}"
        book_data = data.get(key, {})
        identifiers = book_data.get("identifiers", {})
        return cls(
            isbn13=identifiers.get("isbn_13", [""])[0],
            isbn10=identifiers.get("isbn_10", [""])[0],
            title=book_data.get("title", ""),
            subtitle=book_data.get("subtitle", ""),
            author=", ".join(a["name"] for a in book_data.get("authors", [])),
            publish_date=book_data.get("publish_date", ""),
            url=book_data.get("url", ""),
            scanned_input=isbn
        )

    @classmethod
    def from_google_books(cls, isbn: str, data: dict):
        volume_info = data.get("volumeInfo", {})
        identifiers = volume_info.get("industryIdentifiers", [])
        isbn13 = next((id['identifier'] for id in identifiers if id['type'] == 'ISBN_13'), "")
        isbn10 = next((id['identifier'] for id in identifiers if id['type'] == 'ISBN_10'), "")
        return cls(
            isbn13=isbn13,
            isbn10=isbn10,
            title=volume_info.get("title", ""),
            subtitle=volume_info.get("subtitle", ""),
            author=", ".join(volume_info.get("authors", [])),
            publish_date=volume_info.get("publishedDate", ""),
            url=volume_info.get("infoLink", ""),
            scanned_input=isbn
        )

    def to_csv_row(self):
        return [self.isbn13, self.isbn10, self.title, self.subtitle, self.author, self.publish_date, self.url, self.scanned_input]

    @staticmethod
    def csv_headers():
        return ["ISBN-13", "ISBN-10", "Title", "Subtitle", "Author", "Publish Date", "URL", "Scanned Input"]

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
                    isbn13=row.get("ISBN-13", ""),
                    isbn10=row.get("ISBN-10", ""),
                    title=row.get("Title", ""),
                    subtitle=row.get("Subtitle", ""),
                    author=row.get("Author", ""),
                    publish_date=row.get("Publish Date", ""),
                    url=row.get("URL", ""),
                    scanned_input=row.get("Scanned Input", "")
                )
    except FileNotFoundError:
        pass

    # After loading books, resave them to ensure they're sorted
    save_books(books)
    
    return books

def save_books(books: dict):
    sorted_books = sorted(
        books.values(),
        key=lambda b: (get_last_name(b.author).lower(), b.sortable_date())  # Sort by last name, then by publish date
    )
    with open(BOOKS_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(Book.csv_headers())
        for book in sorted_books:
            writer.writerow(book.to_csv_row())

def get_last_name(author: str) -> str:
    """
    Helper function to extract the last name from the author's full name.
    Assumes the last word in the author's name is the last name.
    """
    parts = author.split()
    return parts[-1] if parts else ""

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
        items = response.json().get("items", [])
        if items:
            return items[0]  # Return first match
    return {}

def is_valid_isbn13(s):
    return len(s) == 13 and s.isdigit()

def is_valid_isbn10(s):
    return len(s) == 10 and s[:-1].isdigit() and (s[-1].isdigit() or s[-1] in 'Xx')

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
        user_input = input("Enter ISBN-13 / ISBN-10 or Title (or 'q' to quit): ").strip()
        os.system('clear')
        print(user_input)
        print()

        if user_input.lower() == 'q':
            break

        user_input = user_input.replace('-','')

        if is_valid_isbn13(user_input) or is_valid_isbn10(user_input):
            isbn = user_input
            if isbn in books:
                print("Book already in database:")
                print(books[isbn])
                play_sound("success")
                continue

            data = fetch_book_data_from_open_library(isbn)
            if data and f"ISBN:{isbn}" in data:
                book = Book.from_open_library(isbn, data)
            else:
                print("Not found on Open Library. Trying Google Books...")
                data = fetch_book_data_from_google_books(isbn)
                if not data:
                    print("Book not found.")
                    play_sound("error")
                    continue
                book = Book.from_google_books(isbn, data)

            books[book.isbn13 or isbn] = book
            save_books(books)
            print("\nBook added:")
            print(book)
            play_sound("success")

        elif any(c.isalpha() for c in user_input):
            title = user_input
            author = input("Enter author name: ").strip()
            matches = search_books_by_title_and_author(books, title, author)
            if not matches:
                print("No matches found.")
                play_sound("error")
                continue

            print("Found matches:")
            for i, b in enumerate(matches, 1):
                print(f"{i}. {b.title} by {b.author}")
            choice = input("Choose number or 'q' to cancel: ").strip()
            if choice.lower() == 'q':
                continue
            if choice.isdigit() and 1 <= int(choice) <= len(matches):
                selected = matches[int(choice) - 1]
                print("\nSelected Book:")
                print(selected)
                play_sound("success")
            else:
                print("Invalid selection.")
                play_sound("error")

        else:
            print("Invalid input.")
            play_sound("error")

if __name__ == "__main__":
    main()
