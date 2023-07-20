import requests
import time
import yaml
from dotenv import load_dotenv
import os
from urllib.parse import urlparse
import pykakasi
import re


def get_from_raindrop(collection_id):
    url = "https://api.raindrop.io/rest/v1"
    endpoint = "/raindrops"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    query = {
        "perpage": 50,
    }

    resp = requests.get(
        f"{url}{endpoint}/{collection_id}",
        headers=headers,
        params=query,
    )

    if resp.status_code != requests.codes.ok:
        print(resp.text)
        exit()

    time.sleep(1)
    return resp


def move_marked_raindrop(collection_id, items, marked):
    url = "https://api.raindrop.io/rest/v1"
    endpoint = "/raindrops"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    query = {
        # "sort": "domain",
        # "page": 1,
        "perpage": 50,
        # "dengerAll": True,
    }
    body = {
        "ids": items,
        "collectionId": marked,
    }

    resp = requests.put(
        f"{url}{endpoint}/{unmark}",
        headers=headers,
        params=query,
        json=body,
    )

    if resp.status_code != requests.codes.ok:
        print(resp.text)
        exit(1)

    time.sleep(1)
    return resp


def unify_username(username):
    # name to id
    kakasi = pykakasi.kakasi()
    kakasi.setMode("H", "a")
    kakasi.setMode("K", "a")
    kakasi.setMode("J", "a")
    conv = kakasi.getConverter()

    username = conv.do(username)
    pattern = r"[^a-zA-Z0-9]"
    username = re.sub(pattern, "_", username)
    return username


if __name__ == "__main__":
    load_dotenv()

    with open("weneedfeed.yml", "r") as f:
        feeds = yaml.safe_load(f)

    # Unify domains
    for feed in feeds["pages"]:
        feed["url"] = feed["url"].replace("party", "su")

    # Get unmarked raindrops
    access_token = os.getenv("RAINDROPIO_ACCESS_TOKEN")
    unmark = int(os.getenv("UNMARK"))  # collection_id
    marked = int(os.getenv("MARKED"))

    resp = get_from_raindrop(unmark)
    if resp.json()["count"] == 0:
        print("There is no unmark raindrops")
        exit()

    # Get kemono.su raindrops
    raindrops = []
    for item in resp.json()["items"]:
        if "kemono" not in item["domain"]:
            continue

        parsed = urlparse(item["link"])
        service = parsed.path.split("/")[1]
        _id = parsed.path.split("/")[3]
        username = unify_username(item["title"].split(" ")[2])

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
        raindrops.append(item["_id"])

    r = move_marked_raindrop(unmark, raindrops, marked)

    # sort pages
    pages = sorted(feeds["pages"], key=lambda x: x["id"])
    pages = list({page["url"]: page for page in pages}.values())
    feeds["pages"] = pages
    print(len(feeds["pages"]))

    with open("weneedfeed.yml", "w") as f:
        yaml.dump(feeds, f, encoding="utf-8", allow_unicode=True)
