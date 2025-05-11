import csv
import os
from openlibrary import fetch_open_library_data
from classes import Book  # Import the Book class

CSV_FILE = "books.csv"

def update_book_tags(book: Book):
    print(f"[+] Processing '{book.title}' by {book.author}")
    
    # Step 1: If tags already exist, skip this book
    if book.tags:  
        print(f"  -> Tags already present: {book.tags}")
        return book  # Skip updating if tags are present
    
    # Step 2: Fetch book data from Open Library (try ISBN-13 first, then ISBN-10)
    book_data = fetch_open_library_data(book.isbn13) or fetch_open_library_data(book.isbn10)
    
    if book_data:
        print(f"  -> Found data for ISBN: {book.isbn13 or book.isbn10}")
        # print(f"  -> Raw Open Library response: {book_data}")  # Debug print to inspect the raw data
        
        # Step 3: If subjects are found in the Open Library response, update them
        book_info = book_data.get(f"ISBN:{book.isbn13}", {})  # Adjust to the correct key
        new_tags = book_info.get("subjects", [])
        
        if new_tags:
            # Extract 'name' from each subject in the list
            tag_string = ", ".join(tag["name"] for tag in new_tags if "name" in tag)
            if tag_string:
                print(f"  -> Tags found: {tag_string}")
                book.tags = tag_string  # Update the tags in the book object
            else:
                print("  -> Subjects exist, but no valid 'name' fields found")
        else:
            print("  -> No subjects found in Open Library data")
    else:
        print("  -> No data found from Open Library")

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
                tags=row["Tags"]
            )
            books.append(book)

    # Step 4: Update tags for each book that doesn't already have them
    updated_books = []
    for book in books:
        updated_books.append(update_book_tags(book))

    # Step 5: Write updated data back to CSV
    with open(CSV_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(Book.csv_headers())  # Write headers
        for book in updated_books:
            writer.writerow(book.to_csv_row())

if __name__ == "__main__":
    main()
