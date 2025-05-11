from dataclasses import dataclass
from datetime import datetime

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
                return datetime.strptime(self.publish_date, "%Y-%m-%d")
            except ValueError:
                try:
                    return datetime(int(self.publish_date), 1, 1)
                except ValueError:
                    try:
                        year = int(self.publish_date[:4])
                        if year < 1900:
                            year = 1900
                        elif year < 2000:
                            year = 2000
                        return datetime(year, 1, 1)
                    except ValueError:
                        return datetime(1900, 1, 1)

    def __str__(self):
        lines = [
            f"Title: {self.title}",
            f"Subtitle: {self.subtitle}" if self.subtitle else None,
            f"Author: {self.author}",
            f"Published: {self.publish_date}",
            f"URL: {self.url}" if self.url else None
        ]
        return "\n".join(filter(None, lines))
