import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import config


def clean_text(value):
    return re.sub(r"\s+", " ", value or "").strip()


def limit_text(value):
    if isinstance(value, str) and len(value) > config.MAX_TEXT_LENGTH:
        return value[:config.MAX_TEXT_LENGTH] + " ...[truncated]"
    return value


def unique_limited(values, limit):
    result = []
    seen = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
            if len(result) >= limit:
                break
    return result


def fetch_with_requests(url):
    response = requests.get(
        url,
        headers={"User-Agent": config.USER_AGENT},
        timeout=config.REQUEST_TIMEOUT,
        allow_redirects=True,
    )
    soup = BeautifulSoup(response.text, "html.parser")
    if _looks_blocked(soup.get_text(" ", strip=True), response.text):
        raise RuntimeError("BLOCKED: CAPTCHA/anti-bot/browser challenge detected. No bypass was attempted.")
    response.raise_for_status()
    return soup, response.url


def _looks_blocked(text, html):
    """
    Sirf ASLI challenge/block page pakadta hai. Pehle "captcha" lafz HTML
    mein kahin bhi mile to BLOCKED maan leta tha — is se har wo normal
    site jis par contact form ke sath reCAPTCHA ho, ghalat BLOCKED hoti thi.
    """
    t = (text or "").lower()
    h = (html or "")[:100000].lower()
    strong_html = ("cf-chl-", "challenge-platform", "cf-browser-verification", "_cf_chl_opt")
    if any(m in h for m in strong_html):
        return True
    # Challenge pages CHHOTE hote hain — lambi normal page par ye lafz
    # (jaise "access denied" kisi article mein) block nahi hote
    phrases = ("verify you are human", "checking your browser", "attention required",
               "access denied", "are you a robot", "just a moment")
    if len(t) < 3000 and any(p in t for p in phrases):
        return True
    if len(t) < 1500 and "captcha" in t:
        return True
    return False


def fetch_with_browser(url):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright is not installed. Run install_playwright.bat") from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=config.USER_AGENT,
            viewport={"width": 1440, "height": 1000},
        )
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=config.REQUEST_TIMEOUT * 1000)
            # Browser 404/500 par bhi page de deta hai — usko Success na samjho.
            # Error uthao taake requests wala rasta sahi HTTP_ERROR status de.
            if response is not None and response.status >= 400:
                raise RuntimeError(f"HTTP status {response.status}")
            if config.WAIT_AFTER_LOAD_MS:
                page.wait_for_timeout(config.WAIT_AFTER_LOAD_MS)

            for selector in config.CLICK_SELECTORS:
                try:
                    page.locator(selector).first.click(timeout=5000)
                except Exception:
                    pass

            for selector in config.WAIT_FOR_SELECTORS:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                except Exception:
                    pass

            if config.ENABLE_INFINITE_SCROLL:
                last_height = page.evaluate("document.body.scrollHeight")
                for _ in range(config.MAX_SCROLLS):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(config.SCROLL_WAIT_MS)
                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

            html = page.content()
            final_url = page.url
            visible_text = page.locator("body").inner_text(timeout=5000)
            if _looks_blocked(visible_text, html):
                raise RuntimeError("BLOCKED: CAPTCHA/anti-bot/browser challenge detected. No bypass was attempted.")
            return BeautifulSoup(html, "html.parser"), final_url
        finally:
            browser.close()


def fetch_page(url):
    if config.USE_BROWSER:
        try:
            return fetch_with_browser(url)
        except RuntimeError as browser_error:
            if str(browser_error).startswith("BLOCKED:"):
                raise
            return fetch_with_requests(url)
        except Exception:
            return fetch_with_requests(url)
    return fetch_with_requests(url)


def scrape_general_content(soup, url):
    title = clean_text(soup.title.get_text(" ", strip=True)) if soup.title else "N/A"
    h1 = soup.find("h1")
    heading = clean_text(h1.get_text(" ", strip=True)) if h1 else title
    paragraphs = []
    for p in soup.find_all("p"):
        text = clean_text(p.get_text(" ", strip=True))
        if text and len(text) > 20:
            paragraphs.append(text)
    return {"URL": url, "Page Title": title, "Heading": heading,
            "Content": limit_text("\n\n".join(paragraphs) or "No detailed text found")}


