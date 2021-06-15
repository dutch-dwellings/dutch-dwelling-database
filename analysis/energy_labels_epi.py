import os
import sys

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_utils import get_connection


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

def main():
	connection = get_connection()
	cursor = connection.cursor()
	get_boundaries(cursor)

if __name__ == "__main__":
	main()
