Scraper to collect and resize kpop images for a captcha. Made for 4get

1. Downloads images accoding to groups specified in `PULL_GROUPS` in `groups.py`
2. Renames images to numberd `[x].png`
3. Uses insightface's `buffalo_1` face detection to crop a 100x100 area around faces in downloaded image

Configure `groups.py` accordingly before running
```
uv sync
uv scrape_data.py
```
