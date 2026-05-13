import json
import os
import readline

GENRES_FILE = "genres.json"


def _input_with_prefill(prompt: str, prefill: str) -> str:
    """input() with editable pre-filled text (Linux/macOS terminals)."""
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()


def load_genre_map() -> dict:
    if not os.path.exists(GENRES_FILE):
        return {}
    with open(GENRES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_genre_map(genre_map: dict):
    with open(GENRES_FILE, "w", encoding="utf-8") as f:
        json.dump(genre_map, f, indent=2, ensure_ascii=False)
        f.write("\n")


def derive_genre(tags: str = "", categories=None, title: str = "", subtitle: str = "") -> str:
    """Match tags/categories/title against genres.json keyword map.

    Returns bucket name on first hit (priority = order in genres.json), else "".
    """
    genre_map = load_genre_map()
    if not genre_map:
        return ""

    cats_str = ""
    if categories:
        if isinstance(categories, list):
            cats_str = " ".join(categories)
        else:
            cats_str = str(categories)

    haystack = " ".join([tags or "", cats_str, title or "", subtitle or ""]).lower()
    if not haystack.strip():
        return ""

    for bucket, keywords in genre_map.items():
        for kw in keywords:
            if kw.lower() in haystack:
                return bucket
    return ""


def prompt_for_genre(book) -> str:
    """Interactive prompt. Returns chosen genre. Adds new bucket to genres.json if user types one.

    Special return values:
    - "" (empty) = user skipped
    - "__QUIT__" = user wants to abort batch loop
    """
    genre_map = load_genre_map()
    buckets = list(genre_map.keys())

    print()
    print("=" * 60)
    print(f"Title:  {book.title}")
    if book.subtitle:
        print(f"Sub:    {book.subtitle}")
    print(f"Author: {book.author}")
    print(f"Tags:   {book.tags}")
    print("=" * 60)
    print("Pick genre:")
    for i, b in enumerate(buckets, 1):
        print(f"  {i}. {b}")
    print("  s. skip (leave blank)")
    print("  q. quit (stop prompting)")
    print("  or type new genre name")

    choice = input("> ").strip()

    if choice.lower() == "q":
        return "__QUIT__"
    if choice.lower() == "s" or choice == "":
        return ""
    if choice.isdigit() and 1 <= int(choice) <= len(buckets):
        picked = buckets[int(choice) - 1]
        _maybe_learn_keyword(genre_map, picked, book)
        return picked

    new_bucket = choice.lower()
    if new_bucket not in genre_map:
        genre_map[new_bucket] = []
        save_genre_map(genre_map)
        print(f"  -> Added new genre '{new_bucket}' to {GENRES_FILE}")
    _maybe_learn_keyword(genre_map, new_bucket, book)
    return new_bucket


GENERIC_TAGS = {"fiction"}


def _maybe_learn_keyword(genre_map: dict, bucket: str, book):
    """Prompt to add one keyword (first non-generic tag pre-filled, editable) to bucket."""
    if not book.tags:
        return
    first_tag = ""
    for raw in book.tags.split(","):
        candidate = raw.strip().lower()
        if candidate and candidate not in GENERIC_TAGS:
            first_tag = candidate
            break
    if not first_tag:
        return

    print(f"Add keyword to '{bucket}'? (Enter to accept, edit text, or blank to skip)")
    kw = _input_with_prefill("> ", first_tag).strip().lower()
    if not kw:
        print("  -> Skipped.")
        return

    existing = {k.lower() for k in genre_map.get(bucket, [])}
    if kw in existing:
        print(f"  -> '{kw}' already in '{bucket}'")
        return
    genre_map.setdefault(bucket, []).append(kw)
    save_genre_map(genre_map)
    print(f"  -> Added '{kw}' to '{bucket}'")
