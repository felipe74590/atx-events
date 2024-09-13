from datetime import datetime

import requests
from bs4 import BeautifulSoup

from db_helper import add_events_to_db

SOURCE1 = "https://do512.com"
SOURCE2 = "https://heyaustin.com/austin-events/"


def get_page(page: str):
    """
    Gets html data for url page provided.
    """
    try:
        this_page = requests.get(page)
        soup = BeautifulSoup(this_page.text, features="html.parser")
    except Exception as err:
        print("There was an error getting page", err)

    return soup


def gather_512_events_data(url: str) -> list:
    """
    Gather important data from events in Do512 pages
    :param url: the current url of the page being scraped
    """
    hot_soup = get_page(url)
    events_soup = hot_soup.find_all("div", class_="ds-listing")
    next_page = hot_soup.find("a", class_="ds-next-page")

    events = []
    for event in events_soup:
        event_details_links = SOURCE1 + event["data-permalink"]
        category_types = event["class"][2][9:]

        title = event.find("span", class_="ds-listing-event-title-text").text.strip()
        event_date = event.find("meta", itemprop="startDate")["datetime"]
        venue_details = event.find("div", class_="ds-venue-name")
        venue_location = venue_details.find("span", itemprop="name").text.strip()
        this_event = {
            "title": title,
            "category": category_types,
            "venue": venue_location,
            "link": event_details_links,
            "start_datetime": event_date,
        }

        events.append(this_event)

    if next_page != None:
        next_page_url = next_page["href"]
        source = SOURCE1 + next_page_url
        gather_512_events_data(source)
    else:
        print("No next page")
    return events



def extract_details(details_url: str):
    """
    Extract all details from subpage
    :param events_soup
    """
    hot_soup = get_page(details_url)
    event_soup = hot_soup.find("div", class_="fbecol-8-12")
    title = event_soup.h1.text.strip()
    venue_details = hot_soup.find("div", class_="detail_items")
    date = venue_details.div.span.text.strip()
    ##TODO: Find out how to get the second div in venue_details which contains event start time and the third div in venue_details which contains venue name.


def gather_events_data_hey_austin(url: str):
    """
    Gather important data from events in HeyAustin pages
    :param url: the current url of the page being scraped
    """
    hot_soup = get_page(url)
    events_soup = hot_soup.find_all("div", class_="fbe_col_title")
    for event in events_soup:
        event_details = extract_details(event.a["href"])


if __name__ == "__main__":
    data = gather_events_data_hey_austin(SOURCE2)
    # data = gather_512_events_data(SOURCE1)
    # add_events_to_db(data)
