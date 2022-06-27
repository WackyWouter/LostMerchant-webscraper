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
import aiofiles
from telebot.async_telebot import AsyncTeleBot
import config

# Set up Telegram bot
bot = AsyncTeleBot(config.botToken)


# Handler for the /help message
@bot.message_handler(commands=['help'])
async def send_welcome(message):
    await bot.reply_to(message, "Hi! I'm the Lost Merchant bot. You can start receiving updates from me by sending "
                                "/start or stop receiving updates by sending /stop")

# Handler for the /start message
@bot.message_handler(commands=['start'])
async def add_user(message):
    # Read the user ids file
    user_ids = await read_file()

    # Save the current user's id as a string
    current_user_id = str(message.from_user.id)

    # Check if the current user's id is not already saved in the user_ids.txt file
    if current_user_id not in user_ids:
        # If the current user's id is not saved add it to the list and write the new list to the file
        user_ids.append(current_user_id)
        user_ids_str = ','.join(user_ids)
        await write_file(user_ids_str)

        # Let the user know that he has been added to the list
        await bot.reply_to(message, "Hi " + message.from_user.username + ", you wil now be receiving updates from me.")
    else:
        # Tell the user that he is already receiving updates
        await bot.reply_to(message, "Hi " + message.from_user.username + ", you are already receiving updates from me.")


# Handler for the /stop message
@bot.message_handler(commands=['stop'])
async def remove_user(message):
    # Read the user ids file
    user_ids = await read_file()

    # Save the current user's id as a string
    current_user_id = str(message.from_user.id)

    # Check if the current user's id is saved in the user_ids.txt file
    if current_user_id in user_ids:
        # If the current user's id is saved remove it from the list and write the new list to the file
        user_ids.remove(current_user_id)
        user_ids_str = ','.join(user_ids)
        await write_file(user_ids_str)

    # Tell the user that he is not going to receive anymore updates
    await bot.reply_to(message, "Hi " + message.from_user.username + ", you will now stop receiving updates from me.")


# Read the user_ids.txt file and return an array of user ids
async def read_file():
    async with aiofiles.open('user_ids.txt', mode='r') as f:
        user_ids = await f.read()
        return user_ids.split(',')


# Write a comma separated string of user ids to the user_ids.txt file
async def write_file(user_ids):
    async with aiofiles.open('user_ids.txt', mode='w') as f:
        await f.write(user_ids)


# Send provided message to saved user ids
async def send_message(message):
    # Get the user ids
    user_ids_list = await read_file()

    # Loop over the user ids making sure they are not empty and then send the message
    for user_id in user_ids_list:
        if user_id != '':
            await bot.send_message(user_id, message)


# Wait until a designated time
async def wait_until(minute_mark):
    while True:
        # Get the current minutes
        now_utc = datetime.utcnow()
        current_minutes = now_utc.minute

        # Calculate the difference in minutes and wait half that time
        diff_in_seconds = (minute_mark - current_minutes) * 60
        await asyncio.sleep(diff_in_seconds / 2)

        # If the diff is smaller than 0.1 we have reached the designated time
        if diff_in_seconds <= 0.1:
            return


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

    # TODO find a way to pick the right one when a merchant has multiple locations suggested
    # Part of that is removing the earlier wrong suggestion if a new suggestion (correct one) comes in
    while True:
        # Update the time
        now_utc = datetime.utcnow()
        current_minutes = now_utc.minute

        # Set up lists for the results and reset it every loop
        epic_loc = []
        leg_loc = []

        while 55 > current_minutes >= 30:

            result_leg = ''

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
                    await send_message(result_leg + result_epic)
            except TimeoutException:
                print('no epic items found yet')

            # Sleep for two minutes because we don't need to check every second
            await asyncio.sleep(120)

            # Update the time
            now_utc = datetime.utcnow()
            current_minutes = now_utc.minute

        # Sleep for 6min to make sure we are past the hour mark to make calculations easier
        await asyncio.sleep(360)

        # Sleep until we are back at the half hour mark
        await wait_until(30)


async def main():
    await asyncio.gather(
        item_scraper(),
        bot.infinity_polling(timeout=60, request_timeout=60)
    )


if __name__ == '__main__':
    asyncio.run(main())