def scrape_product_details(soup, url):
    product_name = "N/A"
    for selector in config.CUSTOM_SELECTORS["product_name"].split(","):
        element = soup.select_one(selector.strip())
        if element:
            value = clean_text(element.get_text(" ", strip=True))
            if value:
                product_name = value
                break

    price = "N/A"
    for selector in config.CUSTOM_SELECTORS["price"].split(","):
        element = soup.select_one(selector.strip())
        if element:
            value = clean_text(element.get_text(" ", strip=True))
            if value:
                price = value
                break
    if price == "N/A":
        match = re.search(r"(?:PKR|Rs\.?|USD|\$|£|€)\s?[\d,]+(?:\.\d{1,2})?",
                          soup.get_text(" ", strip=True), re.IGNORECASE)
        if match:
            price = match.group(0)

    page_text = soup.get_text(" ", strip=True).lower()
    availability = "N/A"
    for selector in config.CUSTOM_SELECTORS["stock"].split(","):
        element = soup.select_one(selector.strip())
        if element:
            value = clean_text(element.get_text(" ", strip=True))
            if value:
                availability = value
                break
    if availability == "N/A":
        if "out of stock" in page_text:
            availability = "Out of Stock"
        elif "in stock" in page_text:
            availability = "In Stock"

    images = []
    for image in soup.find_all("img"):
        src = image.get("data-src") or image.get("src")
        if src and not src.strip().lower().startswith("data:"):  # base64 placeholder skip
            images.append(urljoin(url, src.strip()))

    return {
        "Source URL": url,
        "Product Name": product_name,
        "Price": price,
        "Availability": availability,
        "Image URLs": ", ".join(unique_limited(images, 10)) if images else "None",
    }


def scrape_tables(soup, url):
    records = []
    for table_index, table in enumerate(soup.find_all("table"), 1):
        rows = table.find_all("tr")
        if not rows:
            continue
        headers = [clean_text(c.get_text(" ", strip=True)) for c in rows[0].find_all(["th", "td"])]
        headers = [h if h else f"Column_{i+1}" for i, h in enumerate(headers)]
        # Same naam ke columns (jaise do "Price") ka data zaya na ho, aur
        # humare apne columns (Source URL, Table, Row...) overwrite na hon
        reserved = {"Source URL", "Table", "Row", "Page", "Status"}
        fixed, counts = [], {}
        for h in headers:
            if h in reserved:
                h = f"{h} (table)"
            counts[h] = counts.get(h, 0) + 1
            fixed.append(h if counts[h] == 1 else f"{h}_{counts[h]}")
        headers = fixed
        for row_index, row in enumerate(rows[1:], 1):
            cells = [clean_text(c.get_text(" ", strip=True)) for c in row.find_all(["th", "td"])]
            if not any(cells):
                continue
            cells += [""] * max(0, len(headers) - len(cells))
            record = {"Source URL": url, "Table": table_index, "Row": row_index}
            record.update(dict(zip(headers, cells[:len(headers)])))
            records.append(record)
    return records or [{"Source URL": url, "Table": "N/A", "Row": "N/A", "Message": "No HTML table found"}]


def _valid_phone(candidate):
    """
    Ghalat numbers (dates, order IDs) phone na samjhe jayen.
    Valid: 10-15 digits, date jaisa nahi, aur + ya 0 se shuru ho,
    ya beech mein space/dash wagera ho.
    """
    candidate = candidate.strip()
    digits = re.sub(r"\D", "", candidate)
    if not 10 <= len(digits) <= 15:
        return None
    if re.search(r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}", candidate):
        return None
    has_separator = bool(re.search(r"[\s().-]", candidate))
    if candidate.startswith("+") or digits.startswith("0") or has_separator:
        return candidate
    return None


