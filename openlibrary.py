import requests
import sys
import json

def fetch_open_library_data(isbn: str) -> dict:
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {}

def pretty_print_open_library(query: str):
    data = fetch_open_library_data(query)
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pretty_print_open_library(sys.argv[1])
    else:
        print("Usage: python openlibrary.py <ISBN>")
