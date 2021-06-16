import os
import sys
import csv

from psycopg2.errors import UndefinedFile
from psycopg2 import sql

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from database_utils import get_connection, table_empty
from file_utils import data_dir


FILE_NAME_IN = 'CBS_PC6_2019_Publicatiefile_Energie_postcode6_2019.csv'
FILE_NAME_OUT = 'CBS_PC6_2019_Publicatiefile_Energie_postcode6_2019_fixed.csv'
TABLE_NAME = 'cbs_pc6_2019_energy_use'

# note: '''' means: use the character ' as quote character.
# It is escaped by the preceding ' and then included in ' ', hence the 4 ''''.
load_statement = sql.SQL("COPY {dbname} FROM %s WITH DELIMITER AS ';' NULL AS '' QUOTE '''' CSV HEADER;")


def main():

	if not table_empty(TABLE_NAME):
		print(f"Table '{TABLE_NAME} already populated, skipping loading of new records")
		return

	path_in = os.path.join(data_dir, FILE_NAME_IN)
	path_out = os.path.join(data_dir, FILE_NAME_OUT)
	statement = load_statement.format(dbname=sql.Identifier(TABLE_NAME))

	with open(path_in) as infile:
		reader = csv.DictReader(infile, delimiter = ';')
		fieldnames = reader.fieldnames

		with open(path_out, 'w', newline='') as csv_file:
			fieldnames = fieldnames
			writer = csv.DictWriter(csv_file, fieldnames, delimiter=';')
			writer.writeheader()
			for row in reader:
				row.update({fieldname: value.strip() for (fieldname, value) in row.items()})
				row.update({fieldname: value.replace('.','') for (fieldname, value) in row.items()})
				writer.writerow(row)

	connection = get_connection()
	cursor = connection.cursor()

	try:
		print("Loading CBS energy use records, this might take a minute or so.")
		cursor.execute(statement, (path_out,))
		cursor.close()
		connection.commit()
		connection.close()
		print("Done.")
	except UndefinedFile:
		print(f"\nError: CBS energy use data file not found.\nExpected file at {path}.")

if __name__ == "__main__":
	main()
