import requests
import json
import sys

def fetch_google_books_data(query: str) -> dict:
    # Read the API key from the googleapi.key file
    try:
        with open('googleapi.key', 'r') as f:
            api_key = f.read().strip()
    except FileNotFoundError:
        print("Error: The 'googleapi.key' file was not found.")
        return {}

    # Construct the URL with the query and API key
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&key={api_key}&maxResults=1"
    
    print('Searching google books')
    print(url)

    # Make the API request
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        return data.get('items', [{}])[0]  # Return the first item if exists
    else:
        print(f"Error: Unable to fetch data (Status code: {response.status_code})")
        return {}

def pretty_print_google_books(query: str):
    data = fetch_google_books_data(query)
    if data:
        # Pretty print the data if available
        print(json.dumps(data, indent=2))
    else:
        print("No data found.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        query = f"isbn:{query}"
        pretty_print_google_books(query)
    else:
        query = input("Enter ISBN or title/author for Google Books: ").strip()
        pretty_print_google_books(query)
