
from datetime import datetime
from typing import NamedTuple
import feedparser
import re

import requests
from bs4 import BeautifulSoup
from decouple import config

from playwright.sync_api import sync_playwright

source_one = config("SOURCE1")
source_two = config("SOURCE2")
source_three = config("SOURCE3")

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
    category: str | None
    event_link: str | None


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
        event_details_links = source_one + event["data-permalink"]
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
        source = source_one + next_page_url
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
        date, time, venue_maybe, venue_maybe2 = (
            detail.text.strip() for detail in venue_details
        )

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


def gather_events_data_source_atxorg(url: str, events_list=None) -> list[Event]:
    """
    Gather important data from events in Austin Texas.org pages.
    :param url: url of page being scraped.
    :param events_list: ongoing list of events from this source
    """
    #The following are the relevant data keys withing the feed entry
    #dict_keys(['title', 'link', 'tags', 'summary', 'summary_detail'])
    feed = feedparser.parse(url)

    for entry in feed.entries:
        print(entry.summary_detail)
        # date_pattern = r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s\w+\s\d{1,2}(?:st|nd|rd|th)?|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2}(?:st|nd|rd|th)?'
        # date_matches = re.findall(date_pattern, entry.summary)
        # print(date_matches)
        # address_pattern = r'\(\s*(.*?)\s*\)'
        # address_matches = re.findall(address_pattern, entry.summary)
        # print(address_matches)

        # getting the event category from the tags
        categories = ""
        for tag in entry.tags:
            categories += tag.term + " "
        event = Event(
            title=entry.title,
            start_datetime="",
            venue="",
            category=categories,
            event_link=entry.link
        )

##TODO:Inner_text() lacks
def gather_events_data_atx_culture(url:str, events_list=None) -> list[Event]:
    """
    Gather important event data in Austin Culture map pages.
    :param url: url of page being scraped.
    :param events_list: ongoing list of events from this source
    """
    inner_html = None
    soup = None
    with sync_playwright() as p:
        with p.chromium.launch(headless=True) as browser:
            page = browser.new_page()
            page.goto(url)
            page.wait_for_selector('.grid-flow-row-dense')
            element_handle = page.query_selector('div.grid-flow-row-dense')
            inner_html = element_handle.inner_html()
            soup = BeautifulSoup(inner_html, 'html.parser')
            events = soup.find_all('a')
        
        #TODO: Solve issue that doesn't allow event.find('div', class_='headline') to work
        # Same with event.find('div', _class='location')
        # Issue with date, the current function only shows time, this data source might be inefficient
            for event in events:
                print(event.prettify())
                event_link = event["href"]
                location = event.find('div', _class='location')
                print(location)
                break


