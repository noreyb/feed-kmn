import requests
import time
import yaml
from dotenv import load_dotenv
import os
from urllib.parse import urlparse
import pykakasi
import re


if __name__ == "__main__":
    with open("weneedfeed.yml", "r") as f:
        feeds = yaml.safe_load(f)
    print(feeds["pages"][0])

    # Unify domains
    for feed in feeds["pages"]:
        feed["url"] = feed["url"].replace("party", "su")

    # Raindrop
    # Load env
    load_dotenv()
    access_token = os.getenv("RAINDROPIO_ACCESS_TOKEN")
    url = "https://api.raindrop.io/rest/v1"
    endpoint = "/raindrops"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    query = {
        "perpage": 50,
    }

    unmarked = 36039260  # collection_id
    marked = 36039262  # collection_id

    resp = requests.get(
        f"{url}{endpoint}/{unmarked}",
        headers=headers,
        params=query,
    )
    time.sleep(1)

    if resp.status_code != requests.codes.ok:
        print(resp.text)
        exit(1)

    for item in resp.json()["items"]:
        if "kemono" not in item["domain"]:
            continue

        # name to id
        kakasi = pykakasi.kakasi()
        kakasi.setMode("H", "a")
        kakasi.setMode("K", "a")
        kakasi.setMode("J", "a")
        conv = kakasi.getConverter()

        username = item["title"].split(" ")[2]
        username = conv.do(username)
        pattern = r"[^a-zA-Z0-9]"
        username = re.sub(pattern, "_", username)

        parsed = urlparse(item["link"])
        service = parsed.path.split("/")[1]
        _id = parsed.path.split("/")[3]

        page = {
            'id': f"{username}",
            'item_image_selector': 'img',
            'item_link_selector': 'a',
            'item_selector': 'article',
            'item_time_selector': 'time',
            'item_title_selector': '.post-card__header',
            'title': f"{username}",
            'url': f"https://kemono.su/{service}/user/{_id}",
        }
        feeds["pages"].append(page)

    # sort pages
    pages = sorted(feeds["pages"], key=lambda x: x["id"])
    pages = list({page["id"]: page for page in pages}.values())
    feeds["pages"] = pages

    with open("weneedfeed.yml", "w") as f:
        yaml.dump(feeds, f, encoding="utf-8", allow_unicode=True)
