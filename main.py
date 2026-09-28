import os

from scraper import scrape_single_url
from formatter import clean_extracted_data
from exporter import export_to_structured_excel
import config


def run_universal_pipeline(urls):
    if not urls:
        print("No URLs provided.")
        return

    results = []

    print("=== UNIVERSAL WEB SCRAPER ===")
    print(f"Mode: {config.SCRAPE_MODE}")
    print(f"JavaScript Browser: {config.USE_BROWSER}")
    print(f"URLs: {len(urls)}\n")

    for index, url in enumerate(urls, 1):
        print(f"[{index}/{len(urls)}] {url}")

        result = scrape_single_url(url)
        result = clean_extracted_data(result)
        results.append(result)

        if isinstance(result, list):
            print(f"  Records: {len(result)}")
        else:
            print(f"  Status: {result.get('Status', 'Unknown')}")

    export_to_structured_excel(results)


def load_urls(path="urls.txt"):
    """urls.txt ho to usme se URLs lo (har line ek URL, # wali lines ignore)."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]


if __name__ == "__main__":
    target_urls = load_urls() or [
        "https://example.com",
        "https://httpbin.org/html",
    ]

    run_universal_pipeline(target_urls)
