import os
import re
import time
from urllib.parse import urlparse

import pykakasi
import requests
import yaml
from dotenv import load_dotenv


def get_raindrops(collection_id, token):
    url = "https://api.raindrop.io/rest/v1"
    endpoint = "/raindrops"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    query = {
        "perpage": 50,
    }

    r = requests.get(
        f"{url}{endpoint}/{collection_id}",
        headers=headers,
        params=query,
    )

    if r.status_code != requests.codes.ok:
        print(r.text)
        exit()

    time.sleep(1)
    return r


def fetch_tagged_raindrops(items, tegs, has_tag=True):
    filtered_items = []
    for item in items:
        for tag in item["tags"]:
            if tag in tags:
                filtered_items.append(item)

    if has_tag:
        return filtered_items
    else:
        return [item for item in items if item["_id"] not in [fi["_id"] for fi in filtered_items]]


def tag_raindrop(items, collection, tag, token):
    url = "https://api.raindrop.io/rest/v1"
    endpoint = "/raindrops"

    tags = [tag]
    resp = requests.put(
        f"{url}{endpoint}/{collection}",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        params={"perpage": 50},
        json={
            "ids": items,
            "collectionId": collection,
            "tags": tags,
        },
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
    token = os.getenv("RD_TOKEN")
    collection = int(os.getenv("SUBSCRIBE"))

    with open("weneedfeed.yml", "r") as f:
        feeds = yaml.safe_load(f)

    # Unify domains
    for feed in feeds["pages"]:
        feed["url"] = feed["url"].replace("party", "su")

    # Get subscribe raindrops
    resp = get_raindrops(collection, token)
    items = resp.json()["items"]
    tags = ["kemono_marked"]
    items = fetch_tagged_raindrops(items, tags, has_tag=False)
    if len(items) == 0:
        exit("No new item")

    # Get kemono.su raindrops
    marked_id = []
    for item in items:
        if "kemono" not in item["domain"]:
            continue

        parsed = urlparse(item["link"])
        service = parsed.path.split("/")[1]
        _id = parsed.path.split("/")[3]
        username = unify_username(item["title"].split(" ")[2])

        page = {
            "id": f"{username}",
            "item_image_selector": "img",
            "item_link_selector": "a",
            "item_selector": "article",
            "item_time_selector": "time",
            "item_title_selector": ".post-card__header",
            "title": f"{username}",
            "url": f"https://kemono.su/{service}/user/{_id}",
        }
        feeds["pages"].append(page)
        marked_id.append(item["_id"])

    tag = "kemono_marked"
    r = tag_raindrop(marked_id, collection, tag, token)

    # sort pages
    pages = sorted(feeds["pages"], key=lambda x: x["id"])
    pages = list({page["url"]: page for page in pages}.values())
    feeds["pages"] = pages
    print(len(feeds["pages"]))

    with open("weneedfeed.yml", "w") as f:
        yaml.dump(feeds, f, encoding="utf-8", allow_unicode=True)
