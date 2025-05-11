import os
import csv
from classes import Book
from openlibrary import fetch_open_library_data
from googlebooks import fetch_google_books_data

BOOKS_CSV = "books.csv"
SOUND_ON = True  # Optional, hardcoded

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
                    scanned_input=row.get("Scanned Input", ""),
                    tags=row.get("Tags", "")
                )
    except FileNotFoundError:
        pass

    save_books(books)
    return books


def save_books(books: dict):
    sorted_books = sorted(
        books.values(),
        key=lambda b: (get_last_name(b.author).lower(), b.sortable_date())
    )
    with open(BOOKS_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(Book.csv_headers())
        for book in sorted_books:
            writer.writerow(book.to_csv_row())


def get_last_name(author: str) -> str:
    parts = author.split()
    return parts[-1] if parts else ""


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

        user_input = user_input.replace('-', '')

        if is_valid_isbn13(user_input) or is_valid_isbn10(user_input):
            isbn = user_input
            if isbn in books:
                print("Book already in database:")
                print(books[isbn])
                play_sound("success")
                continue

            data = fetch_open_library_data(isbn)
            if data and f"ISBN:{isbn}" in data:
                book = Book.from_open_library(isbn, data)
            else:
                print("Not found on Open Library. Trying Google Books...")
                data = fetch_google_books_data(f"isbn:{isbn}")
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
