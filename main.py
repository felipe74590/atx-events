import argparse
from src.constants import SOURCE_ONE, SOURCE_THREE, SOURCE_TWO
from src.data.db_helper import add_events_to_db
from src.web_scrapping.web_scraper import (
    gather_events_data_atx_culture,
    gather_events_data_source_do512,
    gather_events_data_source_heyaustin,
)


def handler_function():
    add_events_to_db(gather_events_data_source_do512(SOURCE_ONE))
    add_events_to_db(gather_events_data_source_heyaustin(SOURCE_TWO))
    add_events_to_db(gather_events_data_atx_culture(SOURCE_THREE))
    print("All events scraped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", help="Enter source: source1, source2, source3, all")
    args = parser.parse_args()

    match args.source:
        case "source1":
            data = gather_events_data_source_do512(SOURCE_ONE)
            add_events_to_db(data)
        case "source2":
            data = gather_events_data_source_heyaustin(SOURCE_TWO)
            add_events_to_db(data)
        case "source3":
            data = gather_events_data_atx_culture(SOURCE_THREE)
            add_events_to_db(data)
        case _:
            print("No source provided, run all")
            for func, source in [
                (gather_events_data_source_do512, SOURCE_ONE),
                (gather_events_data_source_heyaustin, SOURCE_TWO),
                (gather_events_data_atx_culture, SOURCE_THREE),
            ]:
                data = func(source)
                add_events_to_db(data)

