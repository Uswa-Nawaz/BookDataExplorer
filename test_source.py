"""Temporary test for Step 1C part 1. Run:  python test_source.py"""
from scraper.open_library_source import OpenLibrarySource

pages = OpenLibrarySource().iter_pages()

for number in range(1, 4):                 # download just 3 pages
    books = next(pages)
    print(f"Page {number}: {len(books)} complete books out of 100 downloaded")

print("\nSample books from the last page:")
for book in books[:5]:
    print(book)