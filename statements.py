#!/usr/bin/env python
import argparse
import pandas as pd
import os
import yaml
from oauth2client.service_account import ServiceAccountCredentials
import gspread


class AnalyseStatement:
    def __init__(self, input):
        content = open(input)
        vars = yaml.load(content, Loader=yaml.FullLoader)
        self.json_name = vars['json_name']
        self.gsheet_id = vars['gsheet_id']

        # read args
        parser = argparse.ArgumentParser(
            description='Analyse weekly statement')
        parser.add_argument('excel_file', type=str,
                            help='weekly statement excel file')
        args = parser.parse_args()
        self.df = pd.read_excel(args.excel_file)
        self.date = self.df['DATE'].sort_values()[0].strftime('%d/%m/%Y')
        self.update_sheet()

    def authen_spreadsheet(self):
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']

        json = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), self.json_name)

        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            json, scope)

        gc = gspread.authorize(credentials)

        wb = gc.open_by_key(self.gsheet_id)
        return wb

    def process_df(self, df):
        # general data
        opening_balance, df = self.item_calculator(
            df, 'GL DESC', 'C&S Opening Balances')
        grant_income, df = self.item_calculator(
            df, 'GL DESC', 'C&S College Grant')
        membership, df = self.item_calculator(
            df, 'GL DESC', 'C&S Membership Fee Income')
        income, df = self.item_calculator(df, 'GL DESC', 'C&S Event Income')
        code_uc, df = self.item_calculator(df, 'CC', 'UC')
        outgoings, df = self.item_calculator(df, 'CC', 'NC')

        # value by grant
        index = df['CC'] == 'GC'
        grouped = df[index].groupby('GL CODE')['NET TOTAL'].sum()
        grant_dict = grouped.to_dict()
        grant_sums = {'grant_' + str(k): v for (k, v) in grant_dict.items()}
        df = df[~index]

        assert len(df) == 0, 'dataframe not empty'

        general = {
            'opening_balance': opening_balance,
            'grant_income': grant_income,
            'membership': membership,
            'general_income': income,
            'code_UC': code_uc,
            'outgoings': outgoings
        }
        output = {**general, **grant_sums}

        return output

    @staticmethod
    def item_calculator(dataframe, key, value):
        index = dataframe[key] == value
        item = abs(dataframe[index]['NET TOTAL'].sum())
        new_df = dataframe[~index]
        return item, new_df

    def update_sheet(self):
        # df dictionary summary
        output = self.process_df(self.df)

        # ghseet handle
        gsheet = self.authen_spreadsheet()

        # update date
        sht = gsheet.worksheet('Latest_Statement')
        sht.update_acell('D1', self.date)

        # update items
        cell_list = sht.range('A2:B' + str(len(output)+1))
        keys, vals = list(output.keys()), list(output.values())
        for count, cell in enumerate(cell_list[::2]):
            cell.value = keys[count]
        for count, cell in enumerate(cell_list[1::2]):
            cell.value = vals[count]

        # Update in batch
        sht.update_cells(cell_list)

if __name__ == '__main__':
    AnalyseStatement('input.yml')
