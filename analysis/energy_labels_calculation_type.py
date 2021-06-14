import os
import sys

import pandas as pd

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_utils import get_connection

def calculation_type_per_inspection_year(cursor):
	query = "SELECT date_part('year', opnamedatum), berekeningstype, COUNT(berekeningstype) FROM energy_labels WHERE gebouwklasse = 'W' GROUP BY date_part('year', opnamedatum), berekeningstype"
	print("Executing calculation type query...")
	cursor.execute(query)
	print("Fetching results...")
	results = cursor.fetchall()
	print("Converting to DataFrame...")
	df = pd.DataFrame(results, columns=['year', 'type', 'count'])
	print("Pivoting DataFrame...")
	df = df.pivot_table(values='count', index='year', columns='type', fill_value=0)

	current_dir = os.path.dirname(os.path.realpath(__file__))
	filename = 'energy_labels_calculation_type.csv'
	path = os.path.join(current_dir, filename)
	print('Writing to file...')
	df.to_csv(path)

def main():
	connection = get_connection()
	cursor = connection.cursor()
	calculation_type_per_inspection_year(cursor)

if __name__ == '__main__':
	main()