def scrape_contacts_and_links(soup, url):
    text = soup.get_text(" ", strip=True)
    image_ext = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")
    emails = set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text))
    phones = set(_valid_phone(p) for p in re.findall(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)", text))
    # mailto: / tel: links bhi (aksar email sirf link mein hoti hai, text "Email us" hota hai)
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if href.lower().startswith("mailto:"):
            emails.add(href[7:].split("?")[0].strip())
        elif href.lower().startswith("tel:"):
            phones.add(_valid_phone(href[4:].strip()))
    emails = sorted(e for e in emails if e and not e.lower().endswith(image_ext))
    phones = sorted(p for p in phones if p)
    links, social = [], []
    social_domains = ("facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com", "youtube.com", "tiktok.com")
    for anchor in soup.find_all("a", href=True):
        href = urljoin(url, anchor["href"])
        if href.startswith(("http://", "https://")):
            links.append(href)
            if any(domain in href.lower() for domain in social_domains):
                social.append(href)
    return {
        "URL": url,
        "Page Title": clean_text(soup.title.get_text(" ", strip=True)) if soup.title else "N/A",
        "Emails Found": ", ".join(emails) if emails else "None",
        "Phone Numbers": ", ".join(phones[:20]) if phones else "None",
        "Links Found": ", ".join(unique_limited(links, 50)) if links else "None",
        "Social Links": ", ".join(unique_limited(social, 50)) if social else "None",
    }


def scrape_auto(soup, url):
    general = scrape_general_content(soup, url)
    product = scrape_product_details(soup, url)
    contacts = scrape_contacts_and_links(soup, url)
    general.update({
        "Product Name": product["Product Name"],
        "Price": product["Price"],
        "Availability": product["Availability"],
        "Image URLs": product["Image URLs"],
        "Emails Found": contacts["Emails Found"],
        "Phone Numbers": contacts["Phone Numbers"],
        "Social Links": contacts["Social Links"],
        "HTML Tables Found": len(soup.find_all("table")),
    })
    return general


def extract_by_mode(soup, url):
    mode = config.SCRAPE_MODE.upper().strip()
    if mode == "GENERAL":
        return [scrape_general_content(soup, url)]
    if mode == "PRODUCT":
        return [scrape_product_details(soup, url)]
    if mode == "TABLE":
        return scrape_tables(soup, url)
    if mode == "CONTACTS":
        return [scrape_contacts_and_links(soup, url)]
    if mode == "AUTO":
        return [scrape_auto(soup, url)]
    raise ValueError("Invalid SCRAPE_MODE. Use GENERAL, PRODUCT, TABLE, CONTACTS, or AUTO.")


def _next_page_url(soup, current_url):
    for selector in config.NEXT_BUTTON_SELECTORS:
        element = soup.select_one(selector)
        if not element:
            continue
        classes = " ".join(element.get("class", [])).lower()
        aria_disabled = str(element.get("aria-disabled", "")).lower()
        if element.has_attr("disabled") or "disabled" in classes or aria_disabled == "true":
            continue
        href = element.get("href")
        if href:
            return urljoin(current_url, href)
    return None


def scrape_single_url(url):
    try:
        all_records = []
        current_url = url
        seen_urls = set()
        max_pages = config.MAX_PAGES if config.ENABLE_PAGINATION else 1

        for page_number in range(1, max_pages + 1):
            if current_url in seen_urls:
                break
            seen_urls.add(current_url)

            soup, final_url = fetch_page(current_url)
            page_records = extract_by_mode(soup, final_url)
            for record in page_records:
                record["Page"] = page_number
                record["Status"] = "Success"
            all_records.extend(page_records)

            if not config.ENABLE_PAGINATION:
                break
            next_url = _next_page_url(soup, final_url)
            if not next_url or next_url in seen_urls:
                break
            current_url = next_url

        return all_records if len(all_records) != 1 or config.ENABLE_PAGINATION else all_records[0]

    except requests.HTTPError as exc:
        status = getattr(exc.response, "status_code", "unknown")
        return {"URL": url, "Status": "HTTP_ERROR", "Error": f"HTTP status {status}: {exc}"}
    except requests.RequestException as exc:
        return {"URL": url, "Status": "REQUEST_ERROR", "Error": str(exc)}
    except Exception as exc:
        message = str(exc)
        if message.startswith("BLOCKED:"):
            return {"URL": url, "Status": "BLOCKED", "Error": message}
        return {"URL": url, "Status": "FAILED", "Error": message}
