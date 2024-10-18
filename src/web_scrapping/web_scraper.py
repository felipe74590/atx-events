import time
from datetime import datetime
from typing import NamedTuple

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from tenacity import retry, stop_after_attempt, wait_exponential

from src.constants import SOURCE_ONE

INCOMPLETE_INFO = "Important event information is missing from event descriptions."
HEADLESS = False

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
    category: str | None
    event_link: str | None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5))
def get_page(page: str):
    """Gets html data for url page provided."""
    this_page = requests.get(page, headers=headers, timeout=10)
    this_page.raise_for_status()
    soup = BeautifulSoup(this_page.text, features="html.parser")
    return soup


def gather_events_data_source_do512(url: str, events_list=None) -> list[Event]:
    """
    Gather important data from events in Do512 pages.
    :param url: url of page being scraped.
    :param events_list: ongoing list of events from this source
    """
    hot_soup = get_page(url)
    events_soup = hot_soup.find_all("div", class_="ds-listing")
    next_page = hot_soup.find("a", class_="ds-next-page")
    if events_list is None:
        events_list = []
    events = events_list
    for event in events_soup:
        event_details_links = SOURCE_ONE + event["data-permalink"]
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
        source = SOURCE_ONE + next_page_url
        gather_events_data_source_do512(source, events)
    else:
        print("No next page")
    return events


def extract_details(details_url: str) -> Event:
    """
    Extract all details from subpage.
    :param events_soup.
    """
    hot_soup = get_page(details_url)
    event_soup = hot_soup.find("div", class_="fbecol-8-12")
    title = event_soup.h1.text.strip()
    venue_details = hot_soup.find("div", class_="detail_items").find_all("div")[:4]
    event_link = details_url

    # Sometimes the venue is in index 2 other times, index 2 is a link for tickets and index 3 has the venue name.
    # Sometimes venue is TBA
    if len(venue_details) != 4:
        print(INCOMPLETE_INFO)
        return None
    else:
        date, time, venue_maybe, venue_maybe2 = (detail.text.strip() for detail in venue_details)

    venue = venue_maybe2 if "Get Tickets" in venue_maybe else venue_maybe

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


def gather_events_data_source_heyaustin(url: str, events_list=None) -> list[Event]:
    """
    Gather important data from events in HeyAustin pages.
    :param url: url of page being scraped.
    :param events_list: ongoing list of events from this source
    """
    hot_soup = get_page(url)
    next_page = hot_soup.find("a", class_="next page-numbers")
    events_soup = hot_soup.find_all("div", class_="fbe_col_title")
    if events_list is None:
        events_list = []
    events = events_list
    for event in events_soup:
        event_details = extract_details(event.a["href"])
        if event_details is not None:
            events.append(event_details)
        else:
            print(INCOMPLETE_INFO)

    if next_page is not None:
        next_page_url = next_page["href"]
        source = next_page_url
        gather_events_data_source_heyaustin(source, events)
    else:
        print("No next page")
    return events


def auto_scroll(page, max_scrolls=10):
    """
    Scrolls to load the entire page and its contents for webscrapping
    :param page: url of the page being scraped
    :max_scrolls: the amount of times to scroll down the page
    """
    # Scroll to the bottom of the page to trigger loading of all content
    previous_height = page.evaluate("document.body.scrollHeight")

    scrolls = 0
    while True:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)  # Wait for the new content to load
        scrolls += 1

        # Check if more content has loaded by comparing the page height
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height

        if scrolls >= max_scrolls:
            break


def gather_events_data_atx_culture(url: str) -> list[Event]:
    """
    Gather important event data in Austin Culture map pages.
    :param url: url of page being scraped.
    :param events_list: ongoing list of events from this source
    """
    events = []
    with sync_playwright() as p:
        with p.chromium.launch(headless=HEADLESS) as browser:
            page = browser.new_page()
            page.goto(url)

            # if we want to load more content, but as we run it daily this
            # might not be needed
            auto_scroll(page)

            page.wait_for_selector("div.module-headline__text", timeout=10000)

            event_dates = page.query_selector_all("div.module-headline__text")
            event_grids = page.query_selector_all("div.grid-flow-row-dense")

            event_dates = [event.inner_text() for event in event_dates]

            for date, grid in zip(event_dates, event_grids, strict=False):
                for link in grid.query_selector_all("a"):
                    if link.get_attribute("href") is not None:
                        event_link = link.get_attribute("href")

                date_only = date.splitlines()

                for event in grid.query_selector_all("div.event-post"):
                    event = event.inner_text()
                    fields = event.splitlines()
                    if len(fields) < 3:
                        print("Missing event data: ", fields)
                        continue
                    if len(fields) == 4:  # get editor's pick off
                        fields = fields[1:]

                    title, venue, time = fields
                    date_object = f"{date_only[1].strip()} {time}"
                    start_time = datetime.strptime(date_object, "%B %d, %Y %I:%M %p")
                    events.append(
                        Event(title=title, start_datetime=start_time, venue=venue, category=None, event_link=event_link)
                    )

    return events
