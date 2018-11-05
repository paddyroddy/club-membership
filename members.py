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


class RetrieveMembers:
    def __init__(self, username, csv_name, url, json_name, gsheet_id):
        self.password = getpass.getpass('Union Password:')
        self.username = username
        self.csv_name = csv_name
        self.url = url
        self.json_name = json_name
        self.gsheet_id = gsheet_id

    def login(self, url):
        # opens chrome
        chrome_driver_path = '/usr/local/bin/chromedriver'
        driver = webdriver.Chrome(chrome_driver_path)

        # open union website and logs in
        driver.get(url)
        driver.find_element_by_id('username').send_keys(self.username)
        driver.find_element_by_id('password').send_keys(self.password)
        driver.find_element_by_name('_eventId_proceed').click()

        return driver

    def member_df(self):
        home = os.path.expanduser('~')
        filename = home + self.csv_name

        # remove old csvs
        try:
            for f in glob.glob(filename + '*csv'):
                os.remove(f)
        except OSError:
            pass

        # download file and wait
        driver = self.login(self.url)

        # read csv file
        wait = 0
        while(not glob.glob(filename + '*.csv')):
            wait += 1
            time.sleep(1)
            print('Time Waiting', wait)
        df = pd.read_csv(glob.glob(filename + '*.csv')[0])

        # close chrome
        driver.quit()
        return df

    @staticmethod
    def find_price(dataframe):
        return dataframe['Total'].replace(
            '\u00a3', '', regex=True).astype(float).sum()

    def authen_spreadsheet(self):
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']

        json = os.path.dirname(os.path.realpath(
            __file__)) + '/' + self.json_name

        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            json, scope)

        gc = gspread.authorize(credentials)

        wb = gc.open_by_key(self.gsheet_id)
        return wb

    def update_sheet(self):
        # find member list
        df = self.member_df()

        # find price
        price = self.find_price(df)
        print('\u00a3' + str(price))

        # ghseet handle
        gsheet = self.authen_spreadsheet()

        # update price
        sht = gsheet.worksheet('Balance')
        sht.update_acell('B8', price)

        # update list
        sht = gsheet.worksheet('Members')
        set_with_dataframe(sht, df)


if __name__ == '__main__':
    content = open('input.yml')
    loaded = yaml.load(content)
    username = loaded['username']
    csv_name = loaded['csv_name']
    url = loaded['url']
    json_name = loaded['json_name']
    gsheet_id = loaded['gsheet_id']

    members = RetrieveMembers(username, csv_name, url, json_name, gsheet_id)
    members.update_sheet()
