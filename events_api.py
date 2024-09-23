import json
from datetime import datetime

import requests
from decouple import config

from web_scraper import Event

base_url = config("PREDICT_API")
access_token = config("EVENTS_HQ_TOKEN")
LIMIT = 50 #max events per page

def get_events(offset)->dict:
    headers = {
        "Authorization": "Bearer " + access_token,
        "Accept": "application/json"
    }
    params = {
        "q": "Austin,Texas",
        "limit": 188,
        "offset": offset
    }

    response = requests.get(url=base_url, headers=headers, params=params)
    response.raise_for_status()
    austin_data = json.loads(response.text)
    return austin_data

#TODO: API takes time frame parameters, create a window of time to pull event info because default pull only brings 5-6 events
def get_predict_api_events()->list[Event]:
    """
    Call Predict API and get all events from
    """
    offset = 0
    all_events = []

    while True:
        events = get_events(offset)
        if not events["results"]:
            break
        all_events.extend(events["results"])
        offset += LIMIT

    events_list= []
    for atx_event in all_events:
        if "formatted_address" not in atx_event["geo"]["address"]:
            print("This is a city wide alert, not an event.")
            continue

        event_time = atx_event["start_local"]
        start_time = datetime.strptime(event_time, "%Y-%m-%dT%H:%M:%S")

        event = Event(
            atx_event["title"],
            start_time,
            atx_event["geo"]["address"]["formatted_address"],
            atx_event["category"],
            None,
        )
        events_list.append(event)

    return events_list

