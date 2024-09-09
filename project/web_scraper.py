from bs4 import BeautifulSoup
import requests

SOURCE1 = 'https://do512.com/'

page = requests.get(SOURCE1)
soup = BeautifulSoup(page.text, features='html.parser')

event_divs = soup.find_all('div', class_ = 'ds-events-group')

# Loop through each event and get specific data

for event in event_divs:
    """ Gather important data from event pages """
    listings = event.find_all('div', class_ = 'ds-listing')
    category_types = []
    for listing in listings:
        category_types.append(listing['class'][2])

    titles = event.find_all('span', class_ = "ds-listing-event-title-text")
    title_list = []
    for title in titles:
       title_list.append(title.text.strip())

    
    event_details = event.find_all('div', class_ = 'ds-listing-details-container')
    start_time_list = []
    for details in event_details:
        start_time_list.append(details.find('div', class_='ds-event-time dtstart').text.strip())

    #venue address names are inconsistent, will store venue name and use google location api to search for the venue address later on
    venue_details = event.find_all('div', class_ = 'ds-venue-name')
    venues_list = []
    for venue in venue_details:
        deets = venue.find_all('span')
        venue_name = deets[1].text
        venues_list.append(venue_name)

    print(title_list, start_time_list, venues_list, category_types)


    