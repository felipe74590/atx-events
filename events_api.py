import json
from datetime import datetime

import requests
from decouple import config

from web_scraper import Event

base_url = "https://api.predicthq.com/v1/events/"
access_token = config("EVENTS_HQ_TOKEN")

headers = {"Authorization": "Bearer " + access_token, "Accept": "application/json"}
params = {"q": "Austin,Texas"}

response = requests.get(url=base_url, headers=headers, params=params)
austin_data = json.loads(response.text)


for atx_event in austin_data["results"]:
    # COULD_DO: should I use google location api to turn address into venue names
    start_time = datetime.strptime(atx_event["start_local"], "%Y-%m-%dT%H:%M")
    event = Event(
        atx_event["title"],
        start_time,
        atx_event["geo"]["address"]["formatted_address"],
        atx_event["category"],
        None,
    )
