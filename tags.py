import csv
import os
from openlibrary import fetch_open_library_data

CSV_FILE = "books.csv"

def get_subject_tags(data):
    subjects = data.get("subjects", [])
    return ", ".join(subject["name"] for subject in subjects) if subjects else ""

def main():
    if not os.path.exists(CSV_FILE):
        print(f"{CSV_FILE} not found.")
        return

    rows = []
    with open(CSV_FILE, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get("Title", "").strip()
            author = row.get("Author", "").strip()
            isbn13 = row.get("ISBN-13", "").strip()
            isbn10 = row.get("ISBN-10", "").strip()
            tags = row.get("Tags", "").strip()

            # Skip if already tagged or missing title
            if tags or not title or title == "Unknown Title":
                rows.append(row)
                continue

            print(f"[+] Processing '{title}' by {author}")
            print(f"    {isbn13} {isbn10}")
            book_data = None

            if isbn13:
                book_data = fetch_open_library_data(isbn13)
            if not book_data and isbn10:
                book_data = fetch_open_library_data(isbn10)

            if book_data:
                tag_string = get_subject_tags(book_data)
                if tag_string:
                    print(f"  -> Tags found: {tag_string}")
                    row["Tags"] = tag_string
                else:
                    print("  -> No tags found")
            else:
                print("  -> No data found")

            rows.append(row)

    with open(CSV_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    main()
