import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from constants import EVENTS_API_URL, MAX_EVENTS_LIMIT


st.title("Events in Austin Texas")
st.write("Here are some upcoming events:")


def load_events(current_count=0, data=None):
    """Loads events based on todays date"""
    if not data:
        data = []

    params = {"skip": current_count, "limit": MAX_EVENTS_LIMIT}
    response = requests.get(url=EVENTS_API_URL + "/events", params=params)
    response.raise_for_status()

    if len(response.json()) >= MAX_EVENTS_LIMIT:
        current_count += 50
        data.extend(response.json())
        load_events(current_count, data)

    return data


events = load_events()
df = pd.DataFrame(events)


for index, row in df.iterrows():
    dt = datetime.fromisoformat(row["start_datetime"])
    friendly_start_time = dt.strftime("%B %d, %Y, %I:%M %p")
    st.markdown(f"**{row['title']}**")
    st.markdown(f"Venue: {row['venue']}")
    st.markdown(f"Starts:{friendly_start_time}")
    st.markdown(f"[Event Link]({row["event_link"]})")
    st.markdown("--------------------")
st.write(events)
