import requests
import json
import sys

def fetch_google_books_data(query: str) -> dict:
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {}

def pretty_print_google_books(query: str):
    data = fetch_google_books_data(query)
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        pretty_print_google_books(query)
    else:
        query = input("Enter ISBN or title/author for Google Books: ").strip()
        pretty_print_google_books(query)
