import requests
import json

URL = "https://graphql.anilist.co"

query = """
query ($search: String) {
  Media (search: $search, type: ANIME) {
    id
    title {
      romaji
      english
    }
    episodes
    startDate { year }
    studios {
      nodes { name }
    }
    averageScore
    popularity
  }
}
"""

variables = {"search": "Kimetsu no Yaiba"}

response = requests.post(URL, json={"query": query, "variables": variables})

print("Status code:", response.status_code)

data = response.json()
print(json.dumps(data, indent=2))