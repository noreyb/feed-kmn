import os
import re
import time
from urllib.parse import urlparse

import pykakasi
import requests
import yaml
from dotenv import load_dotenv

from domain.raindrop import Raindrop
from domain.raindrop_id import RaindropId
from repository.raindropio import RaindropIO


def unify_username(username):
    # name to id
    kakasi = pykakasi.kakasi()
    username = kakasi.convert(username)

    result = ""
    for u in username:
        if result != "":
            result += "_"
        result += u["hepburn"]
    result = re.sub(r"[^a-zA-Z0-9_]", "", result)
    print(result)
    return result


def is_valid_url(url):
    pattern = r"^https://kemono\.su/(patreon|fantia|fanbox)/user/\d+$"
    return bool(re.match(pattern, url))


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
    handler = RaindropIO(token)
    raindrops = handler.bulk_get_all(collection)

    tags = ["kemono_marked"]
    target_raindrops = []
    for r in raindrops:
        if set(r.tags) <= set(tags):
            target_raindrops.append(r)
    if len(target_raindrops) == 0:
        raise Exception("No new item")

    # Get kemono.su raindrops
    marked_id = []
    for r in raindrops:
        raindrop_id = r._id
        print(raindrop_id)

        if not is_valid_url(r.link):
            continue

        parsed = urlparse(r.link)
        service = parsed.path.split("/")[1]
        _id = parsed.path.split("/")[3]
        username = unify_username(r.title.split(" ")[2])

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
        marked_id.append(
            Raindrop(
                link=r.link,
                _id=RaindropId(raindrop_id),
            )
        )

    tag = ["kemono_marked"]
    handler.bulk_update_tags(
        src_collection_id=collection,
        tags=tags,
        raindrops=marked_id,
    )

    # sort pages
    pages = sorted(feeds["pages"], key=lambda x: x["id"])
    pages = list({page["url"]: page for page in pages}.values())
    feeds["pages"] = pages
    print(len(feeds["pages"]))

    with open("weneedfeed.yml", "w") as f:
        yaml.dump(feeds, f, encoding="utf-8", allow_unicode=True)
