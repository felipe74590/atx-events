import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from operator import itemgetter
from constants import EVENTS_API_URL, MAX_EVENTS_LIMIT

st.set_page_config(layout="centered")
st.title("Events in Austin Texas")
st.write("Here are some upcoming events:")


@st.cache_data(show_spinner=False)
def get_events() -> list:
    """Loads events based on todays date"""
    current_count = 0
    data = []

    while True:
        params = {"skip": current_count, "limit": MAX_EVENTS_LIMIT}
        response = requests.get(url=EVENTS_API_URL + "/events", params=params)
        response.raise_for_status()

        events = response.json()

        if not events:
            break

        current_count += MAX_EVENTS_LIMIT
        data.extend(events)

    return data


def sort_events_by_time(events: list) -> list:
    """Sort events data by date and only return those after the current time."""
    events.sort(key=itemgetter("start_datetime"))
    for index, event in enumerate(events):
        event_time = datetime.fromisoformat(event["start_datetime"])
        if event_time > datetime.now():
            events = events[index:]
            break

    return events


# Load, sort, and convert events to DataFrame
data = get_events()
events = sort_events_by_time(data)
df = pd.DataFrame(events)

# Pagination controls
total_events = len(df)
events_per_page = 50
total_pages = (total_events // events_per_page) + (total_events % events_per_page > 0)

# Sidebar for pagination
page_number = st.sidebar.number_input("Select Page:", 1, total_pages, 1)
start_index = (page_number - 1) * events_per_page
end_index = start_index + events_per_page

for index, row in df.iloc[start_index:end_index].iterrows():
    dt = datetime.fromisoformat(row["start_datetime"])
    friendly_start_time = dt.strftime("%B %d, %Y, %I:%M %p")
    st.markdown(f"**{row['title']}**")
    st.markdown(f"Venue: {row['venue']}")
    st.markdown(f"Starts:{friendly_start_time}")
    st.markdown(f"[Event Link]({row["event_link"]})")
    st.markdown("--------------------")
