import argparse

from src.constants import SOURCE_FOUR, SOURCE_ONE, SOURCE_THREE, SOURCE_TWO
from src.db_helper import add_events_to_db
from src.events_api import get_predict_api_events
from src.web_scraper import (
    gather_events_data_atx_culture,
    gather_events_data_source_atxorg,
    gather_events_data_source_do512,
    gather_events_data_source_heyaustin,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", help="Enter source: source1, source2, source3, source4, source5")
    args = parser.parse_args()

    match args.source:
        case "source1":
            data = gather_events_data_source_do512(SOURCE_ONE)
        case "source2":
            data = gather_events_data_source_heyaustin(SOURCE_TWO)
        case "source3":
            data = gather_events_data_atx_culture(SOURCE_THREE)
        case "source4":
            data = gather_events_data_source_atxorg(SOURCE_FOUR)
        case "source5":
            data = get_predict_api_events()
        case _ :
            print("Invalid input")

    add_events_to_db(data)
