from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Set the path to the Chromedriver
DRIVER_PATH = '/opt/homebrew/bin/chromedriver/'

#configure Chrome options
options = Options()
options.headless = True
options.add_argument("--window-size=1920,1200") #set window size

service = Service(executable_path=DRIVER_PATH)


# Initialize the Chrome Driver
driver = webdriver.Chrome(options=options, service=service)
driver.get('https://do512.com/')
print(driver.page_source)

driver.quit()


