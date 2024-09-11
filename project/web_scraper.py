from datetime import datetime

import requests
from bs4 import BeautifulSoup

from db_helper import add_events_to_db

SOURCE = "https://do512.com"


def get_page(page):
    try:
        this_page = requests.get(page)
        soup = BeautifulSoup(this_page.text, features="html.parser")
        events_soup = soup.find_all("div", class_="ds-listing")
        next_page = soup.find("a", class_="ds-next-page")
    except Exception as err:
        print("There was an error getting page", err)
    return events_soup, next_page


# Loop through each event and get basic event data
def gather_512_events_data(url):
    events_page = url
    event_divs, page_result = get_page(events_page)
    events = []
    try:
        for event in event_divs:
            """Gather important data from events in Do512 pages"""
            event_details_links = SOURCE + event["data-permalink"]
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

        if page_result != None:
            next_page = page_result["href"]
            source = SOURCE + next_page
            gather_512_events_data(source)
        else:
            print("No next page")
        return events

    except Exception as err:
        print("Error parsing and collecting basic event data", err)


if __name__ == "__main__":

    data = gather_512_events_data(SOURCE)
    add_events_to_db(data)
