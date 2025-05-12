# Book Scanner Lookup Script & CSV database

This Python script allows you to search for book metadata using either ISBN (ISBN-13 or ISBN-10) or a title-author pair. It retrieves information from Open Library and Google Books, then stores results in a CSV file.

## Barcode Scanner Keyboard Wedge

To streamline ISBN entry, you can use a barcode scanner keyboard wedge app on your phone. This allows barcode scans to be input directly into the script as if typed.

### Recommended App

**[QR Scanner Keyboard (by AppGround)](https://play.google.com/store/apps/details?id=io.appground.blek&hl=en-US)**  
A reliable Android app that emulates scanned barcodes as keyboard input.

- Supports ISBN-13 and ISBN-10 barcodes
- Works over Bluetooth, USB, or directly on-device
- Ideal for use with terminals, forms, and scripts expecting text input

> 📲 Install from the [Google Play Store](https://play.google.com/store/apps/details?id=io.appground.blek&hl=en-US)

**Note:** Ensure your terminal window or input box is focused when scanning.

## Features

- Accepts ISBN-13 or ISBN-10
- Falls back to title and author lookup (manual)
- Queries google books first (better date format and description and thumbnail), fallback to open library. If possible, takes tags from open library
- Records results in `books.csv` with:
  - ISBN-13
  - ISBN-10
  - Title
  - Subtitle
  - Author
  - Publish Date
  - URL
  - Scanned Input

## Requirements

- Python 3.7+
- `requests` library
- Optional: `mpv` installed for sound feedback

## Usage

Run the script:

```bash
python3 scanner.py
````

Enter:

* An ISBN-13 or ISBN-10
* Or a title, then an author when prompted

Quit with `q`.

## Output

Results are saved in `books.csv`, sorted by author (last name) and publish date (irregular unformatted data supported as datetime).

### Console Display

```bash
9781250400222

Book already in database:
Title: Swordheart
Author: T. Kingfisher
Published: 2025-02-25
URL: [http://books.google.com/books?id=BRkgEQAAQBAJ\&dq=isbn:9781250400222\&hl=\&source=gbs\_api](http://books.google.com/books?id=BRkgEQAAQBAJ&dq=isbn:9781250400222&hl=&source=gbs_api)

```

### books.csv Sample

```csv
ISBN-13,ISBN-10,Title,Subtitle,Author,Publish Date,URL,Scanned Input
9780593312070,,Frozen River,A Novel,Ariel Lawhon,2024,https://openlibrary.org/books/OL53367494M/Frozen_River,9780593312070
```

## License

MIT License

