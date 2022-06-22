from selenium.common import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from datetime import datetime
import time
import telebot
import config

# TODO maybe set up the telegram bot with handles in a separate file so that can constantly run
# Set up Telegram bot
bot = telebot.TeleBot(config.botToken, parse_mode=None)  # parse mode can be html or markdown

# Set up the browser options
options = webdriver.ChromeOptions()
options.add_argument('--incognito')
options.add_argument('--headless')

# Set up the browser driver
chromeService = Service(config.chromeDrivePath)
driver = webdriver.Chrome(service=chromeService, options=options)
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

# Get current time in utc
nowUTC = datetime.utcnow()
currentMinutes = nowUTC.minute

# Set up lists for the results
epicLoc = []
legLoc = []

# TODO find a way to pick the right one when a merchant has multiple locations suggested
while 55 > currentMinutes >= 30:

    resultLeg = ''
    resultEpic = ''

    foundNewItem = False

    try:
        # Wait a few seconds to give the rapport items a change to show up
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.Epic")))

        # Load the content into BeautifulSoup
        html = BeautifulSoup(driver.page_source, features='html.parser')

        # Find all elements in the content matching the attrs and loop over them
        legItems = html.findAll('span', attrs={'class': 'item Legendary'})
        for legendaryItem in legItems:

            # Navigate to the zone column of the table row
            item = legendaryItem.parent
            card = item.previous_sibling.previous_sibling.previous_sibling
            location = card.previous_sibling.previous_sibling.previous_sibling

            # Save the location
            if location.get_text() not in legLoc:
                legLoc.append(location.get_text())
                foundNewItem = True

        # create legendary message
        if len(legItems) > 0:
            resultLeg = (str(len(legItems)) + ' Legendary rapport items have been found at the following locations: '
                         + ', '.join(legLoc) + '. ')

        # Find all elements in the content matching the attrs and loop over them
        epicItems = html.findAll('span', attrs={'class': 'item Epic'})
        for epicItem in epicItems:

            # Navigate to the zone column of the table row
            item = epicItem.parent
            card = item.previous_sibling.previous_sibling.previous_sibling
            location = card.previous_sibling.previous_sibling.previous_sibling

            # Save the location
            if location.get_text() not in epicLoc:
                epicLoc.append(location.get_text())
                foundNewItem = True

        # create Epic message
        resultEpic = (str(len(epicItems)) + ' Epic rapport items have been found at the following locations: '
                      + ', '.join(epicLoc) + '.')

        if foundNewItem:
            bot.send_message(config.chatIdList[0], resultLeg + resultEpic)
    except TimeoutException:
        bot.send_message(config.chatIdList[0], 'No items have been found yet. :(')

    # Sleep for two minutes because we don't need to check every second
    time.sleep(120)

    # Update the time
    nowUTC = datetime.utcnow()
    currentMinutes = nowUTC.minute

# Close the browser
driver.quit()

