from functools import reduce
import os
import string
import sys

from file_utils import data_dir
from WoON_load import sanitize_column_name

FILENAME = 'WoON2018energie_e_1.0.csv'
path = os.path.join(data_dir, FILENAME)

# via https://stackoverflow.com/a/48984697/7770056
def from_excel(chars):
	return reduce(lambda r, x: r * 26 + x + 1, map(string.ascii_uppercase.index, chars.upper()), 0)

def get_postgres_column_name(column_names, excel_column):
	return sanitize_column_name(column_names[from_excel(excel_column) - 1])

def main():

	try:
		with open(path, 'r') as file:
			header = file.readline().strip()
			column_names = header.split(';')
	except FileNotFoundError:
		print(f"Error: WoON survey data file not found.\nExpected file at {path}.")
		return

	if len(sys.argv) > 1:
		print(get_postgres_column_name(column_names, sys.argv[1]))
	else:
		while True:
			column_input = input("Excel column ('QUIT' to quit): ")
			if column_input.lower() in ['quit', 'quit()', 'exit', 'exit()']:
				break
			print(get_postgres_column_name(column_names, column_input))

if __name__ == '__main__':
	main()
