import requests

url = "https://openlibrary.org/search.json"
params = {
    "q": "subject:fiction",
    "limit": 5,
    "page": 1,
    "fields": "key,title,author_name,first_publish_year,number_of_pages_median,"
              "publisher,language,subject,edition_count,ratings_count,want_to_read_count",
}
headers = {"User-Agent": "DSA-Project-Uswa (student project)"}

r = requests.get(url, params=params, headers=headers, timeout=30)
print(r.status_code)
data = r.json()
print("Total found:", data.get("numFound"))
for doc in data["docs"]:
    print(doc)