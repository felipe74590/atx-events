import streamlit as st
import requests
from constants import EVENTS_API_URL, MAX_EVENTS_LIMIT


st.write("Local events")


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
st.write(events)
