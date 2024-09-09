from bs4 import BeautifulSoup
import requests

SOURCE = 'https://do512.com'

##TODO: Figure out how to change page to get all events not just the ones on the home page
class DO512():
    def __init__(self):
        self.source = SOURCE
        self.category_types = []
        self.permalinks = []
        self.title_list = []
        self.start_time_list = []
        self.venues_list = []

    def get_page(self, page):
        try: 
            this_page = requests.get(page)
            soup = BeautifulSoup(this_page.text, features='html.parser')
            events_soup = soup.find_all('div', class_ = 'ds-events-group')
            next_page = soup.find('a', class_ = 'ds-next-page')
        except Exception as err:
            print("There was an error getting page", err)
        return events_soup, next_page

    # Loop through each event and get basic event data
    def gather_512_events_data(self, url):
        events_page = url
        event_divs, page_result = self.get_page(events_page)
        try: 
            for event in event_divs:
                """ Gather important data from events in Do512 pages """
                listings = event.find_all('div', class_ = 'ds-listing')
                # category_types, permalinks = [], []
                for listing in listings:
                    self.category_types.append(listing['class'][2])
                    event_details_links = 'https://do512.com'+listing['data-permalink']
                    self.permalinks.append(event_details_links)

                titles = event.find_all('span', class_ = "ds-listing-event-title-text")
                for title in titles:
                    self.title_list.append(title.text.strip())

                
                event_details = event.find_all('div', class_ = 'ds-listing-details-container')
                for details in event_details:
                    self.start_time_list.append(details.find('div', class_='ds-event-time dtstart').text.strip())

                #venue address names are inconsistent, will store venue name and use google location api to search for the venue address later on
                venue_details = event.find_all('div', class_ = 'ds-venue-name')
                for venue in venue_details:
                    deets = venue.find_all('span')
                    venue_name = deets[1].text
                    self.venues_list.append(venue_name)
            
            if page_result != None:
                next_page = page_result['href']
                self.source = SOURCE + next_page
                self.gather_512_events_data(self.source)
            else:
                print("No next page")
            return self.title_list, self.category_types, self.venues_list, self.permalinks, self.start_time_list
        
        except Exception as err:
            print("Error parsing and collecting basic event data", err)



DO512().gather_512_events_data(SOURCE)
    