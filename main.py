import argparse  # Parse arguments
import certifi  # Certificate issue fix*
import logging
import os
import ssl  # Certificate issue fix*
import time  # Delay execution
from bs4 import BeautifulSoup  # BeautifulSoup; parsing HTML
from urllib import request  # Get OLX page source
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse


REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    )
}

SEARCH_URL_PAUSE_DURATION = 30


def open_url(url):
    req = request.Request(url, headers=REQUEST_HEADERS)
    return request.urlopen(
        req, context=ssl.create_default_context(cafile=certifi.where())
    )


def normalize_ad_url(url):
    parsed_url = urlparse(url)
    return urlunparse(parsed_url._replace(query="", fragment=""))


def filter_extended(url_list):
    new_list = [url for url in url_list if "extended_search_extended" not in url]
    return new_list


def scrap_page(url):
    temp_list_of_items = []

    # Adding delay to not block itself
    pause_duration = 3  # seconds to wait
    logging.debug(f"Waiting for {pause_duration}s before opening URL...")
    time.sleep(pause_duration)
    logging.debug("Opening page...")
    page = open_url(url)
    logging.debug("Scraping page...")
    soup = BeautifulSoup(page, features="lxml")

    for link in soup.find_all("a", href=True):
        half_link = link.get("href")
        if "/d/oferta/" not in half_link:
            continue
        full_link = normalize_ad_url(urljoin("https://www.olx.pl", half_link))
        temp_list_of_items.append(full_link)
    temp_list_of_items = list(dict.fromkeys(temp_list_of_items))
    logging.info(f"Found {len(temp_list_of_items)} items on page.")
    return temp_list_of_items


def get_number_of_pages(url_):
    # *NOTE: number of search results pages
    page = open_url(url_)
    soup = BeautifulSoup(page, "html.parser")  # parse the page
    page_numbers = [1]

    for link in soup.find_all("a", href=True):
        href = link.get("href")
        query = parse_qs(urlparse(urljoin(url_, href)).query)
        page_number = query.get("page", [None])[0]
        if page_number and page_number.isdigit():
            page_numbers.append(int(page_number))

    return max(page_numbers)


def remove_dups(list_):
    temp_list = []
    for item in list_:
        temp_list.append(normalize_ad_url(item))
    return set(temp_list)


def build_page_url(url, page_number):
    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query, keep_blank_values=True)
    query["page"] = [str(page_number)]
    updated_query = urlencode(query, doseq=True)
    return urlunparse(parsed_url._replace(query=updated_query))


def get_list_of_ads(url):
    number_of_pages_to_scrap = get_number_of_pages(url)

    page_number = 1
    list_of_items = []

    while page_number <= number_of_pages_to_scrap:
        logging.info(f"Page number: {page_number}/{number_of_pages_to_scrap}")
        full_url = build_page_url(url, page_number)
        logging.debug(f"Scraping URL: {full_url}")
        list_of_items.extend(scrap_page(full_url))
        page_number += 1  # Go to the next page

    final_set = remove_dups(list_of_items)
    logging.info(f"Finaly found {len(final_set)} records.")
    return final_set


def get_ads_from_urls(urls):
    all_ads = []

    for index, url in enumerate(urls, start=1):
        formatted_url = format_url(url)
        logging.info(f"Processing URL {index}/{len(urls)}: {formatted_url}")
        all_ads.extend(get_list_of_ads(formatted_url))

        if index < len(urls):
            logging.info(
                "Waiting %ss before scraping the next URL...",
                SEARCH_URL_PAUSE_DURATION,
            )
            time.sleep(SEARCH_URL_PAUSE_DURATION)

    return remove_dups(all_ads)


def sanitize_urls(urls):
    return [url.strip() for url in urls if url and url.strip()]


def write_to_file(data):
    with open("previous_results.txt", "a") as file:
        new_data = "\n".join(data)
        if file.tell() > 0 and new_data:
            new_data = f"\n{new_data}"
        file.write(new_data)


def check_data(data):
    global first_run
    try:
        with open("previous_results.txt", "r") as file:
            known_items = {
                normalize_ad_url(line.strip()) for line in file if line.strip()
            }
    except FileNotFoundError:
        logging.info("It's first run, creating file...")
        cwd = os.getcwd()
        os.system(f"touch {cwd}/previous_results.txt")
        first_run = True
        known_items = set()

    if not known_items:
        first_run = True

    found_ads = []
    for item in data:
        normalized_item = normalize_ad_url(item)
        if normalized_item not in known_items:
            found_ads.append(normalized_item)

    filtered_ads = filter_extended(found_ads)

    logging.info(
        f"Found {len(filtered_ads)} new ad(s) compared to the previous search:\n"
    )
    return filtered_ads


def notify_telegram(data, config_path=None):
    import telegram_send  # Telegram message sending library

    logging.info("Sending notification(s) through Telegram!")
    if config_path:
        telegram_send.send(messages=data, conf=config_path)
    else:
        telegram_send.send(messages=data)

def notify_ntfy(data, topic):
    logging.info("Sending notification(s) through Ntfy.sh!")

    message = "\n".join(data)
    req = request.Request(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        headers=REQUEST_HEADERS,
    )
    request.urlopen(req)

def format_url(url):
    if url[-1] == "/":
        url = url[:-1]
    return url.replace("olx.pl/d/", "olx.pl/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config",
        help="Provide absolute path to the custom telegram_send config file.",
        type=str,
        required=False
    )
    parser.add_argument(
        "-d", "--debug",
        help="Set debug for a run.",
        action="store_true"
    )
    parser.add_argument(
        "-n", "--notify",
        help="Choose way of notifying about new ads.",
        type=str,
        required=True,
        # choices=["no-notify", "telegram", "ntfy"]
    )
    parser.add_argument(
        "-u", "--url",
        help="Provide one or more urls to check ads from.",
        nargs="+",
        required=False
    )
    args = parser.parse_args()
    log_lvl = logging.INFO
    if args.debug:
        log_lvl = logging.DEBUG
    first_run = False

    logging.basicConfig(
        level=log_lvl,
        format="%(levelname)s : %(asctime)s : %(message)s",
        handlers=[
            logging.FileHandler("logs.log"),
            logging.StreamHandler(),
        ],
    )

    # ========== URLs to scrape if nothing given in parameter ==========
    given_urls = [
        ""
    ]
    # ==================================================================

    if args.url:
        given_urls = sanitize_urls(args.url)
        logging.debug("Using URLs from parameter...")
    else:
        given_urls = sanitize_urls(given_urls)
        logging.debug("You didn't provide urls, taking URLs from code file...")
        if not given_urls:
            logging.error(
                "Didn't find URLs in code nor in parameter, provide at least one URL!"
            )
            raise SystemExit(
                "Didn't find URLs in code nor in parameter, provide at least one URL!"
            )

    ads_list = get_ads_from_urls(given_urls)
    new_ads = check_data(ads_list)
    if new_ads:
        write_to_file(new_ads)
        if first_run:
            logging.info("It's first run, not sending any notifications.")
        else:
            for ad in new_ads:
                logging.info(ad)
            if args.notify == "telegram":
                if args.config:
                    notify_telegram(new_ads, args.config)
                else:
                    notify_telegram(new_ads)
            elif args.notify.startswith("ntfy"):
                notify_ntfy(new_ads, args.notify[5:])
            else:
                logging.info(
                    "You've chosen --notify no-notify -not sending any notify."
                )
