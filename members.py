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


def member_df(csv_name, url):
    home = os.path.expanduser('~')
    filename = home + csv_name

    # remove old csvs
    try:
        for f in glob.glob(csv_name + '*csv'):
            os.remove(f)
    except OSError:
        pass

    # download file and wait
    driver = login(url)

    # read csv file
    wait = 0
    while(not glob.glob(csv_name + '*.csv')):
        wait += 1
        time.sleep(1)
        print('Time Waiting', wait)
    df = pd.read_csv(glob.glob(csv_name + '*.csv')[0])

    # close chrome
    driver.quit()
    return df


def find_price(dataframe):
    return dataframe['Total'].replace(
        '\u00a3', '', regex=True).astype(float).sum()


def authen_spreadsheet(json_name, gsheet_id):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    json = os.path.dirname(os.path.realpath(__file__)) + '/' + json_name

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        json, scope)

    gc = gspread.authorize(credentials)

    wb = gc.open_by_key(gsheet_id)
    return wb
