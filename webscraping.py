from selenium.common import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
import config

# Set up the browser driver
chromeService = Service(config.chromeDrivePath)
driver = webdriver.Chrome(service=chromeService)
driver.get(config.url)

wait = WebDriverWait(driver, 10)

# Wait for the serverRegion select to be present
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "option[value='EUC']")))

# Select server region
serverSelect = Select(driver.find_element(by=By.ID, value='severRegion'))
serverSelect.select_by_value('EUC')

# Wait for the server select to be present
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#server option")))

# Select server
serverSelect = Select(driver.find_element(by=By.ID, value='server'))
serverSelect.select_by_visible_text('Mokoko')

# Wait for the table to be present
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table")))

try:
    # Wait a few seconds to give the rapport items a change to show up
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.Epic")))

    # Results will be stored here
    results = []

    # Load the content into BeautifulSoup
    html = BeautifulSoup(driver.page_source, features='html.parser')

    # Find all elements in the content matching the attrs and loop over them
    legendaryItems = html.findAll('span', attrs={'class': 'item Legendary'})

    # print the amount
    if len(legendaryItems) > 0:
        print('The script has found ' + str(len(legendaryItems)) + ' legendary items!!' )
    else:
        print('No legendary items have been found. :(')
except TimeoutException:
    print('No items have been found yet. :(')
finally:
    # Close the browser
    driver.quit()
