import os
import sys

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_utils import get_connection
from energy_labels_utils import label_to_epi

def get_boundaries(cursor):

	boundaries_query = '''
	SELECT energieklasse, MIN(energieprestatieindex), AVG(energieprestatieindex), MAX(energieprestatieindex), COUNT(energieprestatieindex)
	FROM energy_labels
	WHERE
		gebouwklasse = 'W'
		AND
			(berekeningstype = 'EP'
			OR berekeningstype = 'EPA'
			OR berekeningstype = 'ISSO82.3, versie 3.0, oktober 2011')
		AND energieprestatieindex IS NOT NULL
	GROUP BY
		energieklasse
	ORDER BY
		energieklasse DESC
	'''

	# NOTE:
	# to get the cleanest boundaries, take only those with berekeningstype = 'EP' or 'EPA', since the other one has some outliers.

	cursor.execute(boundaries_query)
	results = cursor.fetchall()
	print(results)


def construct_labels_with_imputed_epi(cursor):
	query = '''
	SELECT
		bag.vbo_id, bag.pc6, bag.bouwjaar, bag.woningtype, berekeningstype, energieklasse, energieprestatieindex
	FROM
		energy_labels, bag
	WHERE
		energy_labels.vbo_id = bag.vbo_id
		AND energieklasse IS NOT NULL
	'''
	print('Executing query...')
	cursor.execute(query)

	print('Processing results...')
	filename = 'energy_labels_epi_imputed.csv'
	current_dir = os.path.dirname(os.path.realpath(__file__))
	path = os.path.join(current_dir, filename)
	with open(path, 'w') as file:

		header = ['pc6', 'bouwjaar', 'woningtype', 'epi_imputed']
		csv_header = ','.join(header)
		file.write(f'{csv_header}\n')

		i = 0

		for row in cursor:
			i += 1
			(vbo_id, pc6, bouwjaar, woningtype, berekeningstype, energieklasse, energieprestatieindex) = row

			if berekeningstype in ['EP','EPA', 'ISSO82.3, versie 3.0, oktober 2011']:
				epi_imputed = energieprestatieindex
			else:
				epi_imputed = label_to_epi(energieklasse)

			values = (pc6, str(bouwjaar), woningtype, str(epi_imputed))
			csv_row = ','.join(values)
			file.write(f'{csv_row}\n')

			if i % 10000 == 0:
				print(i)

def main():
	connection = get_connection()
	cursor = connection.cursor()
	# get_boundaries(cursor)
	construct_labels_with_imputed_epi(cursor)

if __name__ == "__main__":
	main()
