"""One-shot migration: add Genre column (first) to books.csv.

Pass 1: auto-derive genre from existing tags via genre.derive_genre.
Pass 2: interactively prompt for unmatched rows. 'q' aborts remaining prompts.
"""

import csv
import os
import shutil

from classes import Book
from genre import derive_genre, prompt_for_genre

CSV_FILE = "books.csv"
BACKUP_FILE = "books.csv.bak"


def load_rows() -> list:
    books = []
    with open(CSV_FILE, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            book = Book(
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
                thumbnail=row.get("Thumbnail", ""),
                genre=row.get("Genre", "")
            )
            books.append(book)
    return books


def write_rows(books: list):
    with open(CSV_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(Book.csv_headers())
        for book in books:
            writer.writerow(book.to_csv_row())


def main():
    if not os.path.exists(CSV_FILE):
        print(f"{CSV_FILE} not found.")
        return

    shutil.copy(CSV_FILE, BACKUP_FILE)
    print(f"Backup written: {BACKUP_FILE}")

    books = load_rows()
    print(f"Loaded {len(books)} rows.")

    # Pass 1: auto-derive
    matched = 0
    for book in books:
        if not book.genre:
            g = derive_genre(tags=book.tags, title=book.title, subtitle=book.subtitle)
            if g:
                book.genre = g
                matched += 1
    print(f"Pass 1: auto-matched {matched} rows.")

    # Write intermediate so partial progress survives a crash
    write_rows(books)

    # Pass 2: prompt for blanks
    blanks = [b for b in books if not b.genre]
    print(f"Pass 2: {len(blanks)} rows still blank.")

    if not blanks:
        print("Done. No prompting needed.")
        return

    print("Starting interactive prompts. 'q' to quit early.")
    quit_early = False
    prompted = 0
    for book in blanks:
        result = prompt_for_genre(book)
        if result == "__QUIT__":
            quit_early = True
            break
        if result:
            book.genre = result
            prompted += 1
        # Save after each input so quit/Ctrl-C keeps progress
        write_rows(books)

    write_rows(books)

    print()
    print(f"Filled {prompted} via prompt.")
    if quit_early:
        remaining = sum(1 for b in books if not b.genre)
        print(f"Quit early. {remaining} rows still blank — rerun cleanup.py to resume.")
    else:
        print("All rows processed.")


if __name__ == "__main__":
    main()
