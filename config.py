# ======================================================
# UNIVERSAL WEB SCRAPER - FINAL CONFIGURATION
# ======================================================

OUTPUT_FILENAME = "Universal_Scraped_Data_V4.xlsx"

# GENERAL  -> page title, headings, paragraphs
# PRODUCT  -> product name, price, stock, images
# TABLE    -> HTML tables
# CONTACTS -> emails, phones, links, social links
# AUTO     -> combined extraction
SCRAPE_MODE = "AUTO"

# True = use Chromium/Playwright for JavaScript-rendered pages.
# False = use requests + BeautifulSoup only.
USE_BROWSER = True

REQUEST_TIMEOUT = 20
WAIT_AFTER_LOAD_MS = 1500
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Infinite-scroll settings
ENABLE_INFINITE_SCROLL = False
MAX_SCROLLS = 30
SCROLL_WAIT_MS = 1500

# Pagination settings
ENABLE_PAGINATION = False
MAX_PAGES = 20
NEXT_BUTTON_SELECTORS = [
    "a[rel='next']",
    "a.next",
    "button.next",
    "[aria-label='Next']",
    "[aria-label='Next page']",
]

# Optional interaction before extraction.
# Keep empty unless a client/site specifically requires it.
CLICK_SELECTORS = []
WAIT_FOR_SELECTORS = []

# Excel ek cell mein max 32767 characters leta hai — isliye 32000
MAX_TEXT_LENGTH = 32000

CUSTOM_SELECTORS = {
    "product_name": "h1, .product-title, .product_title, [itemprop='name']",
    "price": ".price, .amount, [itemprop='price'], [class*='price']",
    "stock": ".stock, .availability, [itemprop='availability'], [class*='stock']",
}
