import argparse

from decouple import config

from db_helper import add_events_to_db
from events_api import get_predict_api_events
from web_scraper import (
    gather_events_data_source_atxorg,
    gather_events_data_source_do512,
    gather_events_data_source_heyaustin,
    gather_events_data_atx_culture
)

source_one = config("SOURCE1")
source_two = config("SOURCE2")
source_three = config("SOURCE3")
source_four = config("SOURCE4")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", help="Enter source: source1, source2, source3")
    args = parser.parse_args()

    match args.source:
        case "source1":
            data = gather_events_data_source_do512(source_one)
        case "source2":
            data = gather_events_data_source_heyaustin(source_two)
        case "source3":
            data = gather_events_data_source_atxorg(source_three)
        case "source4":
            data = gather_events_data_atx_culture(source_four)
        case "source5":
            data = get_predict_api_events()
        case _ :
            print("Invalid input")

    # add_events_to_db(data)
