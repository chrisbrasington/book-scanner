from dataclasses import dataclass
from datetime import datetime
from genre import derive_genre

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
    tags: str = ""
    description: str = ""
    thumbnail: str = ""
    genre: str = ""

    @classmethod
    def from_open_library(cls, isbn: str, data: dict):
        key = f"ISBN:{isbn}"
        book_data = data.get(key, {})
        identifiers = book_data.get("identifiers", {})
        subjects = book_data.get("subjects", [])

        tag_list = [s["name"] for s in subjects]
        tags = ", ".join(tag_list) if tag_list else ""

        thumbnail_url = book_data.get("cover", {}).get("large", "")

        title = book_data.get("title", "")
        subtitle = book_data.get("subtitle", "")

        return cls(
            isbn13=identifiers.get("isbn_13", [""])[0],
            isbn10=identifiers.get("isbn_10", [""])[0],
            title=title,
            subtitle=subtitle,
            author=", ".join(a["name"] for a in book_data.get("authors", [])),
            publish_date=book_data.get("publish_date", ""),
            url=book_data.get("url", ""),
            scanned_input=isbn,
            tags=tags,
            description="",
            thumbnail=thumbnail_url,
            genre=derive_genre(tags=tags, title=title, subtitle=subtitle)
        )

    @classmethod
    def from_google_books(cls, isbn: str, data: dict):
        volume_info = data.get("volumeInfo", {})
        identifiers = volume_info.get("industryIdentifiers", [])
        categories = volume_info.get("categories", [])

        isbn13 = ""
        isbn10 = ""
        for ident in identifiers:
            if ident["type"] == "ISBN_13":
                isbn13 = ident["identifier"]
            elif ident["type"] == "ISBN_10":
                isbn10 = ident["identifier"]

        authors = volume_info.get("authors", [])
        author_str = ", ".join(authors) if authors else ""

        tags = ", ".join(categories) if categories else ""

        thumbnail_url = volume_info.get("imageLinks", {}).get("thumbnail", "")

        title = volume_info.get("title", "")
        subtitle = volume_info.get("subtitle", "")

        return cls(
            isbn13=isbn13,
            isbn10=isbn10,
            title=title,
            subtitle=subtitle,
            author=author_str,
            publish_date=volume_info.get("publishedDate", ""),
            url=volume_info.get("canonicalVolumeLink", volume_info.get("infoLink", "")),
            scanned_input=isbn,
            tags=tags,
            description=volume_info.get("description", ""),
            thumbnail=thumbnail_url,
            genre=derive_genre(tags=tags, categories=categories, title=title, subtitle=subtitle)
        )

    def to_csv_row(self):
        return [
            self.genre,
            self.isbn13, self.isbn10, self.title, self.subtitle, self.author,
            self.publish_date, self.url, self.scanned_input, self.tags,
            self.thumbnail,
            self.description
        ]

    @staticmethod
    def csv_headers():
        return [
            "Genre",
            "ISBN-13", "ISBN-10", "Title", "Subtitle", "Author",
            "Publish Date", "URL", "Scanned Input", "Tags", "Thumbnail", "Description"
        ]

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
            f"Genre: {self.genre}" if self.genre else None,
            f"Title: {self.title}",
            f"Subtitle: {self.subtitle}" if self.subtitle else None,
            f"Author: {self.author}",
            f"Published: {self.publish_date}",
            f"URL: {self.url}" if self.url else None,
            f"Tags: {self.tags}",
            f"Thumbnail: {self.thumbnail}" if self.thumbnail else None
        ]
        return "\n".join(filter(None, lines))
