import argparse  # Parse arguments
import certifi  # Certificate issue fix*
import logging
import os
import re  # Regex; extract substrings
import ssl  # Certificate issue fix*
import time  # Delay execution
from bs4 import BeautifulSoup  # BeautifulSoup; parsing HTML
from urllib.request import urlopen  # Open URLs
from urllib import request  # Get OLX page source


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
    page = request.urlopen(
        url, context=ssl.create_default_context(cafile=certifi.where())
    )
    logging.debug("Scraping page...")
    soup = BeautifulSoup(page, features="lxml")

    target_class = "css-qo0cxu"

    for link in soup.find_all("a", {"class": target_class}):
        half_link = link.get("href")
        if "https://" not in half_link:
            full_link = f"https://www.olx.pl{half_link}"
        else:
            full_link = half_link
        temp_list_of_items.append(full_link)
    logging.info(f"Found {len(temp_list_of_items)} items on page.")
    return temp_list_of_items


def get_number_of_pages(url_):
    # *NOTE: number of search results pages
    page = urlopen(
        url_, context=ssl.create_default_context(cafile=certifi.where())
    )
    soup = BeautifulSoup(page, "html.parser")  # parse the page
    target_class = "css-1mi714g"
    pages = soup.find_all("a", {"class": target_class})
    try:
        num_of_pages = str(re.findall(">..<", str(pages))[-1])[1:-1]
        if not num_of_pages.isdigit():
            num_of_pages = str(re.findall(">.<", str(pages))[-1])[1:-1]
        # num_of_pages = len(soup.find_all("a", {"class": target_class}))
        # logging.debug(soup.find_all("a", {"class": target_class}))
        return int(num_of_pages)
    except IndexError:
        # in this case we have just one page, returning int: 1
        return 1


def remove_dups(list_):
    temp_list = []
    for item in list_:
        # temp_item = temp_item.split("?")[0]
        temp_list.append(item.split("#")[0])
    return set(temp_list)


def get_list_of_ads(url):
    number_of_pages_to_scrap = get_number_of_pages(url)

    page_prefix = "?page="
    page_number = 1
    list_of_items = []

    while page_number <= number_of_pages_to_scrap:
        logging.info(f"Page number: {page_number}/{number_of_pages_to_scrap}")
        p_pos = url.find("?search")
        if p_pos == -1:
            p_pos = url.find("&search")
            page_prefix = "&page="
            full_url = f"{url[:p_pos]}{page_prefix}{page_number}{url[p_pos:]}"
        else:
            # in this case we need to replace "?search" with "&search"
            full_url = f"{url[:p_pos]}{page_prefix}{page_number}&{url[p_pos + 1:]}"
        print(full_url)
        list_of_items.extend(scrap_page(full_url))
        page_number += 1  # Go to the next page

    final_set = remove_dups(list_of_items)
    logging.info(f"Finaly found {len(final_set)} records.")
    return final_set


def write_to_file(data):
    with open("previous_results.txt", "a") as file:
        if len(data) == 1:
            new_data = f"\n{str(data)[2:-2]}"
        else:
            new_data = str(data)[2:-2].replace("', '", "\n")
        file.write(new_data)


def check_data(data):
    global first_run
    try:
        with open("previous_results.txt", "r") as file:
            file_content = file.read()
    except FileNotFoundError:
        logging.info("It's first run, creating file...")
        cwd = os.getcwd()
        os.system(f"touch {cwd}/previous_results.txt")
        first_run = True
        file_content = ""

    found_ads = []
    for item in data:
        if item not in file_content:
            found_ads.append(item)

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

    req = request.Request(f"https://ntfy.sh/{topic}", data=str(*data).encode("utf-8"))
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
        help="Provide url to check ads from.",
        type=str,
        required=False
    )
    args = parser.parse_args()
    # log_lvl = logging.INFO
    log_lvl = logging.DEBUG
    if args.debug:
        log_lvl = logging.DEBUG
    first_run = False

    logging.basicConfig(
        level=log_lvl,
        filename="logs.log",
        format="%(levelname)s : %(asctime)s : %(message)s"
    )

    # ========== URL to scrape if nothing given in parameter ==========
    given_url = ""
    # =================================================================

    if args.url:
        given_url = args.url
        logging.debug("Using URL from parameter...")
    else:
        logging.debug("You didn't provide url, taking url from code file...")
        if not given_url:
            logging.error(
                "Didn't find URL in code nor in paramter, provide URL!"
            )
            raise SystemExit(
                "Didn't find URL in code nor in paramter, provide URL!"
            )

    page_url = format_url(given_url)
    ads_list = get_list_of_ads(page_url)
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
