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
    """Loads events sorted by start_datetime, starting with the current date"""

    params = {"from_date": datetime.now()}
    response = requests.get(url=EVENTS_API_URL + "/search_events/", params=params)
    response.raise_for_status()

    events_response = response.json()

    return events_response


def load_main_page():
    # Load page first time
    events_loaded = get_events()
    total_events = events_loaded["total_events"]

    # Calculate total pages
    events_per_page = MAX_EVENTS_LIMIT
    total_pages = (total_events // events_per_page) + (total_events % events_per_page > 0)

    # Sidebar for pagination
    page_number = st.sidebar.number_input("Select Page:", 1, total_pages, 1)

    # Load events for the current page
    events_returned = events_loaded["events"]
    events_returned.sort(key=itemgetter("start_datetime"))
    df = pd.DataFrame(events_returned)

    start_index = (page_number - 1) * events_per_page
    end_index = start_index + events_per_page

    # Create a list to store saved events
    saved_events = st.session_state.get("saved_events", [])
    for index, row in df.iloc[start_index:end_index].iterrows():
        dt = datetime.fromisoformat(row["start_datetime"])
        friendly_start_time = dt.strftime("%B %d, %Y, %I:%M %p")
        st.markdown(f"**{row['title']}**")
        st.markdown(f"Venue: {row['venue']}")
        st.markdown(f"Starts:{friendly_start_time}")
        st.markdown(f"[Event Link]({row["event_link"]})")

        event_id = row["id"]
        is_saved = event_id in saved_events
        if st.session_state.get("logged_in"):
            if st.checkbox("Save Event", value=is_saved, key=event_id):
                if event_id not in saved_events:
                    saved_events.append(event_id)
                else:
                    if event_id in saved_events:
                        saved_events.remove(event_id)

        st.markdown("--------------------")
    st.session_state["saved_events"] = saved_events


if __name__ == "__main__":
    load_main_page()
