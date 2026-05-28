from pathlib import Path
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import requests

from groups import PULL_GROUPS, EXCLUSIONS

KPOPPING_BASE = "https://kpopping.com"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".tif", ".avif"}
OUTPUT_DIR = Path("../captcha-original")

def fetch_female_idols() -> dict:
    has_more = True
    idx = 1
    result = {}
    while has_more:
        response = requests.get(f"{KPOPPING_BASE}/api/index-entries?type=idols&range={idx}&gender=female")
        api_response = dict(response.json())
        member_data = api_response["data"]
        for curr_letter_list in member_data:
            for member in curr_letter_list["entries"]:
                if "group" not in member:
                    continue
                group = member["group"]
                if group not in result:
                    result[group] = [member]
                else:
                    result[group].append(member)
        has_more = bool(api_response["hasMore"])
        idx += 1
    return result

def extract_idol_id(idol_name_id: str):
    response = requests.get(f"{KPOPPING_BASE}/profiles/idol/{idol_name_id}")
    soup = BeautifulSoup(response.text, 'html.parser')
    a_tags = soup.find_all("a")
    for tag in a_tags:
        href = tag.get("href")
        idol_id_regex =re.search("^\/kpics\?idol=([^&]+)&idolName=.+$", href)
        if idol_id_regex is None:
            continue
        return idol_id_regex.group(1)
    return None

def download_images(group_data):
    for group in PULL_GROUPS:
        dest = OUTPUT_DIR / group
        dest.mkdir(parents=True,exist_ok=True)
        if group not in PULL_GROUPS:
            print(f"{group} not in {PULL_GROUPS}")
            continue
        exclude_list = []
        if group in EXCLUSIONS:
            exclude_list = EXCLUSIONS[group]
        for member in group_data[group]:
            if member["id"] in exclude_list:
                continue
            print(f"Downloading images for {member["name"]}")
            member_id = member["id"]
            idol_id = extract_idol_id(member_id)
            photo_api_url = f"{KPOPPING_BASE}/api/idol-sections?idolId={idol_id}&section=photos"
            response = requests.get(photo_api_url)
            if not response:
                print(f"Failed to get photos for {member}")
            photo_data = dict(response.json())
            progress = 1
            photos_found = len(photo_data["photos"])
            for photo in photo_data["photos"]:
                print(f"Now downloading {photo["slug"]} ({progress}/{photos_found})")
                url = photo["src"]
                filename = Path(urlparse(url).path).name
                out_path = dest / filename
                resp = requests.get(url, stream=True, timeout=15)
                resp.raise_for_status()
                with open(out_path, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                progress += 1


def renumber_images_recursive(root_folder: str | Path) -> None:
    root = Path(root_folder)
    for current_dir, _, _ in os.walk(root):
        directory = Path(current_dir)
        images = sorted(
            [p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS],
            key=lambda p: p.name.lower(),
        )
        if not images:
            continue

        temp_files = []
        for i, image in enumerate(images):
            temp = directory / f"__tmp_{i+1}{image.suffix.lower()}"
            image.rename(temp)
            temp_files.append(temp)

        for i, temp in enumerate(temp_files):
            temp.rename(directory / f"{i+1}{temp.suffix.lower()}")

        print(f"Renumbered {len(images)} images in {directory}")

def main():
    group_data = fetch_female_idols()
    download_images(group_data)
    renumber_images_recursive("../captcha-original")

if __name__ == "__main__":
    main()
