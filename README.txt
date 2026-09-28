UNIVERSAL WEB SCRAPER V5

Modes: GENERAL, PRODUCT, TABLE, CONTACTS, AUTO (config.py -> SCRAPE_MODE).
Uses requests/BeautifulSoup for normal HTML and optional Playwright/Chromium for JavaScript pages.
Protection challenges are detected and reported as BLOCKED; no CAPTCHA/Cloudflare bypass is attempted.

Install (once):
  install_playwright.bat
  (or: py -m pip install -r requirements.txt  then  py -m playwright install chromium)

URLs:
  Make a file urls.txt next to main.py — one URL per line (# lines ignored).
  If urls.txt is missing, the example URLs inside main.py are used.

Run:
  py main.py

Test:
  py test_v4.py
  py test_v5.py

Pagination: config.py -> ENABLE_PAGINATION=True and MAX_PAGES.
If the Excel file is open while saving, the output is saved with a new timestamped name.

License:
  All Rights Reserved - shared publicly for portfolio/demonstration purposes only.
  See LICENSE file. No reuse, copying, or redistribution without permission.
