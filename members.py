from selenium import webdriver
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import glob
import os
import time
import pandas as pd
from gspread_dataframe import set_with_dataframe
import getpass
import yaml


pswd = getpass.getpass('Union Password:')


def login(url, username):
    # opens chrome
    chrome_driver_path = '/usr/local/bin/chromedriver'
    driver = webdriver.Chrome(chrome_driver_path)

    # open union website and logs in
    driver.get(url)
    driver.find_element_by_id('username').send_keys(username)
    driver.find_element_by_id('password').send_keys(pswd)
    driver.find_element_by_name('_eventId_proceed').click()

    return driver
