#!/usr/bin/env python
import argparse
import pandas as pd

parser = argparse.ArgumentParser(description='Analyse weekly statement')
parser.add_argument('excel_file', type=str,
                    help='weekly statement excel file')
args = parser.parse_args()
df = pd.read_excel(args.excel_file)

index = df['GL DESC'] == 'C&S Opening Balances'
opening_balance = -df[index]['NET TOTAL'].values[0]
df = df[~index]

index = df['GL DESC'] == 'C&S College Grant'
initial_grant = -df[index]['NET TOTAL'].values[0]
df = df[~index]

index = df['GL DESC'] == 'C&S Membership Fee Income'
membership = -df[index]['NET TOTAL'].sum()
df = df[~index]

index = df['CC'] == 'UC'
code_uc = df[index]['NET TOTAL'].sum()
df = df[~index]

index = df['CC'] == 'GC'
grouped = df[index].groupby(['GL Code']).sum()
print()
