#!/usr/bin/env python
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
    def __init__(self, input):
        self.password = getpass.getpass("Union Password:")
        content = open(input)
        vars = yaml.load(content, Loader=yaml.FullLoader)
        self.username = vars["username"]
        self.xls_name = vars["xls_name"]
        self.url = vars["url"]
        self.json_name = vars["json_name"]
        self.gsheet_id = vars["gsheet_id"]
        self.cell_id = vars["cell_id"]

    def login(self, url):
        # opens chrome
        chrome_driver_path = "/usr/local/bin/chromedriver"
        driver = webdriver.Chrome(chrome_driver_path)

        # open union website and logs in
        driver.get(url)
        driver.find_element_by_id("username").send_keys(self.username)
        driver.find_element_by_id("password").send_keys(self.password)
        driver.find_element_by_name("_eventId_proceed").click()

        return driver

    def member_df(self):
        home = os.path.expanduser("~")
        filename = home + self.xls_name

        # remove old xls
        try:
            for f in glob.glob(filename + "*xls"):
                os.remove(f)
        except OSError:
            pass

        # download file and wait
        driver = self.login(self.url)

        # read xls file
        wait = 0
        while not glob.glob(filename + "*.xls"):
            wait += 1
            time.sleep(1)
            print("Time Waiting", wait)
        df = pd.read_html(glob.glob(filename + "*.xls")[0], index_col="Order created")[
            0
        ]

        # close chrome
        driver.quit()

        # clean up date columns
        df.index = pd.to_datetime(df.index, format="%d/%m/%Y, %H:%M")
        df.sort_index(inplace=True, ascending=False)
        return df

    @staticmethod
    def find_price(dataframe):
        return (
            dataframe["Amount paid"]
            .replace("\u00a3", "", regex=True)
            .astype(float)
            .sum()
        )

    def authen_spreadsheet(self):
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            self.json_name, scope
        )

        gc = gspread.authorize(credentials)

        wb = gc.open_by_key(self.gsheet_id)
        return wb

    def update_sheet(self):
        # find member list
        df = self.member_df()

        # find price
        price = self.find_price(df)
        print("Members:", len(df), "Income:", "\u00a3" + str(price))

        # ghseet handle
        gsheet = self.authen_spreadsheet()

        # update price
        sht = gsheet.worksheet("Balance")
        sht.update_acell(self.cell_id, price)

        # update list
        sht = gsheet.worksheet("Members")
        set_with_dataframe(sht, df, include_index=True)


if __name__ == "__main__":
    members = RetrieveMembers("input.yml")
    members.update_sheet()
