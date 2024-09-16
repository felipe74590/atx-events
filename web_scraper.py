from datetime import datetime
from typing import NamedTuple, Optional

import requests
from bs4 import BeautifulSoup

from db_helper import add_events_to_db

SOURCE1 = "https://do512.com"
SOURCE2 = "https://heyaustin.com/austin-events/"
INCOMPLETE_INFO = "Important event information is missing from event descriptions."

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US, en; q=0.5",
    "Accept": "text/html, application/xhtml+xml",
}


class Event(NamedTuple):
    title: str
    start_datetime: datetime
    venue: str
    category: Optional[str] = None
    event_link: Optional[str] = None


def get_page(page: str):
    """
    Gets html data for url page provided.
    """
    this_page = requests.get(page, headers=headers)
    this_page.raise_for_status()
    soup = BeautifulSoup(this_page.text, features="html.parser")
    return soup


def gather_512_events_data(url: str, event_list=[]) -> list[Event]:
    """
    Gather important data from events in Do512 pages
    :param url: the current url of the page being scraped
    """
    hot_soup = get_page(url)
    events_soup = hot_soup.find_all("div", class_="ds-listing")
    next_page = hot_soup.find("a", class_="ds-next-page")
    events = event_list
    for event in events_soup:
        event_details_links = SOURCE1 + event["data-permalink"]
        category_types = event["class"][2][9:]

        title = event.find("span", class_="ds-listing-event-title-text").text.strip()
        # Accounts for events that have TBD dates
        if event.find("meta", itemprop="startDate") is None:
            print(INCOMPLETE_INFO)
            continue
        else:
            event_date = event.find("meta", itemprop="startDate")["datetime"][:-5]

        start_time = datetime.strptime(event_date, "%Y-%m-%dT%H:%M")
        venue_details = event.find("div", class_="ds-venue-name")
        venue_location = venue_details.find("span", itemprop="name").text.strip()
        this_event = Event(
            title,
            start_time,
            venue_location,
            category_types,
            event_details_links,
        )

        events.append(this_event)

    if next_page is not None:
        next_page_url = next_page["href"]
        source = SOURCE1 + next_page_url
        gather_512_events_data(source, events)
    else:
        print("No next page")
    return events


def extract_details(details_url: str) -> Event:
    """
    Extract all details from subpage
    :param events_soup
    """
    hot_soup = get_page(details_url)
    event_soup = hot_soup.find("div", class_="fbecol-8-12")
    title = event_soup.h1.text.strip()
    venue_details = hot_soup.find("div", class_="detail_items").find_all("div")[:4]
    event_link = details_url

    # Sometimes the venue is in index 2 other times, index 2 is a link for tickets and index 3 has the venue name.
    # Sometimes venue is TBA
    if len(venue_details) != 4:
        return None
    else:
        date, time, venue_maybe, venue_maybe2 = [
            detail.text.strip() for detail in venue_details
        ]

    if "Get Tickets" in venue_maybe:
        venue = venue_maybe2
    else:
        venue = venue_maybe

    # cleaning up the event start time to be a datetime object that matches those in the first event source
    if "-" in time:
        start_time = time.split("-")
        start_time = start_time[0].strip()
    else:
        start_time = time

    datetime_str = f"{date} {start_time.upper()}"
    start_datetime = datetime.strptime(datetime_str, "%b %d, %Y %I:%M %p")

    event = Event(
        title,
        start_datetime,
        venue,
        None,
        event_link,
    )
    return event


def gather_hey_austin_events_data(url: str, events_list=[]):
    """
    Gather important data from events in HeyAustin pages
    :param url: the current url of the page being scraped
    """
    events = events_list
    hot_soup = get_page(url)
    next_page = hot_soup.find("a", class_="next page-numbers")
    events_soup = hot_soup.find_all("div", class_="fbe_col_title")
    for event in events_soup:
        event_details = extract_details(event.a["href"])
        if event_details is not None:
            events.append(event_details)
        else:
            print(INCOMPLETE_INFO)

    if next_page is not None:
        next_page_url = next_page["href"]
        source = next_page_url
        gather_hey_austin_events_data(source, events)
    else:
        print("No next page")
    return events


if __name__ == "__main__":
    data = gather_512_events_data(SOURCE1)
    # data = gather_hey_austin_events_data(SOURCE2)
    add_events_to_db(data)
