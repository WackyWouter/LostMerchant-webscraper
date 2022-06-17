import pandas as pd
import config
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

chromeService = Service(config.chromeDrivePath)
driver = webdriver.Chrome(service=chromeService)
driver.get(config.url)
