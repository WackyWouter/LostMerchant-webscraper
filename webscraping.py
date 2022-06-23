from selenium.common import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from datetime import datetime
import asyncio
from telebot.async_telebot import AsyncTeleBot
import config

# Set up Telegram bot
bot = AsyncTeleBot(config.botToken)

@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    await bot.reply_to(message, "Hi! This is a test!")


async def item_scraper():
    # Set up the browser options
    options = webdriver.ChromeOptions()
    options.add_argument('--incognito')
    options.add_argument('--headless')

    # Set up the browser driver
    chrome_service = Service(config.chromeDrivePath)
    driver = webdriver.Chrome(service=chrome_service, options=options)
    driver.get(config.url)

    wait = WebDriverWait(driver, 10)

    # Wait for the serverRegion select to be present
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "option[value='EUC']")))

    # Select server region
    server_select = Select(driver.find_element(by=By.ID, value='severRegion'))
    server_select.select_by_value('EUC')

    # Wait for the server select to be present
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#server option")))

    # Select server
    server_select = Select(driver.find_element(by=By.ID, value='server'))
    server_select.select_by_visible_text('Mokoko')

    # Wait for the table to be present
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table")))

    # Get current time in utc
    now_utc = datetime.utcnow()
    current_minutes = now_utc.minute

    # Set up lists for the results
    epic_loc = []
    leg_loc = []

    # TODO find a way to pick the right one when a merchant has multiple locations suggested
    # Part of that is removing the earlier wrong suggestion if a new suggestion (correct one) comes in
    # TODO make it so that it runs continuously
    while 55 > current_minutes >= 30:

        result_leg = ''
        result_epic = ''

        found_new_item = False

        try:
            # Wait a few seconds to give the rapport items a change to show up
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.Epic")))

            # Load the content into BeautifulSoup
            html = BeautifulSoup(driver.page_source, features='html.parser')

            # Find all elements in the content matching the attrs and loop over them
            leg_items = html.findAll('span', attrs={'class': 'item Legendary'})
            for legendaryItem in leg_items:

                # Navigate to the zone column of the table row
                item = legendaryItem.parent
                card = item.previous_sibling.previous_sibling.previous_sibling
                location = card.previous_sibling.previous_sibling.previous_sibling

                # Save the location
                if location.get_text() not in leg_loc:
                    leg_loc.append(location.get_text())
                    found_new_item = True

            # create legendary message
            if len(leg_items) > 0:
                result_leg = (
                        str(len(leg_items)) +
                        ' Legendary rapport items have been found at the following locations: '
                        + ', '.join(leg_loc) + '. ')

            # Find all elements in the content matching the attrs and loop over them
            epic_items = html.findAll('span', attrs={'class': 'item Epic'})
            for epicItem in epic_items:

                # Navigate to the zone column of the table row
                item = epicItem.parent
                card = item.previous_sibling.previous_sibling.previous_sibling
                location = card.previous_sibling.previous_sibling.previous_sibling

                # Save the location
                if location.get_text() not in epic_loc:
                    epic_loc.append(location.get_text())
                    found_new_item = True

            # create Epic message
            result_epic = (str(len(epic_items)) + ' Epic rapport items have been found at the following locations: '
                           + ', '.join(epic_loc) + '.')

            if found_new_item:
                await bot.send_message(config.chatIdList[0], result_leg + result_epic)
        except TimeoutException:
            await bot.send_message(config.chatIdList[0], 'No items have been found yet. :(')

        # Sleep for two minutes because we don't need to check every second
        await asyncio.sleep(120)

        # Update the time
        now_utc = datetime.utcnow()
        current_minutes = now_utc.minute

    # Close the browser
    driver.quit()

async def main():
    await asyncio.gather(bot.infinity_polling(), item_scraper())


if __name__ == '__main__':
    asyncio.run(main())
