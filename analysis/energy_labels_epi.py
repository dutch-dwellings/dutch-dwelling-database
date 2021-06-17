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


def get_labels_with_imputed_epi_and_pc6_average(cursor):
	query = '''
	SELECT
	bag.bouwjaar, bag.woningtype, epi_imputed, q.epi_pc6_average
	FROM
		energy_labels, bag,
		(SELECT pc6, AVG(epi_imputed) as epi_pc6_average FROM energy_labels GROUP BY pc6) q
	WHERE
		energy_labels.vbo_id = bag.vbo_id
		AND energieklasse IS NOT NULL
		AND q.pc6 = bag.pc6
	'''

	# inspired by https://stackoverflow.com/a/22789702/7770056
	outputquery = f"COPY ({query}) TO STDOUT WITH CSV HEADER"

	current_dir = os.path.dirname(os.path.realpath(__file__))
	filename = 'energy_labels_epi_imputed_pc6_average.csv'
	path = os.path.join(current_dir, filename)
	with open(path, 'w') as f:
		print('Executing query... (this can take a minute or so)')
		cursor.copy_expert(outputquery, f)

def main():
	connection = get_connection()
	cursor = connection.cursor()
	# get_boundaries(cursor)
	get_labels_with_imputed_epi_and_pc6_average(cursor)

if __name__ == "__main__":
	main()
