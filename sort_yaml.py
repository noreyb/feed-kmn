import yaml

if __name__ == "__main__":
    with open("weneedfeed.yml") as f:
        obj = yaml.safe_load(f)
    pages = obj["pages"]
    pages = sorted(pages, key=lambda x: x["id"])
    pages = list({page["id"]: page for page in pages}.values())
    obj["pages"] = pages

    with open("weneedfeed.yml", "w") as f:
        yaml.dump(obj, f, encoding="utf-8", allow_unicode=True)
