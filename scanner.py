import os
import csv
import sys
from classes import Book  # Ensure that Book is imported from classes.py
from openlibrary import fetch_open_library_data
from googlebooks import fetch_google_books_data

BOOKS_CSV = "books.csv"
SOUND_ON = True  # Optional, hardcoded

def load_books() -> dict:
    """Load books from the CSV file into a dictionary."""
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
                    tags=row.get("Tags", ""),
                    description=row.get("Description", ""),
                    thumbnail=row.get("Thumbnail", "")
                )
    except FileNotFoundError:
        pass

    save_books(books)
    return books


def save_books(books: dict):
    """Save the updated books to the CSV file."""
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
    """Extract the last name from the author's full name."""
    parts = author.split()
    return parts[-1] if parts else ""


def is_valid_isbn13(s):
    """Check if the ISBN is a valid 13-digit number."""
    return len(s) == 13 and s.isdigit()


def is_valid_isbn10(s):
    """Check if the ISBN is a valid 10-digit number."""
    return len(s) == 10 and s[:-1].isdigit() and (s[-1].isdigit() or s[-1] in 'Xx')


def search_books_by_title_and_author(books: dict, title: str, author: str) -> list:
    """Search books in the database by title and author."""
    return [book for book in books.values() if title.lower() in book.title.lower() and author.lower() in book.author.lower()]


def play_sound(sound_type: str):
    """Play a sound based on the action."""
    if SOUND_ON:
        if sound_type == "success":
            os.system("mpv sounds/success.ogg > /dev/null 2>&1")
        elif sound_type == "error":
            os.system("mpv sounds/error.wav > /dev/null 2>&1")


def add_book_by_isbn(books: dict, isbn: str):
    """Add a book to the collection using its ISBN."""
    isbn = isbn.replace("-", "")
    if isbn in books:
        print("Book already in database:")
        print(books[isbn])
        play_sound("success")
        return

    book = None

    # Try Google Books first
    google_data = fetch_google_books_data(f"isbn:{isbn}")
    if google_data:
        print("  -> Found on Google Books")
        book = Book.from_google_books(isbn, google_data)

        # Store the thumbnail from Google Books (if available)
        if 'thumbnail' in google_data:
            book.thumbnail = google_data['thumbnail']

        # Even if found, get better tags from Open Library
        openlib_data = fetch_open_library_data(isbn)
        if openlib_data and f"ISBN:{isbn}" in openlib_data:
            print("  -> Found in Open Library, updating tags...")
            ol_book = Book.from_open_library(isbn, openlib_data)  # Create Book from Open Library data
            # Replace the tags from Open Library (if available)
            if ol_book.tags:
                print(f"  -> Replacing tags with Open Library subjects: {ol_book.tags}")
                book.tags = ol_book.tags
    else:
        print("  -> Not found on Google. Trying Open Library...")
        openlib_data = fetch_open_library_data(isbn)
        if openlib_data and f"ISBN:{isbn}" in openlib_data:
            book = Book.from_open_library(isbn, openlib_data)
        else:
            print("  -> Book not found in either service.")
            play_sound("error")
            return

    books[book.isbn13 or isbn] = book
    save_books(books)
    print("\nBook added:")
    print(book)
    play_sound("success")


def process_isbns_from_file(file_path: str, books: dict):
    """Process each ISBN from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                isbn = line.strip()
                if is_valid_isbn13(isbn) or is_valid_isbn10(isbn):
                    add_book_by_isbn(books, isbn)
                else:
                    print(f"Invalid ISBN: {isbn}")
                    play_sound("error")
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        play_sound("error")


def main():
    """Main loop for handling user input and managing books."""
    books = load_books()
    os.system('clear')

    # Check if file argument is provided
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        process_isbns_from_file(input_file, books)
    else:
        # Run interactive mode
        while True:
            print()
            user_input = input("Enter ISBN-13 / ISBN-10 or Title (or 'q' to quit): ").strip()
            os.system('clear')
            print(user_input)
            print()

            if user_input.lower() == 'q':
                break

            user_input = user_input.replace('-', '')

            if is_valid_isbn13(user_input) or is_valid_isbn10(user_input):
                add_book_by_isbn(books, user_input)
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
