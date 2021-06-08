import os
import pdb

import pandas as pd
from psycopg2 import  sql
from openpyxl import load_workbook


from database_utils import create_table, get_connection
from file_utils import data_dir

FILENAME_CSV = 'WoON2018energie_e_1.0.csv'
FILENAME_XLSX = 'WoON2018energie_e_1.0 met labels.xlsx'
TABLE_NAME = 'woon_2018_energie'
path_csv = os.path.join(data_dir, FILENAME_CSV)
path_xlsx = os.path.join(data_dir, FILENAME_XLSX)

load_statement = sql.SQL("COPY {table_name} FROM %s WITH DELIMITER AS ';' NULL AS ' ' CSV HEADER;")

def sanitize_column_name(column_name):
	# TODO: anything else? Maybe make this a general
	# database util.
	return column_name.replace('.', '_')

def main():

	try:
		with open(path_csv, 'r') as file:
			header = file.readline().strip()
			column_names = header.split(';')
	except FileNotFoundError:
		print(f"Error: WoON survey data file not found.\nExpected file at {path}.")
		return

	n_columns = len(column_names)
	columns = [(sanitize_column_name(column_name), 'text') for column_name in column_names]


	print('Creating table...')
	create_table(TABLE_NAME, columns)

	try:
		print('Reading in Excel file...')
		wb = load_workbook(filename=path_xlsx, read_only=True)
	except FileNotFoundError:
		print(f"Error: WoON survey data file not found.\nExpected file at {path_xlsx}.")
		return

	ws = wb.active

	# we skip the header
	rows = ws.rows
	header = next(rows)

	def sanitize_woon_values(value):
		if value == '#NULL!':
			return None
		else:
			return value

	values = ', '.join(['%s'] * n_columns)

	connection = get_connection()
	cursor = connection.cursor()

	insert_statement = f'INSERT INTO {{table_name}} VALUES ({values})'
	statement = sql.SQL(insert_statement).format(table_name=sql.Identifier(TABLE_NAME))

	i = 0
	for row in rows:
		entry = []
		for cell in row:
			entry.append(sanitize_woon_values(cell.value))
		cursor.execute(statement, entry)
		# print(entry)
		# return
		i += 1
		print(i)

	wb.close()
	cursor.close()
	connection.commit()
	connection.close()

	return

	pdb.set_trace()


	# TODO: make this idempotent somehow?
	statement = load_statement.format(table_name=sql.Identifier(TABLE_NAME))
	try:
		print("Loading WoON survey data...")
		cursor.execute(statement, (path_csv,))
		print("Committing...")
		cursor.close()
		connection.commit()
		connection.close()
		print("Done.")
	except UndefinedFile:
		print(f"Error: WoON survey data file not found.\nExpected file at {path}.")

if __name__ == '__main__':
	main()