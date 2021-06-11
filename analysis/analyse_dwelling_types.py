import os
import pprint
import sys

import pandas as pd

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_utils import get_connection

cursor = get_connection().cursor()
pp = pprint.PrettyPrinter(indent=4)

def energy_labels():
	# Note: alle 'W'-buildings have an assigned gebouwtype
	energy_label_query = "SELECT gebouwtype, gebouwsubtype, COUNT(gebouwtype) FROM energy_labels WHERE gebouwklasse = 'W' GROUP BY gebouwtype, gebouwsubtype"
	print("Querying energy labels...")
	cursor.execute(energy_label_query)
	energy_label_results = cursor.fetchall()
	pp.pprint(energy_label_results)

def bag():
	bag_query = "SELECT woningtype, COUNT(woningtype) FROM bag GROUP BY woningtype"
	print("\nQuerying BAG...")
	cursor.execute(bag_query)
	bag_results = cursor.fetchall()
	pp.pprint(bag_results)

def woon():
	woon_query = "SELECT vormwo, vorm_eg5, vorm_mg2, SUM(ew_huis) from woon_2018_energie GROUP BY vormwo, vorm_eg5, vorm_mg2"
	# WoON:
	# - vormwo (Type woning):
	#	1: eengezins
	#	2: meergezins
	# - vorm_eg5 (Type eengezinswoning)
	#	1: vrijstaande woning
	#	2: 2 onder 1 kap
	#	3: rijwoning hoek
	#	4: rijwoning
	# - vorm_mg2 (Type meergezinswoning)
	#	1: appartement met 1 woonlaag
	#	2: appartement met meerdere woonlagen
	type_lookup = {
		('1', '1', None): 'eengezins vrijstaande woning',
		('1', '2', None): 'eengezins 2 onder 1 kap',
		('1', '3', None): 'eengezins rijwoning hoek',
		('1', '4', None): 'eengezins rijwoning',
		('2', None, '1'): 'meergezins appartement met 1 woonlaag',
		('2', None, '2'): 'meergezins appartement met meerdere woonlagen'
	}
	print("\nQuerying WoON...")
	cursor.execute(woon_query)
	woon_results = cursor.fetchall()
	for vormwo, vorm_eg5, vorm_mg2, sum_huis in woon_results:
		print(f'{type_lookup[(vormwo, vorm_eg5, vorm_mg2)]}: {round(sum_huis)}')

def matrix():
	matrix_query = "SELECT gebouwtype, woningtype, COUNT(*) FROM bag, energy_labels WHERE bag.vbo_id = energy_labels.vbo_id AND woningtype != '' AND gebouwtype IS NOT NULL GROUP BY gebouwtype, woningtype"
	print('\nQuering Energy Labels - BAG matrix')
	cursor.execute(matrix_query)
	df = pd.DataFrame(cursor.fetchall(), columns = ['energy_label_types', 'bag_types', 'count'])
	df = df.pivot_table(index='energy_label_types', columns='bag_types', values='count', fill_value=0)

	current_dir = os.path.dirname(os.path.realpath(__file__))
	filename = 'analyse_dwelling_types_matrix.csv'
	path = os.path.join(current_dir, filename)
	print('Writing to file...')
	df.to_csv(path)

def main():
	energy_labels()
	bag()
	woon()
	matrix()

if __name__ == '__main__':
	main()
