#!/usr/bin/env python3
"""Normalize `source` fields in `docs/good_news.json` using the
`canonical_source` function from `scripts.fetch_news`.
"""
import json
import os
import importlib.util
import pathlib

# Load fetch_news as a module by file path so we don't rely on package imports.
fetch_news_path = pathlib.Path(__file__).resolve().parent / 'fetch_news.py'
spec = importlib.util.spec_from_file_location('fetch_news', str(fetch_news_path))
fetch_news = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch_news)

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'docs', 'good_news.json')
DATA_FILE = os.path.normpath(DATA_FILE)


def main():
    if not os.path.exists(DATA_FILE):
        print(f"No {DATA_FILE} found; nothing to do.")
        return

    # Load via fetch_news helper to handle both legacy (list) and wrapped
    # formats that contain 'last run' and 'stories'.
    data = fetch_news.load_data(DATA_FILE)

    changed = 0
    for item in data:
        old = item.get('source')
        new = fetch_news.canonical_source(item.get('link', ''), old, item.get('link', ''))
        if new != old:
            print(f"Updating source for {item.get('link')}:\n  '{old}' -> '{new}'")
            item['source'] = new
            changed += 1

    if changed:
        # Use fetch_news.save_data so we preserve any existing 'last run'
        # metadata and remain compatible with the wrapped format.
        fetch_news.save_data(data, DATA_FILE)
        print(f"Wrote {changed} updated entries to {DATA_FILE}.")
    else:
        print("No changes needed.")


if __name__ == '__main__':
    main()
